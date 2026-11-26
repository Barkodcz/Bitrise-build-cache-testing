# Python (key-based caching)

Pipeline: `showcase-python`. Sample projects: `projects/python/pip_app` (depends on `numpy`, a real
C-extension dependency, for `pip` scenarios) and `projects/python/poetry_app` (depends on
`requests`, with a real `poetry.lock`, for Poetry scenarios).

Python has **no Bitrise Build Cache backend** — everything here is key-based caching (see
`docs/concepts/caching-mechanisms.md`), same as Node.js/Go/Rust.

## Scenarios implemented so far

| ID | Verdict | Title |
|---|---|---|
| [PY-G01](../scenarios/python/PY-G01.md) | ✅ good | pip cache keyed on `requirements.txt` |
| [PY-G02](../scenarios/python/PY-G02.md) | ✅ good | Poetry cache keyed on `poetry.lock` |
| [PY-B01](../scenarios/python/PY-B01.md) | ❌ bad | Key on stale `requirements.txt` while install reads `poetry.lock` |
| [PY-B02](../scenarios/python/PY-B02.md) | ❌ bad | Whole `.venv` cached instead of pip's download cache |

## Key mechanics

- **Checksum the file the install tool actually reads** (`PY-B01`): a restore key pointed at an
  unrelated file (here, a *different app's* `requirements.txt`) while the save key correctly
  checksums `poetry.lock` produces a permanent miss — the same `NODE-B01` lesson, reframed around
  "which lockfile goes with which tool" rather than npm vs. Yarn.
- **Cache the tool's own download cache, not the installed environment** (`PY-B02`): `~/.cache/pip`
  (or `~/.cache/pypoetry`) is already enough to make repeated installs fast; caching the whole
  `.venv` adds the interpreter + stdlib + installed packages to every archive for no benefit.
