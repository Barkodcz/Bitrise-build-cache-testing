#!/usr/bin/env bash
# tools/run-rust.sh <toolchain> <profile>
#
# Installs rustup (official https://sh.rustup.rs installer, spec §0's "use official steps where
# possible") if not already present, installs the pinned <toolchain> (e.g. "1.75.0" or "stable")
# from scratch via rustup rather than relying on whatever's preinstalled on the stack — this is what
# makes RS-B02's toolchain-drift scenario meaningful — builds projects/rust with the given <profile>
# ("release" or "dev"), runs its tests, and times the build step (spec §8.2).
#
# Rust keeps every past stable release's toolchain downloadable indefinitely via rustup's static
# distribution servers, so pinning an older-but-real version here (as RS-B02 does) is safe long-term.
set -euo pipefail

toolchain="${1:?usage: run-rust.sh <toolchain> <profile>}"
profile="${2:-release}"

export CARGO_HOME="$HOME/.cargo"
export RUSTUP_HOME="$HOME/.rustup"
export PATH="$CARGO_HOME/bin:$PATH"

if ! command -v rustup >/dev/null 2>&1; then
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain none --profile minimal
  export PATH="$CARGO_HOME/bin:$PATH"
fi

rustup toolchain install "$toolchain" --profile minimal --no-self-update

cd "$BITRISE_SOURCE_DIR/projects/rust"
export CARGO_TARGET_DIR="$BITRISE_SOURCE_DIR/projects/rust/target"

echo "run-rust.sh: using $(cargo "+${toolchain}" --version)"

"$BITRISE_SOURCE_DIR"/tools/metrics/timing.sh start build_step
if [ "$profile" = "release" ]; then
  cargo "+${toolchain}" build --release
else
  cargo "+${toolchain}" build
fi
cargo "+${toolchain}" test
"$BITRISE_SOURCE_DIR"/tools/metrics/timing.sh stop build_step
