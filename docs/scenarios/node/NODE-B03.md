---
id: NODE-B03
verdict: bad
stack: node
fix_ref: NODE-G01
tags: [step-order-wrong]
---
# NODE-B03 — Save before install

**In one sentence:** `save-cache` is ordered *before* `npm ci` instead of after, so it captures
`~/.npm`'s pre-install state — every build's cache is one commit behind what it should be.

## What the configuration does
`.bitrise/workflows/node.yml` `node-b03__*`:

```yaml
- bundle::kb_restore: {}
- bundle::kb_save: {}          # ← the defect: save runs before install
- bundle::node_install: {}     # npm ci
```

## What you see
- Log evidence: `> _To be captured from a real run._` — the save step's archive size/content
  reflects the state of `~/.npm` as restored, not as updated by the install that follows it.
- Metrics: `duration.vs_seed` shows no real improvement over repeated runs, since each build's saved
  cache never reflects that same build's own dependency resolution.

## Why it happens
`save-cache` captures whatever is on disk at the moment it runs. If it runs before the step that
populates/updates the cache directory, it saves stale (or empty, on a cold VM) content — the cache
is always "one build behind" the dependencies that were actually just resolved.

## How to fix it
```diff
 - bundle::kb_restore: {}
-- bundle::kb_save: {}
 - bundle::node_install: {}
+- bundle::kb_save: {}
```
→ `NODE-G01`.

## How to confirm the fix
After reordering, the save step's recorded `key_based.archive_bytes`/content reflects the
post-install state, and the *next* build's restore picks up what the *previous* build actually
installed (not what it had before installing).

## Seen in the wild
Classic inverted ordering (spec §3.9) — easy to introduce when copy-pasting a cache bundle template
and not noticing the install step needs to sit between restore and save.

## References
- `docs/PROJECT_SPEC.md` §3.9, §6.6
- `scenarios/catalog.yml` (`NODE-B03`)
