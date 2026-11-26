"""Nothing depends on this module — tools/simulate-change.sh python leaf mutates label() here for
the "leaf" change kind (spec §4.1 default)."""


def label() -> str:
    return "leaf-v1"
