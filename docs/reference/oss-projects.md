# Real open-source sample projects, per stack

Spec §14-Q9 deferred "real OSS projects as an optional realistic mode" to a later pass. This
document is that pass: for every stack (implemented and `planned`), it names one or more real,
actively-maintained open-source projects researched specifically for this showcase, with license,
size/structure, build gotchas, and a fit verdict — so a future contributor can wire one in with
`git submodule add` (or a `SHOWCASE_PROJECT_SOURCE=oss`-style toggle) instead of researching from
scratch. All research below was done 2026-11-26; re-verify before actually vendoring a project
(maintenance status, license, and build requirements can all change).

**Current state:** `projects/android` and `projects/node` (the two `status: implemented` stacks)
are still the small hand-written fixtures described in `CLAUDE.md` — nothing below is wired in yet.
See each section's "why not wired in yet" note.

---

## Android / Gradle

| Candidate | Repo | License | Scale | Secret-free build? |
|---|---|---|---|---|
| **DuckDuckGo-Android** (primary, matches spec's own benchmark reference) | [duckduckgo/Android](https://github.com/duckduckgo/Android) | Apache-2.0 | ~200 Gradle modules, 6,815 Kotlin files, pure Kotlin, Hilt/Anvil DI | **Partially.** `./gradlew jvm_tests` (unit tests) runs secret-free on plain `ubuntu-24.04` + JDK. A full `./gradlew assembleInternalDebug` needs `DEBUG_PROPERTIES`/`DEBUG_KEY`, a `MALICIOUS_SITE_PROTECTION_AUTH_TOKEN`, GitHub Packages auth (private font artifact), and a Go 1.18 toolchain (native bloom-filter submodule). Also needs `git submodule update --init` first. |
| **Now in Android** (practical mid-size alternative) | [android/nowinandroid](https://github.com/android/nowinandroid) | Apache-2.0 | ~30 Gradle modules (core/\*, feature/\*, sync/\*, build-logic convention plugins), Kotlin + Compose, KSP-based Hilt | **Yes.** `./gradlew assembleDebug` / `./gradlew test` work out of the box, no secrets, no submodules. Google's own modularization/build-performance reference app — purpose-built to demonstrate exactly this kind of thing. |

**Recommendation:** use **Now in Android** as the first "realistic mode" upgrade (clone, build, done —
no secrets to manage in a public CI showcase) and keep **DuckDuckGo-Android** documented as the
"at-scale" reference for when someone wants to reproduce the internal benchmark numbers quoted in
`docs/PROJECT_SPEC.md` §3.2/§3.8, using only its `jvm_tests` target to stay secret-free.

**Why not wired in yet:** both are much bigger than the current fixture — even Now in Android's
~30 modules is a real multi-minute cold build, a meaningfully different cost profile than the
current ~1s toy build. Wiring it in means deciding how it coexists with the 6 already-passing
scenarios (parallel `SHOWCASE_PROJECT_SOURCE=oss|synthetic` toggle per spec Q9, or a full swap) —
a design decision, not just a clone.

## iOS / Xcode

| Candidate | Repo | License | Scale | Notes |
|---|---|---|---|---|
| **Kickstarter iOS App** | [kickstarter/ios-oss](https://github.com/kickstarter/ios-oss) | Apache-2.0 | Single `.xcodeproj`, multiple internal frameworks (`Library` = widely-depended core, `KsApi`, `Kickstarter-Framework`/`Kickstarter-iOS`, `KDS` design system, `GraphAPI`, `ServerDrivenUI`, `Experimentation`) | Active (commits within the last day at research time). Explicitly ships an OSS/mock-data mode (`KsApi.Secrets.isOSS = true`) specifically so it builds/runs without a real backend or signing — exactly what `xcode-build-for-simulator` needs. README claims Xcode 26.6 support, good alignment with Bitrise's Xcode 26+ compilation-cache requirement. Gap: no CocoaPods dependency (uses git submodules instead of CocoaPods/SwiftPM-only), so it doesn't exercise the CocoaPods-cache half of `IOS-G01`'s design — that half would need a second, smaller companion project or a manually-added pod. |

**Fit verdict:** good primary pick for the Xcode-Build-Cache half of the iOS stack; the CocoaPods-cache
scenarios (`IOS-B07`/`IOS-B08`) would need their own small example or a deliberately-added pod.

## React Native

**No clean fit found** — flagging the gap honestly rather than forcing a weak pick (per this repo's
own "never fabricate" ethos).

| Candidate | Repo | License | Why it's compromised |
|---|---|---|---|
| Expensify/App | [Expensify/App](https://github.com/Expensify/App) | MIT | Real bare RN app with native Kotlin/Swift code and fastlane tooling, but pulls in a separate `Mobile-Expensify` repo via an SSH-based git submodule for its "HybridApp" setup — real monorepo complexity and an auth requirement awkward for a public showcase. New Architecture status unconfirmed. |
| bluesky-social/social-app | [bluesky-social/social-app](https://github.com/bluesky-social/social-app) | MIT | Native `ios`/`android` dirs checked in (not Expo-managed), but Expo-prebuilt-flavored; needs `.env` + `google-services.json` filled in (likely runtime-only, not compile-blocking, but unverified). | 

**Recommendation:** try **Expensify/App** first and document the submodule step explicitly, or spend a
follow-up research pass on smaller real apps (Mattermost mobile, Infinite Red client apps) before
committing one to the catalog. Don't block implementing the rest of the RN stack on this — the
RN-specific scenarios (unwrapped native command, blind `node_modules` caching, etc.) don't strictly
need a huge app to demonstrate.

## Flutter

| Candidate | Repo | License | Scale | Notes |
|---|---|---|---|---|
| **Wonderous** | [gskinnerTeam/flutter-wonderous-app](https://github.com/gskinnerTeam/flutter-wonderous-app) | MIT | Single app, feature-organized `lib/` tree, android/ios/macos/web/windows platform folders | Real, polished, published app built in partnership with the Flutter team (not a toy demo). Depends on `google_maps_flutter` and `home_widget`, both with real native Android/iOS platform-channel code, so the Gradle/Xcode layers underneath have genuine native compilation to cache. Pins a recent SDK (`flutter: ^3.44.0`) — good toolchain alignment, but older CI images may not have a compatible Flutter installed. API-key-requiring deps (Maps, Unsplash) are runtime-only, not build-blocking. |

**Fit verdict:** good choice, no changes needed before adopting.

## Bazel

| Candidate | Repo | License | Scale | Notes |
|---|---|---|---|---|
| **protobuf** (primary) | [protocolbuffers/protobuf](https://github.com/protocolbuffers/protobuf) | BSD-3-Clause | bzlmod-native (`MODULE.bazel`, published to the Bazel Central Registry), hundreds of BUILD targets across C++ core, Java runtime/codegen, Python/C#/Ruby/PHP/Kotlin test targets | `bazel build //...` / `bazel test //...` work without secrets; proven in extensive GitHub Actions CI on every PR. Moderate build time (not multi-hour). Kotlin presence is thin (mostly C++ + Java) — satisfies "two of C++/Java/Kotlin" but not a true three-language mix. |
| envoy-mobile (stretch alternative) | [envoyproxy/envoy-mobile](https://github.com/envoyproxy/envoy-mobile) | Apache-2.0 | True C++/Kotlin/Swift three-language mix | Better language-mix match, but historically a very long, toolchain-heavy cold build (LLVM/NDK downloads) — riskier CI cost for a showcase repo. Keep as a stretch goal, not the first pick. |

**Fit verdict:** **protobuf** is the pragmatic primary pick; swap to envoy-mobile later if the
three-language mix becomes important enough to justify the longer cold-build cost.

## Java / Maven

| Candidate | Repo | License | Scale | Notes |
|---|---|---|---|---|
| **Apache Dubbo** | [apache/dubbo](https://github.com/apache/dubbo) | Apache-2.0 | 18+ top-level Maven modules, most themselves parent POMs with nested sub-modules (per-protocol, per-registry-backend, etc.) — likely 60–100+ total `pom.xml` files | `mvn package` / `mvn test` work without required secrets; most tests use embedded/mocked registries (e.g. curator-test) rather than live services. Pulls in Netty, Curator, gRPC, Spring — real dependency weight, meaningfully slower cold `~/.m2` population than warm. Actively maintained (JDK 25 support in recent 3.3.x). |

**Fit verdict:** good choice — the deep POM nesting makes the "key on root `pom.xml` only" anti-pattern
(`MVN-B01`) visibly different from "key on `**/pom.xml`" in a way a shallow project wouldn't show.

## Node.js (upgrade candidates for the already-implemented stack)

| Candidate | Repo | License | Lockfile | Notes |
|---|---|---|---|---|
| **NestJS** | [nestjs/nest](https://github.com/nestjs/nest) | MIT | npm, `package-lock.json`, ~1,631 resolved packages (workspaces monorepo) | Pure-JS install (no native/postinstall compile found in a lockfile grep) — still plenty of file/IO volume to show warm-vs-cold savings, just won't demonstrate node-gyp compile time specifically. Clean `build`/`test`/`test:cov` scripts, no secrets. Extremely recognizable framework. |
| **Sequelize** | [sequelize/sequelize](https://github.com/sequelize/sequelize) | MIT | Yarn (Berry-style `yarn.lock`), ~1,407 resolved packages | Includes `sqlite3` as a devDependency — triggers a real node-gyp/prebuild-install compile step on cache-miss, near-instant on cache-hit, so this is the better pick specifically for demonstrating *native dependency* caching. Use `test-unit`/`build`/`test-typings` scripts only — `test-integration-*` needs live DB servers. |

Several other well-known candidates (Ghost, n8n, Docusaurus, TypeORM, Gatsby) were ruled out: most
have migrated to pnpm (this showcase's current Node scenarios are npm/yarn-specific), and n8n uses a
non-permissive "Sustainable Use License."

**Recommendation:** **NestJS** for the general npm-cache story (`NODE-G01`/`NODE-B01`/`NODE-B02`/`NODE-B03`),
**Sequelize** if/when a scenario specifically wants to show native-dependency compile-cache savings.

**Why not wired in yet:** same reasoning as Android — a ~1,400-1,600-package install is a real,
multi-tens-of-seconds-to-minutes cold install, a different cost profile than the current trivial
`left-pad`-only project. Needs the same `SHOWCASE_PROJECT_SOURCE` design decision.

## Ruby

| Candidate | Repo | License | Notes |
|---|---|---|---|
| **Discourse** (primary) | [discourse/discourse](https://github.com/discourse/discourse) | **GPL-2.0** ⚠️ | Large Rails app; Gemfile/Gemfile.lock includes `nokogiri` (compiles libxml2/libxslt C extensions) plus 100+ other gems — strong "real compiled native gem" demo. `bundle install` works without secrets (a full *running* app needs Postgres/Redis, but gem install alone doesn't). **License caveat: GPL-2.0 is copyleft, not permissive** — fine to reference/link, but don't vendor Discourse's code into this repo without checking GPL implications for the rest of the (MIT-licensed) showcase. |
| fastlane/fastlane (thematic alternative) | [fastlane/fastlane](https://github.com/fastlane/fastlane) | MIT | Thematically perfect (this stack is literally "Ruby/CocoaPods/fastlane"), but its own Gemfile.lock (used for fastlane's own dev/test suite) is much smaller and `nokogiri` as a *direct* runtime dependency wasn't confirmed — weaker "native extension" demo than Discourse. Worth a quick manual check before committing either way. |

**Fit verdict:** no single candidate is clean on all axes (scale + native-gem demo + permissive license +
thematic fit). If license cleanliness matters more, go with fastlane and accept a weaker native-gem
story; if the native-gem demo matters more, go with Discourse and flag the GPL-2.0 license prominently
in any doc page that references it.

## Go

| Candidate | Repo | License | Scale | Notes |
|---|---|---|---|---|
| **Hugo** | [gohugoio/hugo](https://github.com/gohugoio/hugo) | Apache-2.0 / MIT (mixed) | ~80 direct + 100+ indirect deps (hundreds of `go.sum` lines) | Well-known static-site-generator CLI. Builds cleanly via `go build ./...`, no secrets. Some versions touch cgo (libsass bindings), adding real compile weight beyond pure-Go deps. |

**Fit verdict:** good choice, no changes needed.

## Rust

| Candidate | Repo | License | Scale | Notes |
|---|---|---|---|---|
| **Alacritty** | [alacritty/alacritty](https://github.com/alacritty/alacritty) | Apache-2.0 | Genuine 4-crate Cargo workspace (`alacritty`, `alacritty_terminal`, `alacritty_config`, `alacritty_config_derive`) | Moderate dependency tree (windowing/GPU rendering libs give real compile weight). Pins a Rust version (`rust-version`/edition 2024, rust 1.85.0) in the workspace manifest — **verify whether this is expressed as a `rust-toolchain.toml`** (needed for the planned `RS-B02` floating-toolchain scenario) or just `Cargo.toml`'s `rust-version` field before relying on it. Builds via `cargo build` without secrets (some platforms need system GL/X11 dev headers, not secrets). |

**Fit verdict:** good choice; confirm the toolchain-pin mechanism before writing `RS-B02` against it.

## Python

| Candidate | Repo | License | Package manager | Notes |
|---|---|---|---|---|
| **Apache Superset** (pip path) | [apache/superset](https://github.com/apache/superset) | Apache-2.0 | pip, `requirements.txt` | Large requirements list including pandas, numpy, pyarrow, cryptography — all C-extension-heavy, so cold `pip install` has real, measurable compile/wheel-build cost vs. warm. No secrets needed for install. Pick a recent tag (older ones had numpy/Python-version install breakage). Ignore the Node-based frontend build — irrelevant to the Python cache scenario. |
| *(Poetry path — no strong candidate found)* | — | — | — | Could not verify a project that's simultaneously Poetry-based, has a numpy/pandas-class C-extension dependency, and is well-known enough to vouch for confidently in this research pass (a candidate like `ibis-project/ibis` looked plausible from memory but wasn't verified). **Honest gap:** either demonstrate the "wrong lockfile" distinction using Superset alone (`requirements.txt` vs. `requirements-dev.txt`), or spend a follow-up pass specifically vetting a Poetry candidate before committing it to the catalog. |

**Fit verdict:** Superset is a strong, ready-to-use pip-path candidate. The Poetry-path gap is real —
don't force a weak pick; revisit with dedicated research time if the Poetry-specific scenarios
(`PY-G02`, `PY-B01` depending on which lockfile it targets) need their own project.

---

## Summary table

| Stack | Primary pick | License | Secret-free? | Status |
|---|---|---|---|---|
| Android | Now in Android (practical) / DuckDuckGo-Android (at-scale) | Apache-2.0 (both) | Now in Android: yes. DDG: unit tests only | researched, not wired in |
| Node.js | NestJS (general) / Sequelize (native-dep demo) | MIT (both) | Yes | researched, not wired in |
| iOS | Kickstarter iOS App | Apache-2.0 | Yes (OSS/mock mode) | researched, stack `planned` |
| React Native | *(no clean fit — see above)* | — | — | gap documented |
| Flutter | Wonderous | MIT | Yes | researched, stack `planned` |
| Bazel | protobuf | BSD-3-Clause | Yes | researched, stack `planned` |
| Java/Maven | Apache Dubbo | Apache-2.0 | Yes | researched, stack `planned` |
| Ruby | Discourse ⚠️ GPL-2.0 / fastlane (weaker native-gem demo) | GPL-2.0 / MIT | Yes (both) | researched, stack `planned` |
| Go | Hugo | Apache-2.0/MIT | Yes | researched, stack `planned` |
| Rust | Alacritty | Apache-2.0 | Yes | researched, stack `planned` |
| Python | Superset (pip) / gap (Poetry) | Apache-2.0 | Yes | researched, stack `planned` |

See `CLAUDE.md` "Scope status" for the overall implementation plan this feeds into.
