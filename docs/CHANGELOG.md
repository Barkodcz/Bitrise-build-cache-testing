# Changelog

Notable deviations between `docs/PROJECT_SPEC.md` (the source-of-truth design doc) and reality,
per spec §0's instruction to "fix the code, then update this spec and note it in CHANGELOG.md."

## Unreleased — initial implementation pass (2026-11-26)

- Scoped to two fully-implemented stacks (Android/Gradle, Node.js key-based caching) out of the
  spec's full 10-stack design; every other stack is catalogued (`status: planned`) with a doc stub.
  See `CLAUDE.md` "Scope status".
- Report/utility workflows are named `report_<stack>`, not `_report_<stack>` as spec §7.1 suggests —
  Bitrise's platform rejects leading-underscore "utility workflow" names referenced from a pipeline.
  See `docs/reference/verified-facts.md`.
- `tools/yaml/flatten.py` shells out to the official `bitrise yml merge` CLI command instead of
  re-implementing Bitrise's modular-YAML merge semantics by hand.
- Byte-traffic metrics (download/upload ratio) are not collected yet; `AND-G01`'s and `AND-B03`'s
  catalog expectations were trimmed accordingly — see the inline notes in `scenarios/catalog.yml`.
- `projects/android` is a plain Kotlin/JVM multi-module project (no Android Gradle Plugin / SDK
  dependency), not a full Android app — chosen so it builds anywhere a JDK is available, including
  outside Bitrise's Android stack.
