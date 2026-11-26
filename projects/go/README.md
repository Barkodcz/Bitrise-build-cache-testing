# projects/go

Minimal Go module used by the key-based caching scenarios (`scenarios/catalog.yml` `GO-*`).
Real dependency (`rsc.io/quote`, with its own transitive deps `rsc.io/sampler` and
`golang.org/x/text`) so `go.sum`/`go mod download` and `GOCACHE` have real content to restore/save.

- `pkg/core` — a "widely depended" package; `main.go` and (in the future) every feature package
  would import it.
- `pkg/leaf` — depends on `core`, nothing depends on it; `tools/simulate-change.sh go leaf`
  mutates its `Label()` return value to simulate a code change.

`go build ./...` and `go test ./...` are the two commands every `GO-*` scenario runs.
