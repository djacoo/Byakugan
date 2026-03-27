# Refactoring — Working Standards

## What Refactoring Is
Refactoring is changing the internal structure of code without changing its observable behavior. The tests pass before the refactoring, the tests pass after the refactoring, and they pass at every step in between. If the behavior changes — even to fix a bug — that is not refactoring. Refactoring and behavior change must never happen in the same commit.

## When to Refactor
- Before adding a feature: make the code easy to add the feature to first.
- When understanding the code requires more mental effort than the code's complexity warrants.
- When the same change requires modifying more than 2–3 unrelated files.
- When tests are hard to write because of tight coupling.
- When code review feedback consistently points to the same structural issues.

Do NOT refactor:
- Code that is not being touched for any other reason.
- Code without test coverage (write the tests first).
- Simultaneously with a bug fix or feature addition.

## The Refactoring Procedure
1. Verify tests pass before starting.
2. Make the smallest possible structural change.
3. Run tests. They must pass.
4. Commit with a message that describes the structural change (not "refactoring" alone).
5. Repeat.

If tests fail after a refactoring step, stop and revert the last step. Debugging a large refactor is harder than doing it incrementally. **Never accumulate a large uncommitted refactor.**

## Refactoring Without Test Coverage
If the code to be refactored has no tests:
1. Write characterization tests first: run the code with representative inputs, capture the outputs, and assert they match. These tests document the current behavior, bugs included.
2. Only then refactor, using those tests as the safety net.
3. Once the refactoring is done, replace characterization tests with proper behavior tests.

## The Refactoring Catalog

**Extract Function**: a block of code can be named → extract it. The name removes the need for a comment.

**Inline Function**: the function's body is as clear as its name → inline it. Indirection with no benefit is complexity.

**Rename**: any name that does not accurately describe what it represents → rename it. Names are the primary documentation.

**Extract Variable**: a complex expression used more than once → extract it with a descriptive name.

**Introduce Parameter Object**: the same group of 3+ parameters appears in multiple function signatures → group them into a named type.

**Replace Primitive with Domain Type**: a string representing an email, an integer representing a user ID, a float representing money → make it a type. This makes invalid states unrepresentable.

**Replace Conditional with Polymorphism**: a long `switch`/`if-else` chain on a type tag → replace with polymorphism or a dispatch table. Adding a new case should not require modifying the switch.

**Separate Query from Command**: a function that both returns a value and modifies state → split into two functions. Queries should have no side effects.

**Move Function**: a function uses more data from another module than from its own → move it to the module it belongs to.

**Extract Class**: a class has grown and parts of it are cohesive enough to stand alone → extract into a focused class.

**Remove Middle Man**: a class that only delegates every call to another class → remove it and call the delegate directly.

**Replace Nested Conditionals with Guard Clauses**: deeply nested if-else → use early returns for all the special cases first, then the main logic falls naturally at the end.

## Identifying Refactoring Targets (Code Smells)

| Smell | Refactoring |
|-------|-------------|
| Function > 20 lines | Extract Function |
| Nesting > 3 levels | Guard Clauses |
| Parameter list > 3 | Introduce Parameter Object |
| "and" in function name | Split into two functions |
| Comment explains *what* | Rename the code |
| Duplicated code | Extract and reuse |
| Large class with multiple responsibilities | Extract Class |
| Switch on type that grows | Polymorphism or dispatch table |
| Primitive for domain concept | Domain Type |
| Function uses another class's data more than its own | Move Function |

## Commit Message Standard for Refactoring
```
refactor(scope): extract payment validation into PaymentValidator class

No behavior change. Moves validation logic out of OrderController
to make it independently testable and reusable by the invoice flow.
```

The commit message must state: what structural change was made, and (if not obvious) why. It must confirm there is no behavior change.

## Definition of Done for a Refactoring Task
- [ ] All tests pass before and after every step.
- [ ] No behavior changes — refactoring commits and behavior change commits are separate.
- [ ] Code is objectively easier to understand or modify than before.
- [ ] No new test coverage was lost (tests still cover the extracted code).
- [ ] Commit messages describe the structural change, not just "refactoring".
