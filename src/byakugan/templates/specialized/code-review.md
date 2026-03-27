# Code Review — Working Standards

## Purpose
Code review is a quality gate and a knowledge-sharing mechanism. The goal is to catch real problems — bugs, security issues, design flaws — and to share context. It is not a performance review, a style debate, or an opportunity to rewrite the code the way you would have written it.

## Before Reviewing
- Read the PR description and linked issue. Understand the intent before judging the implementation.
- Understand the scope: bug fix, feature, refactor, or hotfix? Different standards apply.
- If the diff is >500 lines of non-generated code, ask the author to split it before reviewing.

## Severity Classification
Use these labels in every comment that requests a change:

- **[BLOCKER]** — Must be fixed before merge. Bugs, security issues, data corruption risk, incorrect behavior.
- **[MAJOR]** — Should be fixed before merge. Design problems, significant performance issues, missing test coverage for critical paths.
- **[MINOR]** — Can be fixed now or tracked as follow-up. Small improvements, readability, better naming.
- **[NIT]** — Purely stylistic. Author's discretion. Do not block on these.
- **[QUESTION]** — Seeking understanding, not requesting a change.
- **[SUGGESTION]** — An alternative worth considering. Not a request.

If a comment has no label, it is treated as a [MINOR].

## What to Review

### Correctness (highest priority)
- Does the code actually do what the PR description says?
- Are there edge cases not handled? (null/empty/zero, max values, concurrent access, large input)
- Is the logic correct? Walk through it with concrete test cases mentally.
- Are error paths handled, not just the happy path?
- Are off-by-one errors, operator precedence mistakes, or incorrect conditionals present?

### Security
- Is user input validated before use in queries, file paths, shell commands, or HTML output?
- Are secrets handled correctly? Not logged, not hardcoded, not sent to clients?
- Is authorization checked at the right level — not just route-level, but resource-level?
- Do new dependencies have known vulnerabilities?
- Are new attack surfaces introduced (endpoints, file uploads, external calls)?

### Tests
- Is new behavior covered by tests?
- Do the tests test behavior (observable outputs) rather than implementation details?
- Are error paths tested, not just the happy path?
- Would a realistic bug in this code cause at least one test to fail?

### Design
- Does each piece of code belong in the right layer or module?
- Is the abstraction appropriate? Not too broad (over-engineered), not too narrow (will need to change immediately)?
- Are there unintended couplings or circular dependencies introduced?
- Is this decision reversible, or does it create lock-in?

### Observability
- Are new operations logged with appropriate context?
- Are new failure modes observable (metrics, logs, alerts)?

## Writing Effective Comments

**Structure**: State the problem clearly. Explain why it is a problem. If you have a specific suggestion, provide it. If not, acknowledge that you are raising the concern without prescribing the solution.

**Good**: `[BLOCKER] This will throw a NullPointerException if the user has no orders. The orders list can be null for new accounts (see UserFactory line 42). Add a null check or initialize to an empty list at creation.`

**Bad**: `This is wrong.`

**Good**: `[SUGGESTION] An alternative to the switch statement here would be a dispatch map, which would make adding new cases O(1) and eliminate the fallthrough risk. Not blocking, just worth considering if this grows.`

**Bad**: `I would have done this differently.`

**Good**: `[QUESTION] I'm not following the logic in lines 88–103. What is the invariant that makes this safe? Could you add a comment explaining the intent?`

## Final Decision
- **Approve**: No blockers or majors. Minor issues documented. Trust the author to address or track them.
- **Request Changes**: One or more BLOCKERs or MAJORs that must be resolved.
- **Comment**: Questions or suggestions only. Not blocking the merge.

Do not leave a PR in indefinite "Request Changes" state. If blockers are resolved, approve or re-review promptly.

## Common Patterns to Catch

**Logic bugs**: equality vs. identity, signed/unsigned comparison, off-by-one, short-circuit operator confusion, float equality.

**Security**: SQL injection via concatenation, XSS via unescaped output, path traversal in file operations, SSRF in URL fetch, missing auth check on new endpoint, secrets in logs.

**Reliability**: uncaught exceptions in async code, no timeout on external calls, missing retry on transient failures, N+1 queries, unbounded list returns, connection/resource leaks.

**Maintainability**: magic numbers without names, commented-out code, misleading names, deep nesting, a function that does two things (the "and" in the name is a signal).
