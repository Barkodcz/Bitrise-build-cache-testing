---
id: RB-B02
verdict: bad
stack: ruby
fix_ref: RB-G01
tags: []
---
# RB-B02 — Ruby version drift

**In one sentence:** Gems reinstall despite an exact key hit.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** Seed on Ruby 3.2, measure on Ruby 3.3; .ruby-version not pinned, version not in the key.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
Fixed by following `RB-G01`.

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`RB-B02`)
