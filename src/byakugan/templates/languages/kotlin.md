# Kotlin — Working Standards

## Mindset
Kotlin eliminates entire categories of bugs through null safety, immutability, and expressive type modeling. Leverage these fully. Do not write Java with Kotlin syntax — idiomatic Kotlin is concise, safe, and expressive. Null should only exist at the edges of the system where external data enters; the core should be non-null by design.

## Before Writing Code
- Determine the architecture: MVVM + Clean Architecture for Android, hexagonal for backend. Match what exists in the project.
- Identify all nullable boundaries: API responses, user input, platform callbacks. Plan how each is validated and converted to non-null types before entering the domain.
- Establish the coroutine scope and dispatcher strategy for any async work. Who owns the scope? What dispatcher runs what work?
- Confirm the data modeling approach: `data class` for DTOs, `sealed class`/`sealed interface` for state, `value class` for typed wrappers.
- Check build files before adding any dependency. The Gradle build is part of the codebase.

## How to Approach Any Task
1. Model the data and state types first. The types drive the implementation.
2. Write the interface or contract before the implementation.
3. Implement using structured concurrency: `coroutineScope`, `viewModelScope`, `supervisorScope`. Never create bare `GlobalScope` coroutines.
4. Use the type system to make illegal states unrepresentable — `sealed class` over boolean flags.
5. Run `./gradlew build` and verify zero new warnings before finishing.

## Code Standards
- `val` by default. `var` only when mutation is required.
- Use `data class` for value holders. Use `sealed class`/`sealed interface` for state machines and discriminated types.
- Use `when` expressions exhaustively on sealed types. No `else` branch when all cases are handled.
- Use scope functions (`let`, `run`, `apply`, `also`, `with`) where they genuinely improve readability — not everywhere by default.
- Coroutines: collect `Flow` in `lifecycle`-aware scopes on Android. Use `viewModelScope` for ViewModel coroutines.
- Use Detekt for static analysis. Fix all reported issues.
- Use `ktfmt` or the built-in Kotlin formatter consistently.

## Hard Rules
- Never use `!!` (force non-null assertion) without a comment that proves the value cannot be null at that point.
- Never launch a coroutine without a defined scope and cancellation strategy.
- Never use `GlobalScope` in production code.
- Never call blocking I/O on the main dispatcher. Use `Dispatchers.IO` or `Dispatchers.Default`.
- Never use platform types (Java interop `!` types) without explicitly annotating nullability.
- Never model mutually exclusive states as multiple optional properties — use `sealed class`.
- Never leave uncaught exceptions in coroutines — use `CoroutineExceptionHandler` or `supervisorScope` where appropriate.

## Testing Standards
- Use JUnit 5 with `kotlin.test` or Kotest for assertions.
- Use `MockK` for mocking — it handles Kotlin-specific constructs (`object`, `companion`, extension functions).
- Use `kotlinx.coroutines.test.runTest` for all coroutine tests.
- Test `ViewModel` logic with `TestCoroutineDispatcher` / `StandardTestDispatcher` — not with real dispatchers.
- Use `turbine` for testing `Flow` emissions in a structured way.

## Definition of Done
- [ ] `./gradlew build` passes with zero errors and zero new warnings.
- [ ] Detekt passes with zero new issues.
- [ ] All tests pass.
- [ ] No `!!` without a justified comment.
- [ ] No `GlobalScope` usage.
- [ ] All coroutines have a defined scope with proper cancellation.
- [ ] `sealed class` `when` expressions are exhaustive (no missing branches).
- [ ] New behavior covered by unit tests.
