#!/usr/bin/env python3
"""Merge timer/collector fragments into the final metrics/<SCENARIO>__<phase>.json (spec §8.1).

Reads every fragment under $SHOWCASE_METRICS_DIR/.fragments/<scenario>__<phase>/ written during the
workflow by tools/metrics/timing.sh, the Gradle init script, and tools/metrics/keybased_record.sh,
and assembles one file matching docs/reference/metrics-schema.json. Missing data is always written
as `null` plus a note (spec §8.3 "never fabricate").
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"warning: could not parse {path}: {e}", file=sys.stderr)
        return None


def detect_datacenter():
    hostname = os.environ.get("HOSTNAME", "") or os.environ.get("BITRISE_IO_HOSTNAME", "")
    for token, dc in (("-ams-", "ams"), ("-ord-", "ord"), ("-iad-", "iad")):
        if token in hostname:
            return dc
    return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--phase", required=True)
    ap.add_argument("--out", required=True, help="$SHOWCASE_METRICS_DIR")
    args = ap.parse_args()

    frag_dir = os.path.join(args.out, ".fragments", f"{args.scenario}__{args.phase}")
    notes = []

    def timer(name):
        d = load_json(os.path.join(frag_dir, f"{name}.json"))
        if d is None:
            notes.append(f"timer '{name}' missing")
            return None
        return d.get("duration_s")

    durations_s = {
        "total_workflow": timer("total_workflow"),
        "build_step": timer("build_step"),
        "cache_restore": timer("cache_restore"),
        "cache_save": timer("cache_save"),
        "dependency_install": timer("dependency_install"),
    }

    gradle = load_json(os.path.join(frag_dir, "gradle.json"))
    remote_cache = None
    if gradle is not None:
        hits = gradle.get("from_cache", 0)
        misses = gradle.get("executed", 0)
        total = hits + misses
        remote_cache = {
            "tool": "gradle",
            "hits": hits,
            "misses": misses,
            "hit_rate": (hits / total) if total else 0.0,
            "bytes_downloaded": None,
            "bytes_uploaded": None,
            "download_upload_ratio": None,
            "proxy_total": None,
            "engaged": hits > 0,
        }
        notes.append("byte traffic (bytes_downloaded/uploaded) not yet parsed from the Build Cache "
                      "step's own summary output — see tools/metrics/gradle/ in verified-facts.md")
    else:
        notes.append("no gradle.json fragment found (not a Gradle scenario, or build failed before buildFinished)")

    key_based = []
    if os.path.isdir(frag_dir):
        for fname in sorted(os.listdir(frag_dir)):
            if fname.startswith("keybased__") and fname.endswith(".json"):
                d = load_json(os.path.join(frag_dir, fname))
                if d:
                    d.setdefault("archive_bytes", None)
                    d.setdefault("restore_s", None)
                    d.setdefault("save_s", None)
                    d.setdefault("saved", False)
                    key_based.append(d)

    metrics = {
        "schema_version": 1,
        "scenario_id": args.scenario,
        "stack": os.environ.get("SHOWCASE_STACK"),
        "phase": args.phase,
        "verdict_expected": None,
        "run": {
            "pipeline_id": os.environ.get("BITRISEIO_PIPELINE_ID"),
            "build_slug": os.environ.get("BITRISE_BUILD_SLUG"),
            "workflow": os.environ.get("BITRISE_TRIGGERED_WORKFLOW_ID"),
            "stack_id": os.environ.get("BITRISE_STACK_ID"),
            "machine_type": os.environ.get("BITRISE_MACHINE_TYPE_ID"),
            "datacenter": detect_datacenter(),
            "isolation": os.environ.get("SHOWCASE_ISOLATION"),
            "namespace": os.environ.get("SHOWCASE_NS"),
            "change_kind": os.environ.get("SHOWCASE_CHANGE_KIND"),
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
        "durations_s": durations_s,
        "remote_cache": remote_cache,
        "gradle": gradle,
        "xcode": None,
        "bazel": None,
        "key_based": key_based,
        "test_distribution": None,
        "notes": notes,
        "raw_logs": [f for f in ["gradle-build.log"] if os.path.exists(os.path.join(frag_dir, f))],
    }

    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, f"{args.scenario}__{args.phase}.json")
    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"merge_fragments: wrote {out_path}")


if __name__ == "__main__":
    main()
