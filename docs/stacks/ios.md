# iOS / Xcode

Pipeline: `showcase-ios`. Sample project: `projects/ios` — a real XcodeGen-generated single-target
SwiftUI app (`project.yml` is the committed source of truth; `ShowcaseiOS.xcodeproj` is
regenerated fresh every run, never committed, per spec §4.3). No code signing required — builds
target the iOS Simulator only.

This is the first stack in this repo using Bitrise's **remote Build Cache** mechanism rather than
key-based caching (see `docs/concepts/caching-mechanisms.md`) — same mechanism family as
Android/Gradle, different backend (`activate-build-cache-for-xcode` instead of
`activate-build-cache-for-gradle`).

## Scenarios implemented so far

| ID | Verdict | Title |
|---|---|---|
| [IOS-G01](../scenarios/ios/IOS-G01.md) | ✅ good | Correct setup (Xcode 26+, simulator build) |
| [IOS-B01](../scenarios/ios/IOS-B01.md) | ❌ bad | Old Xcode = silent no-op |
| [IOS-B03](../scenarios/ios/IOS-B03.md) | ❌ bad | Shim bypass via absolute path |
| [IOS-B04](../scenarios/ios/IOS-B04.md) | ❌ bad | Volatile Swift flag |
| [IOS-B05](../scenarios/ios/IOS-B05.md) | ❌ bad | Activation after build |

`IOS-G02` (archive build), `IOS-B02` (DerivedData caching alongside Build Cache), `IOS-B06`
(`no_swift_cache` as default), `IOS-B07`/`IOS-B08` (CocoaPods key mistakes — this project doesn't
use CocoaPods yet), `IOS-B09` (caching Archives/CoreSimulator), `IOS-R01` (regression guard), and
`IOS-B10` remain `status: planned`.

## Key mechanics

- **Activation must run before any `xcodebuild` invocation** (`IOS-B05`), same lesson as Gradle's
  `AND-B02`.
- **Activation only intercepts invocations that go through its own mechanism** (`IOS-B03`): a
  script, build tool, or third-party step calling the real `xcodebuild` binary directly bypasses
  it entirely, even with activation green.
- **Xcode version matters** (`IOS-B01`): Build Cache for Xcode needs Xcode 26+; on an older stack
  it's a silent no-op.
- **Volatile compiler flags bust the whole module's cache** (`IOS-B04`): the Swift/Clang analogue
  of `AND-B03`'s volatile `BuildConfig` field.

## Resolved from this stack's real runs (builds 28–33, 2026-11-26)

The original open question — whether `activate-build-cache-for-xcode@1.10.1`'s alias/PATH-based
interception reaches the **official** `xcode-build-for-simulator` step — was never the real blocker.
The mechanism works fine: activation exports the updated `PATH` via `envman`, and the build step
resolves `xcodebuild` through it.

Three real things were found and fixed along the way, each caught by reading raw logs/assertion
failures rather than assumed:

1. **Workspace entitlement gate** (build 28): Build Cache for Xcode needs to be enabled for the
   workspace — `Bitrise Build Cache auto-activation skipped: workspace ... is not enabled for it`.
   Fixed by the user enabling it via the Bitrise UI.
2. **Metrics bug — wrong log source** (builds 29–30): the real `Proxy blob stats`/`SetSession`
   telemetry lives in a dedicated `xcelerate-<uuid>.log` that the activation step writes into
   `$BITRISE_DEPLOY_DIR`, not in xcodebuild's own text output. Fixed in
   `.bitrise/bundles/xcode.yml`.
3. **Metrics bug — wrong "engaged" definition** (builds 31–32): `SetSession called` succeeds even
   when zero compilation units are ever submitted to the cache — confirmed on `IOS-B01` (Xcode
   16.4): real log ends with `hits: 0 / total: 0`. Fixed `remote_cache.engaged` to require real
   traffic (`proxy_total > 0`), not just a successful handshake, in
   `tools/metrics/merge_fragments.py`.

**Final clean run (build 33)**: all 5 `IOS-*` assertions pass for real reasons. `IOS-G01` shows real
cache hits (252/254, same project state as later confirmed in `IOS-B01`'s build). `IOS-B01` (old
Xcode) shows zero real cache traffic despite a successful handshake. `IOS-B03` (bypass) and `IOS-B05`
(wrong order) both show no xcelerate log at all. See `docs/reference/verified-facts.md` for the full
timeline and build IDs.
