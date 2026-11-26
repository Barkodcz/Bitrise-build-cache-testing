---
id: NODE-G01
verdict: good
stack: node
fix_ref: null
tags: [exact-key-match, fallback-chain]
---
# NODE-G01 — npm: `~/.npm` keyed on `package-lock.json`, fallback chain, `is_key_unique`

**In one sentence:** `restore-cache`/`save-cache` use the *same* key template, checksumming the
file `npm ci` actually reads, with `is_key_unique: true` — the baseline every `NODE-B*` scenario is
compared against.

## What the configuration does
`.bitrise/workflows/node.yml` `node-g01__*`, via `.bitrise/bundles/key-based.yml` `kb_restore`/`kb_save`:

```yaml
- bundle::kb_restore:
    inputs:
    - key: npm-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/node/package-lock.json" }}
- bundle::node_install: {}        # npm ci --prefer-offline
- bundle::kb_save:
    inputs:
    - key: npm-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/node/package-lock.json" }}
    - paths: ~/.npm
    - is_key_unique: 'true'
```

Restore and save use the **literal same key template** (spec §3.9's #1 priority rule: "diff the
literal strings"), checksumming `package-lock.json` — the exact lockfile `npm ci` reads — and caches
`~/.npm` (the package manager's own cache directory), not `node_modules/`.

## What you see
- Log evidence: `> _To be captured from a real run._` — `BITRISE_CACHE_HIT=exact` on the measure
  run's restore step.
- Metrics: `key_based.restore_hit == "exact"`, `key_based.saved == true`.

## Why it doesn't need a fix
N/A — this is the GOOD baseline. Every `NODE-B*` page's "How to fix it" section points back here.

## How to confirm it's working
`key_based.restore_hit` is `"exact"` on the measure phase, and `npm ci`'s install step is markedly
faster than a cold install.

## Seen in the wild
Canonical correct key-based setup — used as the comparison baseline for every `NODE-B*` scenario
(spec §6.6).

## References
- `docs/PROJECT_SPEC.md` §3.9, §6.6
- `scenarios/catalog.yml` (`NODE-G01`)
