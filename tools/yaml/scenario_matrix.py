#!/usr/bin/env python3
"""Print a Markdown scenario matrix from scenarios/catalog.yml, grouped by stack (spec §10.5
README requirement: "the scenario matrix (generated from the catalog by `make docs`)").
Usage: python3 tools/yaml/scenario_matrix.py"""
import os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERDICT_EMOJI = {"good": "✅", "bad": "❌", "regression-guard": "🛡️"}


def main():
    with open(os.path.join(ROOT, "scenarios", "catalog.yml")) as f:
        catalog = yaml.safe_load(f)

    by_stack = {}
    for scn in catalog["scenarios"]:
        by_stack.setdefault(scn["stack"], []).append(scn)

    lines = ["| Stack | Implemented | Planned | Total |", "|---|---|---|---|"]
    total_impl = total_planned = 0
    for stack, scns in sorted(by_stack.items()):
        impl = sum(1 for s in scns if s.get("status") == "implemented")
        planned = len(scns) - impl
        total_impl += impl
        total_planned += planned
        lines.append(f"| {stack} | {impl} | {planned} | {len(scns)} |")
    lines.append(f"| **total** | **{total_impl}** | **{total_planned}** | **{total_impl + total_planned}** |")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
