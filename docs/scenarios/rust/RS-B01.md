---
id: RS-B01
verdict: bad
stack: rust
fix_ref: RS-G01
tags: [under-scoped-key, profile-mismatch]
---
# RS-B01 — target/ keyed only on Cargo.lock across profiles

**In one sentence:** the seed build compiles the `release` profile, the measure build compiles the
`dev` profile, but both share the exact same `cargo-target` cache key — restoring one profile's
`target/` into a build that wants the other profile's output is mostly useless, and whichever
profile ran most recently keeps overwriting the saved cache slot.

## What the configuration does
`.bitrise/workflows/rust.yml` `rs-b01__*` — same as `RS-G01` except the `cargo-target` key drops
the toolchain+profile suffix, and the profile itself differs between phases:

```yaml
# rs-b01__1_seed
- bundle::kb_restore:
    inputs:
    - key: cargo-target-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/rust/Cargo.lock" }}
- bundle::rust_build:
    inputs:
    - toolchain: "1.82.0"
    - profile: "release"

# rs-b01__2_measure
- bundle::kb_restore:
    inputs:
    - key: cargo-target-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/rust/Cargo.lock" }}
- bundle::rust_build:
    inputs:
    - toolchain: "1.82.0"
    - profile: "dev"
```

## What you see
- **Real captured log** (`rs-b01__2_measure`, build 23, app `84c7a274-43b0-477d-9141-ea174ad0ce6e`, 2026-11-26):
  ```
  keybased_record: restore name=cargo-registry hit=exact
  keybased_record: restore name=cargo-target hit=exact
  run-rust.sh: using cargo 1.82.0 (8f40fc59f 2024-08-21)
  ```
  — the seed built the `release` profile; this measure run builds `dev`, yet `cargo-target` still
  reports `hit=exact` under the shared, profile-agnostic key.
- Metrics: `key_based.restore_hit` may report a hit (the literal key string matches), but the
  restored `target/` was built for a different profile than the one now compiling — Cargo's own
  fingerprinting will notice the mismatch per-unit and recompile, so the restore time was wasted.

## Why it happens
`cargo build --release` and plain `cargo build` (dev profile) produce structurally different
artifacts under `target/release/` vs `target/debug/` — they don't even collide on disk within the
same `target/` directory, but restoring/saving the *whole* `target/` tree under one shared key means
every save overwrites the previous profile's half of the tree, and every restore brings back
whichever profile was saved last, regardless of which one the current build actually wants.

## How to fix it
```diff
-    key: cargo-target-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/rust/Cargo.lock" }}
+    key: cargo-target-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-1.82.0-release-{{ checksum "projects/rust/Cargo.lock" }}
```
(include the profile — and the toolchain, see `RS-B02` — in the key, and use the **same** profile in
both seed and measure) → `RS-G01`.

## How to confirm the fix
Once the key includes the profile, each profile gets its own cache slot and stops contending with
the other — restoring a `release` cache no longer competes with a `dev` build's own cache.

## Seen in the wild
Debug and release builds produce structurally different `target/` artifacts; a shared key means
whichever profile ran last "wins" the cache slot — a subtler version of `AND-B08`'s JDK-mismatch
lesson, scoped to a build profile instead of a toolchain version.

## References
- `docs/PROJECT_SPEC.md` §6.9
- `scenarios/catalog.yml` (`RS-B01`)
