#!/usr/bin/env python3
"""tools/report/render.py — turns metrics/*.json + scenarios/catalog.yml into showcase-report.html
(self-contained, inline CSS, no CDN, dark/light aware) + showcase-report.md + showcase-summary.json
(spec §9.1, §9.2). No external templating dependency (Jinja2 not assumed installed) — plain Python
string building, kept simple on purpose.
"""
import argparse
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expectations import build_view  # noqa: E402

import yaml

VERDICT_EMOJI = {"good": "✅", "bad": "❌", "regression-guard": "🛡️"}


def load_metrics(metrics_dir, scenario_id, phase):
    path = os.path.join(metrics_dir, f"{scenario_id}__{phase}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def fmt(value, digits=2, suffix=""):
    if value is None:
        return "—"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}{suffix}"
    return str(value)


def row_for_scenario(scn, metrics_dir):
    sid = scn["id"]
    seed = load_metrics(metrics_dir, sid, "seed")
    measure = load_metrics(metrics_dir, sid, "measure")
    view = build_view(measure, seed) if measure else {}

    from_cache_share = (view.get("gradle") or {}).get("from_cache_share") if measure else None
    ratio = (view.get("cache") or {}).get("download_upload_ratio") if measure else None
    duration_vs_seed = (view.get("duration") or {}).get("vs_seed") if measure else None
    kb_hit = (view.get("key_based") or {}).get("restore_hit") if measure else None

    return {
        "id": sid,
        "stack": scn["stack"],
        "verdict": scn["verdict"],
        "title": scn["title"],
        "has_data": measure is not None,
        "from_cache_share": from_cache_share,
        "ratio": ratio,
        "duration_vs_seed": duration_vs_seed,
        "kb_hit": kb_hit,
        "symptom": scn.get("symptom"),
        "doc": scn.get("doc"),
    }


HTML_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Bitrise Build Cache Showcase — report</title>
<style>
  :root {
    color-scheme: light dark;
    --bg: #ffffff; --fg: #1a1a1a; --muted: #666; --border: #ddd;
    --good: #1a7f37; --bad: #cf222e; --guard: #9a6700;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg: #0d1117; --fg: #e6edf3; --muted: #9198a1; --border: #30363d; }
  }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--fg); font-family: -apple-system, BlinkMacSystemFont,
    "Segoe UI", Helvetica, Arial, sans-serif; margin: 0; padding: 2rem; line-height: 1.5; }
  h1 { font-size: 1.4rem; }
  .honesty-box { border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin: 1rem 0;
    font-size: 0.9rem; color: var(--muted); }
  table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.9rem; }
  th, td { border: 1px solid var(--border); padding: 0.5rem 0.75rem; text-align: left; }
  th { background: color-mix(in srgb, var(--fg) 6%, transparent); }
  tr.stack-header td { background: color-mix(in srgb, var(--fg) 10%, transparent); font-weight: 600; }
  .verdict-good { color: var(--good); font-weight: 600; }
  .verdict-bad { color: var(--bad); font-weight: 600; }
  .verdict-regression-guard { color: var(--guard); font-weight: 600; }
  .muted { color: var(--muted); }
  code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85em; }
</style>
</head>
<body>
"""

HTML_TAIL = "</body>\n</html>\n"

HONESTY_BOX = (
    "The sample projects are synthetic and sized for a demo. Absolute numbers depend on your "
    "project's module graph, change patterns and machines. Treat this report as a demonstration of "
    "<strong>mechanisms and symptoms</strong>, not a promise of a specific speed-up."
)


def render_html(rows, out_dir):
    by_stack = {}
    for r in rows:
        by_stack.setdefault(r["stack"], []).append(r)

    parts = [HTML_HEAD, "<h1>Bitrise Build Cache Showcase — report</h1>\n",
              f'<div class="honesty-box">{HONESTY_BOX}</div>\n',
              "<table>\n<tr><th>Scenario</th><th>Verdict</th><th>Title</th>"
              "<th>Gradle FROM-CACHE share</th><th>Download/upload ratio</th>"
              "<th>Measure/seed duration</th><th>Key-based restore</th></tr>\n"]

    for stack, stack_rows in sorted(by_stack.items()):
        parts.append(f'<tr class="stack-header"><td colspan="7">{html.escape(stack)}</td></tr>\n')
        for r in stack_rows:
            verdict_class = f"verdict-{r['verdict']}"
            emoji = VERDICT_EMOJI.get(r["verdict"], "")
            data_note = "" if r["has_data"] else ' <span class="muted">(no metrics yet)</span>'
            parts.append(
                "<tr>"
                f"<td><code>{html.escape(r['id'])}</code></td>"
                f'<td class="{verdict_class}">{emoji} {r["verdict"]}</td>'
                f"<td>{html.escape(r['title'])}{data_note}</td>"
                f"<td>{fmt(r['from_cache_share'], 2)}</td>"
                f"<td>{fmt(r['ratio'], 1)}</td>"
                f"<td>{fmt(r['duration_vs_seed'], 2)}</td>"
                f"<td>{fmt(r['kb_hit'])}</td>"
                "</tr>\n"
            )
    parts.append("</table>\n")
    parts.append(HTML_TAIL)

    out_path = os.path.join(out_dir, "showcase-report.html")
    with open(out_path, "w") as f:
        f.write("".join(parts))
    return out_path


def render_markdown(rows, out_dir):
    md_honesty = HONESTY_BOX.replace("<strong>", "**").replace("</strong>", "**")
    lines = ["# Bitrise Build Cache Showcase — report\n", f"> {md_honesty}\n",
              "| Scenario | Verdict | Title | FROM-CACHE share | DL/UL ratio | Measure/seed | KB restore |",
              "|---|---|---|---|---|---|---|"]
    for r in rows:
        emoji = VERDICT_EMOJI.get(r["verdict"], "")
        lines.append(
            f"| `{r['id']}` | {emoji} {r['verdict']} | {r['title']} | "
            f"{fmt(r['from_cache_share'], 2)} | {fmt(r['ratio'], 1)} | "
            f"{fmt(r['duration_vs_seed'], 2)} | {fmt(r['kb_hit'])} |"
        )
    out_path = os.path.join(out_dir, "showcase-report.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics-dir", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stack", default=None,
                     help="Only include scenarios for this stack (e.g. a single-stack "
                          "report_<stack> workflow). Omit to include every implemented scenario.")
    args = ap.parse_args()

    with open(args.catalog) as f:
        catalog = yaml.safe_load(f)

    implemented = [s for s in catalog["scenarios"] if s.get("status") == "implemented"]
    if args.stack:
        implemented = [s for s in implemented if s["stack"] == args.stack]
    rows = [row_for_scenario(scn, args.metrics_dir) for scn in implemented]

    os.makedirs(args.out, exist_ok=True)
    html_path = render_html(rows, args.out)
    md_path = render_markdown(rows, args.out)

    summary_path = os.path.join(args.out, "showcase-summary.json")
    with open(summary_path, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"render: wrote {html_path}, {md_path}, {summary_path} ({len(rows)} scenarios)")


if __name__ == "__main__":
    main()
