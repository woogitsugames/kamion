"""ADR 0348 (neon-windows-s24): rural / Tykocin house windows (8-12 cm reveal, 3D PVC/wood frame + mullion/transom,
bright exterior sill, sky-reflecting glass), facades (0.3-0.6 m darker/stone plinth, subtle sill runoff, 2-3 plaster
shades from seed via _FACADE_TINT), and >= 4 rural fence variants without repetitive yellow pickets."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import box

from roads import pipeline
from streetscape import buildings_mesh as BM
from streetscape import facade_atlas as FA
from streetscape import materials as MT
from streetscape import plot_kit as PK
from streetscape import plots as PL
from test_buildings_0167 import _Buf, _HF

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "art-source/world/materials/_src"))

DW09_DIR = ROOT / "Data/Regions/dw671-tykocin-09"
DW09_ORIGIN = (751371.0, 602367.0)


class _ColBuf:
    """Buffer recording COLOR_0 and UV1 alongside geometry."""

    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, src="", UV1=None, COL=None):
        self.parts.append({
            "layer": layer,
            "mat": mat,
            "V": np.asarray(V, float),
            "UV": np.asarray(UV, float),
            "T": np.asarray(T, np.int64).reshape(-1, 3),
            "src": src,
            "UV1": None if UV1 is None else np.asarray(UV1, float),
            "COL": None if COL is None else np.asarray(COL, float),
        })


def test_dw671_09_enables_small_town_and_reveal_plinth_ranges():
    fc = json.loads((DW09_DIR / "buildings.geojson").read_text(encoding="utf8"))
    ovs = pipeline.load_overrides("dw671-tykocin-09")
    blds = BM.load(fc, DW09_ORIGIN, ovs)
    assert len(blds) >= 80
    assert all(b.get("small_town") is True for b in blds)
    assert all(b.get("small_town_roofs") is False for b in blds)
    assert 0.08 <= BM.REVEAL_SMALL_TOWN <= 0.12
    assert 0.08 <= BM.REVEAL_SMALL_TOWN_WOOD <= 0.12
    assert all(0.30 <= h <= 0.60 for h in BM.SMALL_TOWN_PLINTH_HS)


def test_house_window_atlas_has_sky_reflection_and_crisp_frames():
    import sets_buildings as SB
    px = 0.005
    for i in range(4):
        p = SB.paint_cell("house", i, px)
        # Glass interior (middle of panes) must not be a pitch-black hole: blue-tinted sky reflection present
        mid = p.alb[p.ny // 5: 4 * p.ny // 5, p.nx // 5: 4 * p.nx // 5]
        # Low-roughness glass pixels exist and carry sky-blue reflection (B > R on open sky-reflecting glass)
        rgh_mid = p.rgh[p.ny // 5: 4 * p.ny // 5, p.nx // 5: 4 * p.nx // 5]
        glass = mid[rgh_mid < 0.25]
        assert len(glass) > 50, f"house variant {i} missing smooth glass"
        assert float(glass.mean()) > 0.045, f"house variant {i} glass too dark ({glass.mean():.4f})"
        # Height relief between outer frame (0.0) and recessed glass (< -0.045) feeds crisp normal map
        assert float(p.hgt.max() - p.hgt.min()) >= 0.05
    # Engine sky_occ on facade_atlas lets horizontal reflections catch live sky probe
    assert MT.M["facade_atlas"]["sky_occ"][1] <= 0.45


def test_rural_house_3d_frame_bright_sill_and_multishade_plaster():
    fc = json.loads((DW09_DIR / "buildings.geojson").read_text(encoding="utf8"))
    ovs = pipeline.load_overrides("dw671-tykocin-09")
    blds = BM.load(fc, DW09_ORIGIN, ovs)
    houses = [b for b in blds if b["typ"] == "house" and b["poly"].area > 80][:25]
    buf = _ColBuf()
    rep = {}
    BM.build(buf, houses, _HF, lambda e, n: 100.0, None, None, rep)
    # 1) 3D window frames reuse facade_atlas swatches (0 extra draws) & bright sills use reveal_plaster
    atlas_parts = [p for p in buf.parts if p["layer"] == "buildings" and p["mat"] == "facade_atlas"]
    assert atlas_parts
    sw_uvs = [FA.CELLS[("sw_" + s, 0)] for s in ("pvc_white", "pvc_brown", "wood")]
    has_3d_sw = False
    for p in atlas_parts:
        assert len(p["UV"]) % 4 == 0
        for u0, v0, w, h in sw_uvs:
            if np.any((p["UV"][:, 0] >= u0) & (p["UV"][:, 0] <= u0 + w)
                      & (p["UV"][:, 1] >= v0) & (p["UV"][:, 1] <= v0 + h)):
                has_3d_sw = True
    assert has_3d_sw, "expected 3D window frame / mullion / transom quads mapped to facade_atlas swatches"
    # 2) Plaster walls on small_town houses carry 2-3 deterministic COLOR_0 shades per house
    plaster_by_src = {}
    for p in buf.parts:
        if p["layer"] == "buildings" and p["mat"].startswith("plaster_") and p["COL"] is not None:
            cols = np.round(p["COL"][p["COL"][:, 3] > 0.5, :3], 3)
            if len(cols):
                plaster_by_src.setdefault(p["src"], set()).update(map(tuple, cols.tolist()))
    assert plaster_by_src, "expected COLOR_0 plaster shades on rural houses"
    multi = [s for s, cs in plaster_by_src.items() if len(cs) >= 2]
    assert len(multi) >= int(0.7 * len(plaster_by_src)), f"expected >=70% houses with >=2 plaster shades, got {len(multi)}/{len(plaster_by_src)}"
    # 3) Shader & importer wire _FACADE_TINT cleanly
    pbr = (ROOT / "game/Assets/_Project/Environment/Shaders/WorldPBR.shader").read_text(encoding="utf8")
    imp = (ROOT / "game/Assets/_Project/World/Import/WorldPbrMaterials.cs").read_text(encoding="utf8")
    assert "_FACADE_TINT" in pbr and "_FACADE_TINT" in imp and "facade_tint" in imp
    assert MT.M["plaster_cream"].get("facade_tint") is True and MT.M["plinth_dark"].get("facade_tint") is True


def test_gable_attic_window_has_uniform_gable_tint():
    """ADR 0348 r2: splitting the attic-window column at eave zt prevents a vertical colour seam on gables."""
    b = {"id": "test:gable-seam", "poly": box(0, 0, 10, 8),
         "props": {"storeys": 2, "height_m": 7.4, "roof_shape": "gable"},
         "ovr": {"wall_material": "plaster_cream"}, "typ": "house", "sub": "dom", "small_town": True, "small_town_roofs": False}
    buf = _ColBuf()
    BM.build(buf, [b], _HF, lambda e, n: 100.0, None, None, {})
    # Above eave zt (~104.7 m) on each gable face (x ~ 0 or x ~ 10), all plaster vertices must carry one uniform shade
    plaster = [p for p in buf.parts if p["layer"] == "buildings" and p["mat"] == "plaster_cream" and p["COL"] is not None]
    assert plaster
    for gx in (0.0, 10.0):
        shades_above = set()
        for p in plaster:
            V, C = p["V"], p["COL"]
            for tri in p["T"]:
                pts = V[tri]
                if np.all(np.abs(pts[:, 0] - gx) < 0.05) and pts[:, 2].min() > 105.0:
                    shades_above.add(tuple(np.round(C[tri[0], :3], 3).tolist()))
        assert len(shades_above) <= 1, f"vertical tint seam on gable x={gx}: {shades_above}"


def test_rural_fences_four_variants_no_yellow_and_anti_repeat():
    # No loud yellow-ochre paint in PICKET_PAINTS (R >> B with high R and G)
    for rgb, _ in PL.PICKET_PAINTS:
        r, g, b = rgb
        assert not (r > 0.65 and g > 0.40 and b < 0.25), f"loud yellow-ochre picket paint found: {rgb}"
        assert max(rgb) <= 0.70, f"picket paint too bright/garish: {rgb}"
    # Street of 16 rural single-family plots along one road
    road = box(-20, -6, 360, 0)
    houses = [{"id": f"rural:{k:03d}", "poly": box(20 * k, 6, 20 * k + 10, 14),
               "props": {"storeys": 1 if k % 3 != 0 else 2, "height_m": 5.5 if k % 3 != 0 else 8.0}}
              for k in range(16)]
    plots = PL.plan(houses, road, [], [])
    assert len(plots) == 16
    styles = [p["front_style"] for p in plots]
    fams = {PL._fence_family(s) for s in styles}
    # At least 4 distinct fence families (picket, chainlink, panel, masonry) + no adjacent identical front style
    assert len(fams) >= 4, f"expected >= 4 fence families, got {fams} ({styles})"
    adj_same = sum(1 for a, b in zip(styles, styles[1:]) if a == b)
    assert adj_same == 0, f"adjacent plots repeated identical front_style: {styles}"
    # New stone_picket / stone_bars / panel_graphite / panel_green / picket_raw build cleanly in plot_kit (0 new mats)
    for st in ("picket_raw", "panel_graphite", "panel_green", "stone_picket", "stone_bars"):
        assert st in PL.STYLES
        kit = PL.Kit((0.8, 0.8, 0.8))
        PL.fence_run(kit, st, np.array([0.0, 0.0]), np.array([12.0, 0.0]), np.array([0.0, 1.0]), 1.4, lambda p: 0.0, "plot9")
        out = kit.out()
        assert out is not None and len(out[2]) > 0
        assert out[1][:, 1].min() >= 0.0 and out[1][:, 1].max() <= 1.0
