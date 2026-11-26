#!/usr/bin/env bash
# tools/run-go.sh <go_version>
#
# Downloads (and caches locally, outside the key-based cache) the official Go toolchain tarball for
# <go_version> from go.dev/dl if not already present, builds + tests projects/go, and times the
# build step (spec §8.2). Always installing a specific, pinned version from scratch — rather than
# relying on whatever Go happens to be preinstalled on the stack — keeps the GO-B02 "toolchain
# drift" scenario meaningful: seed and measure can genuinely run different Go versions.
#
# go_version must be an exact released version (e.g. "1.22.0") — Go keeps every past release
# tarball downloadable indefinitely (no expiry), so pinning an older-but-real version here is safe
# long-term, unlike pinning a bleeding-edge one that might not exist yet when this runs for real.
set -euo pipefail

go_version="${1:?usage: run-go.sh <go_version>}"

toolchains_dir="$HOME/.go-toolchains"
goroot_dir="$toolchains_dir/go${go_version}"

if [ ! -x "$goroot_dir/bin/go" ]; then
  mkdir -p "$toolchains_dir"
  arch="$(uname -m)"
  case "$arch" in
    x86_64) go_arch="amd64" ;;
    aarch64|arm64) go_arch="arm64" ;;
    *) echo "run-go.sh: unsupported arch $arch" >&2; exit 1 ;;
  esac
  go_os="linux"
  [ "$(uname -s)" = "Darwin" ] && go_os="darwin"  # local dev/testing convenience; Bitrise runs Linux
  tarball="go${go_version}.${go_os}-${go_arch}.tar.gz"
  curl -fsSL "https://go.dev/dl/${tarball}" -o "/tmp/${tarball}"
  tmp_extract="$(mktemp -d)"
  tar -C "$tmp_extract" -xzf "/tmp/${tarball}"
  mv "$tmp_extract/go" "$goroot_dir"
  rm -rf "/tmp/${tarball}" "$tmp_extract"
fi

export GOROOT="$goroot_dir"
export PATH="$GOROOT/bin:$PATH"
export GOPATH="$HOME/go"
export GOCACHE="$HOME/.cache/go-build"

cd "$BITRISE_SOURCE_DIR/projects/go"

echo "run-go.sh: using $(go version)"

"$BITRISE_SOURCE_DIR"/tools/metrics/timing.sh start build_step
go build ./...
go test ./...
"$BITRISE_SOURCE_DIR"/tools/metrics/timing.sh stop build_step
