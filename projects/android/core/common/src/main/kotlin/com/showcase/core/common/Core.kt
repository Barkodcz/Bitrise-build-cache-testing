package com.showcase.core.common

/**
 * Widely-depended core module. Other tooling (tools/simulate-change.sh) appends a comment
 * line to this exact file to simulate a "core" change-kind that invalidates every downstream
 * module's build cache entry.
 */
object Core {
    fun describe(): String = "core-common-v1"
}
