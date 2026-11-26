# Java / Maven (key-based caching)

Pipeline: `showcase-jvm-maven`. Sample project: `projects/maven` — a real multi-module Maven
reactor (parent `pom.xml` + `core`, depending on `commons-lang3` + JUnit 5; `leaf`, depending on
`core` and its own extra dependency `commons-io`, declared only in `leaf/pom.xml`).

Java/Maven has **no Bitrise Build Cache backend** — everything here is key-based caching (see
`docs/concepts/caching-mechanisms.md`), same as Node.js/Go/Rust/Python.

## Scenarios implemented so far

| ID | Verdict | Title |
|---|---|---|
| [MVN-G01](../scenarios/jvm-maven/MVN-G01.md) | ✅ good | `~/.m2/repository` keyed on `**/pom.xml` |
| [MVN-B01](../scenarios/jvm-maven/MVN-B01.md) | ❌ bad | Key on root `pom.xml` only, change in a submodule |
| [MVN-B02](../scenarios/jvm-maven/MVN-B02.md) | ❌ bad | Caching `target/` |

## Key mechanics

- **Glob every module's `pom.xml`, not just the root** (`MVN-B01`): in a multi-module reactor, a
  dependency change can happen in any submodule's own `pom.xml` — a key that only checksums the
  root POM is blind to it, restoring a stale cache under an unchanged key while the build still has
  to download the new dependency.
- **Cache the dependency repository, not the build output** (`MVN-B02`): `~/.m2/repository` is
  worth caching; `target/` directories are cheap to regenerate and just inflate the archive.
