# Rust — Working Standards

## Mindset
Rust makes correctness a compile-time property. When the borrow checker rejects your code, it has found a real problem — understand it, do not circumvent it. The correct response to a compiler error is to understand the ownership model, not to add `.clone()` or reach for `unsafe`. Write Rust that the compiler verifies, and earn the guarantees it provides.

## Before Writing Code
- Model ownership explicitly before writing. Who owns each piece of data? Who borrows it, and for how long?
- Decide the error handling strategy upfront: `anyhow` for applications, `thiserror` for libraries. Establish this at the project level.
- Determine whether the task requires `async`. If so, confirm the runtime (`tokio`) and ensure it is already established in the project. Do not introduce a second runtime.
- Identify what goes in a library crate vs. a binary crate if this is a new project.
- Check `Cargo.toml` for existing patterns and conventions before adding anything.

## How to Approach Any Task
1. Define the data structures and types first. Code structure in Rust follows data structure.
2. Write the public API signatures before the implementations.
3. Use `cargo check` continuously while developing. It is faster than `cargo build` and catches type errors early.
4. Run `cargo clippy -- -D warnings` before considering any code complete.
5. Run `cargo test` and verify all tests pass after every meaningful change.

## Code Standards
- Return `Result<T, E>` from all functions that can fail. Use `?` for propagation.
- Use `Option<T>` for values that may not exist. No sentinel values (`-1`, `""`, etc.).
- Document all public items with `///` doc comments. Run `cargo doc` and verify it renders correctly.
- Use `#[derive(Debug)]` on all types. Use `#[derive(Clone, PartialEq)]` when semantically appropriate.
- Prefer `&str` for function parameters that read strings. Accept `String` only when ownership is transferred.
- Use iterators and adaptors over manual indexed loops.
- Run `rustfmt` on all code. Non-negotiable.

## Hard Rules
- Never use `.unwrap()` in non-test code without a comment that proves the Option/Result cannot be the failure case.
- Never use `unsafe` without a `// SAFETY:` comment that explains why the invariants are upheld.
- Never have clippy warnings in submitted code (`-D warnings` in CI).
- Never introduce a dependency on a crate without evaluating maintenance status, license, and compile-time impact.
- Never block an async executor with synchronous I/O. Use `spawn_blocking` or async equivalents.
- Never ignore a `Result` with `let _ =` unless you have explicitly decided that failure is acceptable, and document why.

## Testing Standards
- Unit tests in `#[cfg(test)]` modules within the source files they test.
- Integration tests in `tests/`. These test the public API as a consumer would.
- Use `cargo nextest` for faster parallel test execution in CI.
- Enable sanitizers in CI: `RUSTFLAGS="-Z sanitizer=address"` for memory safety verification on nightly.
- Benchmark with `criterion` for performance-critical code. Never benchmark in debug mode.

## Definition of Done
- [ ] `cargo build` succeeds with zero warnings.
- [ ] `cargo clippy -- -D warnings` passes with zero issues.
- [ ] `cargo test` passes entirely.
- [ ] `cargo fmt --check` passes.
- [ ] No `.unwrap()` without a proven safety comment in production code.
- [ ] No `unsafe` without a `// SAFETY:` comment.
- [ ] All public items documented.
- [ ] `cargo doc` builds without warnings.
