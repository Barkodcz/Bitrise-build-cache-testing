package com.showcase.app

import com.showcase.core.common.Core
import com.showcase.core.common.ShowcaseBuildConfig
import com.showcase.core.model.ShowcaseItem
import com.showcase.featureleaf.Leaf

fun main() {
    val item = ShowcaseItem(id = 1, name = "sample")
    println("Android build cache showcase app")
    println("core      = ${Core.describe()}")
    println("model     = ${item.describe()}")
    println("feature   = ${Leaf.describe()}")
    println("buildTime = ${ShowcaseBuildConfig.BUILD_TIME}")
}
