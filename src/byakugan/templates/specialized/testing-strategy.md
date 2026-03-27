# Testing Strategy — Working Standards

## Purpose
Tests are the mechanism that lets you change code without fear. A test suite that passes gives you confidence that the system still behaves correctly. Tests that are brittle (break when you refactor), slow (hours to run), or wrong (pass when the system is broken) give false confidence and slow down development.

## The Testing Hierarchy

```
E2E / Integration Tests     ← few, slow, test whole flows, catch wiring bugs
Integration Tests           ← moderate, test module boundaries with real dependencies
Unit Tests                  ← many, fast, test logic in isolation
```

Optimize the shape: many fast unit tests, some integration tests, few E2E tests. Inverting the pyramid (many E2E, few unit) creates a slow, fragile suite.

## Before Writing Any Test
- Identify what behavior you are verifying, not what code you are covering.
- Write the test from the perspective of a caller — what does the caller observe, not what does the implementation do?
- Identify the dependencies: real, fake, or stubbed? See the rules below.

## Unit Testing Standards
- Test one thing per test. One logical assertion per test case. Multiple independent assertions make failures hard to diagnose.
- Test names describe the scenario and expectation, not the function name: `returns_empty_list_when_no_active_users`, not `test_get_users`.
- Arrange, Act, Assert structure. No logic in the test itself — tests are not programs.
- Setup code in fixtures/beforeEach, not duplicated in every test.
- Each test is independent. No test depends on another test's side effects or state.
- Tests run fast: no sleep(), no file I/O, no real network in unit tests.

## Integration Testing Standards
- Test with real infrastructure for I/O boundaries: real database, real cache, real message queue.
- Use test containers or a dedicated test database, not a shared or production environment.
- Each test cleans up its own data. No test leaves state that affects another test.
- Integration tests verify the wiring (does the query produce the right SQL? does the response serialize correctly?), not the business logic (that is for unit tests).

## E2E Testing Standards
- Cover only the 5–10 most critical user flows: login, main feature, purchase, account creation.
- Test flows from the user's perspective: click, fill, submit, verify visible outcome.
- Do not test every edge case in E2E — edge cases belong in unit tests.
- E2E tests must be reliable. A flaky E2E test is deleted, fixed, or quarantined immediately.
- Run E2E on every merge to main and before every production deploy.

## Test Doubles — When to Use Each
- **Real implementation**: always preferred. Use when the real thing is fast and controllable (in-memory DB, pure functions).
- **Fake**: a lightweight real implementation (in-memory repository instead of DB). Use for data stores in unit tests.
- **Stub**: returns predefined values. Use for external services, clocks, random number generators.
- **Mock**: verifies that a specific call was made with specific arguments. Use sparingly — only for testing side effects (email sent, event published). Avoid mocking your own domain logic.

**Do not mock**: the system under test, your own domain model, or anything whose real implementation is fast and deterministic.

## What to Test vs. What Not to Test
**Test**: all business logic, all validation rules, all error paths, all edge cases (null, empty, max, boundary conditions), all documented behaviors, all security-critical code.

**Do not test**: framework internals, third-party library behavior, trivial getters/setters with no logic, implementation details that can change without changing behavior.

## Flaky Tests
A flaky test (sometimes passes, sometimes fails without code changes) is worse than no test. It destroys confidence in the test suite.

**Causes and fixes**:
- Time-dependent: mock or fix the clock.
- Order-dependent: each test must clean up and not depend on other tests.
- Network-dependent: stub external calls.
- Race condition: fix the concurrency issue in the code, or make the test wait properly.

**Policy**: identify flaky tests immediately. Fix them or delete them. Never leave them and `retry` your way to green CI.

## Coverage
Coverage is a floor, not a ceiling. 80% coverage that misses all error paths is worse than 60% coverage that hits every business rule and every failure mode.

- Use coverage to find gaps, not to hit a number.
- If a line is not covered, ask: is this reachable? If yes, write a test. If no, delete the code.
- Critical business logic and security code should have near-100% branch coverage.

## Definition of Done for Tests
- [ ] New behavior covered by at least one test.
- [ ] Error paths and edge cases tested.
- [ ] Tests are in the right layer (unit vs. integration vs. E2E).
- [ ] Tests pass in CI with no flakiness.
- [ ] No `sleep()` in tests.
- [ ] Each test is independent — can run alone in any order.
- [ ] Test names describe behavior, not implementation.
