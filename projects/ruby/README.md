# projects/ruby

Minimal Ruby project used by the key-based caching scenarios (`scenarios/catalog.yml` `RB-*`).
`Gemfile` pins `nokogiri`, a real native-extension gem, so `bundle install` has real,
platform-specific compiled content worth caching — exactly what makes `RB-B01`'s "restored native
gem from the wrong OS" symptom meaningful.

`tools/run-ruby.sh` sets `bundle config set --local path 'vendor/bundle'` (so gems install into a
project-local, cacheable directory) and runs `bundle exec ruby run.rb`, which requires `lib/core.rb`
(the "widely depended" module) and `lib/leaf.rb` (mutated by `tools/simulate-change.sh ruby leaf`).
