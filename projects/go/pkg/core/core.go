// Package core is a "widely depended" core package (spec §4.1) — the leaf package below depends
// on it, so a change here is the "core" change-kind, while a change in leaf/leaf.go is the "leaf"
// change-kind that nothing else depends on.
package core

import "rsc.io/quote"

// Greeting returns a fixed string. tools/simulate-change.sh does not touch this file (reserved
// for a future GO-B-core-style scenario); it exists so the module has a real dependency
// (rsc.io/quote) to populate go.sum with actual content worth caching.
func Greeting() string {
	return quote.Hello()
}
