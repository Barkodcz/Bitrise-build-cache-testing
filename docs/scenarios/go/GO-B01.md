---
id: GO-B01
verdict: bad
stack: go
fix_ref: GO-G01
tags: []
---
# GO-B01 — Only module cache, no GOCACHE

**In one sentence:** Downloads are skipped but the full package set still compiles.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** ~/.cache/go-build never cached, only ~/go/pkg/mod.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
Fixed by following `GO-G01`.

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`GO-B01`)
