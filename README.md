# bitrise-build-cache-showcase

A public, open-source monorepo that demonstrates — side by side in a single Bitrise Pipeline view —
what **correct** and **incorrect** Bitrise Build Cache / key-based caching configuration looks like,
per stack, with quantified before/after metrics and an auto-generated report.

> Requires a Bitrise workspace with Build Cache (a trial works). Gradle Test Distribution and Bazel
> RBE modules (planned, not yet implemented) will need those features enabled for your workspace.

## Quick start

1. Fork this repo and connect it as a Bitrise app.
2. Push (it's already committed) — Bitrise picks up `bitrise.yml` automatically.
3. Start pipeline `showcase-android` or `showcase-node` from the Bitrise dashboard.

Full walkthrough: [`docs/getting-started.md`](docs/getting-started.md).

## How it works

Every scenario is a pair of workflows on two fresh VMs: `<id>__1_seed` (cold build, populates
caches) → `<id>__2_measure` (fresh VM, deterministic simulated commit, builds again, collects
metrics). All scenario pairs in a stack's pipeline run in parallel; a final `report_<stack>` node
pulls every scenario's metrics and renders `showcase-report.html` / `.md` + JUnit assertions. See
[`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md) §4 for the full architecture.

## Scenario matrix

<!-- SCENARIO-MATRIX:START (regenerate with `make docs`, paste the table below) -->
| Stack | Implemented | Planned | Total |
|---|---|---|---|
| android | 6 | 10 | 16 |
| bazel | 0 | 7 | 7 |
| cross-cutting | 0 | 3 | 3 |
| flutter | 0 | 4 | 4 |
| go | 3 | 0 | 3 |
| ios | 0 | 13 | 13 |
| jvm-maven | 3 | 0 | 3 |
| node | 5 | 2 | 7 |
| python | 4 | 0 | 4 |
| react-native | 0 | 7 | 7 |
| ruby | 0 | 3 | 3 |
| rust | 3 | 0 | 3 |
| **total** | **24** | **49** | **73** |
<!-- SCENARIO-MATRIX:END -->

Six stacks are fully implemented and wired into a real `bitrise.yml`: **Android/Gradle**
(`docs/stacks/android.md`), **Node.js key-based caching** (`docs/stacks/node.md`), **Go**
(`docs/stacks/go.md`), **Rust** (`docs/stacks/rust.md`), **Python** (`docs/stacks/python.md`), and
**Java/Maven** (`docs/stacks/jvm-maven.md`). Every other stack from the full spec is catalogued
(`scenarios/catalog.yml`, `status: planned`) with a doc stub, ready to be implemented the same way
— see [`CLAUDE.md`](CLAUDE.md) "Scope status".

## Docs

- [`docs/concepts/caching-mechanisms.md`](docs/concepts/caching-mechanisms.md) — Build Cache vs.
  key-based caching, the two mechanisms this whole repo is about.
- [`docs/concepts/metrics.md`](docs/concepts/metrics.md) — how to actually tell if a cache is
  working (and why naive hit rate lies to you).
- [`docs/concepts/isolation.md`](docs/concepts/isolation.md) — how scenarios stay isolated from each
  other within one pipeline run.
- [`docs/scenarios/`](docs/scenarios/) — one page per scenario: symptom → log evidence → root cause
  → fix diff.
- [`docs/reference/verified-facts.md`](docs/reference/verified-facts.md) — every version-sensitive
  fact (step majors, stack IDs, input names) this repo relies on, with the date and method used to
  verify it against the live steplib/CLI.
- [`docs/reference/oss-projects.md`](docs/reference/oss-projects.md) — a real open-source project
  researched for every stack (implemented and planned), so caching savings can be demonstrated on
  something bigger than the current small fixture projects.

### Honesty box

> The sample projects are synthetic and sized for a demo. Absolute numbers depend on your project's
> module graph, change patterns and machines. Treat the showcase as a demonstration of
> **mechanisms and symptoms**, not as a promise of a specific speed-up. For a realistic estimate,
> benchmark on your own commit history starting from an empty cache.

## License

Code: MIT ([`LICENSE`](LICENSE)). Docs: CC-BY-4.0 ([`LICENSE-docs`](LICENSE-docs)).
