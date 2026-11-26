#!/usr/bin/env python3
"""tools/metrics/xcode_parse.py — extract Build Cache for Xcode signals from a raw xcodebuild log
(spec §8.2 "Xcode" row). Strips ANSI first, looks for `Proxy blob stats: hits: N (...) / total: M
(P%). Uploaded blobs: U (...)` and `SetSession called` lines.

The exact log line format is marked [VERIFY] in the spec — this script is deliberately defensive:
if nothing matches, it writes a fragment with every field `null` and `found_any_signal: false`
rather than fabricating numbers (spec §8.3 "never fabricate"). --raw-log may be empty/missing
entirely (e.g. if $BITRISE_XCODE_RAW_RESULT_TEXT_PATH isn't set by the build step) — handled the
same way.
"""
import argparse
import json
import os
import re

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
PROXY_STATS_RE = re.compile(
    r"Proxy blob stats:\s*hits:\s*(\d+).*?total:\s*(\d+).*?Uploaded blobs:\s*(\d+)",
    re.IGNORECASE | re.DOTALL,
)
SET_SESSION_RE = re.compile(r"SetSession called", re.IGNORECASE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-log", default="", help="path to the raw xcodebuild log, may be empty")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    result = {
        "proxy_hits": None,
        "proxy_total": None,
        "uploaded_blobs": None,
        "set_session_seen": None,
        "xcelerate_logs": [],
        "found_any_signal": False,
    }

    if args.raw_log and os.path.exists(args.raw_log):
        with open(args.raw_log, errors="ignore") as f:
            text = f.read()
        text = ANSI_RE.sub("", text)

        m = PROXY_STATS_RE.search(text)
        if m:
            result["proxy_hits"] = int(m.group(1))
            result["proxy_total"] = int(m.group(2))
            result["uploaded_blobs"] = int(m.group(3))
            result["found_any_signal"] = True

        if SET_SESSION_RE.search(text):
            result["set_session_seen"] = True
            result["found_any_signal"] = True
        elif result["found_any_signal"]:
            result["set_session_seen"] = False
    else:
        result["xcelerate_logs"] = []

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"xcode_parse: wrote {args.out} (found_any_signal={result['found_any_signal']})")


if __name__ == "__main__":
    main()
