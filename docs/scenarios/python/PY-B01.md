---
id: PY-B01
verdict: bad
stack: python
fix_ref: PY-G02
tags: []
---
# PY-B01 — Key on stale requirements.txt while install reads poetry.lock

**In one sentence:** Key never changes when dependencies actually do.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** Checksum targets the wrong lockfile for the install tool in use.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
Fixed by following `PY-G02`.

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`PY-B01`)
