package com.showcase.core.model

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class ModelTest {

    @Test
    fun `describe includes id and name`() {
        val item = ShowcaseItem(id = 1, name = "widget")
        assertEquals("core-common-v1/item-1:widget", item.describe())
    }
}
