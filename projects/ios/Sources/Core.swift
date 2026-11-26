// A "widely depended" core file (spec §4.1) — every other source file in this tiny single-target
// app effectively "depends" on it being compiled as part of the same module.
//
// SHOWCASE_VOLATILE_SWIFT_FLAG (IOS-B04, not yet implemented) would bake a build-number-derived
// value into OTHER_SWIFT_FLAGS; this constant stays fixed so AND-B03-style volatile-input
// scenarios have a stable baseline to diverge from once implemented for iOS.
enum Core {
    static let greeting = "hello from showcase-core"
}
