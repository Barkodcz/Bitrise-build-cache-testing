package com.showcase.core;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

class CoreTest {
    @Test
    void greetingIsNotEmpty() {
        assertTrue(!Core.greeting().isEmpty());
    }
}
