# Performance Optimization — Working Standards

## The Prime Directive
Measure before you optimize. Every optimization decision must be backed by data from a profiler or a benchmark on realistic input. Code changed for performance without measurement is either unnecessary churn or a guess that happens to be right. Both are unprofessional.

The sequence is always: **Measure → Profile → Identify bottleneck → Optimize → Measure again**.

## Before Optimizing Anything
- Establish a baseline measurement with realistic data and realistic load. Document it.
- Identify the actual bottleneck. It is almost never where you intuit it is.
- Define the performance target: what is "fast enough"? Without a target, optimization is endless.
- Determine the cost of the optimization: code complexity, correctness risk, and maintenance burden. Is it worth the gain?

## How to Profile
- **Backend/server**: use the language's profiler (`cProfile`/`py-spy` for Python, `pprof` for Go, `async-profiler` for JVM, Chrome DevTools for Node). Look at CPU flame graphs and wall clock time separately.
- **Database**: run `EXPLAIN ANALYZE` (PostgreSQL) or equivalent. Look for sequential scans on large tables, nested loop joins on large datasets, and sort operations without indexes.
- **Frontend**: Chrome DevTools Performance tab. Look at long tasks (>50ms), layout recalculations, and paint events.
- **Memory**: use a heap profiler. Look for monotonically growing allocations, large retained object trees, and unexpected object counts.

## Common Performance Problems and Fixes

### N+1 Queries
**Symptom**: query count scales linearly with list size. Profiling shows hundreds of near-identical queries.
**Fix**: eager-load associations. Use `JOIN` or the ORM's eager-loading mechanism. Load all needed data in the minimum number of queries.

### Missing Database Index
**Symptom**: `EXPLAIN ANALYZE` shows a sequential scan on a large table.
**Fix**: add an index on the queried column. For multi-column filters, create a composite index with columns in selectivity order.

### Large Payload / Over-fetching
**Symptom**: API responses are large; much of the data is not used by the caller.
**Fix**: return only the fields the caller needs. Add field selection or use a more specific endpoint.

### Synchronous I/O in Async Context
**Symptom**: event loop blocked; all other requests stall while one request reads a file or calls a DB synchronously.
**Fix**: use async I/O. Move blocking work to a thread pool with `spawn_blocking` / `to_thread` equivalents.

### Repeated Expensive Computation
**Symptom**: the same expensive result is computed on every request despite the inputs not changing.
**Fix**: cache the result. Define the cache key from the inputs, set an appropriate TTL, and implement an invalidation strategy.

### Inefficient Algorithm (Algorithmic Complexity)
**Symptom**: operation time grows non-linearly as input size grows (quadratic, cubic).
**Fix**: replace with a more efficient algorithm or data structure. Switch from O(n²) to O(n log n) or O(n) where inputs can be large.

### Memory Leak
**Symptom**: memory grows continuously during a long session, never returns to baseline.
**Fix**: identify what is being retained using a heap profiler. Common causes: event listeners not removed, caches without eviction, circular references, global collections that only grow.

## Caching Strategy
Before adding a cache:
- Confirm the data is actually expensive to generate (measured, not assumed).
- Define the cache key completely — all inputs that affect the output must be in the key.
- Define the invalidation strategy — TTL, event-driven, or manual. No cache without a defined invalidation strategy.
- Define the failure mode — what happens when the cache is unavailable? The system must degrade gracefully.

Cache layers (use the most specific one that works):
1. In-process cache: fastest, limited to one process instance.
2. Distributed cache (Redis): shared across instances, survives process restart.
3. HTTP cache (CDN, browser): for public, idempotent responses.

## Frontend-Specific Optimization
- Eliminate render-blocking resources: defer non-critical JS, preload critical fonts and images.
- Reduce JavaScript bundle size: analyze with bundle visualizer, code-split at route boundaries.
- Eliminate Cumulative Layout Shift: set explicit dimensions on images and dynamic content.
- Virtualize lists with 50+ items.
- Use `transform` and `opacity` for animations (compositor thread). Avoid properties that trigger layout.

## Backend-Specific Optimization
- Connection pooling for databases. Never create a new connection per request.
- Paginate all list queries. No unbounded `SELECT *`.
- Use `SELECT only_needed_columns` — never `SELECT *` in production queries.
- Batch database operations: insert/update 1000 rows in one statement, not 1000 statements.
- Use async I/O for concurrent outbound requests: `await Promise.all(...)`, `asyncio.gather(...)`.

## Documenting Optimizations
Every performance optimization must include a comment that explains:
1. What was measured (the baseline).
2. What the bottleneck was.
3. Why this specific approach was chosen.
4. What the improvement was after the fix.

Without this documentation, future maintainers will revert the optimization or not understand why a seemingly complex pattern exists.
