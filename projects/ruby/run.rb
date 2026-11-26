#!/usr/bin/env ruby
# Minimal "build + smoke test" entrypoint — every RB-* scenario runs this after `bundle install`.
# No test framework dependency; a plain script is enough to prove nokogiri actually loads and
# works, which is exactly what's needed to catch RB-B01's "restored native gem is unusable"
# symptom (see tools/run-ruby.sh).
$LOAD_PATH.unshift(File.join(__dir__, "lib"))
require "core"
require "leaf"

puts Core.greeting
puts Leaf.label
