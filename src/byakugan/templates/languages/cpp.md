# C++ — Working Standards

## Mindset
Modern C++ (17/20) is not C with classes. It is a language with powerful zero-cost abstractions, RAII, move semantics, and a rich standard library. Your job is to use these tools to write code that is safe, correct, and fast — in that order. Raw pointers, manual `new`/`delete`, and C-style patterns are last resorts justified by profiling, not defaults.

## Before Writing Code
- Define the ownership model before writing anything. For every object and resource: who owns it, who borrows it, and when is it destroyed?
- Decide the error handling strategy: exceptions, `std::expected` (C++23), or error codes. Apply consistently. Do not mix strategies in the same codebase.
- Check whether the CMake target, compile flags, and sanitizer configuration are set up correctly before adding code.
- Identify what exception safety guarantee is required for each operation: basic, strong, or nothrow.
- Profile-guided optimization only: never assume a hot path without measurement.

## How to Approach Any Task
1. Write the class/function interface in the header before the implementation.
2. Define the ownership model in the type design (unique vs. shared ownership, RAII wrappers for resources).
3. Implement. Prefer the STL and standard algorithms over raw loops and manual memory operations.
4. Compile with full warnings: `-Wall -Wextra -Wpedantic -Werror`. Address every warning.
5. Run under sanitizers during development and CI: AddressSanitizer, UBSanitizer, ThreadSanitizer.

## Code Standards
- Use smart pointers: `unique_ptr` for exclusive ownership, `shared_ptr` for shared. Raw owning pointers appear only inside RAII wrappers.
- Mark single-argument constructors `explicit`. Mark non-mutating methods `const`. Mark nonthrowing functions `noexcept`.
- Use `[[nodiscard]]` on functions whose return values must not be ignored.
- Use `string_view` for read-only string parameters. `span<T>` for non-owning array views.
- Apply the Rule of Zero where possible (let the compiler generate copy/move). Apply the Rule of Five when you must manage a resource manually.
- Use `constexpr` for compile-time computable values and functions.
- Apply `clang-format` consistently. Use `clang-tidy` with a project-level configuration.

## Hard Rules
- Never use raw `new` or `delete` in user code. Ownership always expressed through smart pointers or containers.
- Never declare uninitialized variables.
- Never use `reinterpret_cast` or `const_cast` without a comment proving it is safe and necessary.
- Never write `unsafe` concurrent access to shared data. Use `std::mutex`, `std::atomic`, or message passing.
- Never ignore compiler warnings. `-Werror` in CI.
- Never use C-style casts (`(Type)value`). Use `static_cast`, `dynamic_cast`, or explicit constructors.
- Never mix ownership models within a single module boundary.

## Testing Standards
- Use `Google Test` or `Catch2`. Test files live in `tests/` and mirror the source structure.
- Run tests under AddressSanitizer and UBSanitizer in CI on every build.
- Benchmark with `Google Benchmark` for performance-sensitive code. Compile in `Release` mode for benchmarks.
- Test exception safety: verify object state is valid after a thrown exception.
- Use `valgrind` on Linux for leak detection in addition to ASAN.

## Definition of Done
- [ ] Compiles with `-Wall -Wextra -Wpedantic -Werror` with zero warnings.
- [ ] All tests pass under AddressSanitizer and UBSanitizer.
- [ ] `clang-tidy` passes with zero issues.
- [ ] `clang-format` applied.
- [ ] No raw `new`/`delete`. No uninitialized variables. No C-style casts.
- [ ] RAII used for all resource management.
- [ ] New behavior covered by tests.
- [ ] Performance changes validated with a benchmark.
