# projects/python

Two small real projects used by the key-based caching scenarios (`scenarios/catalog.yml` `PY-*`):

- `pip_app/` — `requirements.txt` pins `numpy` (a real C-extension dependency, installed from a
  prebuilt wheel) so `pip install` has real content worth caching. `src/core.py` is the
  "widely depended" module; `src/leaf.py` is mutated by `tools/simulate-change.sh python leaf`.
- `poetry_app/` — a Poetry project depending on `requests`, with a real `poetry.lock`.

`PY-G01`/`PY-B02` run against `pip_app`; `PY-G02`/`PY-B01` run against `poetry_app`. See
`docs/stacks/python.md` for which cache mechanism each scenario demonstrates.
