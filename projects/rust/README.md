# projects/rust

Minimal Cargo workspace used by the key-based caching scenarios (`scenarios/catalog.yml` `RS-*`).
Two crates: `crates/core` (depends on `serde`/`serde_json`, including a proc-macro derive, so
there's real, non-trivial compile work worth caching) and `crates/leaf` (a binary depending on
`core`; `tools/simulate-change.sh rust leaf` mutates its `label()` return value).

`cargo build --profile <profile>` and `cargo test` are the two commands every `RS-*` scenario runs,
via `tools/run-rust.sh <toolchain> <profile>`, which always installs the pinned toolchain from
scratch via `rustup` (not whatever's preinstalled on the stack) — this is what makes `RS-B02`'s
toolchain-drift scenario meaningful.
