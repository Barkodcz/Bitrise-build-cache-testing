# PROJECT SPEC — `bitrise-build-cache-showcase`

> **Audience:** Claude Code (the implementing agent) and human maintainers.
> **Owner:** Balázs Barkó (Solutions Architect, Bitrise).
> **License:** MIT (code) + CC-BY-4.0 (docs). Public GitHub repository.
> **Status of this document:** source of truth for v1. When reality (a step input name, a stack ID, a log line) disagrees with this spec, **reality wins** — fix the code, then update this spec and note it in `docs/CHANGELOG.md`.

---

## 0. How to use this document (instructions for Claude Code)

1. Read the whole spec once before writing code. Sections 3–4 (architecture + conventions) constrain everything else.
2. Build in the **milestone order in §13**. Each milestone ends with a runnable, validated state (`bitrise validate` passes, `make lint` passes, docs updated).
3. Copy this file into the repo as `docs/PROJECT_SPEC.md` and create a short `CLAUDE.md` at the repo root that points to it and lists the conventions in §4 (see §12.3 for its content).
4. Facts tagged **[VERIFY]** are things this spec believes to be true but that you must check against the live source (Bitrise docs, the steplib, `bitrise-build-cache-cli` releases, a real build log) before relying on them. Record the outcome in `docs/reference/verified-facts.md` with date + source link.
5. Never commit secrets, workspace slugs, app slugs, tokens or customer names. Everything customer-derived in this spec is already anonymised; keep it that way.
6. Every bad scenario must **still exit 0** (the build is green — the badness is time / cache misses / bytes), unless the scenario is explicitly tagged `expected_failure: true` (there are none in v1).

---

## 1. What we are building — one paragraph

A public, open-source monorepo that **demonstrates, side by side in a single Bitrise Pipeline view, what correct and incorrect build caching looks like** for every major mobile and adjacent stack (Android/Gradle, iOS/Xcode, React Native, Flutter, Bazel, Node.js, Ruby/CocoaPods/fastlane, Go, Rust, Python, Java/Maven), plus an optional module showing how **Bitrise Gradle Test Distribution** (Bitrise's remote execution for Gradle unit tests, built on the Bazel RBE infrastructure) scales with a small vs. a large number of remote worker machines, and an optional module doing the same for **Bazel Remote Build Execution**. Each scenario is a pair of workflows (cold "seed" → warm "measure") that emits machine-readable metrics; a final report workflow turns all metrics into an HTML comparison page, a Markdown summary and pass/fail assertions. The repository is equally a **teaching resource** (docs explain *why* each bad pattern is bad, what the log looks like, and how to fix it) and a **regression canary** for Bitrise Build Cache (if a "good" scenario stops hitting the cache, the report workflow fails).

## 2. Goals, non-goals, success criteria

### 2.1 Goals

| # | Goal |
|---|---|
| G1 | For each stack: at least one **GOOD** scenario and 3–8 **BAD** scenarios, each modelled on a real failure pattern seen in the field (see §6). |
| G2 | **Same-screen visibility:** one Pipeline per stack where every scenario is a row (seed → measure) running in parallel, so GOOD and BAD are visible next to each other with their durations in the Bitrise Pipeline graph. |
| G3 | **Quantified results:** every measure run emits a JSON metrics file (duration, hits/misses, bytes up/down, key-based cache hit type, archive size). |
| G4 | **One report** per pipeline run: `showcase-report.html` (deployed as artifact) + Markdown summary + assertions that the GOOD scenarios behave GOOD and BAD scenarios reproduce their documented symptom. |
| G5 | **All YAML lives in the repo.** `bitrise.yml` uses **step bundles** for every reusable unit and **graph pipelines** (`depends_on`) for orchestration. No logic hidden in the Bitrise web UI. |
| G6 | **Excellent docs:** a concept guide, one page per stack, one page per scenario (symptom → log evidence → root cause → fix diff), a "how to read the report" guide, and a troubleshooting guide. |
| G7 | **Optional advanced modules:** (a) Gradle Test Distribution worker-scaling matrix, (b) Bazel RBE worker-scaling matrix. Off by default, enabled by env flags. |
| G8 | **Forkable:** anyone with a Bitrise workspace that has Build Cache (trial is enough) can fork, add the app, set 0–2 secrets and run. |

### 2.2 Non-goals

- Not a benchmark of Bitrise vs. other CI vendors. No competitor names in code or docs.
- Not a product to sell numbers: the showcase must be honest. Synthetic projects give *directional* numbers; the docs say so prominently (§10.6).
- Not covering Bitrise-internal data sources (BigQuery, Data Mage, GCS log buckets). Everything must be reproducible from public tools + the build itself.
- No customer data, names, or slugs anywhere.

### 2.3 Success criteria (definition of done for v1)

1. `bitrise validate -c bitrise.yml` passes; `make lint` (yamllint + shellcheck + ruff + markdownlint) passes.
2. Running pipeline `showcase-android` on Bitrise produces a report where: GOOD warm-run Gradle `FROM-CACHE` share ≥ 60 % of executed-or-cached cacheable tasks and download/upload byte ratio ≥ 2; every BAD scenario's assertion "symptom reproduced" is true.
3. Same for `showcase-ios`, `showcase-react-native`, `showcase-flutter`, `showcase-bazel`, `showcase-key-based`.
4. Each scenario has a doc page following the template in §10.4.
5. A first-time user can follow `docs/getting-started.md` and get a green run in < 30 minutes of setup.

---

## 3. Background knowledge the implementer must internalise

This section is the condensed domain knowledge the scenarios are built on. It comes from Bitrise public docs, the Bitrise Build Cache CLI changelog, internal SA audit playbooks and field diagnoses (anonymised). Put a cleaned, public version of this into `docs/concepts/` (see §10).

### 3.1 Two different caching mechanisms — never confuse them

| | **Bitrise Build Cache** (managed remote build cache) | **Key-based caching** (`restore-cache` / `save-cache` and the per-ecosystem shortcut steps) |
|---|---|---|
| What it caches | **Compiled task / action outputs**, content-addressed, per individual task/action/compile unit | **Directories** (dependency caches, toolchains) packed into one archive per key |
| Granularity | Fine (each task / compile / action has its own key) | Coarse (one archive, all-or-nothing per key) |
| Supported tools | **Gradle**, **Xcode (26+)**, **Bazel**, **React Native** native layer (Gradle + Xcode + `ccache` for C++) | Any stack: npm/yarn/pnpm, CocoaPods, SPM, pub, Bundler, Go modules, Cargo, pip/Poetry, Maven, Gradle dependency cache |
| Activation | `activate-build-cache-for-gradle`, `activate-build-cache-for-xcode`, `activate-build-cache-for-bazel`, `activate-build-cache-for-react-native` | `restore-cache` + `save-cache` with a key template, or shortcut steps (`restore-gradle-cache`, `restore-npm-cache`, `restore-cocoapods-cache`, `restore-spm-cache`, `restore-dart-cache` … and their `save-*` pairs) **[VERIFY current step versions]** |
| Invalidation | Automatic, by content hash of inputs | By **key template** you write (`{{ checksum "lockfile" }}`, `{{ .OS }}`, `{{ .Branch }}` …) |
| Retention | Managed by Bitrise (TTL/eviction, per data-centre origin) | 7 days since last use, LRU eviction under pressure, 15 GB max per archive, key ≤ 512 chars, no commas |
| Typical failure | Silent: cache activated but never engaged, or keys busted by volatile inputs | Silent: key never changes (stale forever) or restore key ≠ save key (never hits) |

A yaml can have excellent key-based caching of `~/.gradle/caches` and still have **no** Build Cache for Gradle — they solve different problems (dependency downloads vs. compiled outputs). Crediting one for the other is the most common audit mistake. The showcase must make that visible (scenario `AND-B01`).

### 3.2 How to tell if a remote build cache is "working" — the metric that matters

- **Primary metric: download/upload byte ratio** of cache traffic for a build or a set of builds. A healthy cache reads far more than it writes (ratio ≫ 1, often 5–200×). A ratio ≈ 1 or < 1 means the build re-writes about as much as it reads → little reuse ("thrash") or a cold cache.
- **Naive hit rate is misleading.** Averaging per-invocation hit rate across all invocations is diluted by non-cacheable companion invocations (e.g. `xcodebuild -showBuildSettings`, `-resolvePackageDependencies`, `-exportArchive`, Gradle `dependencies`/`projects`). A real case read 12 % naive hit rate while delivering a 195× download/upload ratio. **The showcase reports both, and teaches why the ratio wins.**
- **A screening number is not a verdict.** Ratio ≈ 1 has innocent causes: (a) cold cache / first builds, (b) builds spread across data centres (the cache origin is per-DC; every DC crossing starts cold), (c) a very low build cadence so entries age out, (d) a structural many-flavour/white-label matrix, (e) large always-fresh outputs. The showcase must include a doc section on these and, where possible, a scenario (`AND-B10` for "consecutive builds, same commit, but cache namespace rotated" simulates (a)).
- **Thrash vs. stable partial reuse:** thrash = keys rotate every build, reuse ≈ 0 erratically. Stable partial reuse = the *same* hit/miss split repeats across consecutive builds (structural miss set: non-cacheable tasks). One aggregate can't distinguish them; comparing two consecutive builds can. The report shows seed vs. measure side by side for exactly this reason.
- **Some work is never cacheable by design** — Xcode: storyboard/XIB compilation, asset catalogs, code signing, dSYM generation, linking in some configurations; Gradle: some lint/verification tasks, packaging/signing. A sub-100 % hit rate is normal. Docs must say so up front so readers don't misread GOOD scenarios.
- **Realistic expectations** (from Bitrise's internal "realistic benchmark" method — clean cache, then build a real sequence of commits): Gradle ≈ 32–49 % duration reduction on good projects (but ≈ 3 % on a project whose main branch commits were huge, despite a 70 % hit rate); Bazel ≈ 87–92 %; Xcode ≈ 14–55 %. *Which* tasks are cached matters more than hit-rate %. Docs must quote ranges, never a single headline number.

### 3.3 Gradle — what good and bad look like

**Good:**
- `activate-build-cache-for-gradle` runs **after checkout and before the first Gradle invocation** (`gradle-runner`, `android-build`, `android-unit-test`, `./gradlew` in a script). The step writes `~/.gradle/init.d/bitrise-build-cache.init.gradle.kts` and `~/.gradle/gradle.properties`.
- Gradle wrapper and dependency caches are key-cached separately (`~/.gradle/wrapper` keyed on `gradle-wrapper.properties`; `~/.gradle/caches` keyed on `**/*.gradle*` + `gradle.properties` + version catalogs), *or* use `restore-gradle-cache`/`save-gradle-cache`.
- Inputs are **relocatable and deterministic**: `PathSensitivity.RELATIVE`, no absolute paths as `@Input` strings, no timestamps/build numbers/git SHAs baked into compiled sources of widely-depended modules (inject them only in the final app module, ideally at packaging time / via resource that isn't a compile input of libraries).
- Toolchain pinned and identical across writer and reader workflows (Gradle wrapper version, JDK, AGP, Kotlin).
- One workflow (main branch / nightly) is the canonical writer (push on); PR workflows may push or be read-only, but **someone** must push.
- Healthy log signs: tasks marked `FROM-CACHE` in `--console=plain` output; Build Cache step output shows "Cache plugin usage: enabled"; download ≫ upload.

**Bad (each becomes a scenario):**
- No activation at all; only `~/.gradle/caches` key-cached (looks cached, isn't remote-task-cached).
- Activation step placed **after** the Gradle build step (present in the yaml, zero benefit).
- Volatile input: `buildConfigField("String","BUILD_TIME","\"${System.currentTimeMillis()}\"")` or `BITRISE_BUILD_NUMBER`/git SHA in a **core** library module → that module and every dependant miss on every build.
- Non-relocatable input: absolute path passed as `@Input String`, or `@InputFile` without relative path sensitivity, combined with a checkout directory that differs per build.
- `--rerun-tasks`, `--no-build-cache`, or `org.gradle.caching=false` sneaking in via `gradle.properties`/args.
- A custom expensive task (codegen) that is not `@CacheableTask` / doesn't declare outputs → re-runs every time.
- JDK (or Gradle) mismatch between writer and reader workflows → zero cross-workflow hits.
- Push disabled on every workflow → cache never populated.
- Key-caching raw `**/build/` / `intermediates/` directories on top → huge archives, slower than no cache.
- Configuration-cache add-on with `GRADLE_ENCRYPTION_KEY` regenerated per build → config cache invalidated every run (optional advanced scenario).
- Log of the Build Cache step showing `Cache plugin usage: none` — the plugin was not enabled even though the step ran (real field case).
- NDK/CMake native code compiled without `ccache` (the Gradle plugin doesn't cover it) — optional.

### 3.4 Xcode — what good and bad look like

**Good:**
- Stack with **Xcode 26 or newer** (Xcode compilation caching is an Xcode 26 feature).
- `activate-build-cache-for-xcode` after checkout, **before** `xcode-archive`, `xcode-test`, `xcode-build-for-simulator`, `xcode-build-for-test`, fastlane, or a script calling `xcodebuild`.
- The step installs `xcodebuild`/`xcrun` **shims** in `~/.bitrise-xcelerate/bin` and prepends it to `PATH`; interception is **by name via PATH only**. Builds must call `xcodebuild` via PATH.
- DerivedData is **not** key-cached in the same workflow (let Build Cache own compilation reuse).
- CocoaPods: `~/Library/Caches/CocoaPods` keyed on `Podfile.lock`; SPM: `~/Library/Caches/org.swift.swiftpm` (+ `SourcePackages` if using a custom `-clonedSourcePackagesDirPath`) keyed on `Package.resolved`.
- Build numbers set via `Info.plist`/`agvtool`/`CURRENT_PROJECT_VERSION` at archive time — **not** via preprocessor macros or Swift `-D` flags that become compile inputs.
- Healthy log signs: per-invocation `Proxy blob stats: hits: N (…) / total: M (P%). Uploaded blobs: U (…)` with high P% and small upload on warm runs **[VERIFY exact wording in current CLI]**; verbose per-key `Cache hit`/`Cache miss` lines in `xcelerate-*.log` artifacts when verbose logging is on.

**Bad:**
- Activation on an **older Xcode stack** (15.x/16.x) → **silent no-op**: green step, normal build, zero cache traffic.
- Key-based restore of **DerivedData** in the same workflow → Xcode finds local outputs and never queries the remote cache. Silent.
- **Shim bypass**: `tuist build` / `tuist test` (call `/usr/bin/xcrun xcodebuild` by absolute path), or scripts/fastlane configs calling `/usr/bin/xcodebuild` or `/Applications/Xcode*.app/.../xcodebuild` directly → activation green, zero traffic (`Proxy blob stats: hits: 0 / total: 0`, no `SetSession called`). `tuist generate` followed by a normal Xcode step is fine.
- **Volatile compile flags**: `GCC_PREPROCESSOR_DEFINITIONS=BUILD_NUMBER=$BITRISE_BUILD_NUMBER` or `OTHER_SWIFT_FLAGS=-DBUILD_$N` → every compile key changes → full miss + full re-upload every build.
- Activation step **after** the build step.
- Rotating absolute checkout paths (e.g. source restored by `pull-intermediate-files` into a random temp dir) **used to** bust keys. **Fixed** in Build Cache CLI v2.8.5 (`CLANG_ENABLE_PREFIX_MAPPING=YES` injected; step versions `activate-build-cache-for-xcode` 0.13.7, `activate-react-native-features` 0.8.7). Keep as a **regression-guard scenario** that is expected to look GOOD now (§6.2 `IOS-R01`).
- `no_swift_cache: "true"` input (caches only Clang/ObjC/C++, leaves Swift uncached) used as a default rather than a targeted workaround for explicit-modules errors → most of a Swift app uncached.
- CocoaPods cache with static key, or restore key ≠ save key, or `Pods/` cached instead of the CocoaPods cache dir.
- Caching `~/Library/Developer/Xcode/Archives` or `CoreSimulator` (pointless/harmful bulk).
- Note: Build Cache gives little for `xcode-test` *test execution* time — it accelerates compilation. Test-time acceleration is test sharding (out of scope, mention in docs).

### 3.5 React Native — three layers

| Layer | Mechanism |
|---|---|
| Android native compile | Build Cache (Gradle backend) |
| iOS native compile | Build Cache (Xcode backend, Xcode 26+) |
| C++ native modules / bridge | `ccache`, configured by the same RN activation step |
| JS bundling (Metro) | **Not** cached by Build Cache |
| yarn/npm/pnpm install | **Not** cached by Build Cache → key-based cache of the package manager cache |

- Step: `activate-build-cache-for-react-native@0` right after checkout. Native build commands in **script** steps must be wrapped: `bitrise-build-cache react-native run <cmd>` (e.g. `… run npx react-native run-android --mode=release`). Official `gradle-runner`/`android-build`/`xcode-archive` (latest versions) wrap automatically.
- Inputs: "Enable Xcode cache" / "Enable Gradle cache" toggles **[VERIFY YAML keys]**, `no_swift_cache`, `cache_skip_flags` (skip passing cache build settings except the socket path, for projects managing their own Xcode cache settings).
- Typical gaps: native cache on, JS dependency cache missing; JS cache keyed on the wrong lockfile; unwrapped script commands; iOS leg on old Xcode; blind `node_modules` caching.
- Expected savings ceiling is lower than pure native apps because the JS toolchain isn't touched. Say so in the docs.

### 3.6 Bazel

- Step `activate-build-cache-for-bazel` before any `bazel build/test`; it writes the remote cache config into `.bazelrc` / user bazelrc automatically **[VERIFY where]**.
- Good: hermetic actions, stable flags across writer/reader, `--config=ci` shared, no volatile stamping on widely-depended targets.
- Bad: `--stamp` with a volatile `workspace_status_command` feeding many targets; non-hermetic `genrule` (writes `date`/hostname) upstream of everything; `--action_env` leaking `BITRISE_BUILD_NUMBER`; writer/reader flag differences (`-c opt` vs default, different `--copt`) → disjoint output keys; key-based caching of the output base *on top of* the remote cache (huge archive, little gain).
- Cold remote cache looks like "no improvement" for the first builds — warm-up matters more than on other stacks.
- `bazel build` is the well-trodden path; `bazel test` caching has had field reports of being less reliable in some configs — treat as **[VERIFY]**, don't assert.

### 3.7 Bazel Remote Build Execution (RBE) on Bitrise

- Enable via the Bazel step input `enable_rbe: true` (CI) or `bitrise-build-cache activate bazel --cache --cache-push=false --rbe` (elsewhere). Workers upload results themselves, so keep `--cache-push=false` / `--noremote_upload_local_results`.
- Recommended `.bazelrc` under `build:remote`: `--jobs=100` (default = host CPU count underuses the cluster; raise gradually with worker count), `--remote_default_exec_properties=Pool=<pool-name>` (must match the pool name exactly; same name in every DC; don't set other `exec_properties` on targets), `--spawn_strategy=remote,local`, `--noremote_upload_local_results`. Run with `bazel build //... --config=remote`.
- Per-target pool routing via a `platform` with `exec_properties = {"Pool": "<name>"}` + `--extra_execution_platforms`.
- Workers are co-located with CI machines in the same DCs (Amsterdam, Chicago, West Virginia), same VM images as CI. RBE in a DC uses the cache in that DC only; if a pool exists only in one DC, builds landing in another DC fail with "workers don't exist" unless cache + RBE endpoints are overridden to that DC. **Create the pool in every DC the builds can land in.**
- Trials typically get up to ~10 workers. Worker pools are created in the Bitrise UI (Build Cache → Bazel remote execution) and can also be managed via the RBE REST API (`/infrastructure/remote-execution/v1/workspaces/{workspace}/worker_pools`, `PATCH` to change `minReplicas`/`maxReplicas`; auth header `Authorization: <PAT>`, no `Bearer`) **[VERIFY public availability of the API for customers]**.

### 3.8 Gradle remote execution on Bitrise = Gradle Test Distribution (private beta)

There is **no general-purpose Gradle RBE** (remote execution of compile tasks) on Bitrise. What exists is **Gradle Test Distribution (GTD)**: a Gradle plugin that discovers tests, splits them into shards, sends shards to remote workers (the same worker-pool infrastructure as Bazel RBE), runs them in parallel with JUnit, and merges results back into normal Gradle output/test reports. Facts:

- **Status: private beta** (since late 2025). Requires the Advanced CI team to enable Remote Execution for the workspace. The showcase module must be **off by default** and the docs must say how to request access.
- **Requirements:** Gradle-built project with **a few thousand unit tests**. With small suites, per-shard overhead (~5–6 s JUnit start-up per shard) eats the gain — a great BAD scenario.
- **Worker pool setup** (Workspace settings → Remote Execution → + Worker pool): image `linux-docker-bitvirt` (Linux); machine type XL–4XL; **concurrency ≈ 4** per machine (set internally by Bitrise for now); start with **3–4 replicas**; create a pool in each DC; rolling update 50 %; label `gradle`; warm-up script downloads the JUnit console launcher:
  `wget -O /junit.jar https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.12.0/junit-platform-console-standalone-1.12.0.jar`
- **Workflow:** two **unpublished** git-sourced steps:
  ```yaml
  - git::https://github.com/bitrise-steplib/bitrise-step-activate-gradle-features.git@main:
      inputs:
      - build_cache_enabled: "true"
      - build_cache_push: "false"
      - build_cache_validation_level: none
      - test_distribution_enabled: "true"
      - test_distribution_shard_size: "200"
      - verbose: "true"
  # ... gradle test invocation (must contain the top-level test task / test flavour) ...
  - git::https://github.com/bitrise-steplib/bitrise-step-collect-distributed-gradle-test-results.git@main: {}
  ```
  Pin to a commit SHA in the showcase, never `@main` **[VERIFY latest SHA at implementation time]**.
- **Not compatible with configuration cache** yet → add `--no-configuration-cache` to test invocations.
- Default worker Java: SE 17 (class file 61); other versions need a warm-up script change.
- **Verification signals:** log lines tagged `[Bitrise Test Distribution]`; `rbeTest` tasks in the invocation list; test results deployed.
- **Benchmark reference (DuckDuckGo-Android, internal, 2025):** baseline single CI node (16 vCPU / 64 GB) 3 m 20 s; with distribution 2 m 00 s (−40 %) up to 1 m 27 s (−56.5 %), best on 3–4 Linux XL machines; best cost/benefit was **560 tests/shard on 4 XL nodes × 3 workers (12 workers)**. Shard sizes 70 and 140 also tested — larger shards amortise start-up overhead. Discovery/upload/fetch overhead < 2 s total; the two real levers are execution time and queue time.
- **Interpretation for the scaling module:** wall time falls as workers increase until (a) queue time hits zero, (b) per-shard fixed overhead dominates, (c) the longest shard dominates. Past that point more machines cost more and don't help. The module must show that curve, including the "too many workers / too-small shards" bad case.

### 3.9 Key-based caching mechanics (applies to every stack)

- `restore-cache` right after checkout and before the install step it feeds; `save-cache` after the install/build step and before deploy/cleanup. Inverted order = always one build behind or useless.
- Key quality, in priority order: (1) restore key ≠ save key → permanent miss (diff the literal strings!); (2) static key → never invalidates (stale forever) or manual bumping; (3) wrong lockfile in `checksum` (e.g. `package-lock.json` in a Yarn repo) → key never changes when deps do; (4) missing `{{ .OS }}` when a key is shared across Linux and macOS (native binaries); (5) no fallback chain — good practice is multiple keys, exact → prefix (`npm-{{ checksum "package-lock.json" }}`, `npm-{{ .Branch }}`, `npm-`); (6) `is_key_unique: "true"` on save avoids re-uploading an unchanged archive every build.
- Restore step output `BITRISE_CACHE_HIT` = `exact` / `partial` / `false` **[VERIFY]** — the showcase records it.
- Never cache secrets: keychains, `.netrc`, `.npmrc` with `_authToken`, private keys, `.env`, `~/.aws/credentials`. A cache archive is shared infrastructure. Include a doc page (no scenario that actually caches a real secret — use a **fake** `FAKE_TOKEN_DO_NOT_USE` file to demonstrate detection by the showcase's own linter, §9.4).
- Too-broad paths (`$HOME`, `./`, whole `node_modules` without measurement, Rust `target/` with an unscoped key) inflate archives and can be slower than no cache.
- Legacy `cache-pull` / `cache-push` are superseded; show only in docs (and in an optional scenario if the steps are still runnable **[VERIFY]**).
- Per-stack recommended paths and keys are in §6.6–§6.11.

---

## 4. Architecture

### 4.1 The core idea: scenario = (seed → change → measure)

A remote cache can only be judged on a **second** build. So every scenario is two workflows on two fresh VMs:

```
<SCENARIO>__1_seed     cold build on a fresh VM; populates caches (push on unless the scenario says otherwise)
        │  (depends_on)
        ▼
<SCENARIO>__2_measure  fresh VM, applies a deterministic "simulated commit", builds again, collects metrics
        │
        ▼
report                 pulls every metrics file, renders HTML + Markdown, runs assertions
```

- **Fresh VM per phase** is deliberate: it is the only honest way to prove a remote/key-based round-trip (no local Gradle build cache, no DerivedData, no `~/.npm` left over).
- The **simulated commit** (`tools/simulate-change.sh <stack> <kind>`) makes the measure build realistic. Kinds:
  - `none` — same commit rebuilt (best case; useful to show the theoretical ceiling),
  - `leaf` (**default**) — change one function body in a leaf module/file nothing depends on,
  - `core` — change a widely-depended module (worst realistic case),
  - `deps` — bump one dependency / lockfile entry (exercises key-based invalidation).
  The kind is controlled by `SHOWCASE_CHANGE_KIND` (pipeline-level env) and recorded in metrics. Changes must be **deterministic and identical for GOOD and BAD** variants (same file, same edit), and must not be committed back.

### 4.2 Cache isolation between scenarios and runs (critical for honest results)

All scenarios of a pipeline run share one Bitrise workspace cache. Without isolation, a BAD scenario could be rescued by entries uploaded by the GOOD scenario (or by yesterday's run), and the seed would not be cold.

Introduce a **cache namespace** string: `SHOWCASE_NS = <run-id>-<scenario-id>` and inject it so that it changes every cache key of that scenario **without** being one of the anti-patterns being demonstrated:

| Stack | Injection mechanism (namespace only — never use these in production) |
|---|---|
| Gradle | Convention plugin in `build-logic/` adds `inputs.property("showcaseNamespace", ns)` to `JavaCompile`, `KotlinCompile`, `Test`, and the codegen task types. Read from Gradle property `-PshowcaseNs=…` passed via `GRADLE_OPTS`/`ORG_GRADLE_PROJECT_showcaseNs` env. |
| Xcode | `OTHER_SWIFT_FLAGS=$(inherited) -DSHOWCASE_NS_<sanitised>` and `OTHER_CFLAGS=$(inherited) -DSHOWCASE_NS_<sanitised>` passed through a generated `showcase.xcconfig` (`-xcconfig`) **[VERIFY that this does not collide with the step's own `temp.xcconfig` injection; if it does, use `xcodebuild` build-setting args instead]**. |
| Bazel | `--action_env=SHOWCASE_NS=<ns>` in a generated `.bazelrc.showcase` (adds to every action key). |
| Key-based | `{{ getenv "SHOWCASE_NS" }}` as part of every key prefix. |
| ccache (RN) | `CCACHE_NAMESPACE` if supported by the bundled ccache version **[VERIFY]**, else an extra `-D` define via the same xcconfig/CMake flags. |

Two modes, selected by `SHOWCASE_ISOLATION`:
- `isolated` (**default**): `run-id = $BITRISEIO_PIPELINE_ID` **[VERIFY env var name]** → every run starts cold; seed is genuinely cold; scenarios can't help each other.
- `steady`: `run-id = "steady"` → namespace stable across runs; demonstrates steady-state behaviour ("even with a warm cache, the BAD scenario still misses").

Document clearly in `docs/concepts/isolation.md` that the namespace is a **test harness device** and that in real projects injecting a per-build value into compile inputs is exactly the anti-pattern shown in `AND-B03` / `IOS-B04`.

### 4.3 Repository layout

```
bitrise-build-cache-showcase/
├── README.md                       # pitch, screenshot of the pipeline graph, quick start, scenario matrix
├── CLAUDE.md                       # agent conventions (see §12.3)
├── LICENSE / LICENSE-docs
├── Makefile                        # lint, validate, generate, render-yaml, docs-serve, test
├── bitrise.yml                     # GENERATED flat config (works on every Bitrise plan) — do not hand-edit
├── bitrise.modular.yml             # root of the modular config (Enterprise "include:" feature) — source of truth
├── .bitrise/                       # modular YAML sources (≤ 49 files, nesting ≤ 10 — current platform limits)
│   ├── 00-app.yml                  # format_version, project_type, app envs, meta/default stack
│   ├── bundles/
│   │   ├── common.yml              # setup, namespace, metrics, deploy bundles
│   │   ├── gradle.yml
│   │   ├── xcode.yml
│   │   ├── react-native.yml
│   │   ├── flutter.yml
│   │   ├── bazel.yml
│   │   └── key-based.yml           # node/ruby/go/rust/python/maven bundles
│   ├── workflows/
│   │   ├── android.yml             # AND-* scenario workflows
│   │   ├── ios.yml
│   │   ├── react-native.yml
│   │   ├── flutter.yml
│   │   ├── bazel.yml
│   │   ├── key-based.yml
│   │   ├── gradle-test-distribution.yml   # optional module
│   │   ├── bazel-rbe.yml                  # optional module
│   │   └── report.yml
│   └── pipelines/
│       ├── android.yml
│       ├── ios.yml
│       ├── react-native.yml
│       ├── flutter.yml
│       ├── bazel.yml
│       ├── key-based.yml
│       ├── gradle-test-distribution.yml
│       ├── bazel-rbe.yml
│       └── smoke.yml               # 1 GOOD + 1 BAD per stack, cheapest end-to-end check
├── scenarios/
│   └── catalog.yml                 # SINGLE SOURCE OF TRUTH for scenario metadata (§5)
├── projects/                       # sample projects (generated or vendored), one per stack
│   ├── android/                    # multi-module Gradle (Kotlin) app + build-logic convention plugins
│   ├── ios/                        # Swift app, N SwiftPM local packages + one CocoaPods dependency, XcodeGen spec
│   ├── react-native/               # bare RN app (new architecture) with ≥1 C++ native module
│   ├── flutter/                    # Flutter app with Android + iOS targets
│   ├── bazel/                      # C++/Java/Kotlin Bazel workspace (bzlmod), deep dependency graph
│   ├── jvm-maven/                  # multi-module Maven project
│   ├── node/                       # pnpm workspace + an npm and a yarn sub-project (lockfile variants)
│   ├── ruby/                       # Gemfile with native gems (nokogiri) + fastlane
│   ├── go/
│   ├── rust/                       # workspace with a few crates; rust-toolchain.toml
│   ├── python/                     # pip + poetry variants
│   └── gradle-tests/               # test-heavy Gradle project for Test Distribution (≥ 3,000 unit tests)
├── generators/                     # deterministic project generators (python), seedable sizes S/M/L
├── tools/
│   ├── simulate-change.sh          # §4.1
│   ├── namespace.sh                # computes & exports SHOWCASE_NS (§4.2)
│   ├── metrics/
│   │   ├── gradle/showcase-metrics.init.gradle.kts
│   │   ├── xcode_parse.py
│   │   ├── bazel_parse.py
│   │   ├── keybased_record.sh
│   │   ├── timing.sh               # start/stop timers → metrics fragment
│   │   └── merge_fragments.py      # → metrics/<scenario>__<phase>.json
│   ├── report/
│   │   ├── render.py               # metrics/*.json + scenarios/catalog.yml → HTML + Markdown
│   │   ├── assertions.py           # expected vs observed → JUnit XML + exit code
│   │   └── templates/              # Jinja2 templates, inline CSS, no external assets
│   ├── yaml/
│   │   ├── flatten.py              # .bitrise/** + bitrise.modular.yml → bitrise.yml (deterministic)
│   │   └── generate_scenarios.py   # catalog.yml → .bitrise/workflows/*.yml + pipelines/*.yml
│   ├── lint/
│   │   └── cache_lint.py           # static checker for the anti-patterns (doubles as teaching tool, §9.4)
│   └── rbe/
│       └── pool.sh                 # resize/inspect worker pools via the RBE API (optional modules)
├── docs/                           # see §10
└── .github/workflows/ci.yml        # lint + validate + flatten-is-up-to-date + generator tests (GitHub Actions is fine for repo hygiene)
```

### 4.4 Generated vs. hand-written YAML

- `scenarios/catalog.yml` is the single source of truth. `tools/yaml/generate_scenarios.py` produces the scenario workflows and pipelines under `.bitrise/workflows/` and `.bitrise/pipelines/` from it, using the step bundles in `.bitrise/bundles/` (bundles are hand-written).
- `tools/yaml/flatten.py` merges `bitrise.modular.yml` + includes into the flat `bitrise.yml`, following Bitrise's documented merge semantics (modules merged in listed order, nested first, root last; scalars: last wins; maps: merged; arrays: concatenated existing-first). Output must be byte-stable (sorted where order is irrelevant, preserved where it matters — steps order!).
- CI check: re-run both generators and fail if the working tree changes (`git diff --exit-code`).
- Both `bitrise.yml` and `bitrise.modular.yml` must pass `bitrise validate`. Users on non-Enterprise plans use the flat file (modular `include:` is an Enterprise-plan feature and requires repo-stored config).
- Generated files start with a header comment: `# GENERATED by tools/yaml/… — edit scenarios/catalog.yml or .bitrise/bundles/* instead`.

---

## 5. Scenario catalog — data model

`scenarios/catalog.yml` drives generation, the report, the docs index and the assertions.

```yaml
schema_version: 1
defaults:
  change_kind: leaf
  isolation: isolated
scenarios:
  - id: AND-G01                    # <STACK>-<G|B|R><nn>  G=good, B=bad, R=regression-guard
    stack: android
    title: "Build Cache for Gradle, correctly placed, key-cached wrapper + deps"
    verdict: good                  # good | bad | regression-guard
    pattern_tags: [placement-ok, relocatable-inputs, pinned-toolchain]
    seed:
      bundle_overrides: {}         # inputs passed to the stack bundle for the seed workflow
    measure:
      bundle_overrides: {}
    stack_id: linux-default        # logical name resolved in 00-app.yml (§7.6)
    machine: linux-medium          # logical name resolved in 00-app.yml
    expectations:                  # evaluated by tools/report/assertions.py on the MEASURE run
      gradle.from_cache_share: ">= 0.6"
      cache.download_upload_ratio: ">= 2"
      duration.vs_seed: "<= 0.75"  # measure duration / seed duration
    symptom: null                  # for BAD: one sentence, shown in report + docs
    root_cause: null
    fix_ref: null                  # id of the GOOD scenario that shows the fix
    doc: docs/scenarios/android/AND-G01.md
    field_evidence: "Pattern seen across multiple customer audits (anonymised)."
```

Rules:
- Every BAD scenario has `symptom`, `root_cause`, `fix_ref`, and at least one expectation that proves the symptom (e.g. `gradle.from_cache_share: "< 0.2"` or `xcode.proxy_total: "== 0"`).
- Expectation keys are dotted paths into the metrics JSON (§8). Supported operators: `== != < <= > >=`, `in [...]`, `exists`, `absent`.
- `verdict: regression-guard` = a historically BAD pattern that a product fix turned GOOD; expectations assert GOOD behaviour. If it regresses, the report fails loudly with a pointer to the historical issue.

---

## 6. Scenario catalog — content

Notation per row: **ID · title · what the YAML/project does · expected observable symptom (measure run) · fix**. Every BAD scenario's doc page must show: the offending YAML/code lines, the log line(s) that prove the symptom, and the fix as a diff. Keep each scenario **one deliberate defect** — never stack two defects in one scenario (that's what makes them teachable).

### 6.1 Android / Gradle (`projects/android`, pipeline `showcase-android`)

Sample project: Kotlin multi-module app, generated at size M by default (`generators/android.py`): ~40 modules (`:core:*` widely depended, `:feature:*`, `:app`), ~1,500 Kotlin classes, ~1,200 unit tests, one KSP or custom codegen task, one `buildConfigField`. Build command for all scenarios: `./gradlew :app:assembleDebug :core:model:testDebugUnitTest --console=plain` (identical across scenarios except where the defect *is* the command).

| ID | Title | What it does | Expected symptom (measure) | Fix |
|---|---|---|---|---|
| AND-G01 | Correct setup | `activate-build-cache-for-gradle` right after checkout; `restore-gradle-cache`/`save-gradle-cache` (or restore/save with `**/*.gradle*`+`gradle.properties`+`libs.versions.toml` checksum key); pinned JDK 17 + wrapper; push on in seed | ≥ 60 % of cacheable tasks `FROM-CACHE`; download/upload ratio ≥ 2; measure ≤ 75 % of seed time | — |
| AND-G02 | Read-only PR reader + main writer | Seed = "main" workflow (push on). Measure = "PR" workflow with push **off** | Same hits as G01, ~0 bytes uploaded on measure | — (teaches posture) |
| AND-B01 | "Cached" but no Build Cache | Only key-based `~/.gradle/caches` cache, no activation step | Restore hit `exact`, but compile tasks `EXECUTED`; remote cache traffic 0; big archive restore time | Add activation step (→ G01) |
| AND-B02 | Activation after the build | Activation step placed after `gradle-runner` | Same as B01 for the build step; activation step green | Move step before first Gradle step |
| AND-B03 | Volatile BuildConfig in core module | `:core:common` gets `buildConfigField BUILD_TIME = System.currentTimeMillis()` | `:core:common` + all dependants miss on every build; ratio ≈ 1 or < 1; measure ≈ seed time | Move volatile values to `:app` only / resource generated at packaging, or make it constant in debug builds |
| AND-B04 | Non-relocatable task input | Custom task declares `@Input val schemaPath: String = file("schema.json").absolutePath`; seed and measure use different clone dirs (`git-clone` `clone_into_dir` with a per-phase suffix) | That task + dependants miss despite identical content | Use `@InputFile @PathSensitive(RELATIVE)` |
| AND-B05 | `--rerun-tasks` left in CI args | gradle-runner `gradle_options: --rerun-tasks` | All tasks `EXECUTED`; upload heavy | Remove flag |
| AND-B06 | Caching disabled via property | `gradle.properties` has `org.gradle.caching=false` (project-level override) | Build Cache step log shows plugin usage but tasks never `FROM-CACHE` **[VERIFY whether the init script overrides this; if it does, the scenario becomes "B06: `--no-build-cache` arg" instead]** | Remove property / arg |
| AND-B07 | Non-cacheable custom codegen | Expensive codegen task without `@CacheableTask` / without declared outputs (`doLast {}` writing files) | Codegen always runs (~N s); downstream compile still caches if outputs are byte-identical — document both effects | Annotate, declare outputs, relocatable inputs |
| AND-B08 | JDK mismatch writer vs reader | Seed on JDK 21, measure on JDK 17 (`set-java-version` step) | ~0 cross hits for JVM compile tasks; ratio ≈ 0–1 | Pin the same JDK everywhere |
| AND-B09 | Nobody pushes | Seed and measure both with push off | Seed uploads 0; measure hits 0 | At least one canonical writer |
| AND-B10 | Cold cache looks like failure | Measure uses a **fresh namespace** (simulates first build / new DC / TTL expiry) | Ratio < 1, hits ≈ 0 — *even though config is GOOD* | No config fix; explain cold vs thrash (docs: "screening ≠ verdict") |
| AND-B11 | Key-caching build outputs | Key-based cache adds `**/build/` + `.gradle/` project dirs on top of G01 | Archive several GB; restore/save time eats the gain; measure slower than G01 | Remove; let Build Cache handle outputs |
| AND-B12 | Under-specified dependency key | `restore/save-cache` key = `gradle-{{ checksum "build.gradle.kts" }}` (root only) with change kind `deps` in a module | Stale deps restored (key unchanged) → Gradle downloads anyway; cache grows forever | Glob `**/*.gradle*` + catalogs |
| AND-B13 *(optional, M5)* | Config cache with rotating encryption key | Configuration-cache add-on with `GRADLE_ENCRYPTION_KEY=$(openssl rand …)` each build | `Configuration cache entry discarded`/re-calculated every build **[VERIFY message]** | Stable key in Secrets; Gradle ≥ 8.6; Save transforms on |
| AND-B14 *(optional)* | NDK without ccache | Module with CMake/NDK code, only Gradle BC | Native compile time unchanged | ccache via RN-style activation or key-based ccache dir |

### 6.2 iOS / Xcode (`projects/ios`, pipeline `showcase-ios`)

Sample project: Swift app generated via **XcodeGen** (deterministic `project.yml`, no committed `.xcodeproj`), ~30 local SwiftPM packages (`Core*` widely depended, `Feature*`), ~1,000 Swift files + a small Objective-C/C target (to exercise Clang caching), one CocoaPods pod (pure Swift, small) and one remote SPM package. Build via `xcode-build-for-simulator` (fast, no signing) for most scenarios; one archive scenario (`IOS-G02`) uses `xcode-archive` with an **ad-hoc/development export using a throwaway signing setup** **[VERIFY: if code signing in a public repo is impractical, use `xcode-build-for-test` instead and document]**.

| ID | Title | What it does | Expected symptom (measure) | Fix |
|---|---|---|---|---|
| IOS-G01 | Correct setup | Xcode 26 stack; activation after checkout; CocoaPods cache keyed on `Podfile.lock`; SPM cache keyed on `Package.resolved`; `xcode-build-for-simulator` | High proxy hit %; small upload; ratio ≫ 1; measure noticeably faster | — |
| IOS-G02 | Correct setup, archive | Same with `xcode-archive` | Same; plus doc note on never-cacheable phases (signing, asset catalogs, storyboards, dSYM) | — |
| IOS-B01 | Old Xcode = silent no-op | Activation on an Xcode 16.x stack | Step green; zero cache traffic; durations equal | Move to Xcode 26+ stack |
| IOS-B02 | DerivedData key-cached alongside Build Cache | restore/save `~/Library/Developer/Xcode/DerivedData` + activation | Remote cache barely queried on measure (local outputs short-circuit); ratio ≪ expected; DerivedData archive restore time | Remove DerivedData key cache |
| IOS-B03 | Shim bypass via absolute path | Script step runs `/usr/bin/xcrun xcodebuild …` (simulates `tuist build`/custom fastlane) | `Proxy blob stats` absent or `total: 0`; no `SetSession` | Call `xcodebuild` via PATH; with Tuist use `tuist generate` + Xcode step |
| IOS-B04 | Volatile preprocessor/Swift flag | `GCC_PREPROCESSOR_DEFINITIONS=$(inherited) BUILD_NUMBER=$BITRISE_BUILD_NUMBER` + `OTHER_SWIFT_FLAGS=-DBUILD_$BITRISE_BUILD_NUMBER` on all targets | ≈ 0 % hits, full re-upload each build (ratio < 1) | Set build number in Info.plist / `CURRENT_PROJECT_VERSION` at archive time |
| IOS-B05 | Activation after build | Activation placed after the build step | Same as B01 for that step | Move step |
| IOS-B06 | `no_swift_cache` as default | `no_swift_cache: "true"` with no explicit-modules problem | Clang/ObjC targets hit, Swift targets all compile; most of the time uncached | Remove input; only use as targeted workaround |
| IOS-B07 | CocoaPods key mismatch | restore key `pods-{{ checksum "Podfile.lock" }}`, save key `pods-{{ checksum "Podfile" }}` | `BITRISE_CACHE_HIT=false` every time; `pod install` downloads | Same template in both |
| IOS-B08 | Pods/ instead of CocoaPods cache | Caches `Pods/` dir | Works but larger archive, more invalidation (minor) | Cache `~/Library/Caches/CocoaPods` |
| IOS-B09 | Caching Archives/CoreSimulator | Adds `~/Library/Developer/Xcode/Archives`, `~/Library/Developer/CoreSimulator` to a cache | Huge archive, no speed gain | Remove |
| IOS-R01 | Rotating checkout path (regression guard) | Measure clones into a random temp dir (mimics `pull-intermediate-files`) | **Must look GOOD** (prefix mapping, CLI ≥ 2.8.5). If hits collapse → regression | Historical fix: CLI 2.8.5 injects `CLANG_ENABLE_PREFIX_MAPPING=YES` |
| IOS-B10 *(optional)* | Different configuration writer vs reader | Seed builds `Release`, measure `Debug` | Mostly misses (different flags) — expected, teaches "scheme/config splits the cache" | Warm each configuration you build |

### 6.3 React Native (`projects/react-native`, pipeline `showcase-react-native`)

Sample: bare RN app (new architecture), Yarn (Berry or classic — pick one and document), one C++ TurboModule, Android + iOS. Native builds in script steps wrapped with `bitrise-build-cache react-native run`.

| ID | Title | What it does | Expected symptom | Fix |
|---|---|---|---|---|
| RN-G01 | Correct setup | `activate-build-cache-for-react-native@0` after checkout; Yarn cache keyed on `yarn.lock`; wrapped Android + iOS builds; Xcode 26 stack | Gradle + Xcode hits high; ccache hits on C++; Yarn restore `exact` | — |
| RN-B01 | Native cached, JS deps not | No key-based Yarn cache | `yarn install` full download time every build | Add key-based Yarn cache |
| RN-B02 | Wrong lockfile in key | key `{{ checksum "package-lock.json" }}` in a Yarn repo (file absent → constant) + change kind `deps` | Restore `exact` but stale; yarn re-resolves | Key on `yarn.lock` |
| RN-B03 | Unwrapped native command | `npx react-native run-ios …` without the wrapper prefix in a script step | iOS/Android legs: zero cache traffic | Prefix with `bitrise-build-cache react-native run` (or use official steps) |
| RN-B04 | iOS leg on old Xcode | Xcode 16 stack | Android leg cached, iOS leg no-op | Xcode 26+ |
| RN-B05 | Blind `node_modules` caching | Caches `node_modules/` instead of the Yarn cache | Large archive; native addons OS-sensitive; often slower than install | Cache the package-manager cache |
| RN-B06 | Gradle leg disabled by flag | Activation with Gradle cache input disabled | Android leg uncached | Remove flag |

### 6.4 Flutter (`projects/flutter`, pipeline `showcase-flutter`)

No Flutter-specific Build Cache backend: Dart is key-based (`~/.pub-cache`), native legs use Gradle / Xcode Build Cache.

| ID | Title | What it does | Expected symptom | Fix |
|---|---|---|---|---|
| FL-G01 | Correct setup | pub cache keyed on `pubspec.lock`; Gradle BC for `flutter build apk`; Xcode BC for `flutter build ios --no-codesign` on Xcode 26; CocoaPods cache | Native legs hit; pub restore exact | — |
| FL-B01 | One key for everything | Single cache with pub + pods + gradle keyed on `pubspec.lock` | Any `Podfile.lock` / Gradle change ignored (stale) or everything invalidated together | Separate caches/keys |
| FL-B02 | Caching `build/` + `.dart_tool/` | Adds build outputs to key cache | Big archive, little gain, occasional stale artefacts | Remove |
| FL-B03 | "pub cache = Flutter cached" | Only pub cache; no native Build Cache | Native compile times unchanged | Add Gradle + Xcode activation |
| FL-V01 *(verification task, not a scenario)* | Does `flutter build ios` go through the Xcode shim? | — | **[VERIFY]** If Flutter invokes `xcodebuild` by absolute path, this becomes BAD scenario `FL-B04` with the workaround documented | — |

### 6.5 Bazel (`projects/bazel`, pipeline `showcase-bazel`)

Sample: bzlmod workspace, C++ + Java (or Kotlin) libraries, a deep dependency chain (~300 targets), a `genrule` codegen step, a `cc_test`/`java_test` set. Command: `bazel build //... --config=ci` then `bazel test //:fast_tests --config=ci`.

| ID | Title | What it does | Expected symptom | Fix |
|---|---|---|---|---|
| BZ-G01 | Correct setup | `activate-build-cache-for-bazel` after checkout; hermetic rules; shared `--config=ci` | `INFO: N processes: X remote cache hit …` with X ≈ N on measure (minus changed targets) | — |
| BZ-B01 | Non-hermetic genrule | `genrule` at the root of the graph embeds `date +%s` | Root + all dependants miss | Make output deterministic / move stamping to final binary with `stamp = 1` only there |
| BZ-B02 | Stamping everywhere | `--stamp` + `workspace_status_command` printing a timestamp, many targets `stamp = 1` | Stamped link actions miss | Stamp only release binaries, keep volatile keys `STABLE_` vs volatile correctly |
| BZ-B03 | Env leak into actions | `--action_env=BITRISE_BUILD_NUMBER` | Every action misses | Remove; use `--repo_env`/stamping for metadata |
| BZ-B04 | Writer/reader flag drift | Seed `-c opt`, measure default `fastbuild` (or different `--copt`) | Disjoint keys, ~0 hits | Same flags (shared `--config=ci`) |
| BZ-B05 | Output base key-cached on top | key-based cache of `~/.cache/bazel` + remote cache | Multi-GB archive restore dominates | Remove |
| BZ-B06 *(observe)* | `bazel test` caching | Test-only change kind | Record whether test actions show `remote cache hit` (field reports vary) **[VERIFY]** | — |

### 6.6 Node.js (`projects/node`, part of pipeline `showcase-key-based`)

| ID | Title | Expected symptom | Fix |
|---|---|---|---|
| NODE-G01 | npm: `~/.npm` keyed on `package-lock.json`, fallback chain, `is_key_unique` | exact restore; `npm ci` fast | — |
| NODE-G02 | pnpm: store keyed on `pnpm-lock.yaml` | exact restore; fastest install | — |
| NODE-B01 | restore ≠ save key (`package-lock.json` vs `yarn.lock`) — the canonical worked example | `BITRISE_CACHE_HIT=false` forever, but save uploads every build | Same template |
| NODE-B02 | Static key `npm-cache` + change kind `deps` | exact hit with stale content; never refreshes | Checksum lockfile |
| NODE-B03 | Save before install | Save captures previous state (one build behind) | Reorder |
| NODE-B04 | `node_modules` + no `{{ .OS }}` shared between Linux & macOS workflows | Native addon ABI errors **avoided by design here** — instead record restore of foreign-OS archive + forced rebuild time | Cache store, add `{{ .OS }}` |
| NODE-B05 | No `is_key_unique` | Archive re-uploaded every build (save time every run) | `is_key_unique: "true"` |

### 6.7 Ruby / CocoaPods / fastlane (`projects/ruby`)

| ID | Title | Expected symptom | Fix |
|---|---|---|---|
| RB-G01 | `vendor/bundle` (via `bundle config set path`) keyed on `Gemfile.lock` + `{{ .OS }}` | exact restore, no native compile of nokogiri | — |
| RB-B01 | Key without `{{ .OS }}` shared Linux↔macOS (seed Linux, measure macOS) | Restored native gem unusable → `bundle install` recompiles (or fails — the scenario must catch and record, not fail) | Add `{{ .OS }}` |
| RB-B02 | Ruby version drift (seed 3.2, measure 3.3) | Gems reinstall despite exact hit | Pin `.ruby-version`, include version in key |

### 6.8 Go (`projects/go`)

| ID | Title | Expected symptom | Fix |
|---|---|---|---|
| GO-G01 | `~/go/pkg/mod` + `~/.cache/go-build` keyed on `go.sum` | build mostly from GOCACHE | — |
| GO-B01 | Only module cache, no `GOCACHE` | downloads skipped but full compile | Add GOCACHE |
| GO-B02 | Go toolchain drift between seed and measure | GOCACHE entries unusable | Pin Go version, include in key |

### 6.9 Rust (`projects/rust`)

| ID | Title | Expected symptom | Fix |
|---|---|---|---|
| RS-G01 | `~/.cargo/registry` + `~/.cargo/git` keyed on `Cargo.lock`; `target/` cached with key = toolchain + profile + `Cargo.lock` | fast incremental build | — |
| RS-B01 | `target/` keyed only on `Cargo.lock`, seed `--release`, measure debug (or different toolchain) | Huge archive, mostly recompiled | Scope key by toolchain + profile |
| RS-B02 | No `rust-toolchain.toml`, floating toolchain + `target/` | Invalidation after toolchain update (simulated via `RUSTUP_TOOLCHAIN` change) | Pin toolchain |

### 6.10 Python (`projects/python`)

| ID | Title | Expected symptom | Fix |
|---|---|---|---|
| PY-G01 | `~/.cache/pip` keyed on `requirements*.txt` | exact restore, wheels reused | — |
| PY-G02 | Poetry: `~/.cache/pypoetry` keyed on `poetry.lock` | — | — |
| PY-B01 | Key on stale `requirements.txt` while install reads `poetry.lock` | Key never changes when deps do | Key the file the install reads |
| PY-B02 | Whole `.venv` cached across Python versions | Broken/rebuilt env | Cache pip/poetry cache, include Python version |

### 6.11 Java / Maven (`projects/jvm-maven`)

| ID | Title | Expected symptom | Fix |
|---|---|---|---|
| MVN-G01 | `~/.m2/repository` keyed on `**/pom.xml` | offline-fast resolution | — |
| MVN-B01 | Key on root `pom.xml` only, change kind `deps` in a submodule | Stale cache, downloads anyway | Glob all poms |
| MVN-B02 | Caching `target/` | Large archive, no correctness benefit | Remove |

### 6.12 Cross-cutting scenarios (pipeline `showcase-key-based` or `smoke`)

| ID | Title | Expected symptom | Fix |
|---|---|---|---|
| X-B01 | Cache step before `git-clone` | Restore into a dir later wiped / `checksum` of missing file → constant key | Clone first |
| X-B02 | Too-broad path (`$HOME` minus excludes) | Multi-GB archive, slow | Narrow paths |
| X-B03 | Secret-looking file in cached path (fake token file) | **Detected by `tools/lint/cache_lint.py`** and flagged in report (no real secret ever used) | Never cache credentials |

---

## 7. Bitrise YAML design (step bundles + graph pipelines)

> All examples below are **illustrative skeletons**. Step major versions, stack IDs and machine type IDs are **[VERIFY]**: resolve them at implementation time (Bitrise steplib / `bitrise stepman`, the Bitrise MCP `list_available_stacks`, docs) and record them once in `.bitrise/00-app.yml` comments + `docs/reference/versions.md`. Always pin step **major** versions (`@2`), never bare step IDs, never `-edge` stacks.

### 7.1 Conventions

- **Workflow names:** `<scenario-id-lowercase>__1_seed`, `<scenario-id-lowercase>__2_measure` (e.g. `and-b03__1_seed`). Prefix sorts rows in the graph view. Add a `title:` and `summary:` to every workflow: summary = verdict emoji + one-line symptom, e.g. `"❌ BAD — volatile BuildConfig in :core:common busts every downstream key"`. GOOD = `✅`, BAD = `❌`, regression guard = `🛡️`.
- **Utility workflows** start with `_` (e.g. `_report`) and are never triggered directly.
- **Every workflow is composed only of bundles** (`bundle::…`) plus at most one scenario-specific step. If you need a raw step in a scenario, that is a smell: make it a bundle input instead.
- **Bundle inputs** are the only parametrisation channel into bundles (bundles don't take `envs`). Workflow-level `envs:` carry scenario metadata (`SHOWCASE_SCENARIO_ID`, `SHOWCASE_PHASE`, `SHOWCASE_STACK`).
- All shell lives in `tools/` scripts; YAML `script` contents are one-liners calling them (`set -euxo pipefail` inside scripts). This keeps YAML readable and scripts shellcheck-able.
- Every scenario-specific defect is visible **in the YAML of that workflow** (an input value, a step order, a stack) or in a clearly named project variant (`projects/android/variants/b03-volatile-buildconfig.patch` applied by a bundle input `project_patch`). Readers of `bitrise.yml` must be able to see the defect without reading Kotlin.

### 7.2 App-level section (`.bitrise/00-app.yml`)

```yaml
format_version: "17"          # [VERIFY] latest supported
default_step_lib_source: https://github.com/bitrise-io/bitrise-steplib.git
project_type: other

meta:
  bitrise.io:
    stack: ubuntu-noble-24.04-bitrise-2025-android   # [VERIFY] default Linux stack
    machine_type_id: g2.linux.large                  # [VERIFY]

app:
  envs:
  - SHOWCASE_ISOLATION: isolated        # isolated | steady   (§4.2)
  - SHOWCASE_CHANGE_KIND: leaf          # none | leaf | core | deps (§4.1)
  - SHOWCASE_PROJECT_SIZE: M            # S | M | L (generators)
  - SHOWCASE_METRICS_DIR: $BITRISE_SOURCE_DIR/.showcase/metrics
  - SHOWCASE_ENABLE_GRADLE_TD: "false"  # optional module (§11.1)
  - SHOWCASE_ENABLE_BAZEL_RBE: "false"  # optional module (§11.2)
  - SHOWCASE_FAIL_ON_ASSERTION: "true"  # report workflow fails if expectations aren't met
```

Logical stack/machine names used in `catalog.yml` (`linux-default`, `xcode-26`, `xcode-16-legacy`, `linux-medium`, `mac-m-medium` …) map to real IDs in one place: `tools/yaml/stacks.yml`. The generator writes them into each workflow's `meta.bitrise.io`. Xcode legacy stack for IOS-B01/RN-B04 must be a stack that is **still available** **[VERIFY]**; if no pre-26 stack remains, mark those scenarios `skipped: "no legacy stack available"` and keep the doc page.

### 7.3 Step bundles — required set

Hand-written in `.bitrise/bundles/*.yml`. Each bundle has a header comment explaining purpose, inputs, and which scenarios use it. Names use snake_case.

**common.yml**

| Bundle | Purpose | Key inputs |
|---|---|---|
| `setup_checkout` | `activate-ssh-key` (if needed) + `git-clone`; optional `clone_into_dir` override for relocation scenarios | `clone_dir` |
| `setup_showcase` | export `SHOWCASE_*`, compute namespace (`tools/namespace.sh`), start total timer, generate project if `generated: true` | `stack`, `scenario_id`, `phase`, `project_patch` |
| `simulate_change` | runs `tools/simulate-change.sh` (measure only) | `stack`, `kind` |
| `timer_start` / `timer_stop` | named timers → metrics fragments | `name` |
| `collect_metrics` | merges fragments into `metrics/<scenario>__<phase>.json` | — |
| `deploy_metrics` | `deploy-to-bitrise-io` with `pipeline_intermediate_files: "$SHOWCASE_METRICS_DIR:SHOWCASE_METRICS_DIR_<SCENARIO>"` and the raw logs as artifacts | — |
| `report` | pull all intermediate files, render, assert, deploy HTML/MD/JUnit | `fail_on_assertion` |

**gradle.yml**

| Bundle | Purpose | Key inputs |
|---|---|---|
| `gradle_build_cache` | `activate-build-cache-for-gradle` | `push` (true/false), `verbose`, `enabled` (to model B01) |
| `gradle_deps_cache_restore` / `gradle_deps_cache_save` | key-based wrapper + deps cache | `key`, `paths`, `extra_paths` (B11) |
| `gradle_build` | runs the build via `gradle-runner` (or script `./gradlew`) with the metrics init script | `tasks`, `options`, `jdk` |
| `gradle_android` | composite: deps restore → (build cache) → build → deps save, with `build_cache_position: before|after|none` input so placement scenarios stay one-line | `build_cache_position`, `push`, `tasks`, `options`, `jdk`, `deps_key` |

**xcode.yml**: `xcode_build_cache` (`push`, `no_swift_cache`, `verbose`), `cocoapods_cache_restore/save`, `spm_cache_restore/save`, `deriveddata_cache_restore/save` (exists only to model IOS-B02 — header comment says "ANTI-PATTERN, used by IOS-B02 only"), `xcode_build_sim` (official step or `script` with `invoker: path|absolute`), `xcode_ios` composite with `build_cache_position`.

**react-native.yml**: `rn_build_cache` (`gradle_enabled`, `xcode_enabled`, `no_swift_cache`, `cache_skip_flags`), `yarn_cache_restore/save` (`key`, `paths`), `rn_build_android` / `rn_build_ios` (`wrapped: true|false`).

**flutter.yml**: `flutter_install` (pinned version, FVM or `flutter-installer` step), `pub_cache_restore/save`, `flutter_build_android`, `flutter_build_ios`.

**bazel.yml**: `bazel_build_cache` (`enable_rbe`), `bazel_build` (`targets`, `config`, `extra_flags`), `bazel_outputbase_cache_restore/save` (anti-pattern, BZ-B05 only), `bazel_metrics`.

**key-based.yml**: generic `kb_restore` / `kb_save` (`key`, `paths`, `is_key_unique`) plus thin stack bundles (`node_install`, `ruby_install`, `go_build`, `rust_build`, `python_install`, `maven_build`) that call the generic ones with stack defaults.

Example (illustrative):

```yaml
step_bundles:
  gradle_build_cache:
    inputs:
    - push: "true"
    - verbose: "false"
    steps:
    - activate-build-cache-for-gradle@2:        # [VERIFY major + input names]
        inputs:
        - push: $push
        - verbose: $verbose

  gradle_deps_cache_restore:
    inputs:
    - key: 'gradle-deps-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "**/*.gradle*" "gradle.properties" "gradle/libs.versions.toml" }}'
    steps:
    - restore-cache@2:
        inputs:
        - key: $key

  gradle_deps_cache_save:
    inputs:
    - key: 'gradle-deps-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "**/*.gradle*" "gradle.properties" "gradle/libs.versions.toml" }}'
    - paths: |-
        ~/.gradle/caches/modules-2
        ~/.gradle/wrapper
    steps:
    - save-cache@1:
        inputs:
        - key: $key
        - paths: $paths
        - is_key_unique: "true"

  gradle_build:
    inputs:
    - tasks: ":app:assembleDebug :core:model:testDebugUnitTest"
    - options: "--console=plain"
    steps:
    - script@1:
        title: Gradle build (instrumented with showcase metrics init script)
        inputs:
        - content: tools/run-gradle.sh "$tasks" "$options"
```

> ⚠️ Placement inside composites: because bundle `run_if` is evaluated per bundle instance, implement `build_cache_position` by **three separate bundle references** in the composite, each with `run_if` on the position value (`'{{ enveq "SHOWCASE_BC_POSITION" "before" }}'` …). The position value is exported to an env by `setup_showcase` from the bundle input (bundle inputs aren't visible to `run_if` templates — **[VERIFY]** whether bundle inputs are exposed as envs during template evaluation; if they are, simplify).

### 7.4 Generated scenario workflows

From the catalog, the generator emits (illustrative output for `AND-B02`):

```yaml
workflows:
  and-b02__1_seed:
    title: "AND-B02 · seed"
    summary: "❌ BAD — Build Cache activated AFTER the Gradle build step"
    meta:
      bitrise.io:
        stack: ubuntu-noble-24.04-bitrise-2025-android
        machine_type_id: g2.linux.large
    envs:
    - SHOWCASE_SCENARIO_ID: AND-B02
    - SHOWCASE_PHASE: seed
    - SHOWCASE_STACK: android
    steps:
    - bundle::setup_checkout: {}
    - bundle::setup_showcase: {}
    - bundle::gradle_deps_cache_restore: {}
    - bundle::gradle_build: {}            # ← runs uncached: activation comes after
    - bundle::gradle_build_cache: {}      # ← the defect, visible in the YAML
    - bundle::gradle_deps_cache_save: {}
    - bundle::collect_metrics: {}
    - bundle::deploy_metrics: {}

  and-b02__2_measure:
    title: "AND-B02 · measure"
    summary: "❌ BAD — Build Cache activated AFTER the Gradle build step"
    envs:
    - SHOWCASE_SCENARIO_ID: AND-B02
    - SHOWCASE_PHASE: measure
    - SHOWCASE_STACK: android
    steps:
    - bundle::setup_checkout: {}
    - bundle::setup_showcase: {}
    - bundle::simulate_change: {}
    - bundle::gradle_deps_cache_restore: {}
    - bundle::gradle_build: {}
    - bundle::gradle_build_cache: {}
    - bundle::gradle_deps_cache_save: {}
    - bundle::collect_metrics: {}
    - bundle::deploy_metrics: {}
```

Decision: the generator writes **explicit step order** per scenario (rather than a composite with position flags) when that makes the defect more readable. Prefer readability of the generated YAML over DRYness — the catalog + bundles already give DRYness at the source level.

### 7.5 Pipelines — the "same screen" layout

One pipeline per stack. Every scenario is a two-node chain; all chains run in parallel; the report node depends on every measure node. In the Bitrise graph view this renders as a grid: **rows = scenarios, column 1 = seed, column 2 = measure, column 3 = report**, each node showing its duration and green/red status.

```yaml
pipelines:
  showcase-android:
    workflows:
      and-g01__1_seed: {}
      and-g01__2_measure: { depends_on: [and-g01__1_seed] }
      and-b01__1_seed: {}
      and-b01__2_measure: { depends_on: [and-b01__1_seed] }
      and-b02__1_seed: {}
      and-b02__2_measure: { depends_on: [and-b02__1_seed] }
      # … one pair per scenario in catalog order (GOOD first, then BAD, then regression guards)
      _report_android:
        depends_on: [and-g01__2_measure, and-b01__2_measure, and-b02__2_measure]   # all measures
        should_always_run: workflow    # report even if a scenario node failed
```

Requirements:
- `_report_<stack>` uses `should_always_run: workflow` so a broken scenario still gets reported (as "no metrics").
- Pipelines must not exceed the workspace's concurrency in a way that serialises everything without saying so: document the **minimum concurrency for a readable run** (e.g. Android: 2 × #scenarios concurrent jobs; with less, the pipeline still completes but the graph looks staggered). Provide `showcase-smoke` (1 GOOD + 1–2 BAD per stack) for low-concurrency workspaces.
- **Fairness:** seed workflows of one pipeline should start together. Note in docs that queue time differs; the report uses **build-step durations** (timers around the build command), not total workflow duration, as the primary comparison; total workflow time is shown secondarily.
- Data-centre effect: per-DC cache origins mean seed and measure can land in different DCs → cold measure. The report must record the DC/region of each run if detectable (hostname token such as `-ams-`/`-ord-`/`-iad-` or an env var **[VERIFY what's exposed to the build]**) and flag "seed and measure ran in different DCs — result not comparable" instead of mis-reporting a BAD.
- Optional trigger map: none by default (manual start). Provide a commented example `trigger_map`/`triggers` that runs `showcase-smoke` nightly via a scheduled build (Bitrise "Scheduled builds" are configured in the UI — document it; YAML can't define schedules).

### 7.6 Pipelines list

| Pipeline | Contents | Approx. jobs |
|---|---|---|
| `showcase-android` | AND-* | ~2 × 13 + 1 |
| `showcase-ios` | IOS-* | ~2 × 11 + 1 |
| `showcase-react-native` | RN-* | ~2 × 7 + 1 |
| `showcase-flutter` | FL-* | ~2 × 4 + 1 |
| `showcase-bazel` | BZ-* | ~2 × 6 + 1 |
| `showcase-key-based` | NODE/RB/GO/RS/PY/MVN/X-* | ~2 × 24 + 1 (all Linux except RB-B01 macOS) |
| `showcase-smoke` | 1 GOOD + 1 BAD per stack | ~2 × 12 + 1 |
| `showcase-gradle-test-distribution` | §11.1 | sequential chain |
| `showcase-bazel-rbe` | §11.2 | sequential chain |

### 7.7 Validation

- `bitrise validate -c bitrise.yml` and `-c bitrise.modular.yml` in CI (install the Bitrise CLI in GitHub Actions).
- Optional: the implementing agent may use the Bitrise MCP `validate_bitrise_yml` tool against the real app.
- `tools/yaml/check_conventions.py`: every workflow has title + summary with a verdict emoji; every scenario workflow uses only bundles + ≤ 1 raw step; every scenario in the catalog appears in exactly one pipeline; every measure node is a dependency of its pipeline's report node.

---

## 8. Metrics — collection and schema

### 8.1 JSON schema (`docs/reference/metrics-schema.json`, JSON Schema draft 2020-12)

One file per workflow run: `metrics/<SCENARIO>__<phase>.json`.

```json
{
  "schema_version": 1,
  "scenario_id": "AND-B03",
  "stack": "android",
  "phase": "measure",
  "verdict_expected": "bad",
  "run": {
    "pipeline_id": "…", "build_slug": "…", "workflow": "and-b03__2_measure",
    "stack_id": "ubuntu-noble-24.04-bitrise-2025-android", "machine_type": "g2.linux.large",
    "datacenter": "ams | ord | iad | unknown",
    "isolation": "isolated", "namespace": "…", "change_kind": "leaf",
    "started_at": "2026-12-01T10:00:00Z"
  },
  "durations_s": {
    "total_workflow": 412.3,
    "build_step": 301.7,
    "cache_restore": 12.1,
    "cache_save": 18.4,
    "dependency_install": 0.0
  },
  "remote_cache": {
    "tool": "gradle | xcode | bazel | ccache | none",
    "hits": 120, "misses": 410, "hit_rate": 0.226,
    "bytes_downloaded": 182000000, "bytes_uploaded": 905000000,
    "download_upload_ratio": 0.20,
    "proxy_total": 530,
    "engaged": true
  },
  "gradle": {
    "tasks_total": 812, "executed": 410, "from_cache": 120, "up_to_date": 40, "skipped": 242, "no_source": 0,
    "from_cache_share": 0.226,
    "top_executed_tasks": [{"path": ":core:common:compileKotlin", "duration_s": 22.1}]
  },
  "xcode": { "proxy_hits": null, "proxy_total": null, "uploaded_blobs": null, "set_session_seen": null, "xcelerate_logs": [] },
  "bazel": { "processes": null, "remote_cache_hit": null, "local": null, "remote": null },
  "key_based": [
    { "name": "gradle-deps", "key": "…", "restore_hit": "exact | partial | false",
      "archive_bytes": 1200000000, "restore_s": 12.1, "save_s": 18.4, "saved": true }
  ],
  "test_distribution": null,
  "notes": ["datacenter differs from seed"],
  "raw_logs": ["build_step.log"]
}
```

### 8.2 Per-stack collectors

| Stack | How | Notes |
|---|---|---|
| Gradle | `tools/metrics/gradle/showcase-metrics.init.gradle.kts` registered via `--init-script` in `tools/run-gradle.sh`. Uses `BuildEventsListenerRegistry` + a `BuildService` implementing `OperationCompletionListener` to classify each `TaskFinishEvent` (`TaskSuccessResult.isFromCache`, `isUpToDate`, `TaskSkippedResult`, failure). Must be **configuration-cache compatible**. Also parse `--console=plain` output for `FROM-CACHE` as a cross-check. | Byte traffic: parse the Bitrise Build Cache plugin's end-of-build summary if it prints one **[VERIFY output format]**; otherwise `null` + note. |
| Xcode | `tools/metrics/xcode_parse.py` over (a) the build step's raw xcodebuild log (`$BITRISE_XCODE_RAW_RESULT_TEXT_PATH` or tee'd script output **[VERIFY env var per step]**), (b) any `xcelerate-*.log` files produced by the Build Cache step (locate them on the first real run; enable `verbose` in showcase runs so per-key `Cache hit`/`Cache miss` lines exist). Extract `Proxy blob stats: hits: N (…) / total: M (P%). Uploaded blobs: U (…)` per invocation, `SetSession called`, counts of `Cache hit`/`Cache miss`. | Strip ANSI first: `sed $'s/\x1b\\[[0-9;]*m//g'`. Exclude non-compile invocations (`-showBuildSettings`, `-resolvePackageDependencies`, `-list`, `-exportArchive`) from hit-rate math but keep them listed. |
| Bazel | `--build_event_json_file` + final `INFO: N processes: X remote cache hit, …` line; optional `--execution_log_compact_file` for per-action detail in verbose mode. | |
| ccache | `ccache --show-stats --verbose` (or `-s`) before/after; diff. **[VERIFY]** where the RN step's ccache stats are printed (they may be folded into the Xcode invocation reporting). | |
| Key-based | `tools/metrics/keybased_record.sh` reads `BITRISE_CACHE_HIT` after restore **[VERIFY output name for v2 steps]**, times restore/save via timers, measures archive size from the save step log or by computing the size of the paths. | |
| Durations | `tools/metrics/timing.sh start|stop <name>` writes fragments with monotonic timestamps. | |
| Datacenter | Detect from hostname / env **[VERIFY]**; else `unknown`. | |

### 8.3 Honesty rules for metrics

- Never fabricate. Missing data = `null` + an entry in `notes`.
- Hit rate is always shown next to the byte ratio, with the "naive hit rate is misleading" tooltip.
- Report build-step durations as primary; total workflow durations as secondary (queue + VM boot noise).

---

## 9. Report, assertions, and static lint

### 9.1 `_report_<stack>` workflow

1. `pull-intermediate-files@1` (all sources) → `metrics/*.json` from every scenario node.
2. `tools/report/render.py` → `showcase-report.html` (single self-contained file: inline CSS/JS, no CDN, dark/light aware), `showcase-report.md`, `showcase-summary.json`.
3. `tools/report/assertions.py` → evaluates catalog expectations against measure metrics → `junit-showcase.xml` (one testcase per scenario: "GOOD behaves good" / "BAD reproduces symptom") → deploy to Test Reports via `deploy-to-bitrise-io` test results directory convention (`$BITRISE_TEST_DEPLOY_DIR`) **[VERIFY test report add-on directory structure]**.
4. If available, add a build annotation with the Markdown summary (`bitrise :annotations add …` **[VERIFY feature availability + syntax]**); otherwise skip silently.
5. Exit non-zero only if `SHOWCASE_FAIL_ON_ASSERTION=true` **and** an assertion failed for reasons other than "not comparable" (different DCs, missing data).

### 9.2 HTML report layout

- **Header:** pipeline, date, isolation mode, change kind, project size, stack IDs.
- **Matrix table:** rows = scenarios (GOOD first), columns: verdict badge · seed build-step time · measure build-step time · Δ % · hits/misses · download/upload ratio (with a small bar) · key-based restore hit · archive size · assertion result · link to doc page (GitHub URL from a `SHOWCASE_REPO_URL` env) · link to the two builds.
- **Side-by-side bar chart** (inline SVG, no libraries): measure build-step time per scenario, GOOD bars highlighted, BAD bars labelled with the one-line symptom.
- **Per-scenario expandable card:** symptom, root cause, fix diff snippet (pulled from the doc page front-matter), top 10 executed tasks / missed compile units, notes (e.g. "DC differed").
- **"How to read this" box:** cold vs warm, ratio vs hit rate, never-cacheable work, synthetic-project caveat.
- Accessibility: colour is never the only signal (emoji + text verdicts), tables have headers, contrast AA.

### 9.3 Assertion semantics

- GOOD/regression-guard scenario fails → **real problem** (config drift, product regression, or harness bug) → red.
- BAD scenario's symptom not reproduced → the scenario is **no longer demonstrating** what the docs claim (maybe the product fixed it!) → amber "symptom not reproduced — review scenario"; doesn't fail the pipeline unless `SHOWCASE_STRICT_BAD=true`. This is how we learn a BAD became a regression guard (like IOS-R01).

### 9.4 `tools/lint/cache_lint.py` — static anti-pattern checker

A standalone CLI that reads any `bitrise.yml` (flat) and reports the anti-patterns from §3 with severity and a link to the scenario doc. It's a teaching companion and lets users check their own config. Checks (each maps to a scenario ID):

- activation missing on a workflow that runs Gradle/Xcode/Bazel/RN builds (AND-B01, …);
- activation after first compiling step (AND-B02, IOS-B05);
- `activate-build-cache-for-xcode` on a pre-26 Xcode stack (IOS-B01);
- DerivedData in key-based paths in a workflow with Xcode Build Cache (IOS-B02);
- `/usr/bin/xcodebuild`, `xcrun xcodebuild` with absolute path, `tuist build|test` in script contents (IOS-B03);
- `BITRISE_BUILD_NUMBER`/`$(date` inside `GCC_PREPROCESSOR_DEFINITIONS`/`OTHER_SWIFT_FLAGS`/`--action_env`/`buildConfigField` in scripts (IOS-B04, BZ-B03, AND-B03 heuristics);
- `--rerun-tasks`, `--no-build-cache` (AND-B05);
- restore key ≠ save key for the same paths (NODE-B01, IOS-B07);
- static keys / missing checksum (NODE-B02);
- checksum of a lockfile that doesn't match the package manager used in scripts (RN-B02);
- save before install; cache before checkout (NODE-B03, X-B01);
- legacy `cache-pull`/`cache-push`;
- risky paths (`DerivedData`, `Archives`, `CoreSimulator`, `**/build`, `target/` with unscoped key, `$HOME`, `./`, `node_modules`, `.venv`);
- secret-like paths (`*.keychain*`, `.netrc`, `.npmrc`, `id_rsa`, `.env`, `.aws/credentials`) — critical;
- missing `is_key_unique` on checksum keys; missing `{{ .OS }}` when the same key is used on Linux and macOS stacks;
- release workflow on `-edge` stack.

Output: human table + `--format json|sarif`. Unit tests with fixture YAMLs (one fixture per check, positive + negative). The showcase's own BAD workflows are an integration test: running the linter on `bitrise.yml` must flag exactly the BAD scenarios (allow-list via `# showcase-lint: expected AND-B02` comments).

---

## 10. Documentation

Docs are a first-class deliverable, not an afterthought. Markdown in `docs/`, rendered with MkDocs Material (GitHub Pages via a GitHub Action is fine). Tone: precise, practical, no marketing superlatives, every claim either measured by the showcase or linked to a source.

### 10.1 Structure

```
docs/
├── index.md                         # what this is, the screenshot, scenario matrix, quick links
├── getting-started.md               # fork → add app on Bitrise → secrets → run showcase-smoke → read report (< 30 min)
├── concepts/
│   ├── two-kinds-of-cache.md        # §3.1, with diagrams (Mermaid)
│   ├── reading-cache-health.md      # ratio vs hit rate, cold vs thrash vs stable partial reuse, per-DC origin, never-cacheable work
│   ├── isolation.md                 # namespace harness, isolated vs steady
│   ├── workflow-posture.md          # PR vs main vs nightly vs release caching posture
│   ├── realistic-expectations.md    # benchmark ranges, why synthetic numbers are directional
│   └── security.md                  # never cache secrets
├── stacks/
│   ├── android-gradle.md  ios-xcode.md  react-native.md  flutter.md  bazel.md
│   ├── node.md  ruby.md  go.md  rust.md  python.md  java-maven.md
├── scenarios/<stack>/<ID>.md        # one page per scenario (template §10.4)
├── advanced/
│   ├── gradle-test-distribution.md  # §11.1, incl. how to request beta access
│   └── bazel-rbe.md                 # §11.2
├── reference/
│   ├── yaml-architecture.md         # bundles, generated workflows, pipelines, modular vs flat
│   ├── catalog-format.md            # scenarios/catalog.yml schema
│   ├── metrics-schema.md + metrics-schema.json
│   ├── report.md                    # how to read the HTML report
│   ├── cache-lint.md                # linter usage + check list
│   ├── versions.md                  # pinned steps/stacks/tools + date verified
│   └── verified-facts.md            # every [VERIFY] item, result, source, date
├── troubleshooting.md               # "my GOOD scenario shows misses", DC crossing, concurrency, legacy stack missing…
├── contributing.md                  # how to add a scenario (catalog entry → patch/bundle input → doc page → expectations)
└── CHANGELOG.md
```

### 10.2 Stack page template (`docs/stacks/*.md`)

1. Which mechanism(s) apply (managed Build Cache vs key-based) — table.
2. The GOOD setup as copy-paste YAML (minimal, real step IDs).
3. What "healthy" looks like in the logs (exact lines, annotated).
4. Cache targets table: path · what it is · value · risk · recommendation · key.
5. Pitfalls list → links to each BAD scenario page.
6. Expected-savings context and caveats.
7. Sources (Bitrise docs links).

### 10.3 Concept page must-haves

- `reading-cache-health.md` must include the anonymised field lessons: naive hit rate 12 % vs 195× ratio; DC-crossing cold cache mimicking thrash (consecutive same-DC builds ~100 % hit, every DC crossing 0 % + full re-upload, lever = build frequency, not config); absolute-path key thrash in RN fixed by prefix mapping; Tuist `build/test` shim bypass; "Cache plugin usage: none" line.
- A decision flowchart (Mermaid): "Is the cache helping?" → engaged? → ratio? → same DC? → consecutive builds stable? → look for volatile inputs.

### 10.4 Scenario page template (`docs/scenarios/<stack>/<ID>.md`)

```markdown
---
id: AND-B03
verdict: bad
stack: android
fix_ref: AND-G01
tags: [volatile-input, key-busting]
---
# AND-B03 — Volatile BuildConfig field in a core module

**In one sentence:** …

## What the configuration does
<the exact YAML / code lines, highlighted>

## What you see
- Pipeline graph: measure ≈ seed duration (screenshot placeholder `assets/AND-B03-graph.png`, captured on first real run)
- Log evidence (verbatim, ANSI-stripped):
  ```
  > Task :core:common:compileDebugKotlin
  ```
  (instead of `> Task :core:common:compileDebugKotlin FROM-CACHE`)
- Metrics: from_cache_share ≈ …, ratio ≈ …

## Why it happens
<mechanism, 1–3 paragraphs>

## How to fix it
```diff
- buildConfigField("String", "BUILD_TIME", "\"${System.currentTimeMillis()}\"")
+ // inject only in :app release builds, or at packaging time
```

## How to confirm the fix
<which metric/log line flips>

## Seen in the wild
<anonymised, one paragraph, no names>

## References
```

Placeholders for screenshots/log excerpts are filled from the **first real run** (milestone M7) — never invent log lines; until captured, mark them `> _To be captured from a real run._`

### 10.5 README

Above the fold: one sentence, the pipeline-graph screenshot (GOOD vs BAD rows), a 3-step quick start, the scenario matrix (generated from the catalog by `make docs`), and a clear note: *"Requires a Bitrise workspace with Build Cache (a trial works). Gradle Test Distribution and Bazel RBE modules need those features enabled for your workspace."*

### 10.6 Honesty box (must appear in README + report + realistic-expectations.md)

> The sample projects are synthetic and sized for a demo. Absolute numbers depend on your project's module graph, change patterns and machines. Treat the showcase as a demonstration of **mechanisms and symptoms**, not as a promise of a specific speed-up. For a realistic estimate, benchmark on your own commit history starting from an empty cache.

---

## 11. Optional advanced modules

### 11.1 Gradle Test Distribution — worker-scaling showcase (`showcase-gradle-test-distribution`)

**Gate:** runs only if `SHOWCASE_ENABLE_GRADLE_TD=true`; every workflow's first bundle checks the flag and, if false, records `skipped` metrics and exits 0. Requires: Remote Execution enabled for the workspace by Bitrise (private beta), worker pools created per §3.8, secret `RBE_API_TOKEN` (Bitrise PAT with access to the workspace) **only** if the API-resize approach below is used.

**Project:** `projects/gradle-tests` — generated JVM/Kotlin multi-module project with configurable test volume: `S` = 300 tests (too small — BAD case), `M` = 3,000, `L` = 10,000 unit tests; each test does deterministic CPU work (e.g. 20–200 ms, seeded distribution with a long tail to make shard balancing visible). JUnit 5. Java 17 bytecode (matches worker default).

**Matrix (each cell = one workflow, run sequentially so pool resizing doesn't race):**

| Cell | Workers (replicas × concurrency) | Shard size | Test volume | Purpose |
|---|---|---|---|---|
| TD-BASE-L | local only (Linux large) | — | M | Baseline single node |
| TD-BASE-XL | local only (Linux 2XL/4XL) | — | M | "Just buy a bigger machine" comparison |
| TD-W1 | 1 × 4 | 200 | M | Minimal pool |
| TD-W2 | 2 × 4 | 200 | M | |
| TD-W4 | 4 × 4 (≈ the internal sweet spot was 4 XL × 3) | 200 | M | Recommended start |
| TD-W8 | 8 × 4 | 200 | M | Diminishing returns? |
| TD-S70 / TD-S560 | 4 × 4 | 70 / 560 | M | Shard size effect (start-up overhead ~5–6 s per shard) |
| TD-BAD-SMALL | 4 × 4 | 70 | S | ❌ Too few tests: overhead > gain, slower than local |
| TD-BAD-CC | 4 × 4 | 200 | M | ❌ Configuration cache left on → incompatibility; record the failure mode (must be caught and recorded, exit 0) **[VERIFY behaviour]** |
| TD-BAD-TASK | 4 × 4 | 200 | M | ❌ Invocation lacks a top-level `test` task (e.g. only `:module:someCustomTask` that depends on tests) → plugin doesn't hook, runs locally |

**How worker count is varied — two options, implement A, document B:**
- **A. One pool, resized between cells** via `tools/rbe/pool.sh resize <pool> <replicas>` (RBE API `PATCH …/worker_pools/{id}` with `minReplicas=maxReplicas=N`), then wait until N machines report ready (`GET …/worker_pools?includeMachines=true`) with a timeout. Cells form a sequential chain (`depends_on`) in the pipeline. After the last cell, scale back to the pre-run value (store it in an intermediate file; `should_always_run: workflow` on the restore node).
- **B. Several pools** (`gradle-td-1`, `-2`, `-4`, `-8`) selected per cell — only if the plugin/step supports choosing a pool **[VERIFY: no pool-selection input is documented today]**. Faster, but costs idle capacity.
- If the API isn't available to the user, the module degrades to "fixed pool, vary shard size only" and the docs explain how to do the worker sweep manually in the UI.

**Metrics:** `test_distribution` object: `{workers, concurrency, replicas, shard_size, tests, shards, wall_s, local_baseline_s, speedup, queue_s?, rbe_test_tasks_seen, results_merged, td_log_lines}` — parse `[Bitrise Test Distribution]` log lines **[VERIFY content]** and confirm `rbeTest` tasks executed.

**Report extra:** a line chart (inline SVG) of wall time vs workers for each shard size, with the local baselines as horizontal lines, plus a "cost proxy" column (worker-minutes = replicas × wall time) so the "more machines isn't always better" point is visible. Annotate the knee of the curve.

**Docs (`docs/advanced/gradle-test-distribution.md`):** what it is (and that it's not general Gradle RBE), beta status and how to request access, requirements (thousands of unit tests, no config cache, top-level test task, Java 17 default), pool setup screenshots (placeholders), the two steps (pinned SHAs), how to verify it works, the scaling results and how to interpret them, the internal DuckDuckGo-Android benchmark as reference (3m20s → 2m00s/1m27s, best value 560 tests/shard on 4 XL × 3), cost considerations.

### 11.2 Bazel RBE — worker-scaling showcase (`showcase-bazel-rbe`)

**Gate:** `SHOWCASE_ENABLE_BAZEL_RBE=true`. Requires RBE enabled (trials typically ≤ 10 workers) and a pool named per `SHOWCASE_RBE_POOL` in **every DC** builds can land in.

| Cell | Setup | Purpose |
|---|---|---|
| RBE-LOCAL | remote cache only, no RBE, `--jobs` default | Baseline |
| RBE-W2/W5/W10 | pool resized to N; `--config=remote` with `--jobs` scaled (e.g. 25 × N, capped) | Scaling curve |
| RBE-BAD-JOBS | 10 workers, `--jobs` left at default (= host CPUs) | ❌ Cluster underused: barely faster than W2 |
| RBE-BAD-POOL | `Pool=` name typo / pool missing in the DC | ❌ Build fails fast with "workers don't exist"-style error → caught, recorded, exit 0 **[VERIFY message]** |
| RBE-BAD-PUSH | RBE + `--cache-push=true` / local results uploaded | ❌ Redundant uploads (bytes up ≫), slower |
| RBE-BAD-EXECPROPS | targets also set their own `exec_properties` | ❌ Fails per docs ("no other exec_properties") → recorded |

Bazel project for RBE should be **action-wide** (many independent compile actions) so parallelism is visible — use `generators/bazel.py --shape wide`. Clean the remote cache effect: every RBE cell uses a fresh namespace (§4.2) so we measure execution, not cache hits; one extra cell `RBE-W10-WARM` reuses the namespace to show cache + RBE together.

---

## 12. Repo hygiene, security, CI

### 12.1 Secrets & settings

| Name | Required for | Notes |
|---|---|---|
| *(none)* | all core pipelines | Build Cache auth is handled by the activation steps on Bitrise |
| `RBE_API_TOKEN` | §11 resize automation | Bitrise PAT; Secret, not exposed to PRs |
| `SHOWCASE_REPO_URL` | report doc links | plain env, default to the GitHub URL |

Never echo tokens; `set +x` around API calls. Mark secrets "not exposed for pull requests" in docs.

### 12.2 GitHub-side CI (`.github/workflows/ci.yml`)

`make lint` (yamllint, shellcheck, ruff, mypy for tools, markdownlint, lychee link check), `make generate && git diff --exit-code`, `bitrise validate` on both YAMLs, unit tests for generators/collectors/report/linter (pytest, fixtures with real-shaped log excerpts captured in M7), JSON-schema validation of fixture metrics. Bitrise runs are **not** triggered from GitHub CI by default (cost); maintainers start pipelines manually or on schedule.

### 12.3 `CLAUDE.md` content (create at repo root)

- Source of truth: `docs/PROJECT_SPEC.md`; scenarios: `scenarios/catalog.yml`.
- Never hand-edit `bitrise.yml` or generated `.bitrise/workflows|pipelines` files — run `make generate`.
- One defect per BAD scenario; BAD scenarios exit 0.
- No secrets, slugs, customer names. No invented log lines — capture from real runs.
- Every new scenario = catalog entry + bundle input/patch + doc page + expectations + linter check (if statically detectable).
- Verify version-sensitive facts and log them in `docs/reference/verified-facts.md`.
- Before finishing a task: `make lint generate validate test`.

### 12.4 Cost awareness

Document approximate Bitrise credit/minute consumption per pipeline (fill after M7). Default project size `M`; `S` for smoke. Provide `SHOWCASE_PROJECT_SIZE=S` override to cut cost.

---

## 13. Milestones (build in this order)

| M | Deliverable | Exit criteria |
|---|---|---|
| M0 | Repo skeleton, licenses, `CLAUDE.md`, Makefile, CI lint, this spec copied to `docs/` | CI green |
| M1 | `scenarios/catalog.yml` (all scenarios, even unimplemented → `status: planned`), generator + flattener, common bundles, metrics schema, timing + merge tools, report renderer with fixture data | `bitrise validate` passes; report renders from fixtures |
| M2 | Android: generator, GOOD + all BAD (B13/B14 optional), Gradle init-script collector | First real `showcase-android` run; assertions meaningful |
| M3 | iOS (XcodeGen project, Xcode collector), IOS-* scenarios | Real run; capture real log lines |
| M4 | React Native + Flutter | Real runs; FL-V01 resolved |
| M5 | Bazel + key-based stacks (Node, Ruby, Go, Rust, Python, Maven, X-*) | Real runs |
| M6 | `cache_lint.py` + tests; smoke pipeline | Linter flags exactly the BAD scenarios |
| M7 | Docs complete: concepts, stacks, every scenario page with **real** captured logs/screenshots, README screenshot, verified-facts | Docs build; link check passes |
| M8 | Optional modules: Gradle Test Distribution (if access), Bazel RBE (if access) | Scaling report with real numbers or clearly marked "not run" |
| M9 | Polish: cost table, troubleshooting from real issues, CHANGELOG, v1.0.0 tag | Success criteria §2.3 met |

---

## 14. Risks, open questions, decisions to confirm with the owner

| # | Item | Default if unanswered |
|---|---|---|
| Q1 | Is a pre-Xcode-26 stack still available for IOS-B01/RN-B04? | If not: mark scenario skipped, keep doc |
| Q2 | Can a public repo do `xcode-archive` without real signing? | Use `xcode-build-for-test` / simulator builds; archive only in docs |
| Q3 | Exact Build Cache step input YAML keys (push, verbose, RN toggles) and current majors | Read each step's `step.yml` in the steplib; record in versions.md |
| Q4 | Where do Xcode `Proxy blob stats` / `xcelerate-*.log` land in a Bitrise build today? | Discover on first run; adapt collector |
| Q5 | Is the RBE REST API usable with a customer PAT? | If not: module §11 uses fixed pools + manual sweep docs |
| Q6 | Gradle Test Distribution step SHAs and pool selection | Pin SHAs at implementation; option A resizing |
| Q7 | Datacenter detection from inside a build | hostname token parse; else `unknown` |
| Q8 | Does `org.gradle.caching=false` in project `gradle.properties` beat the init script? | Decide AND-B06 variant after test |
| Q9 | Real OSS projects (e.g. DuckDuckGo-Android, Pocket Casts iOS) as optional "realistic mode" via submodules? | v1: synthetic only; v1.1: optional `SHOWCASE_PROJECT_SOURCE=oss` with license notes |
| Q10 | Build annotations CLI availability | Skip if unavailable |
| Q11 | Modular YAML is Enterprise-only — keep flat `bitrise.yml` as the default root | Yes (decided) |

Known risk: **concurrency**. A full `showcase-android` run wants ~26 parallel jobs. Docs must explain staggering and recommend `showcase-smoke` for small workspaces.

Known risk: **DC crossing** between seed and measure produces false BADs → the report's "not comparable" handling (§7.5) is mandatory, not nice-to-have.

---

## 15. Sources used for this spec

Public:
- Bitrise Build Cache for Gradle — https://docs.bitrise.io/en/bitrise-build-cache/build-cache-for-gradle/configuring-the-build-cache-for-gradle-in-the-bitrise-ci-environment
- Bitrise Build Cache for Xcode — https://docs.bitrise.io/en/bitrise-build-cache/build-cache-for-xcode/configuring-the-build-cache-for-xcode-in-the-bitrise-ci-environment and FAQ https://docs.bitrise.io/en/bitrise-build-cache/build-cache-for-xcode/xcode-compilation-cache-faq.html
- Bitrise Build Cache for React Native — https://docs.bitrise.io/en/bitrise-build-cache/build-cache-for-react-native/configuring-the-build-cache-for-react-native-in-the-bitrise-ci-environment
- Remote Build Execution for Bazel — https://docs.bitrise.io/en/bitrise-build-cache/build-cache-for-bazel/remote-build-execution-for-bazel.html
- Gradle Test Distribution private beta announcement — https://www.bitrise.io/blog/post/accelerate-gradle-testing-on-bitrise-test-distribution-private-beta-now-open
- Fixed Xcode compilation cache misses caused by changing checkout paths — https://discuss.bitrise.io/t/fixed-xcode-compilation-cache-misses-caused-by-changing-checkout-paths/26009
- New Build Cache step inputs for Xcode and React Native — https://discuss.bitrise.io/t/new-build-cache-step-inputs-for-xcode-and-react-native/26122
- Step bundles — https://docs.bitrise.io/en/bitrise-ci/workflows-and-pipelines/steps/step-bundles.html
- Configuring a Bitrise Pipeline (graph pipelines, intermediate files) — https://docs.bitrise.io/en/bitrise-ci/workflows-and-pipelines/build-pipelines/configuring-a-bitrise-pipeline
- Modular YAML configuration — https://docs.bitrise.io/en/bitrise-ci/configure-builds/configuration-yaml/modular-yaml-configuration (limits: 50 files, nesting 10 — https://discuss.bitrise.io/t/modular-yaml-increased-file-and-nesting-limits/25978)
- Bitrise Build Cache CLI — https://github.com/bitrise-io/bitrise-build-cache-cli

Internal (Bitrise staff only — do **not** link from the public repo; facts above are already distilled and anonymised): SA Build Cache YAML audit playbook (stack references, key-based mechanics, workflow posture), Build Cache trial-audit diagnosis classes (errors / thrash / cache-caused failures / silent no-op), "Realistic Benchmarks" (R&D), "Test Distribution benchmark" (R&D), "External setup guide — Gradle Test Distribution — Private Beta" (R&D), RBE API notes, #team-advanced-ci-public discussions on RBE data-centre behaviour.
