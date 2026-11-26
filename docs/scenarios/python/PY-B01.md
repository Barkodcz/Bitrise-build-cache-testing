---
id: PY-B01
verdict: bad
stack: python
fix_ref: PY-G02
tags: [restore-save-key-mismatch]
---
# PY-B01 — Key on stale requirements.txt while install reads poetry.lock

**In one sentence:** the project is 100% Poetry-managed (`poetry install` reads `poetry.lock`), but
the restore-cache key checksums `projects/python/pip_app/requirements.txt` — an unrelated file that
belongs to a *different* app in this repo entirely — so the literal key strings never match.

## What the configuration does
`.bitrise/workflows/python.yml` `py-b01__*`:

```yaml
- bundle::kb_restore:
    inputs:
    - key: poetry-cache-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/python/pip_app/requirements.txt" }}
- bundle::python_install:
    inputs:
    - app: "poetry"
- bundle::kb_save:
    inputs:
    - key: poetry-cache-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/python/poetry_app/poetry.lock" }}
    - paths: ~/.cache/pypoetry
```

## What you see
- **Real captured log** (`py-b01__2_measure`, build 24, app `84c7a274-43b0-477d-9141-ea174ad0ce6e`, 2026-11-26):
  ```
  keybased_record: restore name=poetry-cache hit=false
  ```
  — confirmed `false` on the very first real run, exactly as designed.
- Metrics: `key_based.restore_hit == "false"`.

## Why it happens
`restore-cache` and `save-cache` are independent steps; nothing enforces that their `key` inputs
match. Here the restore key checksums a completely unrelated file — `pip_app/requirements.txt`,
which belongs to a different sample app in this same repository — while the save key correctly
checksums `poetry.lock`. The two literal key strings are different by construction every time, so
this cache can never hit: a full download+build happens on every single install, and a full upload
happens on every save. This is the same class of mistake as `NODE-B01`, here specifically framed as
"checksumming the wrong lockfile for the install tool actually in use" (spec §3.9).

## How to fix it
```diff
 - bundle::kb_restore:
     inputs:
-    - key: poetry-cache-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/python/pip_app/requirements.txt" }}
+    - key: poetry-cache-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/python/poetry_app/poetry.lock" }}
```
→ `PY-G02`.

## How to confirm the fix
`key_based.restore_hit` flips from `"false"` to `"exact"` once both templates checksum the same,
correct file.

## Seen in the wild
The same restore≠save-key mistake as `NODE-B01` — easy to introduce when a repo has more than one
install tool/lockfile present and a copy-pasted key template still points at the wrong one.

## References
- `docs/PROJECT_SPEC.md` §3.9, §6.10
- `scenarios/catalog.yml` (`PY-B01`)
