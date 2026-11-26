---
id: NODE-B05
verdict: bad
stack: node
fix_ref: NODE-G01
tags: [reupload-every-build]
---
# NODE-B05 — No `is_key_unique`

**In one sentence:** `is_key_unique` is left at its default (`false`) instead of `true`, so the
archive is re-uploaded on every build even when its content hasn't changed since the last save.

## What the configuration does
`.bitrise/workflows/node.yml` `node-b05__*`:

```yaml
- bundle::kb_save:
    inputs:
    - key: npm-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/node/package-lock.json" }}
    - paths: ~/.npm
    - is_key_unique: 'false'
```

## What you see
- Log evidence: `> _To be captured from a real run._`
- Metrics: `key_based.saved == true` on every build (the save step always runs and succeeds — see
  the note in `scenarios/catalog.yml` about this expectation's limits: whether the backend actually
  *skips* a redundant upload for an unchanged archive is only observable via Bitrise's own cache
  dashboard / network byte counters, not from this repo's local timers).

## Why it happens
`is_key_unique: true` tells `save-cache` "if an archive already exists under this exact key, don't
bother re-uploading it" — a pure efficiency flag with no correctness implications either way. Left
at its default `false`, the step re-uploads the full archive on every build regardless of whether
its content actually changed, wasting upload time and bandwidth on every single run.

## How to fix it
```diff
 - bundle::kb_save:
     inputs:
     - key: npm-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/node/package-lock.json" }}
     - paths: ~/.npm
-    - is_key_unique: 'false'
+    - is_key_unique: 'true'
```
→ `NODE-G01`.

## How to confirm the fix
Compare upload time / bandwidth on consecutive builds with an unchanged lockfile in the Bitrise
build log for the save-cache step, before and after flipping the flag.

## Seen in the wild
Wastes upload time/bandwidth on every single build — usually just an overlooked default rather than
a deliberate choice.

## References
- `docs/PROJECT_SPEC.md` §3.9, §6.6
- `scenarios/catalog.yml` (`NODE-B05`)
