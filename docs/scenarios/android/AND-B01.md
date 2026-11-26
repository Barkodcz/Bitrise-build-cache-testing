---
id: AND-B01
verdict: bad
stack: android
fix_ref: AND-G01
tags: [no-activation]
---
# AND-B01 — "Cached" but no Build Cache

**In one sentence:** Only the key-based dependency cache is configured; there is no
`activate-build-cache-for-gradle` step anywhere in the workflow, so there is zero remote
*task*-output caching even though the workflow "has caching."

## What the configuration does
`.bitrise/workflows/android.yml` `and-b01__1_seed` / `and-b01__2_measure` steps (no activation bundle at all):

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::gradle_deps_cache_restore: {}
- bundle::gradle_build:
    inputs:
    - options: --console=plain
- bundle::gradle_deps_cache_save: {}
- bundle::collect_metrics: {}
- bundle::deploy_metrics: {}
```

Compare with `AND-G01`: the only difference visible in the generated YAML is the **absence** of the
`bundle::gradle_build_cache` step — this is exactly the point (spec §7.1: the defect must be visible
in the YAML).

## What you see
- Pipeline graph: measure duration ≈ seed duration (no speed-up from a second build).
- Log evidence: `> _To be captured from a real run._` — expect every compile task as `EXECUTED`,
  never `FROM-CACHE`.
- Metrics: `remote_cache.engaged == false`, `gradle.from_cache_share == 0` (`tools/metrics/gradle/
  showcase-metrics.init.gradle.kts` still runs and classifies tasks even without activation — it
  just never sees any `FROM-CACHE` results to count).

## Why it happens
The key-based dependency cache (`~/.gradle/caches/modules-2`, `~/.gradle/wrapper`) restores
successfully — `npm`-equivalent exact hit — which makes the build *look* cached in a superficial
read of the logs (no re-download chatter). But that cache only avoids re-downloading dependency
jars; it does nothing for compiled task outputs. Without `activate-build-cache-for-gradle`, Gradle
has no remote endpoint to query for `FROM-CACHE` results, so every task still executes from scratch.
This is the single most common mistake found in Build Cache audits (spec §3.1): crediting key-based
caching for remote task caching.

## How to fix it
```diff
 steps:
 - bundle::setup_checkout: {}
 - bundle::setup_showcase: {}
+- bundle::gradle_build_cache: {}
 - bundle::gradle_deps_cache_restore: {}
 - bundle::gradle_build: {}
```
→ `AND-G01`.

## How to confirm the fix
`remote_cache.engaged` flips to `true` and `gradle.from_cache_share` rises well above `0` on the
measure run once the activation step is added back.

## Seen in the wild
Most common audit mistake across multiple customer reviews (anonymised): a workspace with excellent
key-based dependency caching and zero remote task caching, reported internally as "caching is
working" based on download-time improvements alone.

## References
- `docs/PROJECT_SPEC.md` §3.1, §3.3, §6.1
- `scenarios/catalog.yml` (`AND-B01`)
