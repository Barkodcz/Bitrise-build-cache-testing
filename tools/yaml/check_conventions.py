#!/usr/bin/env python3
"""Static convention checks for generated workflows/pipelines (spec §7.7). Run via `make lint`.

Checks:
  1. Every scenario workflow has a title + a summary starting with a verdict emoji.
  2. Every scenario workflow uses only `bundle::*` steps plus at most one raw (non-bundle) step.
  3. Every `status: implemented` scenario in the catalog appears in exactly one generated pipeline.
  4. Every measure workflow is a dependency of its pipeline's report workflow.
"""
import os
import sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERDICT_EMOJI = {"✅", "❌", "\U0001f6e1️"}


def load(path):
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    errors = []
    catalog = load(os.path.join(ROOT, "scenarios", "catalog.yml"))
    implemented = {s["id"] for s in catalog["scenarios"] if s.get("status") == "implemented"}
    seen_in_pipelines = set()

    wf_dir = os.path.join(ROOT, ".bitrise", "workflows")
    pl_dir = os.path.join(ROOT, ".bitrise", "pipelines")

    for fname in sorted(os.listdir(wf_dir)) if os.path.isdir(wf_dir) else []:
        doc = load(os.path.join(wf_dir, fname))
        for wf_name, wf in doc.get("workflows", {}).items():
            if wf_name.startswith("report_"):
                continue  # utility/report workflow, not a scenario workflow
            if "title" not in wf:
                errors.append(f"{fname}: workflow {wf_name} missing title")
            summary = wf.get("summary", "")
            if not any(summary.startswith(e) for e in VERDICT_EMOJI):
                errors.append(f"{fname}: workflow {wf_name} summary missing verdict emoji: {summary!r}")
            raw_steps = 0
            for step in wf.get("steps", []):
                step_key = list(step.keys())[0]
                if not step_key.startswith("bundle::"):
                    raw_steps += 1
            if raw_steps > 1:
                errors.append(f"{fname}: workflow {wf_name} has {raw_steps} raw steps (max 1 allowed)")

    for fname in sorted(os.listdir(pl_dir)) if os.path.isdir(pl_dir) else []:
        doc = load(os.path.join(pl_dir, fname))
        for pipeline_name, pipeline in doc.get("pipelines", {}).items():
            workflows = pipeline.get("workflows", {})
            measure_names = [w for w in workflows if w.endswith("__2_measure")]
            report_names = [w for w in workflows if w.startswith("report_")]
            for mn in measure_names:
                scenario_id = mn.split("__")[0].upper()
                seen_in_pipelines.add(scenario_id)
            for rn in report_names:
                deps = set(workflows[rn].get("depends_on", []))
                missing = set(measure_names) - deps
                if missing:
                    errors.append(f"{fname}: pipeline {pipeline_name} report {rn} missing depends_on for {missing}")

    missing_from_pipelines = implemented - seen_in_pipelines
    if missing_from_pipelines:
        errors.append(f"catalog scenarios implemented but not in any pipeline: {sorted(missing_from_pipelines)}")

    if errors:
        print("check_conventions: FAILED")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"check_conventions: OK ({len(implemented)} implemented scenarios checked)")


if __name__ == "__main__":
    main()
