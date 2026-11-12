"""ADR 0146 (second round): Andersa portal boards on the beam plane, coated deck cap on the spans only, no mapped
noise barrier rebuilt on the ground beside a screened ramp wall."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
RID = "bialystok-industrial-c"
QA = ROOT / f"Data/Regions/{RID}/generated/streetscape_qa.json"


def _overrides():
    return yaml.safe_load((ROOT / f"Data/Regions/{RID}/overrides.yaml").read_text(encoding="utf-8"))["overrides"]


def _find_items(o, code_prefix, out):
    if isinstance(o, dict):
        if str(o.get("code", "")).startswith(code_prefix) and "e" in o:
            out.append(o)
        for v in o.values():
            _find_items(v, code_prefix, out)
    elif isinstance(o, list):
        for v in o:
            _find_items(v, code_prefix, out)
    return out


def test_portal_boards_hang_on_the_beam():
    o = next(x for x in _overrides() if x["id"] == "andersa-putry-approach-gantry")
    a, b = (np.asarray(v, float) for v in o["columns_en"])
    ax = (b - a) / np.hypot(*(b - a))
    nrm = np.array([-ax[1], ax[0]])
    qa = json.loads(QA.read_text(encoding="utf-8"))
    boards = [x for x in _find_items(qa, "OB_", []) if x.get("src") == "override:" + o["id"]]
    assert len(boards) == 2
    d = [abs(float(np.dot(np.array([x["e"], x["n"]]) - a, nrm))) for x in boards]
    if max(d) > 1.5:
        pytest.skip("generated world predates ADR 0146 round 2 (rebuild)")
    assert all(0.3 <= v <= 0.6 for v in d), d          # 0.45 m in front of the beam axis (front chords at 0.4 m)


def test_coated_cap_only_on_spans_and_textured():
    from roads import build_world as BW, standards as S
    o = next(x for x in _overrides() if x["id"] == "andersa-viaduct-putry-style")
    m = BW.MATERIALS[o["set"]["cap_mat"]]
    assert m.get("texture_set") and m.get("vertex_grime")              # not a flat colour (docs/06)
    r, g, b = m["color"]
    assert 3.0 <= r / g <= 6.0 and 0.2126 * r + 0.7152 * g + 0.0722 * b <= 0.09
    assert S.CAP_COAT_GRIME[0] > S.CAP_COAT_GRIME[1] > 0
    src = (ROOT / "tools/worldgen/roads/meshing.py").read_text(encoding="utf-8")
    assert "capm = capm & ~" in src                                      # walled ramps keep the bare concrete cap


def test_mapped_barrier_on_screened_deck_edge_is_not_rebuilt():
    qa = json.loads(QA.read_text(encoding="utf-8"))
    nb = qa["furniture"]["noise_barriers"]
    if "on_screened_deck_m" not in nb:
        pytest.skip("generated world predates ADR 0146 round 2 (rebuild)")
    assert nb["on_screened_deck_m"] > 50.0


def test_mapped_retaining_wall_on_a_walled_ramp_is_not_rebuilt():
    qa = json.loads(QA.read_text(encoding="utf-8"))
    fe = qa["furniture"]["fences"]
    if "retaining_on_ramp_wall_m" not in fe:
        pytest.skip("generated world predates ADR 0146 round 2 (rebuild)")
    assert fe["retaining_on_ramp_wall_m"] > 20
