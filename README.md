<div align="center">

# Byakugan

**Active guidelines and memory system for Claude Code.**

Byakugan keeps Claude working the right way — consistently, across every project.<br/>
It installs opinionated, project-aware guidelines into your repo, hooks into every Claude tool use<br/>
to surface the right rules at the right moment, and builds a local memory database that gets smarter as you work.

<br/>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?logo=astral&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-memory%20db-003B57?logo=sqlite&logoColor=white)
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

**Other commands:**
```bash
byakugan status          # show active setup
byakugan update          # pull latest template content, preserve your project context
byakugan add <template>  # add a guideline, e.g. specialized/security-check.md
byakugan remove <template>
byakugan list            # browse all available templates
byakugan doctor          # diagnose and auto-repair
byakugan remember "correction: never use X, use Y instead"
```

---

## How it works

1. **`byakugan init`** detects your tech stack, adapts the relevant guidelines to your project (filling in real tool names, commands, versions), and writes them to `.byakugan/`.
2. **Hooks** fire before every `Edit`, `Write`, or `Bash` call Claude makes — injecting a precise pointer to the right guideline section into Claude's context.
3. **Memory** accumulates corrections, decisions, preferences, and patterns you express during work. The hook queries it automatically and surfaces relevant context on every tool use.

## License

MIT
