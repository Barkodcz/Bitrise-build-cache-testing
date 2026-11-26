# Node.js (key-based caching)

Pipeline: `showcase-node` (a stand-in for the spec's broader `showcase-key-based` pipeline, which
also covers Ruby/Go/Rust/Python/Maven once those stacks move to `status: implemented` — see
`CLAUDE.md` "Scope status"). Sample project: `projects/node` — a minimal npm project
(`left-pad` as its one real dependency) whose entire purpose is giving `npm ci` something real to
resolve and cache.

Node.js has **no Bitrise Build Cache backend** — everything here is key-based caching (see
`docs/concepts/caching-mechanisms.md`), which makes it a clean, fast-to-run second stack to
demonstrate the other half of the mechanism matrix after Android/Gradle.

## Scenarios implemented so far

| ID | Verdict | Title |
|---|---|---|
| [NODE-G01](../scenarios/node/NODE-G01.md) | ✅ good | `~/.npm` keyed on `package-lock.json`, fallback chain, `is_key_unique` |
| [NODE-B01](../scenarios/node/NODE-B01.md) | ❌ bad | restore ≠ save key — the canonical worked example |
| [NODE-B02](../scenarios/node/NODE-B02.md) | ❌ bad | Static key + change kind `deps` |
| [NODE-B03](../scenarios/node/NODE-B03.md) | ❌ bad | Save before install |
| [NODE-B05](../scenarios/node/NODE-B05.md) | ❌ bad | No `is_key_unique` |

`NODE-G02` (pnpm) and `NODE-B04` (OS-mismatch) are catalogued (`status: planned`) but not yet
implemented.

## Key mechanics

- `restore-cache` right after checkout, `save-cache` right after `npm ci` and before any deploy
  step — inverted order (`NODE-B03`) means every build is one commit behind.
- Key quality priority order (spec §3.9): (1) restore key literally ≠ save key — the single most
  common mistake (`NODE-B01`); (2) static key — never invalidates (`NODE-B02`); (3) checksumming the
  wrong lockfile for the install tool in use; (4) missing `{{ .OS }}` when shared across OSes;
  (5) `is_key_unique: true` on save to avoid re-uploading an unchanged archive (`NODE-B05`).
