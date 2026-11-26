// Nothing depends on this file — tools/simulate-change.sh ios leaf mutates label() here for the
// "leaf" change kind (spec §4.1 default).
enum Leaf {
    static func label() -> String {
        "leaf-v1"
    }
}
