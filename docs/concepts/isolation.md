# Cache isolation between scenarios and runs

Condensed from `docs/PROJECT_SPEC.md` §4.2.

All scenarios in a pipeline run share one Bitrise workspace cache. Without isolation, a BAD
scenario could be rescued by entries uploaded by the GOOD scenario (or by yesterday's run), and the
"cold" seed build would not actually be cold.

Every scenario's cache keys are suffixed with `SHOWCASE_NS = <run-id>-<scenario-id>`, computed by
`tools/namespace.sh` and read via `{{ getenv "SHOWCASE_NS" }}` in every cache key template
(`.bitrise/bundles/gradle.yml`, `.bitrise/bundles/key-based.yml`). Two modes, via
`SHOWCASE_ISOLATION`:

- `isolated` (**default**): `run-id = $BITRISEIO_PIPELINE_ID` (falls back to `$BITRISE_BUILD_SLUG`
  for single-workflow runs outside a pipeline) → every pipeline run starts cold; seed is genuinely
  cold; scenarios can't help each other.
- `steady`: `run-id = "steady"` → namespace stable across runs; demonstrates steady-state behaviour
  (even with a warm cache, a BAD scenario still misses).

## This is a test-harness device, not a production pattern

`SHOWCASE_NS` deliberately injects a per-run value into cache keys/compile inputs so this repo's own
scenarios stay isolated from each other. **Never copy this into real production YAML** — injecting a
per-build value into compile inputs is exactly the anti-pattern `docs/scenarios/android/AND-B03.md`
and (once implemented) `IOS-B04` exist to teach against. The difference: this repo's namespace value
is constant *within* one scenario's seed+measure pair (so the measure build can still get real cache
hits against its own seed), and changes only *between* pipeline runs — a real volatile-input bug
changes on every single build, including within the same run.
