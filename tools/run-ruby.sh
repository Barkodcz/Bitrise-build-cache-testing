#!/usr/bin/env bash
# tools/run-ruby.sh <ruby_version>
#
# Installs the pinned Ruby version from scratch via rbenv + ruby-build (both official, cloned
# directly from GitHub if not already present — spec §0's "use official steps where possible")
# unless <ruby_version> is "system", runs `bundle install` + a smoke-test script against
# projects/ruby, and times the build step (spec §8.2).
#
# RB-B01's "restored native gem from the wrong OS is unusable" symptom must NOT hard-fail the
# build (spec §0.6: every BAD scenario still exits 0) -- this script detects it by actually trying
# to load/run the project after `bundle install`, and if that fails, records the failure, forces a
# clean reinstall, and retries once before giving up for real.
set -euo pipefail

ruby_version="${1:?usage: run-ruby.sh <ruby_version>}"

if [ "$ruby_version" != "system" ]; then
  export RBENV_ROOT="$HOME/.rbenv"
  export PATH="$RBENV_ROOT/bin:$PATH"
  if ! command -v rbenv >/dev/null 2>&1; then
    git clone --depth 1 https://github.com/rbenv/rbenv.git "$RBENV_ROOT"
    git clone --depth 1 https://github.com/rbenv/ruby-build.git "$RBENV_ROOT/plugins/ruby-build"
  fi
  eval "$(rbenv init -)"
  rbenv install --skip-existing "$ruby_version"
  rbenv shell "$ruby_version"
fi

cd "$BITRISE_SOURCE_DIR/projects/ruby"

echo "run-ruby.sh: using $(ruby -v)"

bundle config set --local path 'vendor/bundle'

"$BITRISE_SOURCE_DIR"/tools/metrics/timing.sh start build_step
bundle install

if bundle exec ruby run.rb; then
  echo "run-ruby.sh: smoke test passed after bundle install (native gems usable as restored)"
else
  echo "run-ruby.sh: smoke test FAILED after bundle install -- restored gems are unusable" \
       "(this is the symptom RB-B01 demonstrates; recovering with a forced reinstall, not failing the build)"
  bundle install --force
  bundle exec ruby run.rb
  echo "run-ruby.sh: smoke test passed after forced reinstall"
fi
"$BITRISE_SOURCE_DIR"/tools/metrics/timing.sh stop build_step
