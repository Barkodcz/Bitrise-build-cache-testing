---
id: IOS-B06
verdict: bad
stack: ios
fix_ref: IOS-G01
tags: []
---
# IOS-B06 — no_swift_cache as default

**In one sentence:** Clang/ObjC hits, but all Swift targets compile uncached.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** no_swift_cache: true left on without an explicit-modules workaround need.

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
- `scenarios/catalog.yml` (`IOS-B06`)
