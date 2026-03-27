# CLI Tool — Working Standards

## What This Project Type Demands
A CLI tool is a citizen of the Unix pipeline. It must be composable, scriptable, and predictable. Exit codes communicate machine-readable status. stdout is for output. stderr is for diagnostics. A well-designed CLI is explorable through `--help` alone and composable with `|`, `>`, and `&&` without surprises.

## Before Starting Any Feature
- Write the `--help` text for the new command or flag before writing the implementation. Help text is the design document.
- Define the exit code contract: 0 for success, non-zero for every failure mode. Document the specific codes.
- Determine what output the command produces: human-readable by default, `--json` for scripting.
- Identify whether the command is destructive. If so, it needs `--dry-run` and explicit confirmation (or `--force` to skip it).
- Determine where configuration comes from: CLI flags override environment variables override config file override defaults. Establish this order and stick to it.

## Design Standards
- Help text (`--help`) available on every subcommand and flag. This is non-negotiable.
- Long-form flags for everything (`--verbose`). Short flags for the most common options (`-v`).
- Destructive operations have `--dry-run`. Dangerous destructive operations have an explicit confirmation prompt that can be bypassed with `--force` or `-y`.
- Output to stdout. Errors, warnings, and progress go to stderr.
- Use color and formatting only when stdout is a TTY (`isatty()` check). Support `NO_COLOR` and `--no-color`.
- Support `--json` output for any command that produces structured data. The JSON output is machine-readable and stable.
- Read configuration in priority order: CLI flags → environment variables → local config → user config → defaults.

## How to Approach Any Task
1. Write or update the `--help` text. Verify it describes the command completely.
2. Implement argument parsing using the project's established CLI framework.
3. Validate all arguments early. Produce clear, actionable error messages for invalid input — tell the user what is wrong and what the correct usage is.
4. Implement the command logic. Business logic is in a library function, not in the CLI handler directly.
5. Test by invoking the built binary directly and checking stdout, stderr, and exit codes.

## Non-Negotiable Rules
- Exit code 0 on success. Non-zero on any failure. Always.
- Errors go to stderr. Structured output goes to stdout.
- Never mix error messages into stdout — this breaks piping.
- Never prompt for input when stdin is not a TTY (the command is running non-interactively). Check `isatty()` before any interactive prompt.
- Never print sensitive information (tokens, passwords, secrets) to stdout or stderr.
- Config files go in the platform-appropriate location: `~/.config/tool/` on Linux/macOS, `%APPDATA%\tool\` on Windows.
- All user-provided file paths must be validated before use.
- `--version` outputs `toolname version X.Y.Z` and exits 0.

## Output Standards
- Progress messages go to stderr so they can be discarded when piping.
- In non-TTY mode, omit progress indicators entirely unless `--verbose` is set.
- `--quiet` / `-q` suppresses all output except errors.
- `--verbose` / `-v` includes diagnostic information.
- When `--json` is specified, output is always valid JSON, even on error (`{"error": "message"}`).

## Testing Standards
- Test by invoking the compiled binary with arguments and asserting on stdout content, stderr content, and exit code.
- Test piping: pipe output into the next command and verify the chain works.
- Test `--help` output to catch regressions.
- Test the `--json` output against a schema.
- Test non-interactive mode (no TTY). Test invalid arguments. Test missing required arguments.

## Definition of Done
- [ ] `--help` output is complete and accurate.
- [ ] Exit code is 0 on success, non-zero on all failure cases.
- [ ] Errors output to stderr only.
- [ ] Structured output outputs to stdout only.
- [ ] `--dry-run` implemented for all destructive operations.
- [ ] Color disabled when not a TTY and when `NO_COLOR` is set.
- [ ] `--json` output is valid JSON and tested against a schema.
- [ ] Config precedence: flags > env vars > config file > defaults.
- [ ] Integration tests invoke the real binary and check exit codes, stdout, stderr.
- [ ] `--version` implemented and correct.
