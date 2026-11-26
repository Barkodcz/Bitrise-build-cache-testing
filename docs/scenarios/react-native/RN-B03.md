---
id: RN-B03
verdict: bad
stack: react-native
fix_ref: RN-G01
tags: []
---
# RN-B03 — Unwrapped native command

**In one sentence:** iOS/Android legs show zero cache traffic.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** npx react-native run-ios invoked in a script step without the bitrise-build-cache wrapper.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
Fixed by following `RN-G01`.

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`RN-B03`)
