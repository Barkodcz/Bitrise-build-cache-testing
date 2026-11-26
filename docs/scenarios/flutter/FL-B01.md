---
id: FL-B01
verdict: bad
stack: flutter
fix_ref: FL-G01
tags: []
---
# FL-B01 — One key for everything

**In one sentence:** A Podfile.lock or Gradle-only change is ignored, or everything invalidates together.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** Single cache keyed only on pubspec.lock covers pub + pods + gradle.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
Fixed by following `FL-G01`.

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`FL-B01`)
