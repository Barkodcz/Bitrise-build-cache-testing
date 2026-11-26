# Ruby / CocoaPods / fastlane (key-based caching)

Pipeline: `showcase-ruby`. Sample project: `projects/ruby` — depends on `nokogiri`, a real
native-extension gem, installed into a project-local `vendor/bundle` via `bundle config set --local
path`.

Ruby has **no Bitrise Build Cache backend** — everything here is key-based caching (see
`docs/concepts/caching-mechanisms.md`), same as Node.js/Go/Rust/Python/Maven. This is the first
stack with a scenario that deliberately runs its two phases on **different stacks** (`RB-B01`: Linux
seed, macOS measure).

## Scenarios implemented so far

| ID | Verdict | Title |
|---|---|---|
| [RB-G01](../scenarios/ruby/RB-G01.md) | ✅ good | `vendor/bundle` keyed on `Gemfile.lock` + `{{ .OS }}` |
| [RB-B01](../scenarios/ruby/RB-B01.md) | ❌ bad | Key without `{{ .OS }}` shared Linux↔macOS |
| [RB-B02](../scenarios/ruby/RB-B02.md) | ❌ bad | Ruby version drift |

## Key mechanics

- **Native extensions need an OS discriminator in the key** (`RB-B01`): `nokogiri` compiles
  platform-specific shared libraries; a key that doesn't include `{{ .OS }}` lets a Linux-built
  archive and a macOS build collide in the same cache slot.
- **Native extensions also need a Ruby-version discriminator** (`RB-B02`): even on the identical
  OS, a gem compiled under one Ruby version isn't guaranteed to load under another.
- **Catching, not hard-failing, a broken restore** (both BAD scenarios): `tools/run-ruby.sh`
  actually runs the project after `bundle install` and, if that fails, records it and recovers with
  a forced reinstall — spec §0.6 requires every BAD scenario to still exit 0.
