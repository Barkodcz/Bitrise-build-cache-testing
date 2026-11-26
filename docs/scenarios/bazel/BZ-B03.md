---
id: BZ-B03
verdict: bad
stack: bazel
fix_ref: BZ-G01
tags: []
---
# BZ-B03 — Env leak into actions

**In one sentence:** Every action misses.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** --action_env=BITRISE_BUILD_NUMBER leaks a volatile value into every action key.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
Fixed by following `BZ-G01`.

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`BZ-B03`)
