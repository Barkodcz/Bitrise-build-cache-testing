#!/usr/bin/env bash
# tools/run-maven.sh
#
# Installs a pinned Apache Maven version from the official Apache dist archive (spec §0's "use
# official steps where possible") if `mvn` isn't already on PATH, runs `mvn test` against
# projects/maven (both modules, via Maven's reactor), and times the build step (spec §8.2). Which
# directory gets cached (~/.m2/repository alone vs. also target/ dirs) is decided entirely by the
# generator's kb_restore/kb_save wiring per scenario, not by this script.
set -euo pipefail

MAVEN_VERSION="3.9.9"

if ! command -v mvn >/dev/null 2>&1; then
  install_dir="$HOME/.maven-toolchains/apache-maven-${MAVEN_VERSION}"
  if [ ! -x "$install_dir/bin/mvn" ]; then
    mkdir -p "$HOME/.maven-toolchains"
    tarball="apache-maven-${MAVEN_VERSION}-bin.tar.gz"
    curl -fsSL "https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/${tarball}" -o "/tmp/${tarball}"
    tar -C "$HOME/.maven-toolchains" -xzf "/tmp/${tarball}"
    rm -f "/tmp/${tarball}"
  fi
  export PATH="$install_dir/bin:$PATH"
fi

cd "$BITRISE_SOURCE_DIR/projects/maven"

echo "run-maven.sh: using $(mvn --version | head -1)"

"$BITRISE_SOURCE_DIR"/tools/metrics/timing.sh start build_step
mvn -B test
"$BITRISE_SOURCE_DIR"/tools/metrics/timing.sh stop build_step
