"""compare_plots.py diff (D34): identical dumps -> no change; a moved vertex / a lost gate are reported."""
import copy
import json
import pickle
import subprocess
import sys
from pathlib import Path

from shapely.geometry import Polygon

QA = Path(__file__).resolve().parents[1] / "qa" / "compare_plots.py"


def _dump(path, dx=0.0, gate=True):
    poly = Polygon([(0, 0), (10 + dx, 0), (10 + dx, 8), (0, 8)])
    lay = {"runs": [{"style": "picket", "h": 1.3, "a": [0.0, 0.0], "b": [10.0 + dx, 0.0], "front": True}],
           "gate": {"m": [5.0, 0.0], "w": 3.5, "kind": "swing"} if gate else None, "wicket": None, "wickets": [],
           "stubs_dropped": 0, "teeth_bridged": 0}
    d = {"plots": [{"id": "h1", "wkb": poly.wkb, "coords": list(poly.exterior.coords), "area": poly.area, "age": "prl",
                    "front_style": "picket", "lay": lay, "access": None}],
         "drops": [], "astats": {}, "T": {"plan": [1, 0.1]}}
    path.write_bytes(pickle.dumps(d))
    return path


def _diff(a, b):
    out = subprocess.run([sys.executable, str(QA), "diff", str(a), str(b)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_identical(tmp_path):
    r = _diff(_dump(tmp_path / "a.pkl"), _dump(tmp_path / "b.pkl"))
    assert r["poly_bytes_same"] == 1 and r["poly_bytes_diff"] == 0 and r["layout_diff"] == 0 and r["gate_changed"] == []


def test_reports_moved_vertex_and_lost_gate(tmp_path):
    r = _diff(_dump(tmp_path / "a.pkl"), _dump(tmp_path / "b.pkl", dx=1e-4, gate=False))
    assert r["poly_bytes_diff"] == 1 and abs(r["hausdorff_m"]["p100"] - 1e-4) < 1e-9
    assert r["gate_changed"] == ["h1"] and r["gates"] == [1, 0] and r["run_endpoint_max_diff_m"] > 0
