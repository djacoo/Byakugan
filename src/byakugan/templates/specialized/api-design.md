# API Design — Working Standards

## The Design-First Rule
Design the API before implementing it. Write the OpenAPI spec or GraphQL schema first, share it with consumers, and get feedback before writing a single line of implementation code. It is cheap to change a spec. It is expensive to migrate clients after a shipped API.

## Before Designing Any Endpoint
- Identify the consumers: who calls this? What do they need? Design for the consumer's needs, not the internal data model.
- List the operations the consumer needs to perform — not which database operations the backend supports.
- Determine authentication and authorization requirements upfront.
- Confirm the versioning implication: is this a new endpoint (additive) or a change to an existing one (potentially breaking)?

## REST Design Standards

### Resource Naming
- Nouns, plural, kebab-case: `/users`, `/order-items`, `/payment-methods`.
- No verbs in URLs. `GET /users` not `GET /getUsers`.
- One level of nesting maximum: `/orders/{id}/items`. Deeper nesting goes flat with query params.
- Actions that do not map to CRUD: `POST /orders/{id}/cancel`, `POST /documents/{id}/publish`. The verb is the last path segment.

### HTTP Methods
- `GET`: read. No side effects. Safe and idempotent.
- `POST`: create resource or trigger action. Not idempotent (unless using idempotency keys).
- `PUT`: full replacement of a resource. Idempotent.
- `PATCH`: partial update. Provide only the fields being changed.
- `DELETE`: remove. Idempotent.

### Status Codes
Return the specific, correct code — not `200 OK` for everything and an error field in the body.

| Code | Meaning |
|------|---------|
| 200 | Success with response body |
| 201 | Created (POST). Include `Location` header pointing to the new resource |
| 202 | Accepted — async operation started |
| 204 | Success with no response body (DELETE, some PUT/PATCH) |
| 400 | Bad request — malformed syntax, invalid JSON |
| 401 | Unauthenticated — no valid credentials |
| 403 | Forbidden — valid credentials, insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict — duplicate, state precondition not met |
| 422 | Validation error — correct syntax, semantic problem |
| 429 | Rate limited — include `Retry-After` header |
| 500 | Server error — do not expose internal details |

### Response Envelope
Consistent across all endpoints:
```
Success (single):  { "data": { ... } }
Success (list):    { "data": [...], "meta": { "cursor": "...", "has_more": true } }
Error:             { "errors": [{ "code": "VALIDATION_ERROR", "message": "...", "field": "email" }] }
```

Every response (success and error) includes a `meta` object with `request_id` for traceability.

### Pagination
- Cursor-based for large or frequently changing datasets: `?cursor=<opaque>&limit=20`.
- Offset-based only for small, stable datasets: `?page=2&per_page=20`.
- Always include `has_more` (boolean) and `cursor` (next page) in the list `meta`.
- Default page size is defined and documented. Maximum page size is enforced.

### Filtering, Sorting, Field Selection
- Filter with query params: `?status=active&user_id=123`.
- Sort with a `sort` param, prefix `-` for descending: `?sort=-created_at`.
- Field selection for sparse responses: `?fields=id,name,email`.

## Versioning

### Additive (non-breaking) — no version bump needed
- New optional fields in responses.
- New optional query parameters.
- New endpoints.

### Breaking — requires new major version
- Removing or renaming fields.
- Changing field types.
- Changing required fields.
- Changing HTTP status codes or error formats.
- Removing endpoints.

### Version strategy
URL versioning: `/v1/users`, `/v2/users`. The version is part of the contract, not a header.
Deprecated versions: add `Deprecation` and `Sunset` headers. Support for minimum 6 months after sunset announcement.

## Error Design
Every error response must tell the caller:
1. What went wrong (`code`: machine-readable, stable, documented).
2. In human terms, what the problem is (`message`: clear, actionable).
3. Which field caused the problem, if applicable (`field`).

Never include stack traces, database errors, internal paths, or any implementation detail in error responses in production.

## Documentation Standards
- OpenAPI spec is the source of truth. It must be in sync with the running implementation.
- Every endpoint has: description, all parameters with types and constraints, all response codes with example bodies, authentication requirement.
- Provide a quickstart guide with working `curl` examples.
- Provide a changelog documenting all changes per version.
- Interactive docs (Swagger UI, Scalar, Redoc) available in non-production environments.

## Security Checklist for Every New Endpoint
- [ ] Authentication required (or explicitly marked as public with justification).
- [ ] Authorization checked at resource level (not just route level).
- [ ] All input validated and sanitized.
- [ ] Rate limiting applied.
- [ ] Internal errors not leaked in responses.
- [ ] Sensitive data not in URL (use request body or headers).
- [ ] Idempotency key supported if the operation is non-idempotent and retryable.
