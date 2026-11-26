package com.showcase.featureleaf

import com.showcase.core.common.Core

/**
 * A leaf feature module. `tools/simulate-change.sh` performs a sed replacement on the
 * `return "leaf-v[0-9]*"` pattern below to simulate a leaf-module-only code change.
 */
object Leaf {
    fun version(): String {
        return "leaf-v473"
    }

    fun describe(): String = "${Core.describe()}/${version()}"
}
