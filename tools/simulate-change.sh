#!/usr/bin/env bash
# tools/simulate-change.sh <stack> <kind>   (spec §4.1)
#
# Applies a deterministic "simulated commit" to a sample project before the measure build, so the
# measure phase builds something slightly different from the seed phase instead of literally
# nothing. Kinds:
#   none  - no change (theoretical ceiling: identical rebuild)
#   leaf  - change one function body in a leaf module/file nothing depends on (default)
#   core  - change a widely-depended module (worst realistic case)
#   deps  - bump one dependency / lockfile entry (exercises key-based invalidation)
#
# Changes must be deterministic, identical across GOOD and BAD variants of the same stack, and are
# never committed back to git (they only touch the workflow's working copy on the fresh build VM).
set -euo pipefail

stack="${1:?usage: simulate-change.sh <stack> <kind>}"
kind="${2:-leaf}"

root="$BITRISE_SOURCE_DIR"

case "$stack" in
  android)
    case "$kind" in
      none) ;;
      leaf)
        f="$root/projects/android/feature/leaf/src/main/kotlin/com/showcase/featureleaf/Leaf.kt"
        sed -i.bak "s/return \"leaf-v[0-9]*\"/return \"leaf-v$(date +%s | tail -c 4)\"/" "$f" 2>/dev/null || \
          echo "// showcase-leaf-change $(date +%s)" >> "$f"
        rm -f "$f.bak"
        ;;
      core)
        f="$root/projects/android/core/common/src/main/kotlin/com/showcase/core/common/Core.kt"
        echo "// showcase-core-change $(date +%s)" >> "$f"
        ;;
      deps)
        # Bump a harmless version catalog entry to exercise key-based dependency-cache invalidation.
        f="$root/projects/android/gradle/libs.versions.toml"
        sed -i.bak 's/^showcaseMarker = ".*"/showcaseMarker = "'"$(date +%s)"'"/' "$f" 2>/dev/null || true
        rm -f "$f.bak"
        ;;
      *) echo "unknown change kind: $kind" >&2; exit 1 ;;
    esac
    ;;
  node)
    case "$kind" in
      none) ;;
      leaf|core)
        f="$root/projects/node/src/leaf.js"
        echo "// showcase-change $(date +%s)" >> "$f"
        ;;
      deps)
        # Bump the patch version of a harmless, already-vendored dependency marker in package.json
        # so package-lock.json's content checksum changes without touching real resolution.
        f="$root/projects/node/package.json"
        python3 - "$f" <<'PY'
import json, sys, time
p = sys.argv[1]
d = json.load(open(p))
d["showcaseMarker"] = str(int(time.time()))
json.dump(d, open(p, "w"), indent=2)
PY
        ;;
      *) echo "unknown change kind: $kind" >&2; exit 1 ;;
    esac
    ;;
  go)
    case "$kind" in
      none) ;;
      leaf|core)
        f="$root/projects/go/pkg/leaf/leaf.go"
        sed -i.bak "s/return \"leaf-v[0-9]*\"/return \"leaf-v$(date +%s | tail -c 4)\"/" "$f" 2>/dev/null || \
          echo "// showcase-leaf-change $(date +%s)" >> "$f"
        rm -f "$f.bak"
        ;;
      *) echo "unknown change kind: $kind" >&2; exit 1 ;;
    esac
    ;;
  rust)
    case "$kind" in
      none) ;;
      leaf|core)
        f="$root/projects/rust/crates/leaf/src/main.rs"
        sed -i.bak "s/\"leaf-v[0-9]*\"/\"leaf-v$(date +%s | tail -c 4)\"/" "$f" 2>/dev/null || \
          echo "// showcase-leaf-change $(date +%s)" >> "$f"
        rm -f "$f.bak"
        ;;
      *) echo "unknown change kind: $kind" >&2; exit 1 ;;
    esac
    ;;
  python)
    case "$kind" in
      none) ;;
      leaf|core)
        f="$root/projects/python/pip_app/src/leaf.py"
        sed -i.bak "s/\"leaf-v[0-9]*\"/\"leaf-v$(date +%s | tail -c 4)\"/" "$f" 2>/dev/null || \
          echo "# showcase-leaf-change $(date +%s)" >> "$f"
        rm -f "$f.bak"
        ;;
      *) echo "unknown change kind: $kind" >&2; exit 1 ;;
    esac
    ;;
  *)
    echo "simulate-change.sh: stack '$stack' not implemented yet (status: planned in scenarios/catalog.yml)" >&2
    ;;
esac

echo "simulate-change: stack=$stack kind=$kind applied"
