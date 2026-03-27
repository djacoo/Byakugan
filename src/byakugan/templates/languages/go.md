# Go — Working Standards

## Mindset
Go is explicit, simple, and unforgiving about bad practices. There is one right way to do most things in Go, and the community has agreed on it. Do not import patterns from other languages. Write Go the Go way: handle every error, keep packages small, define interfaces where they are consumed, and use goroutines with clear ownership and lifetimes.

## Before Writing Code
- Check the existing package structure before adding anything. Go package design is load-bearing — do not break it.
- Determine where interfaces should live. In Go, interfaces are defined by the consumer, not the producer. If you are adding an interface for a type you control, it likely belongs in the package that needs it.
- Establish the error handling strategy for this package: `fmt.Errorf` with `%w` wrapping, sentinel errors, or custom error types? Match what already exists.
- Confirm all I/O-performing functions accept `context.Context` as the first parameter. Add it now if missing, not later.
- Determine goroutine ownership: who creates, who cancels, who waits? Write this down before writing code.

## How to Approach Any Task
1. Write the package-level documentation and exported function signatures first.
2. Define types and interfaces before implementing functions.
3. Implement. Handle every error. Wrap errors with context using `fmt.Errorf("operation: %w", err)`.
4. Write tests alongside the code. Run `go test -race ./...` to check for data races.
5. Run `go vet ./...` and `golangci-lint run` before considering the work done.

## Code Standards
- Handle every error return. Assign to `_` only with a comment explaining the decision.
- Wrap errors with context that explains what was being attempted, not just what failed.
- Use `defer` for cleanup immediately after acquiring a resource — not later in the function.
- Export only what is part of the public API. Start with everything unexported; open up deliberately.
- Keep packages focused. If a package has more than one clear responsibility, split it.
- Use `go fmt` (non-negotiable). Use `goimports` for import organization.
- Use `context.Context` as the first parameter of every function that performs I/O or may block.

## Hard Rules
- Never ignore an error return without a comment.
- Never use `panic` in library code. Reserve it for truly unrecoverable programmer errors in main.
- Never start a goroutine without knowing how and when it will stop.
- Never share memory between goroutines without synchronization (mutex, channel, or atomic).
- Never use `init()` in library packages — it runs implicitly and creates hidden coupling.
- Never use global mutable variables in library code.
- Never write `time.Sleep` as a synchronization mechanism.

## Testing Standards
- Use the standard `testing` package. Use `testify/assert` and `testify/require` for clearer assertions.
- Use table-driven tests for any function with more than two interesting input scenarios.
- Use `t.Run` for subtests. Every subtest is independently runnable.
- Always run `go test -race ./...` in CI. Race conditions are real bugs.
- Integration tests that require real infrastructure (DB, cache) are in a separate build tag: `//go:build integration`.
- Benchmark with `func BenchmarkXxx(b *testing.B)`. Never benchmark in non-release build mode.

## Definition of Done
- [ ] `go build ./...` succeeds with zero errors.
- [ ] `go vet ./...` passes with zero issues.
- [ ] `golangci-lint run` passes.
- [ ] `go test -race ./...` passes with zero failures and zero race conditions.
- [ ] `gofmt -l .` reports no files needing formatting.
- [ ] No ignored error returns without comments.
- [ ] No goroutine leaks (verify with `goleak` in tests if goroutines are created).
- [ ] All exported symbols have doc comments.
- [ ] New behavior covered by tests.
