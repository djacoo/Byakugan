# Web Backend — Working Standards

## What This Project Type Demands
A backend service is a contract with its clients. Correctness and reliability come first. Security is non-negotiable. Observability is not optional — you will need to diagnose issues in production without touching the running system. Design every component to be understandable at 3am under pressure.

## Before Starting Any Feature
- Define the API contract (request/response shape, status codes, error format) before writing any code. Clients depend on this.
- Identify the authentication and authorization requirements: who can call this? What can they do? Where is that checked?
- Identify all external dependencies this feature introduces (DB, cache, external API, queue). Plan for each one's failure mode.
- Determine if any operation is long-running or should be async. Design for that upfront.
- Check whether the operation is idempotent. If not, consider how clients safely retry.

## Architecture Standards
- Strict layering: HTTP handler → service/use-case → repository → infrastructure.
- Business logic lives in the service/use-case layer. Never in HTTP handlers. Never in repositories.
- Repositories abstract all data access. The service layer never writes SQL or queries a DB directly.
- Cross-cutting concerns (auth, logging, rate limiting) are middleware, not scattered in handlers.
- Configuration comes from environment variables. No hardcoded values for anything that differs between environments.

## How to Approach Any Task
1. Define the contract (endpoint, input schema, output schema, error cases) before implementing.
2. Implement validation at the HTTP boundary. Reject invalid input immediately with a 400/422 and clear message.
3. Implement the service logic. Keep it pure where possible — logic that only transforms data is easy to test.
4. Implement the repository or infrastructure integration. Test this layer against a real test database.
5. Write integration tests that test the full HTTP request/response cycle before considering the feature done.

## Non-Negotiable Rules
- Validate and sanitize all input at the HTTP boundary. Trust nothing from the outside.
- Use parameterized queries. No SQL string concatenation with user data. Ever.
- Check authentication before authorization. Check authorization before every operation, not just at the route level.
- Never log sensitive data: passwords, tokens, credit card numbers, PII, session cookies.
- Never return stack traces or internal error details to clients in production.
- Paginate all list endpoints. Never return an unbounded list.
- Set timeouts on all outbound HTTP calls. No call to an external service runs forever.
- Rate-limit all public endpoints. Auth endpoints get stricter limits.

## Observability Standards
Every request must produce:
- A structured log entry with: `request_id`, `method`, `path`, `status_code`, `duration_ms`, `user_id` (if authenticated).
- Errors logged with full context (request ID, relevant IDs, the error itself) at the appropriate level.
- Never log at `ERROR` for expected conditions (404, validation errors). Use `WARN` or `INFO`.

The service must expose:
- `GET /health` — liveness check (returns 200 if the process is running).
- `GET /ready` — readiness check (returns 200 only if DB, cache, and critical dependencies are reachable).

## Database Standards
- Use transactions for operations that must be atomic.
- Index all foreign keys and all columns used in `WHERE`, `ORDER BY`, or `JOIN` conditions.
- Never `SELECT *` in application code — select only the columns needed.
- Use migrations for all schema changes. Never modify a production schema manually.
- Use soft deletes (`deleted_at`) only when an audit trail is required. Hard delete otherwise.

## Definition of Done
- [ ] Input validation implemented at the HTTP boundary.
- [ ] Authentication and authorization checked for the new endpoint.
- [ ] Parameterized queries used — no raw SQL with user input.
- [ ] Errors do not leak internal details to clients.
- [ ] List endpoints are paginated.
- [ ] All outbound calls have timeouts.
- [ ] Structured logging in place for the new endpoint.
- [ ] `/health` and `/ready` endpoints return correct state.
- [ ] Integration tests cover success, validation failure, auth failure, and infrastructure failure cases.
- [ ] No sensitive data logged.
