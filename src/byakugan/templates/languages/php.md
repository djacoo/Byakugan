# PHP — Working Standards

## Mindset
Modern PHP (8.1+) is a typed, capable language with a mature ecosystem. Write it strictly: `declare(strict_types=1)` everywhere, typed everything, no legacy patterns. The PHP of global functions, raw SQL, and `$_POST` directly into queries is not modern PHP. Follow framework conventions (Laravel, Symfony) precisely — they exist for good reason.

## Before Writing Code
- Confirm `declare(strict_types=1)` is present (or will be added) in every file touched.
- Identify the architectural layer: controller, service, repository, domain model. Each has strict rules about what it may depend on.
- Identify all external input sources: HTTP request, CLI args, queue messages, webhooks. Every one of these is untrusted and must be validated before use.
- Understand the project's DI container usage. Register dependencies properly; do not instantiate services manually inside other services.
- Check if PHPStan or Psalm is configured for this project, and at what level. Write code that passes static analysis.

## How to Approach Any Task
1. Write the interface or type definitions first (DTO, enum, or method signature).
2. Implement following the established architecture. No shortcuts that skip layers.
3. Write or update tests. PHPUnit must pass before the task is done.
4. Run PHPStan/Psalm. Zero new errors at the project's configured level.
5. Run PHP CS Fixer / PHP_CodeSniffer. Zero style violations.

## Code Standards
- `declare(strict_types=1)` at the top of every file. Non-negotiable.
- Full type declarations on all properties, parameters, and return types.
- Use constructor property promotion for simple DTOs and value objects.
- Use `enum` (PHP 8.1+) for any fixed set of values — not class constants or string literals.
- Use `match` instead of `switch`. It is strict, returns a value, and throws on unhandled cases.
- Use `readonly` properties for immutable value objects.
- Use named arguments when calling functions with 4+ parameters for clarity.
- Database queries use the ORM query builder or prepared statements — never string concatenation with user data.

## Hard Rules
- Never use `declare(strict_types=1)` only on some files — it must be everywhere.
- Never use raw `$_GET`, `$_POST`, `$_REQUEST` in application code — use the framework's request abstraction.
- Never interpolate user input into SQL queries. Ever.
- Never use `eval()` or `exec()` with user-provided data.
- Never use `@` error suppression — fix the underlying issue.
- Never use `var_dump()`, `print_r()`, or `die()` in non-debug code.
- Never suppress PHPStan/Psalm errors with `@phpstan-ignore` without a documented reason.
- Never echo/output user-provided HTML without escaping — use the template engine's auto-escaping.

## Testing Standards
- Use PHPUnit. Use Pest for a more expressive syntax if it is already in the project.
- Laravel: use `RefreshDatabase` for DB tests, `Http::fake()` for outbound HTTP, `Queue::fake()` for jobs.
- Test service classes independently of the framework (no container bootstrapping in unit tests).
- Test validation rules explicitly — invalid inputs must produce the correct error messages.
- Run `./vendor/bin/phpunit` and verify green before submitting.

## Definition of Done
- [ ] `declare(strict_types=1)` in every file.
- [ ] PHPStan/Psalm passes at the project's configured level.
- [ ] PHP CS Fixer/CodeSniffer passes with zero violations.
- [ ] All PHPUnit tests pass.
- [ ] No raw SQL with user input. No `$_GET`/`$_POST` accessed directly.
- [ ] No `var_dump`, `die`, `print_r`, `eval` in production code.
- [ ] All inputs validated through the framework's validation layer.
- [ ] New behavior covered by tests.
