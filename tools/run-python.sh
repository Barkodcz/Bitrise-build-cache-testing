#!/usr/bin/env bash
# tools/run-python.sh <pip|poetry>
#
# Installs deps + runs tests for the chosen projects/python app, and times the build step
# (spec §8.2). Installs Poetry via its official installer (https://install.python-poetry.org) if
# not already present (spec §0's "use official steps where possible"). Which directory actually
# gets cached (pip's download cache vs. the whole .venv; poetry's cache dir) is decided entirely
# by which kb_restore/kb_save paths the generator wires around this script, per scenario — this
# script only ever installs + tests, it never touches cache-specific logic itself.
set -euo pipefail

app="${1:?usage: run-python.sh <pip|poetry>}"

cd "$BITRISE_SOURCE_DIR/projects/python"

"$BITRISE_SOURCE_DIR"/tools/metrics/timing.sh start build_step

case "$app" in
  pip)
    cd pip_app
    [ -d .venv ] || python3 -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    pip install --quiet pytest
    pytest tests/ -q
    ;;
  poetry)
    cd poetry_app
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v poetry >/dev/null 2>&1; then
      curl -sSL https://install.python-poetry.org | python3 -
      export PATH="$HOME/.local/bin:$PATH"
    fi
    poetry install --no-interaction
    poetry run pytest tests/ -q
    ;;
  *)
    echo "run-python.sh: unknown app '$app' (expected pip|poetry)" >&2
    exit 1
    ;;
esac

"$BITRISE_SOURCE_DIR"/tools/metrics/timing.sh stop build_step
