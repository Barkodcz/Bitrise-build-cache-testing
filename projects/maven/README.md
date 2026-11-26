# projects/maven

Multi-module Maven project used by the key-based caching scenarios (`scenarios/catalog.yml`
`MVN-*`). Parent `pom.xml` aggregates two submodules:

- `core/` — depends on `commons-lang3` + JUnit 5 (a real test); the "widely depended" module.
- `leaf/` — depends on `core` **and its own extra dependency** (`commons-io`), declared only in
  `leaf/pom.xml`, never in the root `pom.xml`. `tools/simulate-change.sh maven deps` bumps that
  dependency's version — a real change the root-pom-only key in `MVN-B01` fails to notice.

`mvn package` (or `mvn test`) from `projects/maven/` builds both modules via Maven's reactor.
