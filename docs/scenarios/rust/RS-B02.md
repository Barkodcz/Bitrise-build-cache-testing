---
id: RS-B02
verdict: bad
stack: rust
fix_ref: RS-G01
tags: []
---
# RS-B02 — No rust-toolchain.toml, floating toolchain

**In one sentence:** Invalidation after a toolchain update (simulated via RUSTUP_TOOLCHAIN change).

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** Toolchain not pinned; target/ cache key doesn't include it.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
Fixed by following `RS-G01`.

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`RS-B02`)
