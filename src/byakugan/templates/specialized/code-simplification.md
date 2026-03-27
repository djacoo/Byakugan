# Code Simplification — Working Standards

## When to Apply This
Apply code simplification when:
- Code is hard to understand without running it in your head.
- A function does more than one identifiable thing.
- Tests are hard to write because of tight coupling or hidden dependencies.
- The same logic is duplicated in multiple places.
- A change in requirements would require modifying many unrelated places.

Do NOT apply simplification when:
- The code works and is not being touched.
- The "simplification" reduces clarity rather than complexity.
- The abstraction is premature — the use case exists exactly once.

## The Simplification Mindset
Complexity is not measured in lines of code. A 300-line file with clear structure is simpler than a 50-line function with 8 levels of nesting. Ask: "Can a new team member understand the intent of this code in under 60 seconds?" If not, it needs simplification.

## Identifying Complexity — Red Flags
- A function more than 20–30 lines long.
- Nesting deeper than 3 levels (if inside if inside if inside for...).
- A function or method name that contains "and" or "or" — it does two things.
- A comment that explains *what* the code does (not *why*). Rename the code instead.
- Magic numbers or strings: values with no name.
- Long parameter lists (more than 3–4 parameters).
- The same group of 3+ variables always appear together in function calls.
- A `switch`/`if-else` chain that will need a new case every time a new type is added.
- Code that tests implementation details rather than behavior (indicates over-coupling).

## Simplification Techniques

### Guard Clauses (Eliminate nesting)
Invert conditions to return early. Flat is better than nested.
```
// Before: nested
if condition_a:
    if condition_b:
        if condition_c:
            do_the_work()

// After: guard clauses
if not condition_a: return
if not condition_b: return
if not condition_c: return
do_the_work()
```

### Extract Function (Name things that can be named)
If a block of code can be described in a sentence, extract it into a function with that name.
The function name eliminates the need for a comment.

### Replace Magic Values with Named Constants
Every literal number or string that carries meaning gets a name. The name is the documentation.

### Introduce Parameter Object (Reduce parameter lists)
When the same group of parameters appears together in multiple functions, they belong together as a named type or struct.

### Replace Conditional with Lookup / Polymorphism
A long `switch` or `if-else` on a type field is a signal to use a lookup map or polymorphism.
Adding a new case should not require modifying the switch.

### Separate Query from Command
A function should either return data or change state — not both. Functions that do both are hard to test and reason about.

### Delete Dead Code
Commented-out code, unreachable branches, unused parameters, unused imports: delete them.
Version control preserves history. Dead code in the codebase creates confusion.

## How to Simplify Safely
1. Ensure tests cover the code you are about to simplify. If they do not, write characterization tests first.
2. Make one simplification at a time.
3. Run tests after every change. Each change must leave the tests green.
4. Commit each successful simplification separately with a descriptive message.
5. Never simplify and fix bugs in the same change.

## What Good Looks Like After Simplification
- The main function reads like a sequence of business steps, not implementation details.
- Helper functions have names that explain their purpose without reading their body.
- There are no magic numbers, no comments explaining what the code does, and no nesting deeper than 2–3 levels.
- Adding a new case or variant requires touching exactly one place.
- Tests describe behavior, not method calls.

## What NOT to Do
- Do not extract a function that is called exactly once and is clearer inline.
- Do not introduce an abstraction for a pattern that appears fewer than three times.
- Do not add layers of indirection that make debugging harder without improving readability.
- Do not mistake "short" for "simple." A chain of 10 nested function calls can be harder to follow than a 20-line function with clear variable names.
