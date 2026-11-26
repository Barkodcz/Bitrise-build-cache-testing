---
id: RS-G01
verdict: good
stack: rust
fix_ref: null
tags: [scoped-target-key, pinned-toolchain]
---
# RS-G01 — cargo registry + scoped target/ cache

**In one sentence:** the Cargo registry (`~/.cargo/registry`, `~/.cargo/git`) and the `target/`
build-output directory are key-cached separately, with the `target/` key scoped by toolchain
version and build profile on top of `Cargo.lock`'s checksum.

## What the configuration does
`.bitrise/workflows/rust.yml` `rs-g01__*`, via `.bitrise/bundles/key-based.yml` `kb_restore`/`kb_save`
and `rust_build`:

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::kb_restore:
    inputs:
    - key: cargo-registry-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/rust/Cargo.lock" }}
    - name: cargo-registry
- bundle::kb_restore:
    inputs:
    - key: cargo-target-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-1.82.0-release-{{ checksum "projects/rust/Cargo.lock" }}
    - name: cargo-target
- bundle::rust_build:
    inputs:
    - toolchain: "1.82.0"
    - profile: "release"
- bundle::kb_save: { ... same registry key, paths: ~/.cargo/registry / ~/.cargo/git }
- bundle::kb_save: { ... same target key (with toolchain+profile), paths: projects/rust/target }
```

`tools/run-rust.sh` always installs the pinned `toolchain` from scratch via `rustup` (official
installer) rather than relying on whatever's preinstalled on the stack — this is what makes
`RS-B02`'s toolchain-drift scenario meaningful: seed and measure can genuinely run different real
Rust versions.

## What you see
- Log evidence: `> _To be captured from a real run._`
- Metrics: `key_based.restore_hit` in `["exact", "partial"]` on the measure run for both the
  `cargo-registry` and `cargo-target` entries.

## Why it doesn't need a fix
N/A — this is the GOOD baseline. `RS-B01` and `RS-B02` both point back here.

## How to confirm it's working
Both `kb_restore` steps report a non-`false` `restore_hit`, and `cargo build`/`cargo test` run
noticeably faster on the measure build than a genuinely cold run would.

## Seen in the wild
Baseline every `RS-B*` scenario is compared against — the registry (downloaded crate sources) and
`target/` (compiled artifacts, profile- and toolchain-specific) are different kinds of cache with
different scoping needs, the same lesson as `GO-G01`'s module-cache/build-cache split.

## References
- `docs/PROJECT_SPEC.md` §6.9
- `scenarios/catalog.yml` (`RS-G01`)
