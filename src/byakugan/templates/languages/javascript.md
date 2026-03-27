# JavaScript — Working Standards

## Mindset
JavaScript is the language of the web and increasingly the server. You write it with discipline. It has no compiler to catch you — your discipline, tooling, and tests are the safety net. Default to TypeScript for any project beyond a trivial script. If the project is pure JavaScript, enforce the same rigor through ESLint and JSDoc.

## Before Writing Code
- Determine the runtime environment first: browser, Node.js, edge worker, Deno? This affects every API you can use.
- Settle the module system: ESM is the default for all new code. CJS only for legacy compatibility.
- Identify all async boundaries upfront: user events, network, file I/O, timers. Plan error handling for each.
- Decide on state ownership before writing components or functions. Where does state live? Who mutates it?
- Confirm whether to use TypeScript. If the project is any larger than a single file, use TypeScript.

## How to Approach Any Task
1. Read the existing code before writing anything. Understand the patterns already in use.
2. Write the interface (exported functions, event contracts, module API) before the implementation.
3. Use `async/await` for all asynchronous logic. No `.then()` chains, no callback pyramids.
4. Write tests alongside the code, not after. Untested async code always has bugs.
5. Run the linter before considering any task done. Lint errors are not optional to fix.

## Code Standards
- `const` by default. `let` only when reassignment is required. `var` never.
- Named functions for top-level declarations. Arrow functions for callbacks and short expressions.
- Every `async` function that can throw is wrapped in `try/catch` or explicitly `.catch()`-handled at a boundary.
- No `console.log` in production code. Use a logger with structured output.
- No global variable leakage. Every symbol is scoped to its module.
- Clean up side effects: remove event listeners, clear timers, close connections when no longer needed.
- Format with `prettier`. Lint with `eslint`. Both enforced in CI.

## Hard Rules
- Never use `==`. Always use `===`.
- Never use `eval()`, `Function()` constructor, or `with`.
- Never leave an unhandled promise rejection. Every async call has error handling.
- Never pass `null` or `undefined` through layers of code without handling it at the boundary where it can be null.
- Never import entire libraries when only a function is needed (`lodash` vs `lodash-es`).
- Never write synchronous I/O in Node.js production code paths.
- Never trust external data without validation.

## Testing Standards
- Unit tests with `vitest` (preferred) or `jest`. Component tests with `@testing-library`.
- Test behavior as users or callers experience it — not internal implementation details.
- Mock HTTP calls and external services. Never make real network calls in unit/integration tests.
- Test error paths explicitly. Happy path only is not sufficient.
- Run tests in CI on every commit. A failing test blocks merge.

## Definition of Done
- [ ] All tests pass.
- [ ] ESLint and Prettier report no issues.
- [ ] No `console.log`, `debugger`, or commented-out code.
- [ ] No unhandled promise rejections.
- [ ] No `var`, no `==`, no `eval`.
- [ ] All async error paths handled.
- [ ] New behavior is tested.
- [ ] Bundle size impact assessed if adding new dependencies.
