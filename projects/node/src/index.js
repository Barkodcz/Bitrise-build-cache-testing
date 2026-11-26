// Minimal entrypoint so `npm run build` / `node --test` have something to do (spec §6.6 "node" project).
// Deliberately tiny: the point of the NODE-* scenarios is the key-based dependency cache, not the app.
const leftPad = require("left-pad");
const { label } = require("./leaf");

function main() {
  console.log(leftPad(label(), 20, "."));
}

main();

module.exports = { main };
