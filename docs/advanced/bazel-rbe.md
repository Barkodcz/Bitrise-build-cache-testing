# Bazel Remote Build Execution — worker-scaling showcase

**Status: not implemented in this pass.** See `CLAUDE.md` "Scope status" and `docs/PROJECT_SPEC.md`
§11.2 for the full design (worker-pool resize matrix, `--jobs` scaling, bad-pool/bad-push/bad-exec-props
cells). Gated behind `SHOWCASE_ENABLE_BAZEL_RBE` in `.bitrise/00-app.yml` (currently `"false"`
workspace-wide with no workflow consuming it yet, and the Bazel stack itself is also `status:
planned` in `scenarios/catalog.yml`).

Requires RBE enabled for your workspace (trials typically get up to ~10 workers) and a worker pool
created in every datacenter your builds can land in.
