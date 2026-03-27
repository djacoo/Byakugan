# Ruby — Working Standards

## Mindset
Ruby rewards expressive, well-structured code. The language gives you enormous power to write either clear, beautiful code or an unmaintainable mess. Use that power deliberately. Rails and other frameworks have strong conventions — follow them. The moment you fight the framework, you have created technical debt.

## Before Writing Code
- Understand the existing architecture: how is business logic separated from persistence and presentation? Follow the established pattern.
- In Rails: controllers must be thin. Business logic belongs in service objects, not models or controllers.
- Identify side effects (email, external APIs, jobs, file writes) before writing anything. These must be explicit and testable.
- Check if the behavior you are implementing already exists, even partially, somewhere in the codebase.
- Read the test suite for the area you are modifying first. It describes the expected behavior.

## How to Approach Any Task
1. Write or read the tests first. In a TDD context, write the failing test, then the implementation.
2. Design the public method interface before the internal implementation.
3. Keep methods short and single-purpose. A method that cannot be described in one sentence does too much.
4. Use guard clauses to return early and flatten nesting.
5. Run RuboCop before submitting. Zero violations, zero suppressions without comments.

## Code Standards
- Add `# frozen_string_literal: true` to every file.
- Use keyword arguments for methods with 3 or more parameters.
- Use `guard` clauses (early returns) rather than deeply nested `if` blocks.
- Use `Struct` / `Data` (Ruby 3.2+) for simple value objects rather than raw hashes with string keys.
- Use `attr_reader` for read-only attributes, not `attr_accessor`.
- Raise specific, named exception classes. Rescue specific exception classes — never rescue `Exception`.
- Use `Rails.logger` / a proper logger. No `puts` in non-script code.
- Format and lint with RuboCop. The project `.rubocop.yml` is the standard.

## Hard Rules
- Never rescue `Exception` — rescue `StandardError` or a specific subclass.
- Never use `ActiveRecord` queries without pagination on list operations that could return large result sets.
- Never write N+1 queries. Every association accessed in a loop must be eager-loaded.
- Never put business logic in a controller action.
- Never mutate arguments passed into a method unless the method name makes clear it is mutating.
- Never use `eval`, `send` with user-provided method names, or `constantize` on user-controlled strings.
- Never commit with failing tests. Never suppress a RuboCop warning without a documented reason.

## Testing Standards
- Use RSpec with `expect` syntax. Use `let`/`let!`/`subject` properly.
- Use FactoryBot for test data. Never raw model creation (`User.create(...)`) in test setup.
- Use `VCR` or `WebMock` to stub all external HTTP calls in tests.
- Test the public interface of service objects, not their internals.
- Rails request specs cover API endpoints. Model specs cover validations and scopes. Service specs cover business logic.

## Definition of Done
- [ ] RuboCop passes with zero violations.
- [ ] All tests pass (`bundle exec rspec` clean).
- [ ] No N+1 queries introduced (verify with `bullet` gem in development).
- [ ] `frozen_string_literal: true` present in all new files.
- [ ] No `puts`, no `binding.pry`/`byebug` left in code.
- [ ] No business logic in controllers.
- [ ] No rescuing `Exception`.
- [ ] New behavior covered by RSpec tests.
