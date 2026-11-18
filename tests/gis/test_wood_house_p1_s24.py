"""knyszyn-p1-s24 (ADR 0295, review 2026-11-18): boarded wooden houses (P1-1 corner boards, battens, drip board,
vertical gable boarding, opening surrounds; P1-2 boarding runs shorter than the plank tile, each with its own UV
phase) and the farmland mosaic of the terrain dryness mask (P1-4)."""
import json
from pathlib import Path

import numpy as np
import pytest

from roads import pipeline
from streetscape import buildings_mesh as BM
from streetscape import materials as MT
from streetscape import vegetation as VG
from test_buildings_0167 import _build

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "Data/Regions/knyszyn"
ORIGIN = (761611.0, 612607.0)
KLATT = "bdot:2002917F-2F22-5C99-E053-CC2BA8C01CFC"
NO_SRC = {"bdot10k": {"OT_PTTR_A": [], "OT_PTNZ_A": []}, "osm": {"areas": []}}


@pytest.fixture(scope="module")
def blds():
    fc = json.loads((R / "buildings.geojson").read_text(encoding="utf8"))
    return {b["id"]: b for b in BM.load(fc, ORIGIN, pipeline.load_overrides("knyszyn"))}


def _wood_parts(buf, layer="buildings"):
    return [p for p in buf.parts if p.layer == layer and str(p.mat).startswith("wood_planks")]


def test_material_tile_matches_the_generator_constants():
    for m in ("wood_planks", "wood_planks_green"):
        assert tuple(MT.M[m]["set_tile_m"]) == BM.WOOD_TILE_M
    assert "texture_set" not in MT.M[BM.WOOD_TRIM_MAT]            # a flat paint colour: no set, no tiling
    assert max(MT.M[BM.WOOD_TRIM_MAT]["color"]) < MT.M["soffit_boards"]["color"][0]   # review: not "plastic white"
    j = np.asarray(BM.WOOD_JOINT_V)
    assert len(j) == 19 and np.all(np.diff(j) > 0.04) and np.all(np.diff(j) < 0.065)


def test_joint_table_matches_the_built_set():
    png = ROOT / "art-source/world/materials/wood_siding/High/T_wood_siding_BaseColor.png"
    if not png.exists():
        pytest.skip("wood_siding not built")
    from PIL import Image
    from scipy.ndimage import median_filter
    im = np.asarray(Image.open(png).convert("L"), float) / 255
    row = im.mean(1)
    dip = median_filter(row, size=25, mode="wrap") - row            # joints = dark rows
    n = len(row)
    hit = 0
    for v in BM.WOOD_JOINT_V:
        i = int(round((1 - v) * n - 0.5)) % n
        hit += max(dip[(i + k) % n] for k in range(-4, 5)) > 2.0 * np.median(np.abs(dip))
    assert hit >= 16                                                # 2 of the 19 joints are faint in the scan


def test_dom_klattow_has_the_boards_of_a_podlasie_house(blds):
    buf = _build(blds[KLATT])
    assert BM.WOOD_TRIM_MAT in {p.mat for p in buf.parts if p.layer == "buildings"}              # opening surrounds
    assert BM.WOOD_TRIM_MAT not in {p.mat for p in buf.parts if p.layer == "buildings_low"}      # LOD0 detail only
    V = np.concatenate([np.asarray(p.V)[np.asarray(p.T)].reshape(-1, 3, 3) for p in _wood_parts(buf)])
    UV = np.concatenate([np.asarray(p.UV)[np.asarray(p.T)].reshape(-1, 3, 2) for p in _wood_parts(buf)])
    nrm = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0])
    area2 = np.linalg.norm(nrm, axis=1)
    wall = (np.abs(nrm[:, 2]) < 1e-6 * np.maximum(area2, 1e-12)) & (area2 > 1.0)
    dz = np.ptp(V[:, :, 2], axis=1)
    du, dv = np.ptp(UV[:, :, 0], axis=1), np.ptp(UV[:, :, 1], axis=1)
    up = wall & (dz > 0.8) & (np.abs(du - dz) < 1e-6)          # boards run up: UV0.u spans exactly the height
    along = wall & (dz > 0.8) & (np.abs(dv - dz) < 1e-6)       # boards run along the wall: UV0.v spans the height
    assert up.sum() >= 2 and along.sum() >= 4
    zeave = np.percentile(V[along][:, :, 2].max(1), 50)
    assert V[up][:, :, 2].min() >= zeave - 0.2                 # the vertical boarding starts at the eave line


def test_boarding_runs_are_shorter_than_the_tile():
    for L in (5.0, 7.3, 12.0, 20.4, 33.0):
        ops = [(2.0, 3.2, 1.0, 2.4, 0.2, "window", "x"), (L - 3.0, L - 1.8, 1.0, 2.4, 0.2, "window", "x")] if L > 7 else []
        us = [0.0] + BM.wood_runs(L, ops, f"k{L}") + [L]
        runs = np.diff(us)
        assert runs.max() < BM.WOOD_TILE_M[0], (L, runs)             # no run shows the plank tile twice
        for u in us[1:-1]:
            assert all(not (o[0] - BM.WOOD_SURROUND_W - 0.05 < u < o[1] + BM.WOOD_SURROUND_W + 0.05) for o in ops)
    phases = {BM.wood_phase("house-a:0", j) for j in range(6)} | {BM.wood_phase("house-b:0", j) for j in range(6)}
    assert len(phases) >= 10                                         # runs and houses do not share a phase
    assert all(abs(dv / BM.WOOD_ROW_M - round(dv / BM.WOOD_ROW_M)) < 1e-9 for _, dv in phases)   # whole board rows


def test_wooden_houses_of_knyszyn_report_no_run_over_the_tile(blds):
    from shapely.geometry import box
    from test_buildings_0167 import _Buf, _HF
    wooden = [b for b in blds.values() if b["typ"] == "house" and b["ovr"].get("typology") == "dom_drewniany"]
    assert wooden
    buf, rep = _Buf(), {}
    BM.build(buf, wooden, _HF, None, None, box(-5000, -5000, -4990, -4990), rep, sign_out=[])
    w = rep["wooden_houses"]
    assert w["boarding_runs"] >= 4 * len(wooden) and w["runs_over_tile"] == 0
    assert w["longest_run_m"] < BM.WOOD_TILE_M[0]
    assert 100 <= w["board_tris_lod0"] <= 1500 * len(wooden)        # boards on top: a few hundred triangles a house


def test_board_takes_one_row_of_the_set():
    acc = BM.Acc()
    n = BM.wood_board(acc, "wood_planks", np.zeros(2), np.array([1.0, 0.0]), np.array([0.0, -1.0]), 0.0, 0.14, 0.5, 3.0,
                      0.03, "k")
    assert n == 8
    V, _, UV, _ = acc.d[("buildings", "wood_planks")][0]            # the face quad
    v = UV[:, 1] / BM.WOOD_TILE_M[1]
    j = np.asarray(BM.WOOD_JOINT_V + (BM.WOOD_JOINT_V[0] + 1.0,))
    assert not np.any((j > v.min() + 1e-9) & (j < v.max() - 1e-9))   # no joint line runs along the board face
    assert abs(np.ptp(UV[:, 0]) - 2.5) < 1e-9                        # grain along the board (upright: u = height)
    assert np.allclose(V[:, 1], -0.03)                               # 3 cm proud of the wall (outwards = -y here)


class _Hf:
    def __init__(self, n=600, x0=-300.0, y1=300.0):
        self.z = np.zeros((n, n))
        self.x0, self.y1 = x0, y1


def test_field_ids_depend_on_the_position_only():
    x = np.linspace(760000.0, 761000.0, 301)[None, :] + np.zeros((201, 1))
    y = np.linspace(612000.0, 612600.0, 201)[:, None] + np.zeros((1, 301))
    f0, b0 = VG.field_ids(x, y)
    f1, b1 = VG.field_ids(x[50:120, 100:200], y[50:120, 100:200])   # the window of another tile on the same ground
    assert np.array_equal(f0[50:120, 100:200], f1) and np.array_equal(b0[50:120, 100:200], b1)
    assert 4 <= len(np.unique(b0)) <= 40 and len(np.unique(f0)) > 3 * len(np.unique(b0))


def test_farmland_mask_is_a_flag_for_the_per_pixel_mosaic():
    """ADR 0298: fields carry the farmland flag (the shader draws the mosaic per pixel); other ground never reaches it."""
    hf = _Hf()
    sq = [[[-250.0, -250.0], [250.0, -250.0], [250.0, 250.0], [-250.0, 250.0], [-250.0, -250.0]]]
    src = {"bdot10k": {"OT_PTTR_A": [{"geometry": {"type": "Polygon", "coordinates": sq},
                                      "props": {"rodzaj": "roślinność trawiasta"}}], "OT_PTNZ_A": []},
           "osm": {"areas": []}}
    arable = {"bdot10k": {"OT_PTTR_A": [{"geometry": {"type": "Polygon", "coordinates": sq},
                                         "props": {"rodzaj": "uprawa na gruntach ornych"}}], "OT_PTNZ_A": []},
              "osm": {"areas": []}}
    rep = {}
    far = np.full(hf.z.shape, 100.0)
    C = VG.ground_masks(src, (0.0, 0.0), hf, far, [], report=rep)
    C0 = VG.ground_masks(NO_SRC, (0.0, 0.0), hf, far, [])
    b, b0 = C[100:500, 100:500, 2], C0[100:500, 100:500, 2]
    assert np.allclose(b, VG.FIELD_FLAG_B["roślinność trawiasta"], atol=1e-4)      # one flag over the whole field
    assert np.allclose(VG.ground_masks(arable, (0.0, 0.0), hf, far, [])[100:500, 100:500, 2], 1.0, atol=1e-4)
    assert b0.max() <= VG.GROUND_B_MAX + 1e-6                                        # open ground never reads as a flag
    assert rep["farmland"]["share"] > 0.6 and "flag" in rep["farmland"]["encoding"]
    assert np.array_equal(C[..., [0, 1, 3]], C0[..., [0, 1, 3]])     # road distance, forest floor, bare soil untouched
    near = np.full(hf.z.shape, 2.0)                                  # beside a road the verge rule stays
    assert np.array_equal(VG.ground_masks(src, (0.0, 0.0), hf, near, [])[..., 2],
                          VG.ground_masks(NO_SRC, (0.0, 0.0), hf, near, [])[..., 2])


def test_field_mosaic_shader_matches_the_python_reference_layout():
    """KamionFieldMosaic.hlsl ports field_ids (salts 911-929, 300 m blocks, 22-46 m strips); keep both in step."""
    src = (ROOT / "game/Assets/_Project/Environment/Shaders/KamionFieldMosaic.hlsl").read_text(encoding="utf-8")
    for token in ("911u", "913u", "917u", "919u", "923u", "929u", "1597334677u", "3812015801u", "2246822519u"):
        assert token in src, token
    assert f"#define KF_BLOCK_M {VG.FIELD_BLOCK_M:.1f}" in src
    assert f"#define KF_STRIP_MIN_M {VG.FIELD_STRIP_M[0]:.1f}" in src
    assert f"#define KF_STRIP_SPAN_M {VG.FIELD_STRIP_M[1] - VG.FIELD_STRIP_M[0]:.1f}" in src


def test_gardens_of_residential_land_are_calmer_than_open_ground():
    hf = _Hf()
    sq = [[[-250.0, -250.0], [250.0, -250.0], [250.0, 250.0], [-250.0, 250.0], [-250.0, -250.0]]]
    src = {"bdot10k": {"OT_PTTR_A": [], "OT_PTNZ_A": [],
                       "OT_PTZB_A": [{"geometry": {"type": "Polygon", "coordinates": sq}, "props": {"rodzaj": "jednorodzinna"}}]},
           "osm": {"areas": []}}
    ind = {"bdot10k": {"OT_PTTR_A": [], "OT_PTNZ_A": [],
                       "OT_PTZB_A": [{"geometry": {"type": "Polygon", "coordinates": sq}, "props": {"rodzaj": "przemysłowo-składowa"}}]},
           "osm": {"areas": []}}
    far = np.full(hf.z.shape, 100.0)
    rep = {}
    b = VG.ground_masks(src, (0.0, 0.0), hf, far, [], report=rep)[100:500, 100:500, 2]
    b0 = VG.ground_masks(NO_SRC, (0.0, 0.0), hf, far, [])[100:500, 100:500, 2]
    assert b.max() <= VG.GARDEN_B[0] + VG.GARDEN_B[1] + 1e-6 and b.std() < 0.4 * b0.std() and b.mean() < 0.6 * b0.mean()
    assert rep["farmland"]["garden_cells_m2"] > 200000
    assert np.array_equal(VG.ground_masks(ind, (0.0, 0.0), hf, far, []), VG.ground_masks(NO_SRC, (0.0, 0.0), hf, far, []))
