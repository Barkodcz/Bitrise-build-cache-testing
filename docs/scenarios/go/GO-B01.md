---
id: GO-B01
verdict: bad
stack: go
fix_ref: GO-G01
tags: [missing-build-cache]
---
# GO-B01 — Only module cache, no GOCACHE

**In one sentence:** only `~/go/pkg/mod` (downloaded dependency sources) is key-cached; `~/.cache/go-build`
(compiled package objects) never is, so dependency downloads are skipped but the full package set
still compiles from scratch every single build.

## What the configuration does
`.bitrise/workflows/go.yml` `go-b01__*` — same as `GO-G01` except the `gobuild` `kb_restore`/`kb_save`
pair is **absent entirely**:

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::kb_restore:          # gomod only
    inputs:
    - key: gomod-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/go/go.sum" }}
    - name: gomod
- bundle::go_build: { ... }
- bundle::kb_save:              # gomod only — no gobuild save
    inputs:
    - key: gomod-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/go/go.sum" }}
    - paths: ~/go/pkg/mod
    - name: gomod
```

## What you see
- Log evidence: `> _To be captured from a real run._` — `go build`/`go test` still take close to
  full-compile time on the measure run, even though `go mod download` traffic is near-zero
  (the module cache hit).
- Metrics: `key_based.saved == true` for the `gomod` entry; no `gobuild` entry exists in the
  metrics JSON at all.

## Why it happens
The Go module cache (`~/go/pkg/mod`) and the Go build cache (`~/.cache/go-build`, aka `GOCACHE`)
are two separate directories solving two separate problems: one avoids re-downloading dependency
source code, the other avoids re-compiling package objects that haven't changed. Caching only the
first gives a false sense that "Go caching is set up" — downloads genuinely do stop, but every
single compile unit, including the project's own unchanged packages, still runs from scratch.

## How to fix it
```diff
 - bundle::kb_restore:
     inputs:
     - key: gomod-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/go/go.sum" }}
     - name: gomod
+- bundle::kb_restore:
+    inputs:
+    - key: gobuild-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/go/go.sum" }}
+    - name: gobuild
```
(and the matching `kb_save`) → `GO-G01`.

## How to confirm the fix
A `gobuild` entry appears in the metrics JSON with a non-`false` `restore_hit`, and `go build`/`go test`
noticeably speed up on the measure run once `GOCACHE` is actually being restored.

## Seen in the wild
The Go module cache (downloads) and the Go build cache (compiled package objects) are two different
directories that are easy to conflate — the same mistake shows up across ecosystems (see `AND-B01`
for the Gradle equivalent: key-based dependency cache mistaken for remote task caching).

## References
- `docs/PROJECT_SPEC.md` §6.8
- `scenarios/catalog.yml` (`GO-B01`)
