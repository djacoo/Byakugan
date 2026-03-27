# GitFlow Workflow — Working Standards

## When to Use GitFlow
GitFlow is appropriate for projects with scheduled releases, multiple concurrent versions in production, or formal QA/staging gates. If the team deploys continuously (multiple times per day) and maintains only one version, trunk-based development is simpler and more appropriate.

## Branch Model

```
main        ← production. Tagged at every release. Never commit directly.
develop     ← integration. All features merge here. Always releasable.
feature/*   ← new work. Branch from develop. Merge back to develop.
release/*   ← release prep. Branch from develop. Merge to main AND develop.
hotfix/*    ← production fixes. Branch from main. Merge to main AND develop.
```

## Branch Naming
- `feature/short-description-of-work` — kebab-case, concise
- `release/1.4.0` — semver
- `hotfix/fix-payment-timeout` or `hotfix/1.4.1`

## Workflow Procedures

### Starting a Feature
```
git checkout develop && git pull origin develop
git checkout -b feature/my-feature
```
Work in small, logical commits. Push regularly. Keep the feature branch up to date with develop via `git rebase develop` (preferred) or `git merge develop`.

### Finishing a Feature
```
git checkout develop && git pull origin develop
git merge --no-ff feature/my-feature
git push origin develop
git branch -d feature/my-feature
```
Use `--no-ff` always. This preserves the branch topology in history, which makes releases and reversions clearer.

### Starting a Release
```
git checkout develop && git pull origin develop
git checkout -b release/1.4.0
```
Only bug fixes, documentation, and release preparation on this branch. No new features. When ready:
```
git checkout main && git pull origin main
git merge --no-ff release/1.4.0
git tag -a v1.4.0 -m "Release 1.4.0"
git push origin main --tags

git checkout develop
git merge --no-ff release/1.4.0
git push origin develop
git branch -d release/1.4.0
```
Merging back to develop is mandatory. Any fixes made during release prep must not be lost.

### Emergency Hotfix
```
git checkout main && git pull origin main
git checkout -b hotfix/1.4.1
# Fix the bug
git checkout main
git merge --no-ff hotfix/1.4.1
git tag -a v1.4.1 -m "Hotfix 1.4.1"
git push origin main --tags

git checkout develop
git merge --no-ff hotfix/1.4.1
git push origin develop
git branch -d hotfix/1.4.1
```
Merging the hotfix back to develop is mandatory. Missing this step means the fix disappears in the next release.

## Commit Message Standard (Conventional Commits)
```
<type>(<scope>): <description>

[optional body]

[optional footer: BREAKING CHANGE: ..., Closes #123]
```

**Types**: `feat` | `fix` | `docs` | `style` | `refactor` | `test` | `chore` | `perf`

Examples:
```
feat(auth): add OAuth2 login via Google
fix(payments): prevent duplicate charge on network retry
refactor(users): extract email validation to shared validator
test(orders): add edge case tests for empty cart
chore: upgrade ESLint to v9
```

## Pull Request Standards
- PR description states: what changed, why it changed, and how to verify it.
- All CI checks pass before requesting review.
- PRs against `develop` require at least 1 approval.
- PRs against `main` (releases and hotfixes) require at least 2 approvals.
- No self-merging.

## Branch Protection (enforce these)
**`main`**: no direct push, require PRs, require passing CI, require 2 approvals, no force push.
**`develop`**: no direct push, require PRs, require passing CI, require 1 approval, no force push.

## Versioning (Semantic Versioning)
- `MAJOR`: breaking changes (incompatible API, removed features, migration required).
- `MINOR`: new backward-compatible features.
- `PATCH`: backward-compatible bug fixes.
- Tags on `main` only. Format: `v1.2.3`.
- Pre-release: `v1.2.3-rc.1`, `v1.2.3-beta.1`.

## Common Mistakes to Avoid
- Merging `hotfix` to `main` but forgetting to merge back to `develop` — the fix disappears.
- Merging `release` to `main` but forgetting to merge back to `develop` — release fixes disappear.
- Using `--ff` (fast-forward) instead of `--no-ff` — lose branch topology in history.
- Making feature work on a `release` branch — features belong in `develop`.
- Not tagging `main` after a release — releases must be tagged for traceability.
