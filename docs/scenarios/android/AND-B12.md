---
id: AND-B12
verdict: bad
stack: android
fix_ref: AND-G01
tags: []
---
# AND-B12 — Under-specified dependency key

**In one sentence:** Stale dependency cache restored (key unchanged); Gradle re-downloads anyway; archive grows unbounded.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** restore/save-cache key only checksums the root build.gradle.kts, not every module.

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
- `scenarios/catalog.yml` (`AND-B12`)
