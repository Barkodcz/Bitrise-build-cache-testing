---
id: GO-B02
verdict: bad
stack: go
fix_ref: GO-G01
tags: [toolchain-drift]
---
# GO-B02 — Go toolchain drift

**In one sentence:** the seed build runs Go 1.21.0, the measure build runs Go 1.22.0 — the
`GOCACHE` key template doesn't include the toolchain version at all, so a restored cache entry can
report a hit against an incompatible toolchain.

## What the configuration does
`.bitrise/workflows/go.yml` `go-b02__*` — identical bundle structure to `GO-G01`, but
`bundle::go_build`'s `go_version` input differs between phases:

```yaml
# go-b02__1_seed
- bundle::go_build:
    inputs:
    - go_version: "1.21.0"

# go-b02__2_measure
- bundle::go_build:
    inputs:
    - go_version: "1.22.0"
```

Both phases use the exact same `gobuild` cache key template
(`gobuild-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/go/go.sum" }}`) — the Go
version is never part of the key.

## What you see
- **Real captured log** (`go-b02__2_measure`, build 21, app `84c7a274-43b0-477d-9141-ea174ad0ce6e`, 2026-11-26):
  ```
  keybased_record: restore name=gomod hit=exact
  keybased_record: restore name=gobuild hit=exact
  run-go.sh: using go version go1.22.0 linux/amd64
  ```
  — this is the measure run; the seed run used `go1.21.0`. The `gobuild` entry still reports
  `hit=exact` even though the underlying toolchain changed, confirming the symptom exactly as
  designed: an exact key match restoring cache content built by an incompatible toolchain.
- Metrics: the `gobuild` entry's `restore_hit` can still report `exact` (the literal key string
  matched), but the restored cache was built by a different Go toolchain than the one now running —
  `go build` has no obligation to trust or reuse cache entries built by a different version, so real
  savings don't materialize even on a reported "hit."

## Why it happens
Go's build cache format and contents are toolchain-version-specific. Pinning *which* Go version a
workflow runs (this repo's own `go_version` bundle input, or a `go.mod` `go` directive in a real
project) solves "are seed and measure using the same toolchain" — but it does nothing to stop a
*stale* cache entry from a previous, different toolchain from being restored under the same key and
silently wasting restore time for no benefit. The key itself needs to encode the toolchain version
(or any other build-affecting flag) that the cache contents depend on.

## How to fix it
```diff
-    key: gobuild-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/go/go.sum" }}
+    key: gobuild-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-go{{ getenv "SHOWCASE_GO_VERSION" }}-{{ checksum "projects/go/go.sum" }}
```
(so a version change naturally busts the key instead of restoring a now-useless entry) → `GO-G01`
with both phases pinned to the **same** `go_version`.

## How to confirm the fix
Once the key includes the version, a toolchain change produces a clean cache **miss** instead of a
wasted "hit" — and once both phases agree on one version (the actual fix), the build cache delivers
its expected speedup.

## Seen in the wild
Pinning the toolchain (a `go.mod` `go` directive, or the CI image/stack version) is necessary but
not sufficient on its own — the cache key itself should include the version too, the same lesson
`AND-B08` (JDK mismatch) teaches for Gradle.

## References
- `docs/PROJECT_SPEC.md` §6.8
- `scenarios/catalog.yml` (`GO-B02`)
