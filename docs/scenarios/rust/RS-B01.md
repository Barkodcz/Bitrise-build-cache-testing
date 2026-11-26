---
id: RS-B01
verdict: bad
stack: rust
fix_ref: RS-G01
tags: []
---
# RS-B01 — target/ keyed only on Cargo.lock across profiles

**In one sentence:** Huge archive, mostly recompiled anyway.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** Seed builds --release, measure builds debug, same cache key.

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
- `scenarios/catalog.yml` (`RS-B01`)
