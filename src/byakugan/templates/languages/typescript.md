# TypeScript — Working Standards

## Mindset
TypeScript's type system is not a formality — it is the primary tool for expressing intent, preventing bugs, and communicating contracts between modules. Use it fully. A codebase with `any` everywhere is a JavaScript codebase with extra steps. The goal is a type system so complete that the only bugs left are logic bugs.

## Before Writing Code
- Enable `"strict": true` in `tsconfig.json` from day one. Never relax it.
- Also enable: `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitReturns`.
- Model the domain in types before writing any functions or logic. Types are the design document.
- Identify all system boundaries (API responses, user input, file reads, environment variables). These need runtime validation (Zod, Valibot) — the TypeScript compiler does not protect you at runtime.
- Decide on `interface` vs `type` strategy for the project and apply it consistently.

## How to Approach Any Task
1. Write the types first. If you cannot describe the shape of the data in types, you do not understand the problem yet.
2. Define the function signatures before the bodies.
3. Start from the outermost layer (what callers see) and work inward.
4. Validate all external data at the boundary using a schema library. Never cast external data with `as`.
5. After writing, run `tsc --noEmit`. Zero type errors before the task is done.

## Code Standards
- Use `interface` for extensible shapes, `type` for unions, intersections, and aliases. Be consistent.
- Use discriminated unions for state that has mutually exclusive modes. Do not use optional fields for this.
- Use `readonly` on properties that should not be mutated after construction.
- Use `satisfies` to validate object shapes without losing inference.
- Use `unknown` at boundaries, not `any`. Narrow with type guards or schema parsing.
- Use `as const` for literal objects to preserve the narrowest types.
- Derive types from schemas and constants using `z.infer`, `typeof`, `keyof`, mapped types.
- Format with `prettier`. Lint with `eslint` + `typescript-eslint` strict ruleset.

## Hard Rules
- Never use `any`. If a third-party library forces it, wrap it in an adapter that returns typed output.
- Never use `as SomeType` without a comment explaining why the assertion is safe.
- Never use `@ts-ignore`. Use `@ts-expect-error` with a comment if suppression is truly necessary.
- Never use `enum` — use `as const` objects and union types instead. Enums have surprising runtime semantics.
- Never leave `Promise<any>` as a return type. Type the resolution value.
- Never use index access (`arr[0]`) without handling the `T | undefined` case when `noUncheckedIndexedAccess` is on.

## Testing Standards
- Test types explicitly using `tsd` or `expect-type` for public API type contracts.
- Test runtime validation logic (Zod schemas, custom type guards) with unit tests.
- Do not rely on TypeScript to catch runtime errors — validate at boundaries, test error cases.
- Use `vitest` with full TypeScript support.

## Definition of Done
- [ ] `tsc --noEmit` passes with zero errors.
- [ ] ESLint (with typescript-eslint strict) passes with zero issues.
- [ ] Prettier formatting applied.
- [ ] No `any`, no `@ts-ignore`, no unsafe assertions without comment.
- [ ] All external data validated with a schema at the boundary.
- [ ] New public API shapes have types tested.
- [ ] All tests pass.
