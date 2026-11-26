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

## Open verification question for this stack's first real run

`activate-build-cache-for-xcode@1.10.1`'s own description says it "adds an alias to `~/.zshrc` and
`~/.bashrc`" to wrap subsequent `xcodebuild` invocations — a different mechanism than the PATH-shim
description in `docs/PROJECT_SPEC.md` §3.4/§6.2 (written against an older step version). Whether
this alias-based interception actually reaches the **official** `xcode-build-for-simulator` step
(a compiled toolkit, not an interactive shell that would source `.bashrc`) is genuinely unverified
— `IOS-G01`'s first real run is exactly what will answer this. See
`docs/reference/verified-facts.md`.
