---
id: IOS-B01
verdict: bad
stack: ios
fix_ref: IOS-G01
tags: [unsupported-xcode-version]
---
# IOS-B01 — Old Xcode = silent no-op

**In one sentence:** the exact same workflow as `IOS-G01`, run on an Xcode 16.4 stack instead of
Xcode 26+ — the activation step reports success either way, but Build Cache for Xcode is an Xcode
26+ compilation-caching feature, so on an older Xcode it's a complete no-op with zero cache
traffic.

## What the configuration does
`.bitrise/workflows/ios.yml` `ios-b01__*` — identical bundle structure to `IOS-G01`, only the
stack differs:

```yaml
# ios-g01 — stack: osx-xcode-latest-stable (Xcode 27.x)
# ios-b01 — stack: osx-xcode-16.4.x
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::xcode_build_cache: {}
- bundle::xcode_build_sim: { ... }
- bundle::collect_metrics: {}
- bundle::deploy_metrics: {}
```

## What you see
- Log evidence (real, build 28): `xcode_version: 16.4`, activation step still prints
  `✅ Bitrise Build Cache for Xcode activated` (no error, no version warning), then
  `All active build tools in baseline benchmark mode (xcode=baseline (cache disabled)): cache
  disabled, analytics only`.
- Metrics: `remote_cache.engaged == false`, `found_any_signal == false`.
- **Caveat found on this first real run**: this workspace currently lacks the Build Cache for
  Xcode entitlement entirely (`docs/reference/verified-facts.md`), so `IOS-G01` shows the identical
  `engaged == false` signature right now — this scenario's *intended* distinguishing factor (old
  Xcode version) can't yet be isolated from that workspace-level gate. The assertion still passes
  (for the right surface value), but doesn't yet prove the Xcode-version-specific symptom on its
  own; re-verify once the workspace entitlement is granted.

## Why it happens
Build Cache for Xcode relies on Xcode 26's own compilation-caching infrastructure
(`-clang-build-session-file`/compilation-cache integration) — it isn't a Bitrise-side mechanism
layered on top of an arbitrary Xcode version. Running the activation step on a stack whose Xcode
predates that feature is harmless but useless: the step still exits successfully (there's nothing
for it to fail on), it just has nothing to hook into.

## How to fix it
```diff
 meta:
   bitrise.io:
-    stack: osx-xcode-16.4.x
+    stack: osx-xcode-latest-stable
```
→ `IOS-G01`.

## How to confirm the fix
`remote_cache.engaged` flips from `false` to `true`, and real cache hit/miss numbers appear in the
measure-phase metrics once the stack moves to Xcode 26+.

## Seen in the wild
Easy to miss because the activation step never fails or warns on an unsupported Xcode version — it
just does nothing useful, and a quick glance at a green pipeline gives no indication anything is
wrong.

## References
- `docs/PROJECT_SPEC.md` §3.4, §6.2
- `scenarios/catalog.yml` (`IOS-B01`)
