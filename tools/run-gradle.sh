#!/usr/bin/env bash
# tools/run-gradle.sh "<tasks>" "<options>"
#
# Thin wrapper invoked by the gradle_build bundle (.bitrise/bundles/gradle.yml). Registers the
# showcase metrics init script, injects the cache-isolation namespace Gradle property (spec §4.2),
# times the build step, and tees --console=plain output so a FROM-CACHE grep cross-check is possible
# alongside the init-script-based collector (spec §8.2).
set -euo pipefail

tasks="${1:?usage: run-gradle.sh <tasks> <options>}"
options="${2:-}"

cd "$BITRISE_SOURCE_DIR/projects/android"

: "${SHOWCASE_NS:?SHOWCASE_NS must be exported by tools/namespace.sh first}"
: "${SHOWCASE_METRICS_DIR:?}"

log_dir="$SHOWCASE_METRICS_DIR/.fragments/${SHOWCASE_SCENARIO_ID}__${SHOWCASE_PHASE}"
mkdir -p "$log_dir"
build_log="$log_dir/gradle-build.log"

"$BITRISE_SOURCE_DIR"/tools/metrics/timing.sh start build_step

# shellcheck disable=SC2086
./gradlew $tasks $options \
  --init-script "$BITRISE_SOURCE_DIR/tools/metrics/gradle/showcase-metrics.init.gradle.kts" \
  -PshowcaseNs="$SHOWCASE_NS" \
  -Dorg.gradle.internal.showcase.ns="$SHOWCASE_NS" \
  2>&1 | tee "$build_log"

"$BITRISE_SOURCE_DIR"/tools/metrics/timing.sh stop build_step

from_cache_grep_count="$(grep -c 'FROM-CACHE' "$build_log" || true)"
echo "showcase: grep cross-check FROM-CACHE lines = ${from_cache_grep_count}"
