# C — Working Standards

## Mindset
C is explicit about everything. There is no runtime catching your mistakes — the consequences are undefined behavior, memory corruption, and security vulnerabilities. Your job is to be the safety layer: validate everything, own every allocation, close every resource, and document every invariant. Clarity and defensiveness always beat brevity.

## Before Writing Code
- Define the memory ownership model in writing (even as comments) before coding: who allocates, who frees, and when.
- Define the error handling contract for every function: return code? out-param? errno? Apply this consistently across the module.
- Identify all external (untrusted) inputs. These get validated first, before any processing.
- Review the header interface before implementing. The header is the contract; it should be correct before the .c file is touched.
- Confirm compiler flags: `-Wall -Wextra -Wformat=2 -Wshadow -Wconversion -Wpedantic -Werror` on all builds.

## How to Approach Any Task
1. Write or review the header (`.h`) declaration first. Implementation follows the declared contract.
2. Design error handling: define the return codes or error states before writing the logic.
3. Write implementation. Use the `goto cleanup` pattern for functions with multiple resources and exit paths.
4. Test every allocation, every return code, every pointer before dereferencing.
5. Run under `valgrind` and AddressSanitizer before marking anything done.

## Code Standards
- Initialize every variable at declaration. Uninitialized locals are bugs waiting to happen.
- Every `malloc`/`calloc` return is checked for `NULL` before use.
- Every `free` is followed by setting the pointer to `NULL`.
- Every pointer is validated before dereference unless provably non-null by construction.
- Use `const` for pointer parameters that are not modified. Use `size_t` for sizes and counts.
- Use `strncpy`, `snprintf`, `strncat` — never `strcpy`, `sprintf`, `strcat`.
- Use `static` for all functions and globals that are internal to a translation unit.
- Apply `clang-format` consistently.

## Hard Rules
- Never use `gets()`. Never use `sprintf()` or `strcpy()` with externally-sourced data.
- Never dereference a pointer without proving it is non-null at that point.
- Never free memory twice. Never use memory after freeing it.
- Never use `scanf` on strings without a width specifier.
- Never write `printf(user_controlled_string)` — always `printf("%s", user_controlled_string)`.
- Never return a pointer to a local (stack) variable.
- Never ignore the return value of functions that can fail (read, write, malloc, fopen, etc.).
- Never use uninitialized memory.

## Memory Ownership Convention
Document every function that allocates:
```
// Returns a newly allocated Foo. Caller must call foo_free() when done.
// Returns NULL on allocation failure.
Foo *foo_create(...);
```
Document every function that transfers or borrows:
```
// Borrows `data` for the duration of the call. Caller retains ownership.
void process(const Data *data);
```

## Testing Standards
- Use `CMocka`, `Unity`, or `Check`. Every public function has tests.
- Test every error path, not just the success path.
- Run tests with `-fsanitize=address,undefined` always in CI.
- Run `valgrind --leak-check=full --error-exitcode=1` in CI.
- Fuzz parsing and deserialization code with `AFL++` or `libFuzzer`.

## Definition of Done
- [ ] Compiles with `-Wall -Wextra -Wformat=2 -Wshadow -Wconversion -Wpedantic -Werror` clean.
- [ ] All tests pass under AddressSanitizer and UBSanitizer.
- [ ] `valgrind` reports zero errors and zero leaks.
- [ ] Every heap allocation checked for NULL.
- [ ] Every file/socket/resource closed on all exit paths (including error paths).
- [ ] No `printf(user_input)` format string vulnerabilities.
- [ ] Ownership documented for all heap-allocated data.
- [ ] No use of unsafe string functions.
