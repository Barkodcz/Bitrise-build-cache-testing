---
id: PY-G02
verdict: good
stack: python
fix_ref: null
tags: [exact-key-match, lean-cache-path]
---
# PY-G02 — Poetry cache keyed on poetry.lock

**In one sentence:** `~/.cache/pypoetry` (Poetry's own cache directory) is key-cached, with the
same key template for restore and save, checksumming the real `poetry.lock` that `poetry install`
reads.

## What the configuration does
`.bitrise/workflows/python.yml` `py-g02__*`:

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::kb_restore:
    inputs:
    - key: poetry-cache-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/python/poetry_app/poetry.lock" }}
    - name: poetry-cache
- bundle::python_install:
    inputs:
    - app: "poetry"        # poetry install --no-interaction && poetry run pytest
- bundle::kb_save: { ... same key, paths: ~/.cache/pypoetry }
```

## What you see
- **Real captured log** (`py-g02__2_measure`, build 24, app `84c7a274-43b0-477d-9141-ea174ad0ce6e`, 2026-11-26):
  ```
  keybased_record: restore name=poetry-cache hit=exact
  ```
- Metrics: `key_based.restore_hit` in `["exact", "partial"]` on the measure run — confirmed `exact`
  on the first real run.

## Why it doesn't need a fix
N/A — this is the GOOD baseline for the Poetry side of this stack. `PY-B01` points back here.

## How to confirm it's working
`key_based.restore_hit` is `"exact"` on the measure phase.

## Seen in the wild
Baseline `PY-B01` is compared against — same restore=save key template, just pointed at the
*correct* lockfile for the tool actually doing the install.

## References
- `docs/PROJECT_SPEC.md` §6.10
- `scenarios/catalog.yml` (`PY-G02`)
