# Go (key-based caching)

Pipeline: `showcase-go`. Sample project: `projects/go` — a minimal Go module with one real
dependency (`rsc.io/quote`, pulling in `rsc.io/sampler` and `golang.org/x/text` transitively) so
`go.sum`/module downloads and `GOCACHE` have real content to restore/save.

Go has **no Bitrise Build Cache backend** — everything here is key-based caching (see
`docs/concepts/caching-mechanisms.md`), same as Node.js.

## Scenarios implemented so far

| ID | Verdict | Title |
|---|---|---|
| [GO-G01](../scenarios/go/GO-G01.md) | ✅ good | `pkg/mod` + `go-build` cache keyed on `go.sum` |
| [GO-B01](../scenarios/go/GO-B01.md) | ❌ bad | Only module cache, no GOCACHE |
| [GO-B02](../scenarios/go/GO-B02.md) | ❌ bad | Go toolchain drift |

## Key mechanics

- **Two separate caches, easy to conflate** (`GO-B01`): `~/go/pkg/mod` (downloaded dependency
  source) and `~/.cache/go-build` / `GOCACHE` (compiled package objects) solve different problems —
  caching only the first gives a false sense that "Go caching is set up."
- **Toolchain version belongs in the cache key** (`GO-B02`): `tools/run-go.sh` always installs a
  pinned Go version from scratch (`go.dev/dl`, not whatever's preinstalled on the stack), so seed
  and measure can genuinely run different real versions — demonstrating that pinning *which*
  version runs is necessary but not sufficient; the cache key itself needs to encode it too.
