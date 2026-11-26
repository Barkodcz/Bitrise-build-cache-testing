---
id: RB-B01
verdict: bad
stack: ruby
fix_ref: RB-G01
tags: []
---
# RB-B01 — Key without {{ .OS }} shared Linux<->macOS

**In one sentence:** Restored native gem (nokogiri) is unusable; bundle install recompiles (caught and recorded, not a hard failure).

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** Seed on Linux, measure on macOS, same cache key with no OS discriminator.

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
- `scenarios/catalog.yml` (`RB-B01`)
