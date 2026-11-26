"""Shared dotted-path + operator evaluation for scenario `expectations` (spec §5, §9).

Expectation keys are dotted paths into a *view* over the measure-phase metrics JSON, with two
conveniences layered on top of the raw schema (docs/reference/metrics-schema.json) so the catalog
can stay close to the spec's own illustrative examples:

  - `cache.*`        is an alias for `remote_cache.*`
  - `duration.vs_seed` is computed as measure.durations_s.build_step / seed.durations_s.build_step
                       (falls back to total_workflow if build_step is missing on either side)
  - `key_based.<field>` reads `<field>` off the FIRST entry of the `key_based` array (every
                       scenario implemented so far has exactly one key-based cache entry per phase)

Supported operators: == != < <= > >=, `in [...]`, `exists`, `absent`.
"""
import re


def build_view(measure_metrics, seed_metrics):
    view = dict(measure_metrics)
    view["cache"] = measure_metrics.get("remote_cache") or {}

    duration = {"vs_seed": None}
    if seed_metrics:
        m_dur = (measure_metrics.get("durations_s") or {})
        s_dur = (seed_metrics.get("durations_s") or {})
        m = m_dur.get("build_step") or m_dur.get("total_workflow")
        s = s_dur.get("build_step") or s_dur.get("total_workflow")
        if m is not None and s not in (None, 0):
            duration["vs_seed"] = m / s
    view["duration"] = duration

    kb = measure_metrics.get("key_based") or []
    view["key_based"] = kb[0] if kb else {}

    return view


def get_path(view, dotted_path):
    node = view
    for part in dotted_path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None, False
    return node, True


_OP_RE = re.compile(r"^(==|!=|<=|>=|<|>)\s*(.+)$")
_IN_RE = re.compile(r"^in\s*(\[.*\])$")


def _coerce(value_str):
    value_str = value_str.strip()
    if value_str.lower() in ("true", "false"):
        return value_str.lower() == "true"
    if value_str.lower() == "null":
        return None
    try:
        if "." in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        return value_str.strip('"\'')


def evaluate(expectation, view):
    """Returns (passed: bool, detail: str)."""
    expectation = expectation.strip()

    if expectation == "exists":
        raise ValueError("'exists' needs a path, call evaluate_path instead")

    m = _OP_RE.match(expectation)
    if m:
        op, rhs_str = m.groups()
        return op, _coerce(rhs_str)

    m = _IN_RE.match(expectation)
    if m:
        return "in", eval(m.group(1), {"__builtins__": {}})  # literal JSON-ish list, safe-ish eval

    if expectation in ("exists", "absent"):
        return expectation, None

    raise ValueError(f"cannot parse expectation: {expectation!r}")


def check(path, expectation, view):
    value, found = get_path(view, path)

    if expectation.strip() == "exists":
        ok = found and value is not None
        return ok, f"{path} exists -> {found and value is not None} (value={value!r})"
    if expectation.strip() == "absent":
        ok = (not found) or value is None
        return ok, f"{path} absent -> {ok} (value={value!r})"

    op, rhs = evaluate(expectation, view)

    if not found or value is None:
        return False, f"{path} is missing/null, cannot evaluate '{op} {rhs}'"

    try:
        if op == "==":
            ok = value == rhs
        elif op == "!=":
            ok = value != rhs
        elif op == "<":
            ok = value < rhs
        elif op == "<=":
            ok = value <= rhs
        elif op == ">":
            ok = value > rhs
        elif op == ">=":
            ok = value >= rhs
        elif op == "in":
            ok = value in rhs
        else:
            return False, f"unsupported operator {op!r}"
    except TypeError as e:
        return False, f"type error comparing {value!r} {op} {rhs!r}: {e}"

    return ok, f"{path} = {value!r} {op} {rhs!r} -> {ok}"
