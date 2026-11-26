// Leaf module touched by tools/simulate-change.sh for `leaf`/`core` change kinds (spec §4.1).
// Nothing in this project depends on this file's content changing except index.js calling it, so
// touching it is a safe, deterministic "simulated commit" that doesn't affect dependency resolution.
function label() {
  return "showcase-node-leaf";
}

module.exports = { label };
