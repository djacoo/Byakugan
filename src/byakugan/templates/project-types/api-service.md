# API Service — Working Standards

## What This Project Type Demands
An API is a public contract. Every endpoint you ship is a commitment to every client that uses it. Breaking that contract — even accidentally — causes real failures in production systems you do not control. Design for longevity. Be consistent. Document everything. Version deliberately.

## Before Starting Any Feature
- Write the API contract first: endpoint URL, HTTP method, request schema, response schema, all error cases. Get this reviewed before implementation.
- Confirm the versioning strategy for the change: is this additive (no version bump) or breaking (new version required)?
- Confirm authentication and authorization requirements: who can call this endpoint, and at what permission level?
- Identify whether the operation is idempotent. If not, design the idempotency key mechanism upfront.
- Confirm rate limiting strategy for the new endpoint.

## API Design Standards
- Resources are nouns, plural, kebab-case: `/users`, `/order-items`. Actions that do not fit CRUD use `POST` with a verb as the final segment: `POST /orders/{id}/cancel`.
- Consistent response envelope across all endpoints: `{ "data": ... }` for success, `{ "errors": [...] }` for failure.
- Consistent error format: every error object has `code` (machine-readable), `message` (human-readable), `field` (for validation errors).
- Return correct HTTP status codes. 200 for success, 201 for creation, 204 for no-content, 400 for bad input, 401 for unauthenticated, 403 for unauthorized, 404 for not found, 409 for conflict, 422 for validation, 429 for rate limit, 500 for server error.
- Paginate all list endpoints. Cursor-based pagination for large or frequently changing data sets. Return `has_more`, `cursor`, and optionally `total`.

## How to Approach Any Task
1. Update or create the OpenAPI spec for the new endpoint before writing implementation code.
2. Implement input validation at the routing/controller layer — reject invalid requests immediately with a 400/422 and a clear error message.
3. Implement the business logic in the service layer.
4. Write contract tests that verify the response matches the OpenAPI spec.
5. Write integration tests covering: success case, validation failure, auth failure, not-found, and at least one concurrency/conflict scenario where relevant.

## Non-Negotiable Rules
- The OpenAPI spec is the source of truth. It must stay in sync with the implementation.
- Every endpoint is authenticated unless explicitly marked public in both the spec and the code.
- Authorization is checked at the resource level, not just the route level. A user must not access another user's resources by manipulating IDs.
- Internal error details (stack traces, DB error messages, internal IDs) never appear in API error responses in production.
- Outbound calls from the service all have configured timeouts.
- Sensitive data (PII, tokens, passwords) never appears in logs, URLs, or error responses.
- Backward-incompatible changes require a new API version. Never break existing clients silently.

## Versioning Rules
- Additive changes (new optional fields, new endpoints) are non-breaking. No version bump needed.
- Breaking changes (removed fields, changed types, removed endpoints, changed behavior) require a new major version.
- Deprecated endpoints: add `Deprecation` and `Sunset` response headers. Support for at least 6 months after deprecation announcement.
- Old versions are maintained until the `Sunset` date. No silent removal.

## Observability Standards
Every request logs: `request_id`, `method`, `path`, `status_code`, `duration_ms`, `user_id` (if authenticated).
Expose metrics: requests/sec, error rate, p50/p95/p99 latency per endpoint.
Health endpoints: `GET /health` (liveness), `GET /ready` (readiness with dependency checks).

## Definition of Done
- [ ] OpenAPI spec updated and in sync with implementation.
- [ ] Input validation at the boundary — invalid input returns 400/422 with specific error messages.
- [ ] Authentication checked on the new endpoint.
- [ ] Authorization checked at the resource level.
- [ ] Pagination implemented if the endpoint returns a list.
- [ ] Rate limiting applied.
- [ ] Internal errors not leaked in responses.
- [ ] Outbound calls have timeouts.
- [ ] Contract tests verify response against OpenAPI spec.
- [ ] Integration tests cover success, validation failure, and auth failure.
- [ ] No sensitive data in logs.
