---
id: RB-G01
verdict: good
stack: ruby
fix_ref: null
tags: [exact-key-match, os-scoped-key]
---
# RB-G01 — vendor/bundle keyed on Gemfile.lock + {{ .OS }}

**In one sentence:** `bundle config set --local path 'vendor/bundle'` installs gems into a
project-local, cacheable directory, keyed on both `Gemfile.lock`'s checksum **and** `{{ .OS }}` —
necessary because `Gemfile`'s one real dependency, `nokogiri`, is a native-extension gem with
platform-specific compiled binaries.

## What the configuration does
`.bitrise/workflows/ruby.yml` `rb-g01__*`, via `.bitrise/bundles/key-based.yml` `kb_restore`/`kb_save`
and `ruby_install`:

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::kb_restore:
    inputs:
    - key: bundle-{{ .OS }}-{{ getenv "SHOWCASE_NS" }}-{{ checksum "projects/ruby/Gemfile.lock" }}
    - name: bundle
- bundle::ruby_install:
    inputs:
    - ruby_version: "system"       # bundle install + bundle exec ruby run.rb, via tools/run-ruby.sh
- bundle::kb_save: { ... same key, paths: projects/ruby/vendor/bundle }
```

Both the seed and measure phases run on the same Linux stack with the same system Ruby — see
`RB-B01` (OS drift) and `RB-B02` (Ruby version drift) for what happens when either of those vary
without the key noticing.

## What you see
- Log evidence: `> _To be captured from a real run._`
- Metrics: `key_based.restore_hit` in `["exact", "partial"]` on the measure run.

## Why it doesn't need a fix
N/A — this is the GOOD baseline. `RB-B01` and `RB-B02` both point back here.

## How to confirm it's working
`key_based.restore_hit` is `"exact"` on the measure phase, and the smoke-test script
(`tools/run-ruby.sh`) passes on the first try without needing a forced reinstall.

## Seen in the wild
Baseline every `RB-B*` scenario is compared against.

## References
- `docs/PROJECT_SPEC.md` §6.7
- `scenarios/catalog.yml` (`RB-G01`)
