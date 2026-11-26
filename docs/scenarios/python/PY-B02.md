---
id: PY-B02
verdict: bad
stack: python
fix_ref: PY-G01
tags: []
---
# PY-B02 — Whole .venv cached across Python versions

**In one sentence:** Broken or fully rebuilt environment.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** .venv cached directly instead of the pip/poetry cache dir; Python version not in the key.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
Fixed by following `PY-G01`.

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`PY-B02`)
