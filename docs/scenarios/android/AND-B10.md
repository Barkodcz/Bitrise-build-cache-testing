---
id: AND-B10
verdict: bad
stack: android
fix_ref: null
tags: []
---
# AND-B10 — Cold cache looks like failure

**In one sentence:** Ratio < 1, hits ~0 — even though the YAML configuration is identical to AND-G01.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** Measure phase runs in a fresh cache namespace, simulating first build / new DC / TTL expiry.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
_No single fix — see the symptom/root_cause above; this is a structural or informational scenario._

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`AND-B10`)
