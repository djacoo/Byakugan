# Java — Working Standards

## Mindset
Modern Java (17+) is a capable, expressive language. Write it with discipline: strong layering, immutability by default, and explicit contracts. Do not write Java as if it were 2010 — use records, sealed classes, pattern matching, and proper DI. Boilerplate is a smell; if you are writing it, there is a better way.

## Before Writing Code
- Identify the architectural layer of the code being written: domain, application, infrastructure, or presentation. Each has different rules about what it can depend on.
- Understand the existing DI framework (Spring, Quarkus, etc.) and follow its conventions precisely.
- Identify what must be immutable. The default should be immutable; mutability is the exception that requires justification.
- Check what already exists in the codebase before adding a new class, utility, or dependency.
- Determine error handling strategy: checked exceptions for recoverable failures at API boundaries, unchecked for programming errors.

## How to Approach Any Task
1. Define the interface or contract first (interface, abstract class, or public method signatures).
2. Design the data model: use `record` for value types, proper entities for domain objects with identity.
3. Implement from the inside out: domain logic first, then application layer, then infrastructure.
4. Write tests for each layer independently. Domain logic must be testable without starting a container.
5. Run the full build and verify no new warnings are introduced.

## Code Standards
- Use `record` for immutable data carriers. No manual POJO boilerplate for these.
- Use `sealed interface`/`sealed class` for closed type hierarchies.
- Use `Optional<T>` only as a return type for lookups that may return nothing. Never as a parameter or field.
- Use constructor injection everywhere. Never field injection (`@Autowired` on fields).
- Validate preconditions at the start of public methods: `Objects.requireNonNull`, `Preconditions.checkArgument`.
- Close all resources with try-with-resources. No manual `finally` blocks for resource cleanup.
- Use `Stream` API for collection operations. Imperative loops are acceptable for simple iteration.
- Compile and run with `-Xlint:all -Werror` equivalent settings in the build tool.

## Hard Rules
- Never use raw types. Always parameterize generics.
- Never swallow exceptions with an empty `catch` block.
- Never use `null` as a return value from public methods — return `Optional<T>`, throw, or return a default.
- Never share mutable state between threads without explicit synchronization or atomic operations.
- Never access a database or external service from the domain layer — that belongs in infrastructure.
- Never suppress compiler warnings without a comment explaining why.
- Never use `System.out.println` in non-script code. Use a proper logger.

## Testing Standards
- JUnit 5 for all tests. AssertJ for assertions (never raw `assertEquals`).
- Mockito for mocking infrastructure dependencies in application/domain tests.
- Integration tests use `@SpringBootTest` or `Testcontainers` against real infrastructure.
- Each test method has one clear purpose. Name it: `methodName_scenario_expectedResult`.
- Test both the happy path and documented failure modes for every public method.

## Definition of Done
- [ ] Build passes with zero warnings (`mvn clean verify` or `gradle build`).
- [ ] All tests pass including integration tests.
- [ ] No raw types, no null returns from public methods, no empty catch blocks.
- [ ] No `System.out.println` or `e.printStackTrace()` in non-script code.
- [ ] Constructor injection used throughout — no field injection.
- [ ] All resources are closed (no resource leaks detected by static analysis).
- [ ] New behavior covered by unit and/or integration tests.
