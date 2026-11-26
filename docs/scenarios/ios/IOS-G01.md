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
- Log evidence (real, build 28): activation runs cleanly —
  `✅ Bitrise Build Cache for Xcode activated` — then `xcode-build-for-simulator` succeeds
  (`Archive Succeeded`). But right after activation, the log also shows:
  `Bitrise Build Cache auto-activation skipped: workspace "0f453e706a6f6bb6" is not enabled for it`
  and `All active build tools in baseline benchmark mode (xcode=baseline (cache disabled)): cache
  disabled, analytics only`.
- Metrics: `remote_cache.engaged == false`, `found_any_signal == false` — **not** because this
  config is wrong, but because this workspace currently lacks the Build Cache for Xcode
  entitlement, so every `IOS-*` scenario (including this GOOD baseline) runs in a cache-disabled
  analytics-only mode. See `docs/reference/verified-facts.md` for the full finding; re-run once the
  workspace is enabled to capture a real cache hit here.

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
