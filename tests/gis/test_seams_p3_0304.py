"""ADR 0304: qa.seams compares the side profile of the SECOND assign_sides pass (the one the generator meshes), and the
measured edge-line spacing at the corridor seams knyszynska | dk65-01 and Knyszyn (orthophoto 0.1 m)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
REG = REPO / "Data" / "Regions"

from tools.worldgen.qa import seams as Q  # noqa: E402


def _route_rows(rep, param_prefix=None):
    for s in rep["seams"]:
        for rd in s["roads"]:
            if not rd["on_route"]:
                continue
            for r in rd["rows"]:
                if param_prefix is None or r["param"].startswith(param_prefix):
                    yield s, rd, r


def test_dk8_kerb_seam_matches_in_the_pass_the_generator_meshes():
    """kleeberga | knyszynska: DK8 (w261104557) beside the added lane w561326924. First pass: the 26 m chain in
    knyszynska lies inside ADJ_NODE_SKIP_M of its merge node, so its edge stays a kerb while kleeberga (no shared node)
    makes it flush -> FAIL. Second pass (junction trims known, pipeline.build) both tiles build the flush edge."""
    tiles = [Q.load_tile(t) for t in ("bialystok-kleeberga", "bialystok-knyszynska")]
    # This regression checks the measured network (D94=0), including every side
    # and position row. Archived D94 build widths describe different geometry;
    # they are assessed by production QA, not this measured cross-section test.
    for t in tiles:
        t.roads_qa = None
    p1 = Q.run(loaded=tiles, base=None, trims=False)
    p2 = Q.run(loaded=tiles, base=None, trims=True)
    assert p2["sides_pass"] == 2 and p1["sides_pass"] == 1
    bad1 = [(rd["osm_way"], r["param"]) for _, rd, r in _route_rows(p1, "pobocze") if r["status"] == "FAIL"]
    bad2 = [(rd["osm_way"], r["param"]) for _, rd, r in _route_rows(p2) if r["status"] == "FAIL"]
    assert (261104557, "pobocze P") in bad1          # the report before ADR 0304
    assert bad2 == []
    rows = {r["param"]: r for _, rd, r in _route_rows(p2) if rd["osm_way"] == 261104557}
    assert rows["pobocze P"]["left"] == rows["pobocze P"]["right"] == "krawężnik (płasko)"
    assert "2. przebieg" in rows["pobocze P"]["source"]


@pytest.mark.parametrize("pair", [("bialystok-knyszynska", "dk65-01"), ("knyszyn-s", "knyszyn"),
                                  ("knyszyn", "knyszyn-w"), ("knyszyn-w", "dk65-monki-01")])
def test_edge_line_spacing_matches_the_reference_at_the_seam(pair):
    rep = Q.run(list(pair), base=None, trims=False)
    refs = [r for _, _, r in _route_rows(rep, "referencja rozstawu linii")]
    assert len(refs) == 2 and all(r["status"] == "OK" for r in refs), refs
    sp = [r for _, _, r in _route_rows(rep, "rozstaw linii krawędziowych")]
    assert sp and all(r["status"] == "OK" and r["left"] == r["right"] for r in sp)
    want = 6.3 if pair[1] == "dk65-01" else 6.8         # orthophoto 0.1 m: 6.4-6.45 (K1 6.2-6.3) / 6.75-6.8
    assert sp[0]["left"] == pytest.approx(want, abs=1e-6)


def test_same_spacing_entry_in_the_four_knyszyn_tiles():
    sets = {}
    for t in ("knyszyn", "knyszyn-w", "knyszyn-s", "dk65-monki-01"):
        ov = yaml.safe_load((REG / t / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
        o = next(o for o in ov if o["id"] == "dk65-edge-line-spacing-0304")
        sets[t] = o["set"]
        assert 27718745 not in o["target"]["osm_way"]    # width profile 6.6 -> 7.5 m keeps the 0.20 m inset
    assert all(s == {"edge_line_spacing": 6.8} for s in sets.values())


@pytest.mark.parametrize("tile", [*(f"dk65-monki-{i:02d}" for i in range(1, 8)), "monki"])
def test_rural_dk65_to_monki_continues_the_same_edge_line_spacing(tile):
    overrides = {o["id"]: o for o in yaml.safe_load(
        (REG / tile / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]}
    width = overrides["dk65-carriageway-width"]
    spacing = overrides["dk65-edge-line-spacing-0304"]
    assert spacing["target"] == width["target"]
    assert spacing["set"] == {"edge_line_spacing": 6.8}


def test_szosa_knyszynska_same_width_in_both_tiles():
    def _set(t, oid):
        ov = yaml.safe_load((REG / t / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
        return next(o for o in ov if o["id"] == oid)["set"]
    assert _set("bialystok-knyszynska", "knyszynska-seam-w-xsec") == _set("dk65-01", "knyszynska-xsec-main") == \
        {"width": 6.7, "edge_lines": "both"}


def test_ortho_sampler_is_bilinear():
    from tools.worldgen.qa import seam_line_ortho as L
    im = np.zeros((4, 4))
    im[:, 2:] = 100.0
    ul = (0.0, 0.4)                       # 4 px of 0.1 m: E 0..0.4, N 0.4..0
    v = L.sample(im, ul, np.array([[0.05, 0.25], [0.2, 0.25], [0.35, 0.25]]))
    assert v == pytest.approx([0.0, 50.0, 100.0])
