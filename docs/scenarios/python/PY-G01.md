---
id: PY-G01
verdict: good
stack: python
fix_ref: null
tags: [exact-key-match, lean-cache-path]
---
# PY-G01 — pip cache keyed on requirements.txt

**In one sentence:** `~/.cache/pip` (pip's own download cache) is key-cached, with the same key
template used for both restore and save, checksumming the exact `requirements.txt` that `pip
install` reads.

## What the configuration does
`.bitrise/workflows/python.yml` `py-g01__*`, via `.bitrise/bundles/key-based.yml` `kb_restore`/`kb_save`
and `python_install`:

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::kb_restore:
    inputs:
    - key: pip-cache-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/python/pip_app/requirements.txt" }}
    - name: pip-cache
- bundle::python_install:
    inputs:
    - app: "pip"          # python3 -m venv .venv && pip install -r requirements.txt && pytest
- bundle::kb_save: { ... same key, paths: ~/.cache/pip }
```

The virtualenv itself (`projects/python/pip_app/.venv`) is **not** cached — only pip's download
cache is. See `PY-B02` for what happens when the whole `.venv` is cached instead.

## What you see
- Log evidence: `> _To be captured from a real run._`
- Metrics: `key_based.restore_hit` in `["exact", "partial"]` on the measure run.

## Why it doesn't need a fix
N/A — this is the GOOD baseline for the pip side of this stack. `PY-B02` points back here.

## How to confirm it's working
`key_based.restore_hit` is `"exact"` on the measure phase, and `pip install` is markedly faster
than a fully cold install (no re-downloading/re-building the numpy wheel).

## Seen in the wild
Baseline every `PY-B*` scenario pip side is compared against.

## References
- `docs/PROJECT_SPEC.md` §6.10
- `scenarios/catalog.yml` (`PY-G01`)
