package com.showcase.core;

import org.apache.commons.lang3.StringUtils;

/** A "widely depended" core module (spec §4.1) — the leaf module depends on this. */
public final class Core {
    private Core() {
    }

    public static String greeting() {
        return StringUtils.capitalize("hello from showcase-core");
    }
}
