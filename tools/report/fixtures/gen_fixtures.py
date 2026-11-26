import json, os
OUT = os.path.dirname(os.path.abspath(__file__))

def base(sid, stack, phase, extra_run=None):
    return {
        "schema_version": 1, "scenario_id": sid, "stack": stack, "phase": phase,
        "verdict_expected": None,
        "run": {"pipeline_id": "fixture", "build_slug": "fixture", "workflow": f"{sid.lower()}__{'1_seed' if phase=='seed' else '2_measure'}",
                "stack_id": "ubuntu-noble-24.04-bitrise-2025-android", "machine_type": None,
                "datacenter": "ams", "isolation": "isolated", "namespace": f"fixture-{sid}",
                "change_kind": "leaf", "started_at": "2026-11-26T10:00:00Z", **(extra_run or {})},
        "durations_s": {"total_workflow": None, "build_step": None, "cache_restore": None, "cache_save": None, "dependency_install": None},
        "remote_cache": None, "gradle": None, "xcode": None, "bazel": None,
        "key_based": [], "test_distribution": None, "notes": [], "raw_logs": [],
    }

def write(sid, phase, d):
    with open(os.path.join(OUT, f"{sid}__{phase}.json"), "w") as f:
        json.dump(d, f, indent=2)

def gradle_fixture(sid, seed_share, measure_share, seed_dur, measure_dur, engaged=True):
    seed = base(sid, "android", "seed")
    seed["durations_s"]["build_step"] = seed_dur
    seed["durations_s"]["total_workflow"] = seed_dur + 20
    seed["gradle"] = {"tasks_total": 100, "executed": int(100*(1-seed_share)), "from_cache": int(100*seed_share),
                       "up_to_date": 0, "skipped": 0, "no_source": 0, "from_cache_share": seed_share, "top_executed_tasks": []}
    seed["remote_cache"] = {"tool": "gradle", "hits": seed["gradle"]["from_cache"], "misses": seed["gradle"]["executed"],
                             "hit_rate": seed_share, "bytes_downloaded": None, "bytes_uploaded": None,
                             "download_upload_ratio": None, "proxy_total": None, "engaged": seed["gradle"]["from_cache"] > 0}
    write(sid, "seed", seed)

    measure = base(sid, "android", "measure")
    measure["durations_s"]["build_step"] = measure_dur
    measure["durations_s"]["total_workflow"] = measure_dur + 20
    executed = int(100*(1-measure_share))
    from_cache = int(100*measure_share)
    measure["gradle"] = {"tasks_total": 100, "executed": executed, "from_cache": from_cache,
                          "up_to_date": 0, "skipped": 0, "no_source": 0, "from_cache_share": measure_share, "top_executed_tasks": []}
    measure["remote_cache"] = {"tool": "gradle", "hits": from_cache, "misses": executed,
                                "hit_rate": measure_share, "bytes_downloaded": None, "bytes_uploaded": None,
                                "download_upload_ratio": None, "proxy_total": None, "engaged": engaged and from_cache > 0}
    write(sid, "measure", measure)

def kb_fixture(sid, restore_hit, saved=True, seed_dur=40, measure_dur=38, stack="node", name="npm",
               key_based_entries=None):
    seed = base(sid, stack, "seed")
    seed["durations_s"]["dependency_install"] = seed_dur
    seed["durations_s"]["total_workflow"] = seed_dur + 10
    seed["key_based"] = key_based_entries or [
        {"name": name, "key": f"{name}-...", "restore_hit": "false", "archive_bytes": 50_000_000,
         "restore_s": 1.0, "save_s": 5.0, "saved": True}
    ]
    write(sid, "seed", seed)

    measure = base(sid, stack, "measure")
    measure["durations_s"]["dependency_install"] = measure_dur
    measure["durations_s"]["total_workflow"] = measure_dur + 10
    measure["key_based"] = key_based_entries or [
        {"name": name, "key": f"{name}-...", "restore_hit": restore_hit, "archive_bytes": 50_000_000,
         "restore_s": 1.0, "save_s": 5.0, "saved": saved}
    ]
    write(sid, "measure", measure)

# GOOD: high hit share, fast measure
gradle_fixture("AND-G01", seed_share=0.05, measure_share=0.72, seed_dur=300, measure_dur=180)
# BAD: no activation at all -> 0 hits
gradle_fixture("AND-B01", seed_share=0.0, measure_share=0.0, seed_dur=300, measure_dur=295, engaged=False)
# BAD: activation after build -> 0 hits for that build
gradle_fixture("AND-B02", seed_share=0.0, measure_share=0.0, seed_dur=300, measure_dur=298)
# BAD: volatile buildconfig -> near-0 share, duration ~= seed
gradle_fixture("AND-B03", seed_share=0.05, measure_share=0.08, seed_dur=300, measure_dur=290)
# BAD: --rerun-tasks -> 0 share
gradle_fixture("AND-B05", seed_share=0.05, measure_share=0.0, seed_dur=300, measure_dur=305)
# BAD: nobody pushes -> 0 share, not engaged
gradle_fixture("AND-B09", seed_share=0.0, measure_share=0.0, seed_dur=300, measure_dur=298, engaged=False)

# Node
kb_fixture("NODE-G01", restore_hit="exact")
kb_fixture("NODE-B01", restore_hit="false")
kb_fixture("NODE-B02", restore_hit="exact")  # stale-but-exact
kb_fixture("NODE-B03", restore_hit="exact", measure_dur=42)  # one build behind, slightly slower
kb_fixture("NODE-B05", restore_hit="exact", saved=True)

# Go: GO-G01 good (both caches hit); GO-B01 bad (no gobuild entry at all); GO-B02 bad (exact "hit"
# against a stale toolchain — restore_hit still reports exact, the point is the symptom isn't
# visible in restore_hit alone, see docs/scenarios/go/GO-B02.md).
kb_fixture("GO-G01", restore_hit="exact", stack="go", name="gobuild", seed_dur=20, measure_dur=6)
kb_fixture("GO-B01", restore_hit="exact", stack="go", name="gomod", seed_dur=20, measure_dur=19)
kb_fixture("GO-B02", restore_hit="exact", stack="go", name="gobuild", seed_dur=20, measure_dur=18)

# Rust: RS-G01 good (scoped cargo-target cache hits cleanly); RS-B01/RS-B02 bad (under-scoped key
# reports a hit, but the symptom is in wasted time / incompatible content, not restore_hit itself).
kb_fixture("RS-G01", restore_hit="exact", stack="rust", name="cargo-target", seed_dur=15, measure_dur=4)
kb_fixture("RS-B01", restore_hit="exact", stack="rust", name="cargo-target", seed_dur=15, measure_dur=14)
kb_fixture("RS-B02", restore_hit="exact", stack="rust", name="cargo-target", seed_dur=15, measure_dur=14)

# Python: PY-G01/PY-G02 good (clean hits); PY-B01 bad (restore≠save key -> permanent miss);
# PY-B02 bad (saved, but a much larger archive than PY-G01 for the same deps).
kb_fixture("PY-G01", restore_hit="exact", stack="python", name="pip-cache", seed_dur=10, measure_dur=3)
kb_fixture("PY-G02", restore_hit="exact", stack="python", name="poetry-cache", seed_dur=10, measure_dur=3)
kb_fixture("PY-B01", restore_hit="false", stack="python", name="poetry-cache", seed_dur=10, measure_dur=10)
kb_fixture("PY-B02", restore_hit="exact", stack="python", name="pip-venv", seed_dur=10, measure_dur=9)

# Maven: MVN-G01 good (clean hit); MVN-B01 bad (stale "hit", key never saw the submodule's dep
# change); MVN-B02 bad (saved, just a bigger archive).
kb_fixture("MVN-G01", restore_hit="exact", stack="jvm-maven", name="m2-repo", seed_dur=12, measure_dur=4)
kb_fixture("MVN-B01", restore_hit="exact", stack="jvm-maven", name="m2-repo", seed_dur=12, measure_dur=11)
kb_fixture("MVN-B02", restore_hit="exact", stack="jvm-maven", name="m2-repo", seed_dur=12, measure_dur=5)

print("fixtures written")
