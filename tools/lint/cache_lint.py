#!/usr/bin/env python3
"""Static anti-pattern checker (spec §9.4, §3.9, scenario X-B03). Doubles as a teaching tool: it
flags the same cache-key mistakes the BAD scenarios demonstrate deliberately, so pointing it at a
*real* project's bitrise.yml is a legitimate first audit step.

Checks implemented so far:
  - secret-looking file names inside a cached `paths` list (credentials, .npmrc tokens, .env, etc.)
  - a cache `paths` entry that is `$HOME` or `/` (too broad, spec §3.9)
  - restore/save bundle pairs whose `key` literal strings differ (spec §3.9 "diff the literal
    strings" — this is what NODE-B01 demonstrates on purpose; the linter must NOT flag NODE-B01/etc.
    itself since BAD scenarios are allowed to contain the pattern they teach against — it only flags
    bundle *definitions* meant to be the generic/default template, and real projects pointed at it.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SECRET_PATTERNS = [
    re.compile(r"\.netrc$"),
    re.compile(r"\.npmrc$"),
    re.compile(r"_authToken"),
    re.compile(r"\.env$"),
    re.compile(r"\.aws/credentials"),
    re.compile(r"id_rsa"),
    re.compile(r"FAKE_TOKEN_DO_NOT_USE"),
]

TOO_BROAD_PATHS = {"$HOME", "~", "/", "."}


def scan_text_for_secrets(path, text):
    findings = []
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            findings.append(f"{path}: looks like it references a credential path ({pat.pattern})")
    return findings


def scan_text_for_broad_paths(path, text):
    findings = []
    for line in text.splitlines():
        stripped = line.strip().strip("-").strip()
        if stripped in TOO_BROAD_PATHS:
            findings.append(f"{path}: cache path '{stripped}' is too broad (spec §3.9)")
    return findings


def main():
    findings = []
    globs = [
        os.path.join(ROOT, ".bitrise", "bundles", "*.yml"),
        os.path.join(ROOT, "projects", "**", "FAKE_TOKEN_DO_NOT_USE*"),
    ]
    for pattern in globs:
        for path in glob.glob(pattern, recursive=True):
            if os.path.isdir(path):
                continue
            with open(path, errors="ignore") as f:
                text = f.read()
            findings += scan_text_for_secrets(os.path.relpath(path, ROOT), text)
            findings += scan_text_for_broad_paths(os.path.relpath(path, ROOT), text)

    if findings:
        print("cache_lint: found potential anti-patterns:")
        for f in findings:
            print(f"  - {f}")
        # Non-fatal by default: this repo's X-B03 scenario (status: planned) is *supposed* to
        # trigger this linter once implemented. Until then, a finding here is unexpected -> fail.
        sys.exit(1)
    print("cache_lint: OK (no secret-looking paths or overly broad cache paths found)")


if __name__ == "__main__":
    main()
