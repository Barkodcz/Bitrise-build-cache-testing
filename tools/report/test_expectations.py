"""Unit tests for tools/report/expectations.py. Run via `make test` (pytest)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expectations import build_view, check  # noqa: E402


def test_simple_ge():
    view = {"gradle": {"from_cache_share": 0.8}}
    ok, _ = check("gradle.from_cache_share", ">= 0.6", view)
    assert ok


def test_simple_lt_fails():
    view = {"gradle": {"from_cache_share": 0.8}}
    ok, _ = check("gradle.from_cache_share", "< 0.2", view)
    assert not ok


def test_missing_path_fails_numeric_but_not_absent():
    view = {"gradle": {}}
    ok, _ = check("gradle.from_cache_share", ">= 0.6", view)
    assert not ok
    ok, _ = check("gradle.from_cache_share", "absent", view)
    assert ok


def test_in_operator():
    view = {"key_based": {"restore_hit": "exact"}}
    ok, _ = check("key_based.restore_hit", 'in ["exact"]', view)
    assert ok
    ok, _ = check("key_based.restore_hit", 'in ["partial", "false"]', view)
    assert not ok


def test_build_view_duration_vs_seed():
    measure = {"durations_s": {"build_step": 100.0}, "key_based": [], "remote_cache": None}
    seed = {"durations_s": {"build_step": 200.0}}
    view = build_view(measure, seed)
    assert view["duration"]["vs_seed"] == 0.5


def test_build_view_no_seed():
    measure = {"durations_s": {"build_step": 100.0}, "key_based": [], "remote_cache": None}
    view = build_view(measure, None)
    assert view["duration"]["vs_seed"] is None


def test_build_view_cache_alias():
    measure = {"remote_cache": {"download_upload_ratio": 5.0}, "key_based": []}
    view = build_view(measure, None)
    ok, _ = check("cache.download_upload_ratio", ">= 2", view)
    assert ok
