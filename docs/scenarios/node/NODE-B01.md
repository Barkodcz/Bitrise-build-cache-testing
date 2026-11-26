---
id: NODE-B01
verdict: bad
stack: node
fix_ref: NODE-G01
tags: [restore-save-key-mismatch]
---
# NODE-B01 — restore ≠ save key (the canonical worked example)

**In one sentence:** The restore step checksums `package-lock.json`; the save step checksums
`yarn.lock` (which doesn't even exist in this npm project) — the two literal key strings never
match, so `BITRISE_CACHE_HIT` is `false` forever, yet `save-cache` keeps re-uploading a full archive
on every single build.

## What the configuration does
`.bitrise/workflows/node.yml` `node-b01__*`:

```yaml
- bundle::kb_restore:
    inputs:
    - key: npm-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/node/package-lock.json" }}
- bundle::node_install: {}
- bundle::kb_save:
    inputs:
    - key: npm-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/node/yarn.lock" }}
    - paths: ~/.npm
```

## What you see
- Log evidence: `> _To be captured from a real run._` — `BITRISE_CACHE_HIT=false` on every restore,
  on every build, forever.
- Metrics: `key_based.restore_hit == "false"`.

## Why it happens
`restore-cache` and `save-cache` are two independent steps; nothing enforces that their `key` inputs
match. Here the restore key checksums `package-lock.json` (the real lockfile) while the save key
checksums `yarn.lock` (a file that doesn't exist in this project, so its checksum is a constant).
The two literal key strings are different every time by construction, so the archive `save-cache`
writes is never the one `restore-cache` looks for — a full upload happens on every build, and a full
download/miss happens on every restore. Per spec §3.9, diffing the literal key strings is the first
thing to check when a key-based cache "isn't working."

## How to fix it
```diff
 - bundle::kb_save:
     inputs:
-    - key: npm-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/node/yarn.lock" }}
+    - key: npm-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/node/package-lock.json" }}
     - paths: ~/.npm
```
→ `NODE-G01`.

## How to confirm the fix
`key_based.restore_hit` flips from `"false"` to `"exact"` once both templates match.

## Seen in the wild
The single most common key-based caching mistake across audits (spec §3.9) — often introduced when
a project migrates between package managers (npm ↔ Yarn) and one step's key template doesn't get
updated.

## References
- `docs/PROJECT_SPEC.md` §3.9, §6.6
- `scenarios/catalog.yml` (`NODE-B01`)
