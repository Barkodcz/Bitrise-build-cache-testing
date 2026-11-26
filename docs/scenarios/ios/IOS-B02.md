---
id: IOS-B02
verdict: bad
stack: ios
fix_ref: IOS-G01
tags: []
---
# IOS-B02 — DerivedData key-cached alongside Build Cache

**In one sentence:** Remote cache barely queried; local DerivedData short-circuits it.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** ~/Library/Developer/Xcode/DerivedData key-cached in the same workflow as activation.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
Fixed by following `IOS-G01`.

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`IOS-B02`)
