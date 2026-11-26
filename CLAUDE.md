# CLAUDE.md

This repo is `bitrise-build-cache-showcase`. Source of truth for the full design is
`docs/PROJECT_SPEC.md`. Scenario data lives in `scenarios/catalog.yml`.

## Known deviations from the spec in this pass

- `projects/android` is hand-written (static), not produced by a `generators/android.py` deterministic
  generator as spec §4.3 describes. `generators/` is currently empty. If a future pass adds generated
  projects (needed once `S`/`M`/`L` sizing per spec §12.4 matters), follow that pattern instead.
- `projects/android` is a plain Kotlin/JVM multi-module project, not a real Android Gradle Plugin
  project — it builds with just a JDK (no Android SDK) so it's runnable anywhere. See
  `projects/android/README.md`.
- Byte-traffic metrics (`remote_cache.bytes_downloaded`/`bytes_uploaded`/`download_upload_ratio`) are
  not collected yet — always `null`. Expectations relying on them were removed from
  `scenarios/catalog.yml` for the implemented scenarios; see the inline notes there and
  `docs/reference/verified-facts.md`.
- Utility/report workflows are named `report_<stack>`, not `_report_<stack>` — the Bitrise platform
  rejects leading-underscore "utility workflow" names inside a pipeline. See verified-facts.md.

## Scope status (read this first)

The full spec (§13 milestones) covers 10 stacks and ~90 scenarios. This repo currently
**implements** five stacks end-to-end (`android`, `node`, `go`, `rust`, `python` — see `status: implemented` in
`scenarios/catalog.yml`) and carries every other spec'd scenario as `status: planned`
(catalog entry + doc stub, no bundle/workflow yet). When picking up more stacks, follow
the same pattern used for `android`/`node`: generator project → bundles → catalog entries
flipped to `implemented` → `make generate` → doc pages → real run → capture real log lines.
`docs/reference/oss-projects.md` has a real open-source project already researched for every
stack (including bigger upgrade candidates for `android`/`node`'s current tiny fixtures) — check
there before researching a sample project from scratch.

## Conventions

- Never hand-edit `bitrise.yml`, `bitrise.modular.yml` includes under `.bitrise/workflows/`
  or `.bitrise/pipelines/` for *generated* scenario content — run `make generate`. Bundles
  under `.bitrise/bundles/` are hand-written; edit those directly.
- One deliberate defect per BAD scenario. Every BAD/regression-guard scenario must still
  **exit 0** — the point is a measurable symptom, not a red build.
- No secrets, workspace/app slugs beyond the one public app ID already in `docs/`, or
  customer names anywhere. The namespace injection described in §4.2 of the spec is a
  **test-harness-only** device — never copy it into real production YAML.
- Every new scenario = catalog entry + bundle input/patch + doc page (`docs/scenarios/<stack>/<ID>.md`)
  + `expectations` + a static lint check in `tools/lint/cache_lint.py` if statically detectable.
- Don't invent log lines, screenshots or benchmark numbers. Capture them from a real Bitrise
  run and mark anything not yet captured as `_To be captured from a real run._`.
- Verify version-sensitive facts (step majors, stack IDs, input names) against the live
  steplib/CLI before relying on them, and log the outcome + date in `docs/reference/verified-facts.md`.
- Before finishing a task that touches generated files: `make lint generate validate`.

## Useful commands

- `make generate` — regenerate `.bitrise/workflows/*`, `.bitrise/pipelines/*` from
  `scenarios/catalog.yml`, then flatten to `bitrise.yml`.
- `make validate` — `bitrise yml validate -c bitrise.yml`.
- `make lint` — static checks (see `Makefile`; yamllint/shellcheck/ruff are best-effort,
  skipped with a warning if not installed locally).
- `bitrise app list` / `bitrise yml update` — inspect/push config to the live app
  (`84c7a274-43b0-477d-9141-ea174ad0ce6e`, see `docs/reference/verified-facts.md`).
