package com.showcase.core.model

import com.showcase.core.common.Core

/**
 * A tiny domain model that depends on :core:common.
 */
data class ShowcaseItem(val id: Int, val name: String) {
    fun describe(): String = "${Core.describe()}/item-$id:$name"
}
