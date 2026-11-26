package com.showcase.leaf;

import com.showcase.core.Core;

/** Nothing depends on this module — tools/simulate-change.sh maven leaf mutates label() here for
 * the "leaf" change kind (spec §4.1 default). */
public final class Leaf {
    private Leaf() {
    }

    public static String label() {
        return "leaf-v1";
    }

    public static void main(String[] args) {
        System.out.println(Core.greeting());
        System.out.println(label());
    }
}
