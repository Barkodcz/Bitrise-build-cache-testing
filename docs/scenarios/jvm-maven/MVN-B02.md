---
id: MVN-B02
verdict: bad
stack: jvm-maven
fix_ref: MVN-G01
tags: [too-broad-cache-path]
---
# MVN-B02 — Caching target/

**In one sentence:** the cache stores `core/target` and `leaf/target` (compiled `.class` files,
built jars) in addition to `~/.m2/repository` — a larger archive for no correctness or speed
benefit, since `target/` is cheap to rebuild and doesn't need to be cached at all.

## What the configuration does
`.bitrise/workflows/jvm-maven.yml` `mvn-b02__*` — identical key template to `MVN-G01`, but the
cached paths include the two modules' build output directories:

```yaml
- bundle::kb_save:
    inputs:
    - key: m2-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/maven/**/pom.xml" }}
    - paths: |-
        ~/.m2/repository
        projects/maven/core/target
        projects/maven/leaf/target
```

## What you see
- Log evidence: `> _To be captured from a real run._`
- Metrics: `key_based.saved == true`, with a markedly larger `archive_bytes` than `MVN-G01`'s
  `~/.m2/repository`-only archive for the same dependency set.

## Why it happens
`~/.m2/repository` (downloaded/built dependency jars) is what makes repeated builds fast — it's
genuinely worth caching. `target/` directories are **build output**: compiled classes and packaged
jars that Maven regenerates quickly from source + the (already cached) dependency repository on
every build regardless. Adding them to the cache archive makes every restore/save bigger and slower
without making the build itself any faster or more correct.

## How to fix it
```diff
 - bundle::kb_save:
     inputs:
     - key: m2-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/maven/**/pom.xml" }}
-    - paths: |-
-        ~/.m2/repository
-        projects/maven/core/target
-        projects/maven/leaf/target
+    - paths: ~/.m2/repository
```
(and the matching `kb_restore`) → `MVN-G01`.

## How to confirm the fix
Compare `key_based.archive_bytes` before and after — caching `~/.m2/repository` alone should
produce a visibly smaller archive for the identical dependency set, with no change in build
correctness or `mvn test` pass/fail status.

## Seen in the wild
The same "too-broad path" mistake as `AND-B11` (Gradle's `build/`/`.gradle/`), `IOS-B09` (Xcode's
`Archives`/`CoreSimulator`), and `PY-B02` (the whole Python `.venv`) — caching a build output
directory instead of just the tool's own dependency cache.

## References
- `docs/PROJECT_SPEC.md` §6.11
- `scenarios/catalog.yml` (`MVN-B02`)
