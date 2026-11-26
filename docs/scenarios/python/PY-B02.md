---
id: PY-B02
verdict: bad
stack: python
fix_ref: PY-G01
tags: [too-broad-cache-path]
---
# PY-B02 — Whole .venv cached instead of pip's download cache

**In one sentence:** the cache stores the entire `.venv` directory (Python interpreter copy,
stdlib, every installed package including compiled `numpy` binaries) instead of just `~/.cache/pip`
— a much bigger archive for no additional correctness benefit.

## What the configuration does
`.bitrise/workflows/python.yml` `py-b02__*` — identical bundle structure to `PY-G01`, except the
cached path:

```yaml
- bundle::kb_restore:
    inputs:
    - key: pip-venv-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/python/pip_app/requirements.txt" }}
- bundle::python_install:
    inputs:
    - app: "pip"
- bundle::kb_save:
    inputs:
    - key: pip-venv-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/python/pip_app/requirements.txt" }}
    - paths: projects/python/pip_app/.venv   # ← the whole venv, not ~/.cache/pip
```

## What you see
- **Real captured log** (`py-b02__2_measure`, build 24, app `84c7a274-43b0-477d-9141-ea174ad0ce6e`, 2026-11-26):
  ```
  keybased_record: restore name=pip-venv hit=exact
  ```
  — the cache does restore and save successfully (there's no key mismatch here, unlike `PY-B01`);
  the symptom is archive size, not hit rate. (`archive_bytes` is unfortunately not reliably
  collected yet in this repo's metrics tooling on real infra — see
  `docs/reference/verified-facts.md` — so this page can't yet show a real before/after byte count;
  the mechanism-level point — cache the tool's own download cache, not the installed environment —
  still holds regardless.)
- Metrics: `key_based.saved == true`.

## Why it happens
`pip install`'s own download cache (`~/.cache/pip`) is already enough to make repeated installs
fast — pip re-links/re-extracts cached wheels into a fresh virtualenv quickly. Caching the entire
`.venv` instead adds the Python interpreter's own copied files, the full standard library, and every
installed package's *installed* (not just downloaded) form to the archive — all of which
`pip install` would recreate quickly anyway from a warm `~/.cache/pip`. The archive is bigger, the
restore/save steps take longer, and there's no correctness or speed benefit over the leaner
approach.

## How to fix it
```diff
 - bundle::kb_save:
     inputs:
     - key: pip-venv-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/python/pip_app/requirements.txt" }}
-    - paths: projects/python/pip_app/.venv
+    - paths: ~/.cache/pip
```
(and the matching `kb_restore`) → `PY-G01`.

## How to confirm the fix
Compare `key_based.archive_bytes` before and after — caching `~/.cache/pip` alone should produce a
visibly smaller archive for the identical dependency set.

## Seen in the wild
The same "too-broad path" mistake as `AND-B11` (caching Gradle's `build/`/`.gradle/` directories) and
`IOS-B09` (caching Xcode's `Archives`/`CoreSimulator`) — caching a build output or installed-package
directory instead of the tool's own, much leaner, dependency/download cache.

## References
- `docs/PROJECT_SPEC.md` §3.9, §6.10
- `scenarios/catalog.yml` (`PY-B02`)
