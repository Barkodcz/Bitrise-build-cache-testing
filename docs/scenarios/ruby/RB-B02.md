---
id: RB-B02
verdict: bad
stack: ruby
fix_ref: RB-G01
tags: [toolchain-drift]
---
# RB-B02 — Ruby version drift

**In one sentence:** the seed build runs Ruby 3.2.2, the measure build runs Ruby 3.3.0 — the cache
key includes `{{ .OS }}` (both are Linux, so that part matches) but not the Ruby version, so the
restored gems were compiled for the wrong Ruby ABI.

## What the configuration does
`.bitrise/workflows/ruby.yml` `rb-b02__*` — identical bundle structure to `RB-G01`, but
`bundle::ruby_install`'s `ruby_version` input differs between phases, while the cache key stays the
`{{ .OS }}`-only form in both:

```yaml
# rb-b02__1_seed
- bundle::ruby_install:
    inputs:
    - ruby_version: "3.2.2"

# rb-b02__2_measure
- bundle::ruby_install:
    inputs:
    - ruby_version: "3.3.0"
```

`tools/run-ruby.sh` installs each pinned version from scratch via `rbenv` + `ruby-build` (both
cloned directly from GitHub if not already present) — real, historically-released Ruby versions
that stay installable indefinitely.

## What you see
- **Real captured log** (`rb-b02__2_measure`, build 27, app `84c7a274-43b0-477d-9141-ea174ad0ce6e`, 2026-11-26):
  ```
  keybased_record: restore name=bundle hit=exact
  run-ruby.sh: using ruby 3.3.0 (2023-12-25 revision 5124f9ac75) [x86_64-linux]
  run-ruby.sh: smoke test passed after bundle install (native gems usable as restored)
  ```
  — `bundle install + smoke test` took **2.7 minutes** here, vs. ~13 seconds for the equivalent
  step in `RB-G01`/`RB-B01` (same machine class, same gem). The smoke test *did* pass on the first
  try — but only because Bundler/RubyGems install native extensions under a Ruby-ABI-versioned path
  (`extensions/<platform>/<ruby-abi-version>/...`); restoring a `vendor/bundle` built under 3.2.2's
  ABI into a 3.3.0 process means `bundle install` doesn't find a matching extension directory for
  3.3.0 and **silently recompiles `nokogiri` from scratch**, which is where the extra ~2.5 minutes
  goes. This is a *quieter* symptom than `RB-B01`'s hard restore failure: the build "looks" fine
  (no error, no forced-reinstall message) but almost none of the cache's time-saving benefit was
  actually realized.
- Metrics: `key_based.restore_hit == "exact"` — the restore itself genuinely succeeded (same OS,
  same `Gemfile.lock`); the wasted time is downstream of the restore, inside `bundle install`'s own
  native-extension handling.

## Why it happens
Ruby native extensions are compiled against a specific Ruby version's ABI, and RubyGems/Bundler
know this: they install compiled extensions under a per-ABI-version subdirectory
(`extensions/<platform>/<ruby-abi-version>/...`). A cache key that accounts for the OS but not the
Ruby version restores a `vendor/bundle` whose extension directory doesn't match the running Ruby's
ABI version at all — Bundler notices this itself (it's not a cache bug, it's Bundler behaving
correctly) and quietly recompiles, consuming most of the wall-clock time the cache was supposed to
save without any visible error.

## How to fix it
```diff
-    key: bundle-{{ .OS }}-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/ruby/Gemfile.lock" }}
+    key: bundle-{{ .OS }}-{{ getenv "SHOWCASE_NS" }}-{{ getenv "SHOWCASE_RUBY_VERSION" }}-{{ checksum "projects/ruby/Gemfile.lock" }}
```
(so a Ruby version change naturally busts the key) → `RB-G01`, with both phases pinned to the
**same** Ruby version (and ideally a committed `.ruby-version` file in a real project, so the pin
lives with the code, not just the CI config).

## How to confirm the fix
Once the key includes the Ruby version, a version change produces a clean cache **miss** instead of
a restored-but-broken archive, and the smoke test passes on the first try every time.

## Seen in the wild
Pinning the Ruby version (a `.ruby-version` file) is necessary but not sufficient on its own — the
cache key itself should include the version too, the same lesson `GO-B02`/`RS-B02` teach for
Go/Rust and `AND-B08` teaches for Gradle/JDK.

## References
- `docs/PROJECT_SPEC.md` §6.7
- `scenarios/catalog.yml` (`RB-B02`)
