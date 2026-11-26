---
id: NODE-B02
verdict: bad
stack: node
fix_ref: NODE-G01
tags: [static-key]
---
# NODE-B02 — Static key + change kind `deps`

**In one sentence:** The cache key is a hardcoded literal (`npm-cache`) instead of a checksum
template, so it restores an "exact" hit even after `package-lock.json` has genuinely changed — the
cache never refreshes.

## What the configuration does
`.bitrise/workflows/node.yml` `node-b02__*`, measure phase uses `SHOWCASE_CHANGE_KIND=deps`
(`tools/simulate-change.sh node deps` bumps a harmless `showcaseMarker` field in `package.json` so
`package-lock.json`'s content changes):

```yaml
- bundle::simulate_change:
    inputs:
    - kind: deps
- bundle::kb_restore:
    inputs:
    - key: npm-cache
- bundle::node_install: {}
- bundle::kb_save:
    inputs:
    - key: npm-cache
    - paths: ~/.npm
```

## What you see
- Log evidence: `> _To be captured from a real run._` — `BITRISE_CACHE_HIT=exact` even on the
  measure run, despite the simulated dependency change.
- Metrics: `key_based.restore_hit == "exact"` (misleadingly "good-looking").

## Why it happens
A literal string like `npm-cache` is a valid cache key, but it never changes — so once an archive
exists under that key, every future build restores the *same* archive regardless of whether
`package-lock.json` changed. The restore step honestly reports an exact hit (the key did match!);
the dishonesty is in the key design, not the step. This is also why "naive hit rate" style
screening is insufficient on its own (spec §3.2) — a key that never invalidates looks indistinguishable
from a perfectly warm cache unless you specifically check whether the *content* is current.

## How to fix it
```diff
 - bundle::kb_restore:
     inputs:
-    - key: npm-cache
+    - key: npm-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/node/package-lock.json" }}
```
(and the matching `kb_save` key) → `NODE-G01`.

## How to confirm the fix
After the fix, a `deps`-kind simulated change produces a cache **miss** (not an exact hit) on the
next build, because the checksum of the changed lockfile differs.

## Seen in the wild
Stale-forever caches from a key that was never templated — often started as `"my-project-cache"`
during initial setup and never revisited.

## References
- `docs/PROJECT_SPEC.md` §3.9, §6.6
- `scenarios/catalog.yml` (`NODE-B02`)
