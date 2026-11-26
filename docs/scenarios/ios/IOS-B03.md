---
id: IOS-B03
verdict: bad
stack: ios
fix_ref: IOS-G01
tags: [shim-bypass]
---
# IOS-B03 — Shim bypass via absolute path

**In one sentence:** the build calls `/usr/bin/xcodebuild` directly by absolute path (simulating
Tuist, a custom fastlane lane, or any script that doesn't go through Bitrise's own build step),
instead of using the official `xcode-build-for-simulator` step — activation still runs and reports
success, but the actual build never goes through it.

## What the configuration does
`.bitrise/workflows/ios.yml` `ios-b03__*` — same activation step as `IOS-G01`, but the build step
is replaced with `bundle::xcode_build_sim_bypass` (`.bitrise/bundles/xcode.yml`), which calls
`/usr/bin/xcodebuild` directly in a plain script step instead of the official build step:

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::xcode_build_cache: {}
- bundle::xcode_build_sim_bypass:           # /usr/bin/xcodebuild, NOT xcode-build-for-simulator
    inputs:
    - scheme: "ShowcaseiOS"
- bundle::collect_metrics: {}
- bundle::deploy_metrics: {}
```

## What you see
- Log evidence (real, build 33, workspace enabled for Build Cache for Xcode): activation reports
  `✅ Bitrise Build Cache for Xcode activated`, then the build runs `/usr/bin/xcodebuild build`
  directly (absolute path, bypassing `xcode-build-for-simulator`) and succeeds normally.
- Metrics: `remote_cache.engaged == false`, `found_any_signal == false` — **no `xcelerate-*.log`
  file exists at all** in `$BITRISE_DEPLOY_DIR` for this build, unlike every other `IOS-*` scenario
  (which all produce one, win or lose). The direct absolute-path call never goes through the
  wrapper that would have written it — confirmed now that `IOS-G01`/`IOS-B01` are known to
  genuinely produce that file in the same workspace.

## Why it happens
`activate-build-cache-for-xcode` intercepts `xcodebuild` invocations via a mechanism tied to how
it's invoked (per the step's own description, a shell alias added to `~/.zshrc`/`~/.bashrc`,
intended for interactive-shell-style invocations). A script, build tool, or third-party step that
calls the real `xcodebuild` binary directly — by absolute path, or in a way that doesn't consult
that alias — bypasses the interception entirely. The activation step has no way to know this
happened; it only configures the environment, it doesn't (and can't) verify that every later build
invocation actually goes through it.

## How to fix it
```diff
-- bundle::xcode_build_sim_bypass:
-    inputs:
-    - scheme: "ShowcaseiOS"
+- bundle::xcode_build_sim:
+    inputs:
+    - scheme: "ShowcaseiOS"
+    - xcconfig_content: |-
+        CODE_SIGNING_ALLOWED=NO
+        COMPILER_INDEX_STORE_ENABLE=NO
```
(use the official step, or at minimum call `xcodebuild` by name through a shell that has sourced
the activation step's alias) → `IOS-G01`. With Tuist specifically: run `tuist generate` to produce
the `.xcodeproj`, then build it with a normal Xcode step — that combination is fine; it's calling
`xcodebuild`/`xcrun` directly that bypasses the interception.

## How to confirm the fix
`remote_cache.engaged` flips to `true` once the build goes through a path the activation step's
interception actually covers.

## Seen in the wild
The classic Tuist/custom-fastlane-config failure mode — activation looks completely fine in the
logs, but the tool actually driving compilation never goes through it.

## References
- `docs/PROJECT_SPEC.md` §3.4, §6.2
- `scenarios/catalog.yml` (`IOS-B03`)
