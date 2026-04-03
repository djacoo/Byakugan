<div align="center">

# Byakugan

**Active guidelines, memory, and workflow orchestration for Claude Code.**

Byakugan keeps Claude working the right way — consistently, across every project.<br/>
It installs opinionated, project-aware guidelines into your repo, hooks into every Claude tool use<br/>
to surface the right rules at the right moment, and builds a local memory database that gets smarter as you work.<br/>
With v0.3, it adds session continuity, GitFlow enforcement, and a Haiku-powered compression pipeline.

<br/>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?logo=astral&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-memory%20db-003B57?logo=sqlite&logoColor=white)
![Anthropic SDK](https://img.shields.io/badge/Anthropic%20SDK-compression-D97757?logo=anthropic&logoColor=white)
![Claude Code](https://img.shields.io/badge/Claude%20Code-hooks-D97757?logo=anthropic&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

<br/>

<img src="https://giffiles.alphacoders.com/215/215559.gif" width="500" alt="Byakugan" />

</div>

---

## Quickstart

**Install:**
```bash
uv tool install byakugan
```

**Initialize in any project:**
```bash
cd your-project
byakugan init
```

Byakugan will auto-detect your stack, confirm the detected templates, ask a few clarifying questions, and set everything up — guidelines in `.byakugan/`, entry point at `CLAUDE.md`, hooks in `.claude/settings.local.json`. Nothing is committed to the repository.

**Commands:**
```bash
# Setup
byakugan init              # auto-detect stack, install guidelines + hooks
byakugan update            # refresh template content, preserve project context
byakugan sync              # re-detect stack, reconcile drift
byakugan deinit            # remove Byakugan from a project

# Guidelines
byakugan add <template>    # e.g. specialized/security-check.md
byakugan remove <template>
byakugan list              # browse all 38 available templates

# Memory
byakugan remember "correction: never use X, use Y instead"
byakugan remember "decision: we chose X because Y" --importance 5
byakugan remember "pattern: in this codebase, X means Y" --file src/auth.py
byakugan memories list     # browse stored memories
byakugan memories search X # find memories about X
byakugan memories edit <id> "updated content"
byakugan memories forget <id>
byakugan memories prune    # decay stale, remove low-value

# Session continuity
byakugan handoff "Working on auth refactor, need to finish JWT validation"
byakugan session list      # browse compressed session summaries
byakugan session show <id> # view full summary content
byakugan session save      # manually trigger compression

# Diagnostics
byakugan status            # show active setup
byakugan doctor            # diagnose and auto-repair
```

---

## How it works

1. **`byakugan init`** auto-detects your tech stack, lets you confirm templates via an interactive picker, adapts each guideline with your project's specific context (tool names, versions, deployment target), and writes them to `.byakugan/`. It also detects [superpowers](https://github.com/anthropics/claude-code-plugins) if installed and bundles GitFlow and model-selection skills.
2. **Three hooks** cover the full lifecycle — **SessionStart** injects handoff notes, session summaries, and high-importance memories at the start of each conversation; **PreToolUse** fires before every `Edit`, `Write`, `MultiEdit`, or `Bash` call with guideline routing and memory context; **PostToolUse** captures tool events asynchronously for session tracking.
3. **Memory** accumulates corrections, decisions, preferences, and patterns. The hook queries the local SQLite database automatically and surfaces the most relevant context. Claude is instructed (via `CLAUDE.md`) to store memories proactively after corrections and decisions.
4. **Session continuity** tracks tool-use events across a session. When enough events accumulate, a background Haiku compression pipeline summarizes them into digestible session summaries. Use `byakugan handoff` to leave a note for the next session — it appears automatically at session start.
5. **GitFlow enforcement** checks staged files for privacy violations (`.byakugan/`, `CLAUDE.md`, `*.db`, etc.) and warns when committing to protected branches. A bundled GitFlow skill is embedded directly into `CLAUDE.md`.
6. **Nothing is committed** — `.byakugan/`, `CLAUDE.md`, `.claude/settings.local.json`, and all session data are gitignored. Guidelines and memory are per-developer.

## Architecture

```
.byakugan/
├── byakugan.toml              # project config
├── byakugan.db                # unified SQLite database (memories, events, summaries, handoffs)
├── skills/                    # bundled skills (gitflow-workflow.md, model-selection.md)
├── languages/                 # adapted language guidelines
├── project-types/             # adapted project-type guidelines
└── specialized/               # adapted specialized guidelines

CLAUDE.md                      # generated entry point (workflow, gitflow, memory, privacy)
.claude/settings.local.json    # 3 hooks (SessionStart, PreToolUse, PostToolUse)
```

## License

MIT
