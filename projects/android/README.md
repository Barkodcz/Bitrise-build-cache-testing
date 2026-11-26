# Android build-cache showcase (fixture project)

Plain Kotlin/JVM multi-module Gradle project that mimics the shape of a multi-module
Android app, without depending on the Android Gradle Plugin / Android SDK. It builds with
just a JDK (tested with Gradle 8.11 + JDK 21).

## Layout

- `:core:common` — widely-depended core module (`com.showcase.core.common.Core`).
- `:core:model` — depends on `:core:common`; has a JUnit 5 test.
- `:feature:leaf` — depends on `:core:common`; `feature/leaf/src/main/kotlin/com/showcase/featureleaf/Leaf.kt`
  has a `return "leaf-v1"` line that `tools/simulate-change.sh` mutates to simulate a code change.
- `:app` — depends on all of the above; an `application`-plugin module.

Because this is plain Kotlin/JVM (not AGP), the real task names are `:app:assemble` /
`:core:model:test`. To keep existing tooling (`tools/run-gradle.sh`) working unmodified,
each module registers an AGP-style alias: `:app:assembleDebug` (→ `assemble`) and
`:core:model:testDebugUnitTest` (→ `test`).

## Showcase hooks

- **`-PshowcaseNs=<value>`** — a Gradle project property read in the root `build.gradle.kts`
  and wired into `KotlinCompile`/`Test` task inputs across all modules so it participates in
  up-to-date/build-cache checks.
- **`SHOWCASE_VOLATILE_BUILDCONFIG=true`** — read by `:core:common`'s `generateShowcaseBuildConfig`
  task. When `true`, it bakes `System.currentTimeMillis()` into a generated
  `ShowcaseBuildConfig.BUILD_TIME` constant and marks the task never-up-to-date/non-cacheable,
  so every build misses the cache (scenario AND-B03). When unset/`false` (default), the
  constant is fixed at `0L`, keeping inputs stable so cache hits are possible (scenario AND-G01).

## Verifying locally

```
./gradlew :app:assembleDebug :core:model:testDebugUnitTest --console=plain
SHOWCASE_VOLATILE_BUILDCONFIG=true ./gradlew :app:assembleDebug :core:model:testDebugUnitTest --console=plain
```

Both should exit `0`.
