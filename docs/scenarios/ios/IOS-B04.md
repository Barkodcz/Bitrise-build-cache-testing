---
id: IOS-B04
verdict: bad
stack: ios
fix_ref: IOS-G01
tags: [volatile-input]
---
# IOS-B04 — Volatile Swift flag

**In one sentence:** `OTHER_SWIFT_FLAGS` bakes in `$(BITRISE_BUILD_NUMBER)`, a value that changes
on every single build — so every Swift compile unit in the whole app gets a new cache key every
time, regardless of whether any source code actually changed.

## What the configuration does
`.bitrise/workflows/ios.yml` `ios-b04__*` — same as `IOS-G01` except an extra `xcconfig_content`
line:

```yaml
- bundle::xcode_build_sim:
    inputs:
    - scheme: "ShowcaseiOS"
    - xcconfig_content: |-
        CODE_SIGNING_ALLOWED=NO
        COMPILER_INDEX_STORE_ENABLE=NO
        OTHER_SWIFT_FLAGS = $(inherited) -DBUILD_$(BITRISE_BUILD_NUMBER)
```

## What you see
- Log evidence (real, build 33, workspace enabled for Build Cache for Xcode): the generated
  xcconfig content for this scenario is visible in the step log —
  `OTHER_SWIFT_FLAGS = $(inherited) -DBUILD_$(BITRISE_BUILD_NUMBER)` — confirming the volatile flag
  was actually passed to the build.
- Metrics: `found_any_signal == true` — a real `xcelerate-*.log` with a `Proxy blob stats` line
  exists (activation genuinely ran and the wrapper was used), unlike `IOS-B03`/`IOS-B05`. The exact
  hit/total counts for this run weren't re-extracted from the console in this pass (they're only in
  the deployed metrics JSON artifact, not echoed to the human-readable build log) — expected to be
  low/near-zero given every build gets a unique `$BITRISE_BUILD_NUMBER`-based flag, but this exact
  number is a documented gap rather than a fabricated one; see `docs/reference/verified-facts.md`.

## Why it happens
Swift's (and Clang's) compile cache keys on the exact invocation, including every compiler flag.
`$(BITRISE_BUILD_NUMBER)` is a Bitrise-provided environment variable that increments on every
single build, so `-DBUILD_<N>` is a different literal flag every time — which changes the cache key
for every `.swift` file in the module, every single build, regardless of whether any source file
actually changed. This is the Xcode/Swift equivalent of `AND-B03`'s volatile `BuildConfig` field.

## How to fix it
```diff
         CODE_SIGNING_ALLOWED=NO
         COMPILER_INDEX_STORE_ENABLE=NO
-        OTHER_SWIFT_FLAGS = $(inherited) -DBUILD_$(BITRISE_BUILD_NUMBER)
```
If a build number genuinely needs to reach the app, set it via `Info.plist`/`CURRENT_PROJECT_VERSION`
at archive time instead of as a compiler flag that participates in every compile unit's cache key →
`IOS-G01`.

## How to confirm the fix
`remote_cache.hits` rises back toward `IOS-G01`'s baseline once the volatile value is removed from
compile-time flags.

## Seen in the wild
Any volatile value injected into a widely-applied compiler flag busts every single compile unit's
cache key — the same lesson as `AND-B03` (Gradle), `GO-B02`/`RS-B02` (toolchain version in the
key), just applied to a compiler invocation flag instead.

## References
- `docs/PROJECT_SPEC.md` §3.4, §6.2
- `scenarios/catalog.yml` (`IOS-B04`)
