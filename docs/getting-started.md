# Getting started

Requires a Bitrise workspace with Build Cache (a trial works), and this repo forked/connected as a
Bitrise app.

1. **Fork and connect.** Fork this repo, then add it as an app in your Bitrise workspace
   (Workspace → Add app → point at your fork). No secrets are required for the two implemented
   pipelines (`showcase-android`, `showcase-node`) — Build Cache auth is handled by the activation
   steps themselves.
2. **Push `bitrise.yml`.** This repo's `bitrise.yml` is generated (`make generate`) and already
   committed — Bitrise will pick it up automatically from the repo once the app is connected. If you
   change `scenarios/catalog.yml` or anything under `.bitrise/`, run `make generate` locally and
   commit the regenerated `bitrise.yml` + `.bitrise/workflows|pipelines/*` before pushing.
3. **Run a pipeline.** In the Bitrise dashboard, start pipeline `showcase-android` or
   `showcase-node` manually. Each scenario is a `seed → measure` pair running in parallel; the
   `report_<stack>` node at the end renders `showcase-report.html` / `.md` as a build artifact once
   every measure node has finished (`should_always_run: workflow`, so a broken scenario still gets
   reported rather than blocking the whole report).

Gradle Test Distribution and Bazel RBE modules (`docs/PROJECT_SPEC.md` §11) are not implemented in
this pass and need those features enabled for your workspace when they are.

## Local development

- `make generate` — regenerate `.bitrise/workflows/*`, `.bitrise/pipelines/*` and `bitrise.yml` from
  `scenarios/catalog.yml` + `.bitrise/bundles/*` (requires the `bitrise` CLI on `PATH` — the
  flattener shells out to `bitrise yml merge`).
- `make validate` — `bitrise yml validate` on both `bitrise.yml` and `bitrise.modular.yml`.
- `make lint` — static checks (`tools/yaml/check_conventions.py`, `tools/lint/cache_lint.py`, plus
  yamllint/shellcheck/ruff/markdownlint if installed).
- `make report-fixtures` — render the HTML/Markdown report and run assertions against the fixture
  metrics in `tools/report/fixtures/` (no Bitrise run needed) — useful when iterating on
  `tools/report/*`.

See `CLAUDE.md` for repo conventions and current implementation scope.
