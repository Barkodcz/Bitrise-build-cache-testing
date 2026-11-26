---
id: AND-B08
verdict: bad
stack: android
fix_ref: AND-G01
tags: []
---
# AND-B08 — JDK mismatch writer vs reader

**In one sentence:** Near-zero cross-workflow hits for JVM compile tasks.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** Seed workflow builds on JDK 21, measure workflow on JDK 17 (set-java-version step).

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
- `scenarios/catalog.yml` (`AND-B08`)
