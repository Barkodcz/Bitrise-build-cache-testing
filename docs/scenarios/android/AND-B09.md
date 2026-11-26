---
id: AND-B09
verdict: bad
stack: android
fix_ref: AND-G01
tags: [push-disabled-everywhere]
---
# AND-B09 — Nobody pushes

**In one sentence:** Both the seed and measure workflows run with `push: false`, so the remote
cache is never populated by anyone — a perfectly-placed activation step with nothing to read.

## What the configuration does
`.bitrise/workflows/android.yml` `and-b09__*` — same as `AND-G01` except `gradle_build_cache`'s
`push` input:

```yaml
- bundle::gradle_build_cache:
    inputs:
    - push: 'false'
```

## What you see
- Pipeline graph: measure duration ≈ seed duration.
- Log evidence: `> _To be captured from a real run._` — activation step reports success but with
  push disabled; no new cache entries show up between seed and measure.
- Metrics: `remote_cache.engaged == false`, `gradle.from_cache_share == 0`.

## Why it happens
`push: false` is the correct, intentional setting for read-only workflows (e.g. untrusted PR
branches) *as long as some other, trusted workflow pushes*. This scenario simulates the case where
**every** workflow in the workspace — including the one that should be the canonical writer — has
push disabled, so the remote cache is permanently empty: there is nothing wrong with any individual
workflow's configuration, only with the posture across the whole workspace.

## How to fix it
```diff
 - bundle::gradle_build_cache:
     inputs:
-    - push: 'false'
+    - push: 'true'
```
At least one workflow (typically the main/nightly branch) must push. → `AND-G01`.

## How to confirm the fix
`remote_cache.engaged` and `gradle.from_cache_share` rise once at least one workflow's `push` is
`true` and has run at least once before the measure build.

## Seen in the wild
Common on workspaces that enabled Build Cache only on PR workflows, which are read-only by policy —
without a separate always-push main-branch workflow, the cache never gets populated in the first
place.

## References
- `docs/PROJECT_SPEC.md` §3.3, §6.1
- `scenarios/catalog.yml` (`AND-B09`)
