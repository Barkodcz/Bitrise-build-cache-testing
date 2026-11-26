---
id: MVN-B01
verdict: bad
stack: jvm-maven
fix_ref: MVN-G01
tags: [under-scoped-key-glob]
---
# MVN-B01 — Key on root pom.xml only, change in a submodule

**In one sentence:** the measure build bumps `leaf/pom.xml`'s `commons-io` dependency to a real,
different version — a genuine dependency change — but the cache key only checksums the root
`pom.xml`, which never changes, so the stale `~/.m2/repository` cache restores under the same key
and Maven has to download the new dependency anyway.

## What the configuration does
`.bitrise/workflows/jvm-maven.yml` `mvn-b01__*` — same as `MVN-G01` except the key glob is narrowed
to just the root `pom.xml`, and the measure phase applies `tools/simulate-change.sh maven deps`:

```yaml
# mvn-b01__1_seed
- bundle::kb_restore:
    inputs:
    - key: m2-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/maven/pom.xml" }}

# mvn-b01__2_measure
- bundle::simulate_change:
    inputs:
    - kind: deps          # bumps leaf/pom.xml's commons-io 2.15.1 -> 2.16.1
- bundle::kb_restore:
    inputs:
    - key: m2-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/maven/pom.xml" }}
```

Note the key is **identical** in both phases — `projects/maven/pom.xml` (the parent/root POM)
never changes; only `projects/maven/leaf/pom.xml` does.

## What you see
- Log evidence: `> _To be captured from a real run._`
- Metrics: `key_based.restore_hit` may report a hit (the literal key string matches — the root POM
  really didn't change), but the build still has to download `commons-io:2.16.1` since it wasn't in
  the restored `~/.m2/repository`.

## Why it happens
Maven multi-module (reactor) builds can have dependency changes in *any* module's own `pom.xml` —
not just the root/parent POM. A key template that only checksums the root `pom.xml` is blind to
changes made anywhere else in the reactor, so it keeps reporting the same cache key even when the
actual dependency set the build needs has changed.

## How to fix it
```diff
-    key: m2-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/maven/pom.xml" }}
+    key: m2-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/maven/**/pom.xml" }}
```
(glob every module's POM, not just the root) → `MVN-G01`.

## How to confirm the fix
Once the glob covers every module, the same `deps` change produces a genuine cache **miss** (a new
key, because `leaf/pom.xml`'s checksum changed) instead of a stale "hit" that still has to download
the new dependency anyway.

## Seen in the wild
The exact mechanism spec §6.11 warns about: a key glob that doesn't cover every module's `pom.xml`
misses dependency changes made in a submodule — easy to introduce by writing `checksum "pom.xml"`
against a single-module project and never revisiting it after the project grows into a
multi-module reactor.

## References
- `docs/PROJECT_SPEC.md` §6.11
- `scenarios/catalog.yml` (`MVN-B01`)
