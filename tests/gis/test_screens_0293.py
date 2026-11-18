"""ADR 0293: noise barrier style from data (A) and the painted strip beside motorway / expressway lanes (B).

Synthetic checks (no Data/raw) plus checks of the generated QA of the tiles rebuilt with ADR 0293 (skipped when the
tile was not built with it)."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from shapely.geometry import Polygon

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

from roads import gores as GO  # noqa: E402
from roads import meshing as M  # noqa: E402
from roads import standards as S  # noqa: E402
from streetscape import furniture as FU  # noqa: E402


class _Lin(FU.Lin):
    def __init__(self):
        super().__init__(M.MeshBuf(), lambda e, n: np.zeros_like(np.asarray(e, float)))


def test_material_tag_decides_first():
    assert FU.noise_material_style({"barrier": "wall", "wall": "noise_barrier", "material": "glass"}) == "clear"
    assert FU.noise_material_style({"material": "Acrylic_Glass"}) == "clear"
    assert FU.noise_material_style({"material": "concrete"}) == "solid"
    assert FU.noise_material_style({"material": "wood"}) == "solid"
    assert FU.noise_material_style({"barrier": "wall", "wall": "noise_barrier"}) is None
    assert FU.noise_material_style({"material": "unknown_stuff"}) is None


def test_clear_style_is_glass_from_the_plinth_in_light_frames():
    P = np.column_stack([np.linspace(0.0, 12.0, 7), np.zeros(7)])
    st = dict(FU.NOISE_STYLES["clear"], name="clear")
    lin = _Lin()
    FU.noise_wall(lin, P, np.zeros(7), st, 4.0, "t")
    mats = {p.mat for p in lin.buf.parts}
    assert "noise_glass" in mats and "noise_post_light" in mats
    assert "noise_panel_dark" not in mats                    # no cassette band
    glass = np.concatenate([p.V for p in lin.buf.parts if p.mat == "noise_glass"])
    assert abs(glass[:, 2].min() - (st["plinth_m"] + 0.06)) < 1e-6 and abs(glass[:, 2].max() - 4.0) < 1e-6
    # framed panels ~rail_m high: bottom frame + intermediate rails + top rail
    rails = [p for p in lin.buf.parts if p.mat == "noise_post_light" and p.layer == "furniture"
             and np.ptp(p.V[:, 2]) < 0.2]
    zs = sorted({round(float(p.V[:, 2].mean()), 1) for p in rails})
    n_mid = max(1, int(round((4.0 - st["plinth_m"] - 0.06) / st["rail_m"]))) - 1
    assert min(zs) <= st["plinth_m"] + 0.15 and max(zs) >= 3.9, zs          # bottom frame on the plinth, top rail
    assert len([z for z in zs if 1.0 < z < 3.5]) == n_mid, zs


def test_express_main_by_class_or_number():
    sec = lambda **k: SimpleNamespace(**{"highway": "trunk", "cls": "GP", "ref": None, **k})  # noqa: E731
    assert S.is_express_main(sec(highway="motorway", cls="A"))
    assert S.is_express_main(sec(ref="S8"))
    assert S.is_express_main(sec(ref="8;S19"))
    assert not S.is_express_main(sec(highway="motorway_link", cls="A"))
    assert not S.is_express_main(sec(ref="8;65"))
    assert not S.is_express_main(sec())


def test_long_strip_cut_into_pieces():
    strip = Polygon([(0, 0), (200, 0), (200, 2.5), (0, 2.0)])
    parts = GO._chunks(strip, GO.EXPRESS_CHUNK_M)
    assert len(parts) == int(round(200 / GO.EXPRESS_CHUNK_M))
    assert abs(sum(p.area for p in parts) - strip.area) < 1e-6
    assert GO._chunks(Polygon([(0, 0), (10, 0), (10, 2), (0, 2)]), GO.EXPRESS_CHUNK_M)[0].area == 20.0


def test_p21_zones_merge_the_pieces_of_one_strip():
    gp = GO.GorePlan()
    for k in range(5):        # plan() leaves 0.05 m between the pieces
        gp.gores.append(GO.Gore(Polygon([(12 * k + 0.05 * (k > 0), 0), (12 * k + 12, 0), (12 * k + 12, 2),
                                         (12 * k + 0.05 * (k > 0), 2)]), "express", hatch=True, built=True))
    gp.gores.append(GO.Gore(Polygon([(0, 50), (10, 50), (10, 52), (0, 52)]), "merge", built=True))
    z = GO.p21_zones(gp)
    assert len(z) == 1 and z[0]["kind"] == "painted_zone" and z[0]["border"] is False
    assert abs(Polygon(z[0]["polygon_en"]).area - 120.0) < 0.5


def _qa(region, name):
    p = REPO / "Data" / "Regions" / region / "generated" / name
    if not p.exists():
        pytest.skip(f"{region}: {name} not built")
    return json.loads(p.read_text(encoding="utf-8"))


def test_dk65_01_s8_lanes_are_painted_not_kerbed():
    g = _qa("dk65-01", "roads_qa.json")["summary"]
    if "express" not in g["gores"]["paved"]:
        pytest.skip("dk65-01 not rebuilt with ADR 0293")
    assert g["gores"]["paved"]["express"]["area_m2"] > 1500
    rej = [r for r in g["gores"]["rejected"] if r["why"] == "express"]
    assert sum(r["area_m2"] for r in rej) < 0.05 * g["gores"]["paved"]["express"]["area_m2"]
    assert g["markings"].get("gore_p21", {}).get("built", 0) >= 1


def test_maczka_city_barriers_are_clear():
    nb = _qa("bialystok-maczka", "streetscape_qa.json")
    nb = nb.get("furniture", nb).get("noise_barriers")
    if not nb or "style_rule_m" not in nb:
        pytest.skip("bialystok-maczka not rebuilt with ADR 0293")
    assert nb["m_by_style"].get("clear", 0) > 0.8 * sum(nb["m_by_style"].values())
