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
- Log evidence: `> _To be captured from a real run._`
- Metrics: `key_based.restore_hit` in `["exact", "partial"]` on the measure run.

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
