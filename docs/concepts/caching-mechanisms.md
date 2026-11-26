# Two different caching mechanisms — never confuse them

Condensed from `docs/PROJECT_SPEC.md` §3.1. This is the single most important mental model in this
repo: almost every `*-B*` scenario is one of these two mechanisms being mistaken for the other, or
misconfigured on its own terms.

| | **Bitrise Build Cache** (managed remote build cache) | **Key-based caching** (`restore-cache` / `save-cache`) |
|---|---|---|
| What it caches | Compiled task/action outputs, content-addressed, per individual task/compile unit | Directories (dependency caches, toolchains) packed into one archive per key |
| Granularity | Fine (every task/compile/action has its own key) | Coarse (one archive, all-or-nothing per key) |
| Supported tools | Gradle, Xcode 26+, Bazel, React Native's native layer | Any stack — npm/yarn/pnpm, CocoaPods, SPM, pub, Bundler, Go modules, Cargo, pip/Poetry, Maven, the Gradle dependency cache |
| Activation | `activate-build-cache-for-gradle` / `-xcode` / `-bazel` / `-react-native` | `restore-cache` + `save-cache` with a key template, or stack-specific shortcut steps |
| Invalidation | Automatic, by content hash of inputs | By the key template you write |
| Typical failure | Silent: activated but never engaged (wrong placement/stack/shim), or keys busted by a volatile input | Silent: key never changes (stale forever) or restore key ≠ save key (never hits) |

A workflow can have excellent key-based caching of, say, `~/.gradle/caches` and **zero** Build Cache
for Gradle — they solve different problems (dependency downloads vs. compiled outputs). Crediting
one for the other is the most common audit mistake (see `docs/scenarios/android/AND-B01.md` for a
worked example, and `docs/scenarios/node/NODE-B01.md` for the key-based side's own canonical
mistake — restore key ≠ save key).

See also: `docs/concepts/isolation.md`, `docs/concepts/metrics.md`.
