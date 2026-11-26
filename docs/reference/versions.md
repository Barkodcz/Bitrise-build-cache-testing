# Pinned step majors and stack IDs

Single place this repo pins version-sensitive facts. See `docs/reference/verified-facts.md` for how
and when each of these was checked against the live steplib/CLI, and `tools/yaml/stacks.yml` for the
logical-name → real-ID mapping used by the generator.

| Step | Pinned major | Used by |
|---|---|---|
| `git-clone` | `@8.5.3` | `bundle::setup_checkout` |
| `activate-build-cache-for-gradle` | `@3.18.1` | `bundle::gradle_build_cache` |
| `gradle-runner` | `@6.0.0` | not used directly yet — Android scenarios run Gradle via `script@1.2.1` + `tools/run-gradle.sh` so the showcase metrics init script can be injected explicitly |
| `restore-cache` | `@3.0.2` | `bundle::gradle_deps_cache_restore`, `bundle::kb_restore` |
| `save-cache` | `@1.5.3` | `bundle::gradle_deps_cache_save`, `bundle::kb_save` |
| `pull-intermediate-files` | `@1.3.7` | `bundle::report` |
| `deploy-to-bitrise-io` | `@2.26.2` | `bundle::deploy_metrics`, `bundle::report` |
| `script` | `@1.2.1` | every inline shell step |

| Logical stack (catalog `stack_id`) | Real stack ID |
|---|---|
| `linux-default` | `ubuntu-noble-24.04-bitrise-2025-android` |
| `xcode-26` | not yet resolved — iOS stack is `status: planned` |
| `xcode-16-legacy` | `osx-xcode-16.4.x` (tentative, not yet used by an implemented scenario) |

Machine type IDs are intentionally unset in every workflow in this pass — see
`docs/reference/verified-facts.md` for why.
