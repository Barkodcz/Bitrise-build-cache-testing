---
id: GO-G01
verdict: good
stack: go
fix_ref: null
tags: [both-caches, pinned-toolchain]
---
# GO-G01 — pkg/mod + go-build cache keyed on go.sum

**In one sentence:** both Go caches — the module cache (`~/go/pkg/mod`, downloaded dependency
sources) and the build cache (`~/.cache/go-build`, compiled package objects) — are key-cached
separately, keyed on `go.sum`, with the same pinned Go version in every build.

## What the configuration does
`.bitrise/workflows/go.yml` `go-g01__*`, via `.bitrise/bundles/key-based.yml` `kb_restore`/`kb_save`
and `go_build`:

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::kb_restore:
    inputs:
    - key: gomod-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/go/go.sum" }}
    - name: gomod
- bundle::kb_restore:
    inputs:
    - key: gobuild-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/go/go.sum" }}
    - name: gobuild
- bundle::go_build:
    inputs:
    - go_version: "1.22.0"       # go build ./... && go test ./..., via tools/run-go.sh
- bundle::kb_save: { ... same gomod key, paths: ~/go/pkg/mod }
- bundle::kb_save: { ... same gobuild key, paths: ~/.cache/go-build }
```

`tools/run-go.sh` always downloads the pinned `go_version` from `go.dev/dl` from scratch (rather
than relying on whatever Go happens to be preinstalled on the stack) — this is what makes
`GO-B02`'s toolchain-drift scenario meaningful: seed and measure can genuinely run different,
real Go versions.

## What you see
- **Real captured log** (`go-g01__2_measure`, build 21, app `84c7a274-43b0-477d-9141-ea174ad0ce6e`, 2026-11-26):
  ```
  keybased_record: restore name=gomod hit=exact
  keybased_record: restore name=gobuild hit=exact
  run-go.sh: using go version go1.22.0 linux/amd64
  ```
- Metrics: `key_based.restore_hit` in `["exact", "partial"]` on the measure run for both the
  `gomod` and `gobuild` cache entries — confirmed `exact` for both on the first real run.

## Why it doesn't need a fix
N/A — this is the GOOD baseline. `GO-B01` and `GO-B02` both point back here.

## How to confirm it's working
Both `kb_restore` steps report a non-`false` `restore_hit`, and `go build`/`go test` run
noticeably faster on the measure build than a genuinely cold run would.

## Seen in the wild
Baseline every `GO-B*` scenario is compared against — the module cache (downloads) and the build
cache (compiled objects) are two different directories that are easy to conflate (see `GO-B01`).

## References
- `docs/PROJECT_SPEC.md` §6.8
- `scenarios/catalog.yml` (`GO-G01`)
