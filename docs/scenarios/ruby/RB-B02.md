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
- Log evidence: `> _To be captured from a real run._`
- Metrics: `key_based.restore_hit` may report a hit (same OS, same `Gemfile.lock`), but
  `tools/run-ruby.sh`'s smoke test can fail and trigger the forced-reinstall recovery path, the same
  signal as `RB-B01` but caused by a Ruby *version* mismatch rather than an OS mismatch.

## Why it happens
Ruby native extensions are compiled against a specific Ruby version's C API and ABI. A gem built
under Ruby 3.2.2 isn't guaranteed to load correctly under Ruby 3.3.0, even on the identical OS and
architecture. A cache key that accounts for the OS but not the Ruby version misses this entirely.

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
