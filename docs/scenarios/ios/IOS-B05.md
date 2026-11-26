---
id: IOS-B05
verdict: bad
stack: ios
fix_ref: IOS-G01
tags: [placement-wrong]
---
# IOS-B05 — Activation after build

**In one sentence:** `activate-build-cache-for-xcode` is a real, working step — it just runs
*after* `xcode-build-for-simulator`, so the build it was meant to accelerate gets zero benefit from
it.

## What the configuration does
`.bitrise/workflows/ios.yml` `ios-b05__*`:

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::xcode_build_sim: { ... }      # ← runs uncached: activation comes after
- bundle::xcode_build_cache: {}         # ← the defect, visible in the YAML
- bundle::collect_metrics: {}
- bundle::deploy_metrics: {}
```

## What you see
- Log evidence (real, build 33, workspace enabled for Build Cache for Xcode): `xcode-build-for-
  simulator` runs and succeeds *before* the `activate-build-cache-for-xcode` step's
  `✅ Bitrise Build Cache for Xcode activated` lines appear in the log — confirming the step order
  defect is real and visible, not just inferred from the YAML.
- Metrics: `remote_cache.engaged == false`, `found_any_signal == false` — **no `xcelerate-*.log`
  file exists at all** for this build, the same absence seen in `IOS-B03` (bypass), but for a
  different reason: here the wrapper *is* installed, just too late to see the build that already
  ran. Now that `IOS-G01` is confirmed to produce real hits in this same workspace, this absence
  cleanly demonstrates the ordering defect on its own.

## Why it happens
`activate-build-cache-for-xcode` configures the environment (an alias wrapping subsequent
`xcodebuild` invocations) before any build happens — any Xcode invocation that runs before this
step simply never sees that configuration. A green activation step gives a false sense that caching
is active for the whole workflow; it only applies to builds that come *after* it.

## How to fix it
```diff
 steps:
 - bundle::setup_checkout: {}
 - bundle::setup_showcase: {}
+- bundle::xcode_build_cache: {}
 - bundle::xcode_build_sim: { ... }
-- bundle::xcode_build_cache: {}
 - bundle::collect_metrics: {}
 - bundle::deploy_metrics: {}
```
→ `IOS-G01`.

## How to confirm the fix
`remote_cache.engaged` flips to `true` once activation moves before the build step.

## Seen in the wild
Same ordering mistake as `AND-B02`, for Xcode instead of Gradle — easy to introduce in a long
workflow where the activation step gets added at the end almost as an afterthought.

## References
- `docs/PROJECT_SPEC.md` §3.4, §6.2
- `scenarios/catalog.yml` (`IOS-B05`)
