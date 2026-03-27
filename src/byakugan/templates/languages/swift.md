# Swift — Working Standards

## Mindset
Swift's type system and null safety are there to make entire categories of bugs impossible. Work with them — not around them. A force unwrap (`!`) is a bet that you will never be wrong; you will eventually lose that bet. Design for value semantics, structured concurrency, and compile-time safety. Code should express intent, not mechanics.

## Before Writing Code
- Determine the architecture pattern in use: MVVM, MVC, TCA, or other. Match existing conventions strictly.
- Identify every async boundary: network, disk, database, hardware. These must use `async/await`.
- Establish data ownership: which types are value types (`struct`), which require reference semantics (`class`, `actor`)?
- Identify all optionals at the boundary with external data (JSON, user input, OS APIs). Plan how each is handled.
- Confirm minimum OS target. It determines which APIs and concurrency features are available.

## How to Approach Any Task
1. Design the data model first: `struct`, `enum` with associated values, `actor` for shared mutable state.
2. Write the protocol (interface) before the implementation for any component that will be tested or mocked.
3. Implement using structured concurrency: `async/await` + `Task`, `TaskGroup` for concurrent work.
4. Mark all UI-updating code with `@MainActor`. Verify with the compiler, not with assumptions.
5. Test the logic layer independently from the UI and from the framework.

## Code Standards
- `let` by default. `var` only when mutation is required and unavoidable.
- Use `guard let`/`guard else` for early exit and unwrapping. Avoid deeply nested `if let` chains.
- Use `enum` with associated values for state machines. Do not model state as multiple optional properties.
- Use `Result<Success, Failure>` for synchronous failable operations with typed errors.
- Use `async throws` for asynchronous failable operations.
- Use `actor` for classes that manage shared mutable state across concurrent contexts.
- Accessibility: use `@Sendable` where needed to allow safe concurrency.
- Format with `swift-format`. Enforce with SwiftLint in CI.

## Hard Rules
- Never force-unwrap (`!`) without a comment proving the value cannot be nil at that point.
- Never use `try!` in production code.
- Never call `DispatchQueue.main.async` when `@MainActor` or `await MainActor.run` is the right tool.
- Never ignore the result of a `Task` that can fail without explicitly handling the error.
- Never retain a `self` strongly in a closure stored by `self` — use `[weak self]`.
- Never mix Combine and Swift Concurrency in the same data flow without a clear boundary.
- Never bypass the compiler's actor isolation warnings — address them properly.

## Testing Standards
- Use `XCTest` for unit tests. Test `ViewModel` and service layer independently from UI.
- Use dependency injection (protocols + mocks) to make every meaningful unit testable without network or disk.
- Use `async` test methods and `await` assertions for all async code.
- Use `XCUITest` only for high-value user flows — it is slow and fragile.
- Run tests in CI on every push. `xcodebuild test` must pass cleanly.

## Definition of Done
- [ ] Builds with zero warnings.
- [ ] All tests pass (`xcodebuild test` clean).
- [ ] SwiftLint passes with zero violations.
- [ ] No force unwraps (`!`) without a justified comment.
- [ ] No `try!` in production code.
- [ ] All async code uses Swift Concurrency (no raw `DispatchQueue` for new code).
- [ ] `@MainActor` applied to all UI-updating code.
- [ ] New behavior covered by unit tests.
