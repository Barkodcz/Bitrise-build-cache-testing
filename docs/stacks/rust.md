# Rust (key-based caching)

Pipeline: `showcase-rust`. Sample project: `projects/rust` — a genuine Cargo workspace with two
crates (`crates/core`, depending on `serde`/`serde_json` including a proc-macro derive for real
compile weight; `crates/leaf`, a binary depending on `core`). `Cargo.lock` is pinned at lockfile
format version 3 deliberately, so it stays readable by both an old (1.75.0) and a current (1.82.0)
toolchain — needed for `RS-B02`'s toolchain-drift scenario.

Rust has **no Bitrise Build Cache backend** — everything here is key-based caching (see
`docs/concepts/caching-mechanisms.md`), same as Node.js/Go.

## Scenarios implemented so far

| ID | Verdict | Title |
|---|---|---|
| [RS-G01](../scenarios/rust/RS-G01.md) | ✅ good | cargo registry + scoped `target/` cache |
| [RS-B01](../scenarios/rust/RS-B01.md) | ❌ bad | `target/` keyed only on `Cargo.lock` across profiles |
| [RS-B02](../scenarios/rust/RS-B02.md) | ❌ bad | No `rust-toolchain.toml`, floating toolchain |

## Key mechanics

- **Two separate caches with different scoping needs** (spec §6.9): `~/.cargo/registry` +
  `~/.cargo/git` (downloaded crate sources, keyed on `Cargo.lock` alone) vs. `target/` (compiled
  artifacts, which must also be scoped by toolchain version and build profile — `RS-B01`/`RS-B02`
  both demonstrate what happens when that extra scoping is missing).
- `tools/run-rust.sh` always installs the pinned toolchain from scratch via `rustup` (the official
  installer), not whatever's preinstalled on the stack, so seed and measure can genuinely run
  different real Rust versions for `RS-B02`.
