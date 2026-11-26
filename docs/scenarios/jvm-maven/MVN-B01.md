---
id: MVN-B01
verdict: bad
stack: jvm-maven
fix_ref: MVN-G01
tags: []
---
# MVN-B01 — Key on root pom.xml only, change in a submodule

**In one sentence:** Stale cache restored; Maven downloads anyway.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** Key glob only checksums the root pom.xml.

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
- `scenarios/catalog.yml` (`MVN-B01`)
