# Troubleshooting

## `make generate` fails with "bitrise yml merge failed"
The flattener (`tools/yaml/flatten.py`) shells out to the real `bitrise` CLI. Make sure it's
installed and on `PATH` (`bitrise --version`). The flattener has no other dependency on your Bitrise
auth/login state — `bitrise yml merge` resolves includes locally.

## `bitrise yml validate` says a workflow "is a utility workflow"
Workflow names starting with `_` are reserved by the platform and cannot be referenced from a
pipeline at all (not just "not triggerable directly" as earlier drafts of the spec assumed) — see
`docs/reference/verified-facts.md`. Rename it without the leading underscore.

## A scenario's assertion always fails even though the YAML looks right
Check `scenarios/catalog.yml`'s `expectations` for that scenario against
`docs/reference/metrics-schema.json` — a dotted path has to resolve through
`tools/report/expectations.py`'s view (which aliases `cache.*` → `remote_cache.*`, computes
`duration.vs_seed`, and reads `key_based.*` off the first array entry). If the underlying metric is
genuinely not collected yet (e.g. byte traffic, see `docs/concepts/metrics.md`), don't assert on it —
leave a note instead, per the "never fabricate" rule (spec §8.3).

## Pipeline looks "staggered" instead of all scenarios starting together
This is a concurrency limit on your workspace, not a bug — each stack's pipeline wants
`2 × scenario-count` concurrent jobs to render as a clean grid. See `docs/PROJECT_SPEC.md` §7.5.

## Seed and measure give wildly different results for a GOOD scenario
Check `run.datacenter` in both phases' metrics JSON — `tools/report/assertions.py` marks a scenario
"not comparable" (skips, doesn't fail) when seed and measure land in different datacenters, since
the cache origin is per-DC and a DC crossing looks exactly like a cold cache.
