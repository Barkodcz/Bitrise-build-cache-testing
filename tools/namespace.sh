#!/usr/bin/env bash
# Computes & exports SHOWCASE_NS, the cache-isolation namespace (spec §4.2).
#
# SHOWCASE_NS is a TEST-HARNESS-ONLY device used to make every scenario's cache keys unique per
# pipeline run (isolated mode) or stable across runs (steady mode). Never copy this pattern into
# real production YAML — injecting a per-build value into compile inputs is exactly the
# AND-B03 / IOS-B04 anti-pattern this showcase exists to teach against (see docs/concepts/isolation.md).
#
# Usage: `source tools/namespace.sh` from a step's script content. Requires SHOWCASE_SCENARIO_ID
# and SHOWCASE_ISOLATION (defaulted via app envs, spec §7.2) to already be exported.
set -euo pipefail

: "${SHOWCASE_SCENARIO_ID:?SHOWCASE_SCENARIO_ID must be set by the generated workflow}"
: "${SHOWCASE_ISOLATION:=isolated}"

if [ "$SHOWCASE_ISOLATION" = "steady" ]; then
  run_id="steady"
else
  # BITRISEIO_PIPELINE_ID identifies this pipeline run; falls back to the build slug for single-workflow
  # (non-pipeline) runs, e.g. `bitrise local run`, so the namespace is still defined.
  run_id="${BITRISEIO_PIPELINE_ID:-${BITRISE_BUILD_SLUG:-local}}"
fi

export SHOWCASE_NS="${run_id}-${SHOWCASE_SCENARIO_ID}"
echo "SHOWCASE_NS=${SHOWCASE_NS}"

# Persist for later steps in the same workflow via envman, if available (Bitrise step environment).
if command -v envman >/dev/null 2>&1; then
  envman add --key SHOWCASE_NS --value "$SHOWCASE_NS"
fi
