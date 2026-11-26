---
id: IOS-G01
verdict: good
stack: ios
fix_ref: null
tags: [placement-ok, official-steps, no-signing]
---
# IOS-G01 — Correct setup (Xcode 26+, simulator build)

**In one sentence:** `activate-build-cache-for-xcode` runs right after checkout, before the only
build step in the workflow (the official `xcode-build-for-simulator` step), on a real Xcode 26+
stack (`osx-xcode-latest-stable`).

## What the configuration does
`.bitrise/workflows/ios.yml` `ios-g01__*`, via `.bitrise/bundles/xcode.yml`:

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::xcode_build_cache: {}          # activate-build-cache-for-xcode@1.10.1, push: "true"
- bundle::xcode_build_sim:                # xcodegen generate + xcode-build-for-simulator@3.0.3
    inputs:
    - scheme: "ShowcaseiOS"
    - xcconfig_content: |-
        CODE_SIGNING_ALLOWED=NO
        COMPILER_INDEX_STORE_ENABLE=NO
- bundle::collect_metrics: {}
- bundle::deploy_metrics: {}
```

`projects/ios` is a real XcodeGen-generated single-target SwiftUI app (`project.yml` is the
committed source of truth; `ShowcaseiOS.xcodeproj` is regenerated fresh every run, never
committed). No code signing is required — `xcode-build-for-simulator`'s own default `xcconfig`
already sets `CODE_SIGNING_ALLOWED=NO`.

## What you see
- Log evidence (real, build 30, after the workspace was enabled for Build Cache for Xcode): the
  activation step's own `xcelerate-<uuid>.log` (deployed as a build artifact) ends with:
  ```
  Proxy blob stats: hits: 252 (103 MB) / total: 254 (99.21%). Uploaded blobs: 22 (280 kB)
  Proxy KV stats: hits: 126 / total: 128 (98.44%). Uploaded KV blobs: 2.4 kB
  Xcode task stats: hits: 126 / total: 128 (98.44%)
  ```
  A real 99.21% blob hit rate on the measure build.
- Metrics (build 33, final clean run): `remote_cache.engaged == true`, `found_any_signal == true`.
- Note: the Build Cache for Xcode telemetry lives in that dedicated `xcelerate-*.log`
  file in `$BITRISE_DEPLOY_DIR`, not in xcodebuild's own text output — see
  `docs/reference/verified-facts.md` for the full finding (this took two rounds of real-infra
  debugging to pin down correctly).

## Why it doesn't need a fix
N/A — this is the GOOD baseline. Every `IOS-B*` scenario's "How to fix it" section points back
here.

## How to confirm it's working
`remote_cache.engaged` is `true` and `remote_cache.hits`/`proxy_total` show real cache traffic on
the measure run.

## Seen in the wild
Baseline every `IOS-B*` scenario is compared against.

## References
- `docs/PROJECT_SPEC.md` §3.4, §6.2
- `scenarios/catalog.yml` (`IOS-G01`)
