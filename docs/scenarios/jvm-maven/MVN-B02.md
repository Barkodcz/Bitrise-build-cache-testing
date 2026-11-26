---
id: MVN-B02
verdict: bad
stack: jvm-maven
fix_ref: MVN-G01
tags: []
---
# MVN-B02 — Caching target/

**In one sentence:** Large archive, no correctness benefit.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** target/ build output cached instead of just ~/.m2/repository.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
Fixed by following `MVN-G01`.

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`MVN-B02`)
