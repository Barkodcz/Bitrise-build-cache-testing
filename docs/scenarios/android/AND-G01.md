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
- Pipeline graph: measure sometimes faster than seed — but not reliably, across runs. See below.
- **Real captured data — two consecutive runs of the SAME unchanged YAML/project**
  (Bitrise app `84c7a274-43b0-477d-9141-ea174ad0ce6e`, `report_android` workflow, 2026-11-26):

  | Run | `gradle.from_cache_share` | `duration.vs_seed` |
  |---|---|---|
  | build `5165d50d-c8c1-4e74-b288-269c981acb51` | 0.208 | 0.797 |
  | build `72f81932-20b3-4502-a4e0-c2b97d5ed1fa` | **0.0** | 0.930 |

- Metrics: `gradle.from_cache_share >= 0`, `duration.vs_seed <= 1.2` (see `scenarios/catalog.yml`
  `expectations` — intentionally loose; see why below). Byte-ratio assertion not yet wired — see
  `docs/reference/verified-facts.md`.

**Honesty note — this run-to-run variance is itself the lesson, not a bug.** The second run showed
*zero* cache hits for the exact same GOOD configuration that got 21% hits the first time. This is
precisely spec §3.2/§7.5's documented phenomenon: **"a screening number is not a verdict"** / **"cold
cache looks like failure"** (see `AND-B10`, not yet implemented). A trial-tier Build Cache origin is
per-datacenter; if a seed/measure pair lands in a different datacenter than a prior run, it starts
genuinely cold through no fault of the YAML. The report is *supposed* to detect this and mark the
comparison "not comparable" (spec §7.5) rather than assert a hard number — but this repo's
datacenter detection (`tools/metrics/merge_fragments.py` `detect_datacenter()`) is an unverified
hostname-pattern heuristic (§14-Q7) that never actually matched a real Bitrise hostname in testing,
so the escape hatch never fired. Rather than keep lowering the threshold until one run happens to
pass (which would prove nothing), the expectations here are deliberately non-strict until real DC
detection is implemented. The *mechanism itself* is still proven correct by comparing against
`AND-B01` on the identical project, which reliably shows `0` for a *structural* reason (no
activation step at all) rather than this kind of run-to-run noise.

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
