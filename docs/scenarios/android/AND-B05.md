---
id: AND-B05
verdict: bad
stack: android
fix_ref: AND-G01
tags: [cache-disabled-by-flag]
---
# AND-B05 — `--rerun-tasks` left in CI args

**In one sentence:** Everything else is configured correctly, but `--rerun-tasks` is passed to every
Gradle invocation, which unconditionally re-executes every task regardless of any cache, local or
remote.

## What the configuration does
`.bitrise/workflows/android.yml` `and-b05__*` — same as `AND-G01` except `gradle_build`'s `options`
input:

```yaml
- bundle::gradle_build:
    inputs:
    - options: --rerun-tasks
```

## What you see
- Pipeline graph: measure duration ≈ seed duration; no benefit from an otherwise-correct setup.
- Log evidence: `> _To be captured from a real run._` — every task shows `EXECUTED`, none
  `FROM-CACHE` or `UP-TO-DATE`.
- Metrics: `gradle.from_cache_share == 0`.

## Why it happens
`--rerun-tasks` is a Gradle CLI flag that forces every selected task (and its dependencies) to run
regardless of up-to-date checks or any cache (local build cache, remote build cache, or
`UP-TO-DATE`). It's a legitimate local debugging flag that occasionally gets copy-pasted into a CI
workflow's `gradle_options` and never removed.

## How to fix it
```diff
 - bundle::gradle_build:
     inputs:
-    - options: --rerun-tasks
+    - options: --console=plain
```
→ `AND-G01`.

## How to confirm the fix
`gradle.from_cache_share` rises from `0` back to the `AND-G01` baseline once the flag is removed.

## Seen in the wild
Flag left over from local debugging, committed into the CI workflow's Gradle options and never
noticed because the build still passes — it's just slower and uncached.

## References
- `docs/PROJECT_SPEC.md` §3.3, §6.1
- `scenarios/catalog.yml` (`AND-B05`)
