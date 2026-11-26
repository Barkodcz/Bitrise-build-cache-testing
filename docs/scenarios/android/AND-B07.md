---
id: AND-B07
verdict: bad
stack: android
fix_ref: AND-G01
tags: []
---
# AND-B07 — Non-cacheable custom codegen

**In one sentence:** Codegen task always runs even though its output is byte-identical; downstream compile tasks may still cache.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** Expensive codegen task not annotated @CacheableTask / doesn't declare outputs.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
Fixed by following `AND-G01`.

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`AND-B07`)
