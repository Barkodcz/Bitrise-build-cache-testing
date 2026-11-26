---
id: RB-B01
verdict: bad
stack: ruby
fix_ref: RB-G01
tags: [missing-os-in-key]
---
# RB-B01 — Key without {{ .OS }} shared Linux<->macOS

**In one sentence:** the seed build runs on Linux, the measure build runs on macOS, but both share
the exact same cache key (no `{{ .OS }}`) — the Linux-compiled `nokogiri` native extension is
restored into the macOS build, where it's unusable, so `bundle install` has to detect the failure
and recover rather than genuinely benefiting from the restore.

## What the configuration does
`.bitrise/workflows/ruby.yml` `rb-b01__*` — same as `RB-G01` except the key drops `{{ .OS }}`, and
the two phases run on different stacks:

```yaml
# rb-b01__1_seed — stack: ubuntu-noble-24.04-bitrise-2025-android
- bundle::kb_restore:
    inputs:
    - key: bundle-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/ruby/Gemfile.lock" }}

# rb-b01__2_measure — stack: osx-xcode-latest-stable
- bundle::kb_restore:
    inputs:
    - key: bundle-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/ruby/Gemfile.lock" }}
```

`tools/run-ruby.sh` doesn't just run `bundle install` blindly — it then tries to actually run the
project (`bundle exec ruby run.rb`, which requires `nokogiri`). If that fails, it logs the failure,
runs `bundle install --force`, and retries — this is deliberate: spec §0.6 requires every BAD
scenario to still exit 0, so the symptom has to be *caught and recorded*, not left to hard-fail the
build.

## What you see
- Log evidence: `> _To be captured from a real run._` — expect a line like
  `run-ruby.sh: smoke test FAILED after bundle install -- restored gems are unusable`, followed by a
  successful retry after the forced reinstall.
- Metrics: `key_based.restore_hit` may report a hit (the literal key string matches across both
  OSes), but the restored native gem doesn't actually work on the second OS.

## Why it happens
Native-extension gems like `nokogiri` compile to OS- and architecture-specific shared libraries.
`Gemfile.lock` alone doesn't capture *which platform* a `vendor/bundle` archive was built for — the
cache key needs a separate discriminator (`{{ .OS }}`) for that. Without it, a Linux-built archive
and a macOS build share the same cache slot, and whichever one wrote last "wins" the slot for both.

## How to fix it
```diff
-    key: bundle-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/ruby/Gemfile.lock" }}
+    key: bundle-{{ .OS }}-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/ruby/Gemfile.lock" }}
```
(and the matching `kb_save`) → `RB-G01`.

## How to confirm the fix
Once the key includes `{{ .OS }}`, each platform gets its own cache slot, and the smoke test passes
on the first try without ever needing the forced-reinstall recovery path.

## Seen in the wild
The classic "shared cache key across OSes" mistake for any stack with native/compiled dependencies
— every scenario that caches a toolchain or dependency directory across more than one OS needs this
same discriminator (see also `NODE-B04`, not yet implemented, which covers the same mistake for
Node's `node_modules`).

## References
- `docs/PROJECT_SPEC.md` §6.7
- `scenarios/catalog.yml` (`RB-B01`)
