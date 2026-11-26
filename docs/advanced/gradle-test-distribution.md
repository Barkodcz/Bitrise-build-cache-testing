# Gradle Test Distribution — worker-scaling showcase

**Status: not implemented in this pass.** See `CLAUDE.md` "Scope status" and `docs/PROJECT_SPEC.md`
§11.1 for the full design (worker-pool matrix, shard-size sweep, the DuckDuckGo-Android reference
benchmark). Gated behind `SHOWCASE_ENABLE_GRADLE_TD` in `.bitrise/00-app.yml` (currently `"false"`
workspace-wide with no workflow consuming it yet).

Gradle Test Distribution is a private-beta feature — requires Bitrise's Advanced CI team to enable
Remote Execution for your workspace before this module would be usable even once implemented.
