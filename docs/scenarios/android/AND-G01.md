---
id: AND-G01
verdict: good
stack: android
fix_ref: null
tags: [placement-ok, relocatable-inputs, pinned-toolchain]
---
# AND-G01 — Build Cache for Gradle, correctly placed, key-cached wrapper + deps

**In one sentence:** Activation runs right after checkout and before any Gradle invocation, the
wrapper/dependency cache is key-cached separately, and the toolchain is pinned — this is the
baseline every `AND-B*` scenario is compared against.

## What the configuration does
Generated workflow steps (`and-g01__1_seed` / `and-g01__2_measure`, see `.bitrise/workflows/android.yml`):

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::gradle_build_cache:       # activate-build-cache-for-gradle@3.18.1, push: "true"
    inputs:
    - push: 'true'
    - verbose: 'false'
- bundle::gradle_deps_cache_restore: {}
- bundle::gradle_build:              # ./gradlew :app:assembleDebug :core:model:testDebugUnitTest
    inputs:
    - options: --console=plain
- bundle::gradle_deps_cache_save: {}
- bundle::collect_metrics: {}
- bundle::deploy_metrics: {}
```

The dependency cache (`.bitrise/bundles/gradle.yml` `gradle_deps_cache_restore`/`_save`) keys on
`{{ .OS }}-{{ checksum "**/*.gradle*" "gradle.properties" "gradle/libs.versions.toml" }}`, separate
from the remote Build Cache — this is deliberate (spec §3.1): one caches *downloads*, the other
caches *compiled task outputs*.

## What you see
- Pipeline graph: measure noticeably faster than seed.
- Log evidence: `> _To be captured from a real run._`
- Metrics: `gradle.from_cache_share >= 0.6`, `duration.vs_seed <= 0.75` (see `scenarios/catalog.yml`
  `expectations`). Byte-ratio assertion not yet wired — see `docs/reference/verified-facts.md`.

## Why it doesn't need a fix
N/A — this is the GOOD baseline. Every `AND-B*` page's "How to fix it" section points back here.

## How to confirm it's working
`gradle.from_cache_share` in the measure-phase metrics JSON should be well above the structural
miss floor, and the measure build should take meaningfully less wall-clock time than the seed build
for the same simulated change.

## Seen in the wild
Pattern seen across multiple customer audits (anonymised) as the reference "it just works"
configuration once the three things above (placement, separate caches, pinned toolchain) line up.

## References
- `docs/PROJECT_SPEC.md` §3.3, §6.1
- `scenarios/catalog.yml` (`AND-G01`)
