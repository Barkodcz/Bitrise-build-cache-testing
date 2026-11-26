#!/usr/bin/env python3
"""tools/report/assertions.py — evaluate catalog `expectations` against measure-phase metrics
(spec §9.1 step 3). Writes JUnit XML (one testcase per implemented scenario) and exits non-zero
only if `--fail-on-assertion true` AND a real (non-"not comparable") expectation failed.
"""
import argparse
import json
import os
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expectations import build_view, check  # noqa: E402

import yaml


def load_metrics(metrics_dir, scenario_id, phase):
    path = os.path.join(metrics_dir, f"{scenario_id}__{phase}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def different_datacenters(seed, measure):
    if not seed or not measure:
        return False
    sd = (seed.get("run") or {}).get("datacenter")
    md = (measure.get("run") or {}).get("datacenter")
    return sd not in (None, "unknown") and md not in (None, "unknown") and sd != md


def evaluate_scenario(scn, metrics_dir):
    sid = scn["id"]
    measure = load_metrics(metrics_dir, sid, "measure")
    seed = load_metrics(metrics_dir, sid, "seed")

    if measure is None:
        return {"id": sid, "status": "error", "detail": "no measure metrics found", "checks": []}

    if different_datacenters(seed, measure):
        return {
            "id": sid, "status": "not_comparable",
            "detail": "seed and measure ran in different datacenters — result not comparable (spec §7.5)",
            "checks": [],
        }

    view = build_view(measure, seed)
    expectations = scn.get("expectations") or {}
    checks = []
    all_ok = True
    for path, expectation in expectations.items():
        try:
            ok, detail = check(path, expectation, view)
        except Exception as e:  # noqa: BLE001
            ok, detail = False, f"error evaluating {path} {expectation!r}: {e}"
        checks.append({"path": path, "expectation": expectation, "ok": ok, "detail": detail})
        all_ok = all_ok and ok

    return {"id": sid, "status": "pass" if all_ok else "fail", "detail": None, "checks": checks}


def to_junit_xml(results):
    cases = []
    n_failures = 0
    for r in results:
        classname = "showcase.scenario"
        name = r["id"]
        if r["status"] == "error":
            n_failures += 1
            cases.append(
                f'    <testcase classname="{classname}" name="{escape(name)}">\n'
                f'      <failure message="{escape(r["detail"] or "")}"/>\n    </testcase>\n'
            )
        elif r["status"] == "not_comparable":
            cases.append(
                f'    <testcase classname="{classname}" name="{escape(name)}">\n'
                f'      <skipped message="{escape(r["detail"] or "")}"/>\n    </testcase>\n'
            )
        elif r["status"] == "fail":
            n_failures += 1
            failed_checks = "; ".join(c["detail"] for c in r["checks"] if not c["ok"])
            cases.append(
                f'    <testcase classname="{classname}" name="{escape(name)}">\n'
                f'      <failure message="{escape(failed_checks)}"/>\n    </testcase>\n'
            )
        else:
            cases.append(f'    <testcase classname="{classname}" name="{escape(name)}"/>\n')

    body = "".join(cases)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuite name="showcase" tests="{len(results)}" failures="{n_failures}">\n'
        f"{body}"
        "</testsuite>\n"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics-dir", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fail-on-assertion", default="true")
    ap.add_argument("--stack", default=None,
                     help="Only evaluate scenarios for this stack (e.g. a single-stack "
                          "report_<stack> workflow). Omit to evaluate every implemented scenario.")
    args = ap.parse_args()

    with open(args.catalog) as f:
        catalog = yaml.safe_load(f)

    implemented = [s for s in catalog["scenarios"] if s.get("status") == "implemented"]
    if args.stack:
        implemented = [s for s in implemented if s["stack"] == args.stack]
    results = [evaluate_scenario(scn, args.metrics_dir) for scn in implemented]

    os.makedirs(args.out, exist_ok=True)
    junit_path = os.path.join(args.out, "junit-showcase.xml")
    with open(junit_path, "w") as f:
        f.write(to_junit_xml(results))

    summary_path = os.path.join(args.out, "assertions-summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)

    n_fail = sum(1 for r in results if r["status"] in ("fail", "error"))
    n_pass = sum(1 for r in results if r["status"] == "pass")
    n_skip = sum(1 for r in results if r["status"] == "not_comparable")
    print(f"assertions: {n_pass} passed, {n_fail} failed, {n_skip} not comparable "
          f"(of {len(results)} implemented scenarios)")
    for r in results:
        if r["status"] in ("fail", "error"):
            print(f"  FAIL {r['id']}: {r['detail'] or [c['detail'] for c in r['checks'] if not c['ok']]}")

    if args.fail_on_assertion.lower() == "true" and n_fail > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
