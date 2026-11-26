# Android / Gradle

Pipeline: `showcase-android`. Sample project: `projects/android` (Kotlin/JVM multi-module project —
see `projects/android/README.md` for why it's plain Kotlin/JVM rather than a real Android Gradle
Plugin project, and how the two showcase hooks, `showcaseNs` and `SHOWCASE_VOLATILE_BUILDCONFIG`,
work). Build command for every scenario: `./gradlew :app:assembleDebug :core:model:testDebugUnitTest
--console=plain` (identical across scenarios except where the defect *is* the command, e.g.
`AND-B05`'s `--rerun-tasks`).

## Scenarios implemented so far

| ID | Verdict | Title |
|---|---|---|
| [AND-G01](../scenarios/android/AND-G01.md) | ✅ good | Correct setup |
| [AND-B01](../scenarios/android/AND-B01.md) | ❌ bad | "Cached" but no Build Cache |
| [AND-B02](../scenarios/android/AND-B02.md) | ❌ bad | Activation after the build |
| [AND-B03](../scenarios/android/AND-B03.md) | ❌ bad | Volatile BuildConfig in core module |
| [AND-B05](../scenarios/android/AND-B05.md) | ❌ bad | `--rerun-tasks` left in CI args |
| [AND-B09](../scenarios/android/AND-B09.md) | ❌ bad | Nobody pushes |

The remaining `AND-*` scenarios from `docs/PROJECT_SPEC.md` §6.1 (`AND-G02`, `AND-B04`, `AND-B06`
through `AND-B14`) are catalogued (`scenarios/catalog.yml`, `status: planned`) with doc stubs but
not yet implemented — see `CLAUDE.md` "Scope status".

## Key mechanics (see `docs/concepts/caching-mechanisms.md` for the full picture)

- `activate-build-cache-for-gradle` must run after checkout and before the first Gradle invocation.
- The wrapper + dependency cache (`~/.gradle/wrapper`, `~/.gradle/caches/modules-2`) is a *separate*,
  key-based cache (`bundle::gradle_deps_cache_restore`/`_save`) — it solves a different problem than
  the remote Build Cache and having one does not imply the other is working (`AND-B01`).
- Metrics collection: `tools/metrics/gradle/showcase-metrics.init.gradle.kts`, a configuration-cache
  compatible Gradle init script registered via `--init-script` in `tools/run-gradle.sh`.
