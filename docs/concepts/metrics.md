# How to tell if a remote build cache is "working"

Condensed from `docs/PROJECT_SPEC.md` §3.2.

- **Primary metric: download/upload byte ratio** of cache traffic. A healthy cache reads far more
  than it writes (ratio ≫ 1, often 5–200×). A ratio ≈ 1 or below means the build re-writes about as
  much as it reads — little reuse ("thrash") or a cold cache. **This repo does not collect byte
  traffic yet** — `tools/metrics/merge_fragments.py` always emits `remote_cache.bytes_downloaded` /
  `bytes_uploaded` as `null`; see `docs/reference/verified-facts.md` for why, and
  `docs/scenarios/android/AND-G01.md`'s expectations note.
- **Naive hit rate is misleading.** Averaging per-invocation hit rate across all invocations is
  diluted by non-cacheable companion invocations. A real case read 12% naive hit rate while
  delivering a 195× download/upload ratio.
- **A screening number is not a verdict.** Ratio ≈ 1 has innocent causes: cold cache / first builds,
  builds spread across data centres (per-DC cache origin), low build cadence, a structural
  many-flavour matrix, or large always-fresh outputs. See `docs/concepts/isolation.md` for how this
  repo tries to tell cold-cache-looks-like-failure apart from a real misconfiguration.
- **Thrash vs. stable partial reuse:** thrash = keys rotate every build, reuse ≈ 0 erratically.
  Stable partial reuse = the *same* hit/miss split repeats across consecutive builds (a structural
  miss set — e.g. non-cacheable tasks). One aggregate number can't distinguish them; comparing two
  consecutive builds (seed vs. measure, this repo's whole design) can.
- **Some work is never cacheable by design.** Xcode: storyboard/XIB compilation, asset catalogs,
  code signing, dSYM generation; Gradle: some lint/verification and packaging/signing tasks. A
  sub-100% hit rate is normal and expected even on a correctly-configured GOOD scenario.
- **Realistic expectations** (from Bitrise's internal benchmarking method): Gradle ≈ 32–49% duration
  reduction on good projects (but as low as ≈3% when the measured commits were unusually large);
  Bazel ≈ 87–92%; Xcode ≈ 14–55%. *Which* tasks are cached matters more than a headline hit-rate
  percentage. See `docs/concepts/honesty.md`.
