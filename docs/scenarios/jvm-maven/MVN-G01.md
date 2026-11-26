---
id: MVN-G01
verdict: good
stack: jvm-maven
fix_ref: null
tags: [exact-key-match, lean-cache-path]
---
# MVN-G01 — ~/.m2/repository keyed on **/pom.xml

**In one sentence:** `~/.m2/repository` (Maven's local dependency repository) is key-cached, with
the same key template for restore and save, checksumming **every** `pom.xml` in the multi-module
reactor — not just the root one.

## What the configuration does
`.bitrise/workflows/jvm-maven.yml` `mvn-g01__*`:

```yaml
steps:
- bundle::setup_checkout: {}
- bundle::setup_showcase: {}
- bundle::kb_restore:
    inputs:
    - key: m2-{{ getenv "SHOWCASE_NS" }}-{{ .OS }}-{{ checksum "projects/maven/**/pom.xml" }}
    - name: m2-repo
- bundle::maven_build: {}          # mvn test, via tools/run-maven.sh
- bundle::kb_save: { ... same key, paths: ~/.m2/repository }
```

`projects/maven` is a real multi-module project (parent `pom.xml` + `core` + `leaf`); the `**/pom.xml`
glob in the key checksums all three, so a dependency change in *any* module busts the key — see
`MVN-B01` for what happens when the glob only covers the root.

## What you see
- Log evidence: `> _To be captured from a real run._`
- Metrics: `key_based.restore_hit` in `["exact", "partial"]` on the measure run.

## Why it doesn't need a fix
N/A — this is the GOOD baseline. `MVN-B01` and `MVN-B02` both point back here.

## How to confirm it's working
`key_based.restore_hit` is `"exact"` on the measure phase, and `mvn test` noticeably skips
re-downloading dependencies already in `~/.m2/repository`.

## Seen in the wild
Baseline every `MVN-B*` scenario is compared against.

## References
- `docs/PROJECT_SPEC.md` §6.11
- `scenarios/catalog.yml` (`MVN-G01`)
