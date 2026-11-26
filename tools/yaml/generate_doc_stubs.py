#!/usr/bin/env python3
"""Create a doc stub for every scenario in scenarios/catalog.yml that doesn't have one yet,
following the template in spec §10.4. Never overwrites an existing file — hand-written scenario
pages (status: implemented) are expected to replace their stub with real content, at which point
re-running this script is a no-op for that scenario.
"""
import os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOG_PATH = os.path.join(ROOT, "scenarios", "catalog.yml")

TEMPLATE = """---
id: {id}
verdict: {verdict}
stack: {stack}
fix_ref: {fix_ref}
tags: {tags}
---
# {id} — {title}

**In one sentence:** {symptom_or_title}

## What the configuration does
> _Status: `planned` — not implemented yet (see CLAUDE.md "Scope status"). This page is a stub generated
> from `scenarios/catalog.yml`; it will get real YAML/code excerpts, log evidence and a fix diff when
> this scenario moves to `status: implemented`._

{root_cause_line}

## What you see
> _To be captured from a real run._

## Why it happens
> _To be written when implemented._

## How to fix it
{fix_line}

## How to confirm the fix
> _To be captured from a real run._

## Seen in the wild
{field_evidence_line}

## References
- `docs/PROJECT_SPEC.md` (source spec for this scenario)
- `scenarios/catalog.yml` (`{id}`)
"""


def main():
    with open(CATALOG_PATH) as f:
        catalog = yaml.safe_load(f)

    written, skipped = 0, 0
    for scn in catalog["scenarios"]:
        doc_rel = scn.get("doc")
        if not doc_rel:
            continue
        doc_path = os.path.join(ROOT, doc_rel)
        if os.path.exists(doc_path):
            skipped += 1
            continue

        tags = scn.get("pattern_tags", [])
        fix_ref = scn.get("fix_ref") or "null"
        root_cause = scn.get("root_cause")
        root_cause_line = f"**Root cause:** {root_cause}" if root_cause else ""
        fix_line = f"Fixed by following `{fix_ref}`." if scn.get("fix_ref") else "_No single fix — see the symptom/root_cause above; this is a structural or informational scenario._"
        field_evidence = scn.get("field_evidence")
        field_evidence_line = field_evidence if field_evidence else "_No field-evidence note recorded yet._"
        symptom_or_title = scn.get("symptom") or scn["title"]

        content = TEMPLATE.format(
            id=scn["id"], verdict=scn["verdict"], stack=scn["stack"], fix_ref=fix_ref,
            tags=tags, title=scn["title"], symptom_or_title=symptom_or_title,
            root_cause_line=root_cause_line, fix_line=fix_line,
            field_evidence_line=field_evidence_line,
        )
        os.makedirs(os.path.dirname(doc_path), exist_ok=True)
        with open(doc_path, "w") as f:
            f.write(content)
        written += 1

    print(f"generate_doc_stubs: wrote {written} new stub(s), {skipped} already existed")


if __name__ == "__main__":
    main()
