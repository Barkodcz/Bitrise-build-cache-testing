---
id: AND-B02
verdict: bad
stack: android
fix_ref: AND-G01
tags: [placement-wrong]
---
# AND-B02 — Activation after the build

**In one sentence:** `activate-build-cache-for-gradle` is a real, working step — it just runs
*after* the Gradle build step, so the build it was meant to accelerate gets zero benefit from it.

## What the configuration does
`.bitrise/workflows/android.yml` `and-b02__*`:

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::gradle_deps_cache_restore: {}
- bundle::gradle_build: {}              # ← runs uncached: activation comes after
- bundle::gradle_build_cache: {}        # ← the defect, visible in the YAML
- bundle::gradle_deps_cache_save: {}
```

## What you see
- Pipeline graph: measure duration ≈ seed duration, same shape as `AND-B01`.
- Log evidence: `> _To be captured from a real run._` — the activation step itself reports success
  ("Cache plugin usage: enabled"-style output), but it runs after the build log already shows every
  task as `EXECUTED`.
- Metrics: `gradle.from_cache_share <= 0.2`.

## Why it happens
`activate-build-cache-for-gradle` works by writing `~/.gradle/init.d/bitrise-build-cache.init.gradle.kts`
and `~/.gradle/gradle.properties` *before* Gradle starts — any Gradle invocation that runs before
this step simply never sees those files. A green activation step gives a false sense that caching is
active for the whole workflow; it only applies to Gradle invocations that come *after* it.

## How to fix it
```diff
 steps:
 - bundle::setup_checkout: {}
 - bundle::setup_showcase: {}
+- bundle::gradle_build_cache: {}
 - bundle::gradle_deps_cache_restore: {}
 - bundle::gradle_build: {}
-- bundle::gradle_build_cache: {}
 - bundle::gradle_deps_cache_save: {}
```
→ `AND-G01`.

## How to confirm the fix
`gradle.from_cache_share` rises on the measure run once activation moves before the build step.

## Seen in the wild
Observed in yaml audits: activation step present and green, but ordered after the build step it was
meant to accelerate — easy to miss in a long workflow because the step itself never fails.

## References
- `docs/PROJECT_SPEC.md` §3.3, §6.1, §7.4
- `scenarios/catalog.yml` (`AND-B02`)
