---
id: RS-B02
verdict: bad
stack: rust
fix_ref: RS-G01
tags: [toolchain-drift]
---
# RS-B02 — No rust-toolchain.toml, floating toolchain

**In one sentence:** the seed build compiles with Rust 1.75.0, the measure build with Rust 1.82.0 —
the `cargo-target` cache key never includes the toolchain version, so a restored entry can report a
hit against an incompatible toolchain.

## What the configuration does
`.bitrise/workflows/rust.yml` `rs-b02__*` — identical bundle structure to `RS-G01`, but
`bundle::rust_build`'s `toolchain` input differs between phases, while the `cargo-target` key stays
the plain `checksum_only` form (no toolchain/profile suffix) in both:

```yaml
# rs-b02__1_seed
- bundle::rust_build:
    inputs:
    - toolchain: "1.75.0"
    - profile: "release"

# rs-b02__2_measure
- bundle::rust_build:
    inputs:
    - toolchain: "1.82.0"
    - profile: "release"
```

`tools/run-rust.sh` installs each pinned version from scratch via `rustup` — Rust keeps every past
stable release downloadable indefinitely, so pinning two real, years-apart versions here is safe
long-term (verified locally: both `1.75.0` and `1.82.0` installed and built cleanly).

## What you see
- **Real captured log** (`rs-b02__2_measure`, build 23, app `84c7a274-43b0-477d-9141-ea174ad0ce6e`, 2026-11-26):
  ```
  keybased_record: restore name=cargo-registry hit=exact
  keybased_record: restore name=cargo-target hit=exact
  run-rust.sh: using cargo 1.82.0 (8f40fc59f 2024-08-21)
  ```
  — this is the measure run; the seed run used Rust `1.75.0`. The `cargo-target` entry still reports
  `hit=exact` even though the underlying toolchain changed, confirming the symptom exactly as
  designed: an exact key match restoring cache content built by an incompatible toolchain.
- Metrics: the `cargo-target` entry's `restore_hit` can still report a hit (the literal key string
  matched), but the restored cache was compiled by a different Rust toolchain than the one now
  running.

## Why it happens
Rust's compiled artifact format and metadata encoding are toolchain-version-specific — a `target/`
tree built by 1.75.0 is not guaranteed to be safely reusable by 1.82.0. Pinning *which* toolchain a
workflow runs (a `rust-toolchain.toml`, or this repo's own `toolchain` bundle input) solves "are seed
and measure using the same compiler" — but it does nothing to stop a *stale* cache entry built by a
different toolchain from being restored under the same key, wasting restore time/bandwidth while
Cargo's own fingerprinting still has to recompile everything anyway.

## How to fix it
```diff
-    key: cargo-target-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/rust/Cargo.lock" }}
+    key: cargo-target-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ getenv "SHOWCASE_TOOLCHAIN" }}-{{ checksum "projects/rust/Cargo.lock" }}
```
(so a toolchain change naturally busts the key instead of restoring a now-useless entry) →
`RS-G01`, with both phases pinned to the **same** toolchain (and ideally a committed
`rust-toolchain.toml` in a real project, so the pin lives with the code, not just the CI config).

## How to confirm the fix
Once the key includes the toolchain version, a version change produces a clean cache **miss**
instead of a wasted "hit" — and once both phases agree on one toolchain (the actual fix), the build
cache delivers its expected speedup.

## Seen in the wild
Pinning the toolchain is necessary but not sufficient on its own — the cache key itself should
include the version too, the same lesson `GO-B02` teaches for Go and `AND-B08` teaches for Gradle/JDK.

## References
- `docs/PROJECT_SPEC.md` §6.9
- `scenarios/catalog.yml` (`RS-B02`)
