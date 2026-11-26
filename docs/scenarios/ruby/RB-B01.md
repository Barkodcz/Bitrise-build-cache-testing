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
- **Real captured log** (`rb-b01__2_measure`, build 27, app `84c7a274-43b0-477d-9141-ea174ad0ce6e`, 2026-11-26):
  ```
  Cache key: bundle-ca7eaab3-d72f-4c14-9e09-69bba72f7221-RB-B01-5c863bc976a62e4058ccf6c2b58ebd935254923c448a83e8abce971a8958f021
  Exact hit for first key
  Archive size: 9.81MB
  Restoring archive...
  Output: /bitrise/src/projects/ruby/vendor/bundle/: Failed to create dir '/bitrise': Read-only file system
  ... (repeated for every file in the archive)
  ```
  — confirmed via the seed run's log that this is the **exact same literal cache key** used on both
  phases (no `{{ .OS }}` anywhere in it). The restore step reports "Exact hit" (the Linux-built
  archive genuinely matched and started downloading), then fails outright trying to extract it onto
  the macOS stack.
- **This is a more dramatic — and more real — failure mode than originally designed.** The spec's
  hypothesis for this scenario was a *subtler* symptom: the gem restores "successfully" but then
  fails an ABI compatibility check at runtime. What actually happens on this Bitrise macOS stack
  (`osx-xcode-latest-stable`) is blunter: `restore-cache@3.0.2` cannot even extract a Linux-built
  archive's directory structure, apparently because of how `/bitrise/src` is mounted/overlaid on
  this macOS stack image. The restore step itself fails (shown as a yellow "Restore Cache (Failed)"
  in the step list) but — correctly, per spec §0.6 — does **not** fail the overall workflow; the
  build continues straight to a clean `bundle install` from scratch, which is why `run-ruby.sh`'s
  smoke test still passes on the first try (there was nothing broken to catch — the restore never
  got far enough to leave broken files behind).
- Metrics: `key_based.restore_hit == "false"` (the recorder falls back to `"false"` when
  `BITRISE_CACHE_HIT` isn't set to a success value, which is what happens when the step itself
  fails) — not because the key differed, but because of the extraction failure above.

## Why it happens
Native-extension gems like `nokogiri` compile to OS- and architecture-specific shared libraries.
`Gemfile.lock` alone doesn't capture *which platform* a `vendor/bundle` archive was built for — the
cache key needs a separate discriminator (`{{ .OS }}`) for that. Without it, a Linux-built archive
and a macOS build share the same cache slot: on this real infra, that manifests as the restore step
itself failing to extract the mismatched archive (see above) rather than a subtler runtime ABI
failure — either way, the root cause is identical: one cache slot, shared across two platforms that
can't use the same contents.

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
