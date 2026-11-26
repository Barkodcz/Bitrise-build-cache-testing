// Package leaf depends on core but nothing depends on leaf — tools/simulate-change.sh edits the
// Label() return value here for the "leaf" change kind (spec §4.1 default).
package leaf

func Label() string {
	return "leaf-v1"
}
