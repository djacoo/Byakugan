# Model Selection

## Rules

| Task | Model |
|------|-------|
| Brainstorming, design, architecture decisions | Opus 4.6 |
| Writing implementation plans | Opus 4.6 |
| Code review dispatch | Opus 4.6 |
| Systematic debugging phases 1–2 (root cause, pattern analysis) | Opus 4.6 |
| Implementation, TDD cycles, refactoring | Sonnet 4.6 |
| Verification, unit tests, linting fixes | Sonnet 4.6 |
| Systematic debugging phases 3–4 (hypothesis + fix) | Sonnet 4.6 |

## How to Apply

**Subagent dispatch:** When dispatching subagents, use the `model` parameter:
- Brainstorming/planning agents → `model: "opus"`
- Implementation/verification agents → `model: "sonnet"`

**Interactive sessions:** Switch models based on your current phase:
- Planning/designing → switch to Opus 4.6 (`/model opus`)
- Implementing/testing → switch to Sonnet 4.6 (`/model sonnet`)
