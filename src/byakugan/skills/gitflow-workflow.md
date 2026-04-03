# GitFlow Workflow

## Branch Model

```
main       — production only, protected, never commit directly
develop    — integration branch, never commit directly
feature/… → PR to develop
release/x.x.x → PR to main + tag + back-merge to develop
hotfix/…   → PR to main + tag + back-merge to develop
```

## Before Any File Edit

1. Verify current branch: `git branch --show-current`
2. If on `main` or `develop` → STOP. Create or switch to correct branch first.
3. Verify branch is up to date: `git fetch && git status`
4. If behind remote → pull + rebase before starting work.

## Commits

- One atomic commit per logical unit of work
- Conventional Commits: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`, `perf:`
- Message body explains *why*, not *what*
- **No AI mentions anywhere**: no `Co-Authored-By: Claude`, no `🤖 Generated with`, no "AI-assisted"
- Never skip hooks (`--no-verify` forbidden unless user explicitly requests)
- Never amend published commits

## Pull Requests

- Title: short, imperative, human-written style
- Body: scope, motivation, test plan — no AI footers or signatures
- Target: `develop` (never `main` directly, except hotfix/release)

## Working Tree Discipline

- Stash before branch switches if working tree is dirty
- Clean working tree before PR
- Squash fixup commits before PR if history is noisy (ask user first)

## Hard Blocks — Never Proceed

- Staged files include `.byakugan/`, `CLAUDE.md`, `settings.local.json`, `*.db`, `docs/superpowers/` → unstage, warn, explain
- Committing to `main` or `develop` directly → abort
- Force-pushing → abort unless user explicitly confirms

## When Unsure, Ask

- "Should this be a feature branch or a hotfix?"
- "Should I squash these commits before the PR?"
- "This touches both auth and billing — one branch or two?"
- "The branch is 3 commits behind develop — should I rebase first?"
