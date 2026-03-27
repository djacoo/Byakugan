# Library / SDK — Working Standards

## What This Project Type Demands
A library is a contract with every developer who will ever use it. The public API, once released, must be treated as immutable — changing it breaks code you do not control. Every design decision compounds over time. Minimize the surface area. Make the right usage obvious. Make the wrong usage hard or impossible. Earn trust through stability.

## Before Starting Any Feature
- Define the public API (exported types, function signatures) before implementation. The API is the product.
- Write example usage code for the new feature as if you were a consumer. If the usage is awkward, redesign before implementing.
- Determine whether the change is backward-compatible (additive) or breaking. If breaking, it requires a major version bump and a migration guide.
- Identify all transitive dependencies the change introduces. Every dependency you add becomes a dependency for all your users.
- Confirm the new feature is actually needed by at least one real consumer, not speculative generality.

## API Design Standards
- Minimal surface area: expose the minimum needed. You can always add; you can never safely remove.
- Sensible defaults: the simplest usage should be the correct usage. A new user should not need to configure anything to get started.
- Fail fast and loudly: invalid usage should produce a clear error immediately, not silently produce wrong results.
- No global mutable state. Libraries that modify global state cause subtle, hard-to-debug conflicts.
- No side effects at import/module load time.
- No mandatory dependencies on heavy frameworks. Optional integrations are acceptable when clearly separated.

## How to Approach Any Task
1. Write the example usage (README snippet, documentation example) before the implementation.
2. Define the types and function signatures. This is the design review checkpoint.
3. Implement. Validate all inputs at the public API boundary with clear, actionable error messages.
4. Write blackbox tests that test the public API as a consumer would use it.
5. Run the full test suite against all supported runtime versions.

## Non-Negotiable Rules
- All public functions, types, and constants have documentation comments with at least one usage example.
- The CHANGELOG is updated for every release — additions, changes, deprecations, and breaking changes.
- Semantic versioning is applied strictly: patch for bug fixes, minor for new features, major for breaking changes.
- Deprecated APIs are marked with `@deprecated` annotations that include the reason and the migration path. Deprecated code is not removed until the next major version.
- Thread safety is either guaranteed and documented, or the library is documented as non-thread-safe.
- The library does not log to any output by default. Logging, if needed, is opt-in.
- The library does not call `exit()`, `os.Exit()`, `process.exit()`, or equivalent. That is the caller's decision.

## Backward Compatibility Rules
Breaking changes:
- Removing or renaming any exported symbol.
- Adding required parameters to existing functions.
- Changing the type or semantics of existing parameters or return values.
- Changing documented error behavior.
- Dropping support for a previously supported runtime version.

Non-breaking (additive) changes:
- New optional parameters with defaults.
- New functions, types, or constants.
- New fields on output types (be careful with input types).
- Bug fixes that do not change the documented behavior.

## Testing Standards
- Test the public API as a consumer — blackbox tests only. Internal implementation details are not tested directly.
- Test all documented error cases and invalid inputs.
- Test backward compatibility by running the test suite from the previous release against the new version.
- Test on all officially supported runtime versions in CI.
- Benchmark critical paths. Detect performance regressions in CI using comparison benchmarks.

## Publishing Checklist
- [ ] All tests pass on all supported runtime versions.
- [ ] CHANGELOG updated with all changes since the previous release.
- [ ] Version bumped correctly according to semver.
- [ ] API documentation generated and accurate.
- [ ] Breaking changes have a migration guide.
- [ ] Package contents verified (no test files, no secrets, no unintended files in the package).
- [ ] All deprecated APIs have annotations with migration path.
- [ ] No new required dependencies added without justification.
