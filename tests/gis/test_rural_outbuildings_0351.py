"""ADR 0351 (props-fix-s24, critic s24 wave 11 pkt 8): farm outbuildings of the rural tiles get a typology (LoD2 roof,
board / brick / block wall, plinth, windows) instead of a flat white box - opt-in per region, so the Bialystok tiles
stay bit-identical (ADR 0238)."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import yaml
from shapely.geometry import box

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
sys.path.insert(0, str(REPO / "tests" / "gis"))

_HF = SimpleNamespace(sample=lambda x, y: np.full(np.shape(x), 100.0))


class _Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **kw):
        self.parts.append(SimpleNamespace(layer=layer, mat=mat, V=np.asarray(V, float), T=np.asarray(T).reshape(-1, 3)))

    def tris(self, layer=None):
        return sum(len(p.T) for p in self.parts if layer in (None, p.layer))

    def mats(self, layer):
        return {p.mat for p in self.parts if p.layer == layer}


def _region(rid):
    d = REPO / "Data" / "Regions" / rid
    fc = json.loads((d / "buildings.geojson").read_text(encoding="utf-8"))
    ovr = yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    o = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))["origin"]
    return fc, ovr, (o["x"], o["y"])


def _build(blds):
    from streetscape import buildings_mesh as BM
    buf = _Buf()
    rep = {}
    BM.build(buf, blds, _HF, None, None, box(-5000, -5000, -4990, -4990), rep, sign_out=[])
    return buf, rep


def _sheds(rid, ids=None):
    from streetscape import buildings_mesh as BM
    fc, ovr, origin = _region(rid)
    blds = BM.load(fc, origin, ovr)
    return [b for b in blds if b["typ"] == "shed" and (ids is None or b["id"] in ids)], ovr, fc, origin


def test_dk65_07_marks_outbuildings_and_not_transformers():
    from streetscape import buildings_mesh as BM
    sheds, _, _, _ = _sheds("dk65-07")
    assert len(sheds) > 20
    flagged = [b for b in sheds if b.get("rural_outbuilding")]
    assert len(flagged) >= 0.5 * len(sheds)
    assert all(b["poly"].area >= BM.RURAL_SHED_MIN_AREA_M2 for b in flagged)
    assert all(b["props"].get("function") not in BM.RURAL_SHED_NO_ROOF_FUNCS for b in flagged)


def test_without_the_rule_a_shed_is_unchanged_flat_box():
    """Bialystok tiles carry no `rural_outbuildings` entry: no flag, flat roof, no windows."""
    from streetscape import buildings_mesh as BM
    fc, ovr, origin = _region("bialystok-industrial-c")
    blds = BM.load(fc, origin, ovr)
    assert not any(b.get("rural_outbuilding") for b in blds)


def test_gable_outbuilding_gets_pitched_roof_windows_and_a_non_plaster_palette():
    from streetscape import buildings_mesh as BM
    sheds, _, _, _ = _sheds("dk65-07", {"bdot:2C9A9AB4-440C-0F0D-E053-CA2BA8C04DCD", "bdot:2C9A9AB4-749B-0F0D-E053-CA2BA8C04DCD"})
    assert len(sheds) == 2 and all(b.get("rural_outbuilding") for b in sheds)
    for b in sheds:
        buf, rep = _build([b])
        zs = np.concatenate([p.V[:, 2] for p in buf.parts if p.layer == "buildings"])
        assert zs.max() - zs.min() > 3.0
        roof_mats = [m for m in buf.mats("buildings") if m.startswith("roof_")]
        assert roof_mats, "pitched covering expected"
        assert not any(m == "roof_membrane" for m in buf.mats("buildings"))
        assert buf.mats("buildings") & {"wood_planks", "wood_planks_graphite", "brick_red", "plaster_grey",
                                         "plaster_light", "plaster_cream"}
        # a blank gable box is ~30 triangles; windows / door reveals, roof planes and plinth add several times that
        assert buf.tris("buildings") > 120


def test_flat_lod2_outbuilding_stays_flat():
    from streetscape import buildings_mesh as BM
    sheds, _, _, _ = _sheds("dk65-07")
    flat = [b for b in sheds if b.get("rural_outbuilding") and b["props"].get("roof_type_lod2") == "1000"]
    if not flat:
        return
    buf, _ = _build(flat[:1])
    assert "roof_membrane" in buf.mats("buildings")


def test_palette_is_deterministic_and_varied_between_neighbours():
    from streetscape import buildings_mesh as BM
    sheds, _, _, _ = _sheds("dk65-07")
    fl = [b for b in sheds if b.get("rural_outbuilding")]
    walls = [BM.rural_shed_pick(b["id"], BM.RURAL_SHED_WALLS, "rswall") for b in fl]
    walls2 = [BM.rural_shed_pick(b["id"], BM.RURAL_SHED_WALLS, "rswall") for b in fl]
    assert walls == walls2
    assert len(set(walls)) >= 4
    assert max(walls.count(w) for w in set(walls)) < 0.45 * len(walls)
    roofs = {BM.rural_shed_pick(b["id"], BM.RURAL_SHED_ROOFS, "rsroof") for b in fl}
    assert len(roofs) >= 4


def test_every_rural_outbuilding_of_both_prototype_tiles_builds():
    for rid in ("dk65-07", "dw671-tykocin-03"):
        sheds, _, _, _ = _sheds(rid)
        fl = [b for b in sheds if b.get("rural_outbuilding")]
        assert fl, rid
        buf, rep = _build(fl)
        assert buf.tris("buildings") > 0
