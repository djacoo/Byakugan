# Full-Stack Web Application — Working Standards

## What This Project Type Demands
Full-stack means owning the entire data flow, from database schema to UI pixel. With that ownership comes the responsibility to make deliberate architectural decisions at every layer. The most common failure mode is logic scattered across layers — business rules in UI components, presentation logic in SQL queries, validation only on the client. Discipline about where each piece of logic lives is the foundation of maintainability.

## Before Starting Any Feature
- Define the data model change (if any) first. Schema changes affect every layer.
- Determine the rendering strategy for the new page/feature: SSR, SSG, ISR, or CSR? This affects data fetching, caching, and SEO.
- Identify the authentication and authorization requirements: who can access this feature?
- Define the API contract (or Server Action signature) before building the UI that depends on it.
- Identify all states the UI must handle: loading, error, empty, and the data state. Design all four before building.

## Architecture Standards
- Types flow from the database outward: database schema → ORM types → API types → UI types. Do not define types independently at each layer.
- Business logic lives in the service layer or domain layer. Not in route handlers. Not in UI components.
- Validation happens on the server. Client-side validation is a UX convenience, not a security control.
- Server components fetch data directly from the database where applicable — no unnecessary HTTP roundtrips.
- Client components handle interactivity only. They should be leaf nodes in the component tree.
- Shared validation schemas (Zod, Valibot) are defined once and used on both client and server.

## How to Approach Any Task
1. If the feature involves a schema change: write and test the migration first.
2. Define the server-side data contract (API endpoint or Server Action) before building the UI.
3. Implement the server-side logic with tests.
4. Build the UI layer consuming the server contract. Test the UI independently with mocked server responses.
5. Integration test the full stack: real database, real HTTP, real browser.

## Non-Negotiable Rules
- Validation always runs on the server. Never trust client-provided data.
- Authentication checked before every server action or API call that touches private data.
- Sensitive data (secrets, PII beyond what is needed) never sent to the client.
- Database queries never executed from UI components or route handlers directly — through a service/repository layer.
- N+1 query patterns identified and resolved before merging.
- All environment variables validated at startup (missing required vars crash early, not silently).
- Client-side secrets (anything in the bundle) are not secret. Design accordingly.

## Rendering Strategy Decision
- **SSR**: authenticated pages, personalized content, SEO-critical dynamic content.
- **SSG**: content that changes rarely (docs, marketing). Build-time generation.
- **ISR**: content that changes but can be cached (product listings, news). Revalidation on a schedule.
- **CSR**: highly interactive, dashboard-style UI, behind authentication with no SEO requirement.
- Server Components (Next.js): default for any component that only renders data. Use Client Components only for interactivity.

## Database and Data Layer Standards
- ORM (Prisma, Drizzle, etc.) with fully typed queries. No raw SQL unless performance demands it, and it is reviewed separately.
- Connection pooling configured — especially critical for serverless deployments.
- Migrations are sequential and never edited after merging. Create a new migration to fix a previous one.
- No `SELECT *` in production queries. Select only needed fields.
- All queries that can return many rows are paginated or explicitly limited.

## Testing Standards
- Unit tests for service layer logic.
- Integration tests for database operations against a real test database.
- API tests for route handlers: success, validation failure, auth failure.
- E2E tests with Playwright for 5–10 critical user flows (auth, main feature, payment if applicable).
- Tests for migration: apply migration to a copy of the production schema, verify correctness.

## Definition of Done
- [ ] Schema migration written, tested, and applied to staging.
- [ ] Server-side validation implemented and tested.
- [ ] Authentication checked on all new server operations.
- [ ] N+1 queries absent (verify with query logging in development).
- [ ] All four UI states implemented: loading, error, empty, data.
- [ ] Sensitive data not sent to the client.
- [ ] Environment variables validated at startup.
- [ ] Integration tests cover the feature end-to-end.
- [ ] Feature works with JavaScript disabled for the SSR/SSG portions (progressive enhancement).
- [ ] Performance: no new unoptimized images or large bundle additions without justification.
