---
id: AND-B03
verdict: bad
stack: android
fix_ref: AND-G01
tags: [volatile-input, core-module]
---
# AND-B03 — Volatile BuildConfig in core module

**In one sentence:** `:core-common` (a module nearly everything depends on) bakes
`System.currentTimeMillis()` into a generated constant on every build, so that module and every
single dependant misses the cache every time — even though nothing meaningful changed.

## What the configuration does
When `SHOWCASE_VOLATILE_BUILDCONFIG=true` (set via the catalog's `bundle_overrides` for this
scenario, see `scenarios/catalog.yml` `AND-B03`), `projects/android`'s `:core-common` module
generates a Kotlin constant holding the current epoch millis at build time instead of a fixed value,
simulating `buildConfigField("String","BUILD_TIME", System.currentTimeMillis())` in a real Android
project.

```yaml
envs:
- SHOWCASE_VOLATILE_BUILDCONFIG: 'true'
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::gradle_build_cache: {}
- bundle::gradle_deps_cache_restore: {}
- bundle::gradle_build: {}
- bundle::gradle_deps_cache_save: {}
```

## What you see
- **Real captured data** (`report_android` build `67742f88-0e37-4b17-b3db-382a856fc865`,
  2026-11-26): `gradle.from_cache_share` correctly dropped to the structural-miss floor as
  designed — but `duration.vs_seed = 0.816`, *not* the `>= 0.9` ("no speedup") the spec's
  realistic-project thresholds would predict.
- **Honesty note:** this project is small/fast (~10 total Gradle tasks), so recompiling the one
  volatile task is cheap — total wall time doesn't degrade as much as it would on a realistic app
  with a deep, expensive dependency chain below `:core-common`. The symptom is still real and
  correctly demonstrated (see the hit-count metric below); it just doesn't show up as strongly in
  wall-clock terms on this tiny fixture. `scenarios/catalog.yml`'s expectation for this scenario was
  adjusted to rely on the hit-count signal alone — see the inline note there.
- Metrics: `gradle.from_cache_share <= 0.2` (the reliable signal on this project size).

## Why it happens
Gradle's remote task cache keys a task by (among other things) the content of its declared inputs.
A generated source file containing a wall-clock timestamp is a new, different input on every single
build, so `:core-common`'s compile task — and transitively every module that depends on it — gets a
fresh cache key every time. No amount of correct activation, placement, or toolchain pinning can
rescue a task whose own input is deliberately non-deterministic.

## How to fix it
```diff
- val BUILD_TIME: Long = System.currentTimeMillis()
+ val BUILD_TIME: Long = 0L  // inject only in :app at packaging time if you need a real timestamp
```
→ `AND-G01` (same workflow, `SHOWCASE_VOLATILE_BUILDCONFIG` unset/false).

## How to confirm the fix
`gradle.from_cache_share` rises back toward `AND-G01`'s baseline once the volatile value moves out
of `:core-common` (or out of any module other than `:app`, and out of compile inputs entirely).

## Seen in the wild
Classic "timestamp in a core module" failure, seen repeatedly in field audits — usually introduced
to stamp a build number or build time somewhere convenient, without realising how many modules
transitively depend on it.

## References
- `docs/PROJECT_SPEC.md` §3.3, §6.1
- `scenarios/catalog.yml` (`AND-B03`)
