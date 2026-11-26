# projects/node

Minimal npm project used by the key-based caching scenarios (`scenarios/catalog.yml` `NODE-*`).
Not published; exists only so `npm ci` has real dependency resolution to cache/restore.

- `npm ci` restores/installs from `package-lock.json`.
- `tools/simulate-change.sh node leaf|core` edits `src/leaf.js`; `deps` bumps a harmless
  `showcaseMarker` field in `package.json` so `package-lock.json`'s content checksum changes.
