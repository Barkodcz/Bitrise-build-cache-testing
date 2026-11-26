---
id: NODE-B04
verdict: bad
stack: node
fix_ref: NODE-G01
tags: []
---
# NODE-B04 — node_modules cached without {{ .OS }} across Linux & macOS

**In one sentence:** A foreign-OS archive restores, then is force-rebuilt — recorded as wasted restore time rather than a hard ABI failure.

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

**Root cause:** Cache of node_modules/ shared between a Linux and a macOS workflow with no {{ .OS }} in the key.

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
Fixed by following `NODE-G01`.

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
_No field-evidence note recorded yet._

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`NODE-B04`)
