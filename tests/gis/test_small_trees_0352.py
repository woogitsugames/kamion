"""ADR 0352 addendum (garden-trees-s24 / agy-garden-var-s24): small garden trees of the plot kit as forked boughs +
asymmetric clumps, with per-instance scale (0.7-1.3), +-4 deg tilt, 4 forms and per-tree UV1 tint."""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

from streetscape import plantings as PG  # noqa: E402
from streetscape import plot_kit as PK  # noqa: E402
from streetscape import plots as PLT  # noqa: E402
from streetscape import small_trees as ST  # noqa: E402

OLD_YOUNG_TRIS, OLD_ORCHARD_TRIS = 14, 46          # measured on main 9ec10a5a2 (garden_tree full H < 6.5, fruit_tree)


def _tris(kit):
    return sum(len(t) for t in kit.T)


def _split(kit):
    V, UV, T, C = kit.out()
    return V, UV, T, C, C[:, 3] > 0.5


def test_young_tree_budget_forms_and_envelope():
    forms = set()
    shapes = []
    uv1s = set()
    for sp, r, H, cb in (("linden", 1.25, 4.7, 1.6), ("maple", 1.5, 4.6, 1.3), ("birch", 1.2, 5.6, 1.3), ("ash", 1.0, 4.0, 1.3)):
        for k in range(16):
            kit = PLT.Kit()
            forms.add(ST.young_tree(kit, np.zeros(2), 0.0, r, H, cb, sp, PG.HABIT[sp], (sp, k)))
            assert _tris(kit) <= 38                                                # 3 crossed-strip boughs + 6 lobes (<= 44 cap)
            V, UV, T, C, fol = _split(kit)
            uv1 = kit.out_uv1()
            assert uv1 is not None and (uv1[:, 0] > 0.5).all()                     # per-tree tint active
            uv1s.add((round(float(uv1[0, 0]), 3), round(float(uv1[0, 1]), 3)))
            rad = np.hypot(V[fol][:, 0], V[fol][:, 1])
            assert rad.max() <= 1.9 * r, (sp, k, rad.max())
            assert V[fol][:, 2].max() <= H * 1.08 and V[fol][:, 2].min() >= cb - 0.12 * (H - cb) - 0.15
            assert (~fol).sum() >= 12 + 24                                         # 3-sided stem + 3 crossed-strip boughs
            u0, u1, v0, v1 = PK.sprite(PG.HABIT[sp])
            assert ((UV[fol][:, 0] >= min(u0, u1) - 1e-6) & (UV[fol][:, 0] <= max(u0, u1) + 1e-6)).sum() >= 12
            occ = np.linalg.norm(C[fol, :3] * 2 - 1, axis=1)
            assert occ.min() >= 0.6                                                # no dark body
            shapes.append(np.round(np.ptp(V[fol], axis=0) / r, 2).tolist())
    assert forms == set(ST.YOUNG_FORMS) and len(ST.YOUNG_FORMS) == 4
    assert len({tuple(s) for s in shapes}) == len(shapes)                          # no two trees alike
    assert len(uv1s) > 10                                                          # distinct per-tree tints


def test_young_tree_lobes_do_not_cross_on_the_axis_and_are_not_flat():
    kit = PLT.Kit()
    ST.young_tree(kit, np.zeros(2), 0.0, 1.3, 4.8, 1.5, "maple", "crown_round", "x")
    planes = []
    for V, C in zip(kit.V, kit.C):
        if C[0, 3] < 0.5:
            continue
        n0 = np.cross(V[1] - V[0], V[2] - V[0])
        n1 = np.cross(V[2] - V[0], V[3] - V[0])
        n0, n1 = n0 / np.linalg.norm(n0), n1 / np.linalg.norm(n1)
        assert abs(float(n0 @ n1)) < 0.995                                         # twisted: two planes per lobe
        planes.append(V.mean(0))
    assert len(planes) == 6
    d = [np.linalg.norm(a - b) for i, a in enumerate(planes) for b in planes[i + 1:]]
    assert min(d) > 0.15                                                           # no two lobes share a centre


def test_orchard_tree_has_limbs_clumps_and_no_core():
    forms = set()
    for k in range(24):
        kit = PLT.Kit()
        forms.add(PLT.fruit_tree(kit, np.zeros(2), 0.0, 4.2, ("f", k), r=1.7))
        assert _tris(kit) <= 1.5 * OLD_ORCHARD_TRIS and _tris(kit) in (40, 50)
        V, UV, T, C, fol = _split(kit)
        assert kit.out_uv1() is not None
        occ = np.linalg.norm(C[fol, :3] * 2 - 1, axis=1)
        assert occ.min() >= 0.6                                                    # the old _core had 0.22-0.26
        hv0, hv1 = PK.row("hedge")
        assert not ((UV[fol][:, 1] >= hv0) & (UV[fol][:, 1] <= hv1)).any()         # no dense hedge row (= the core's texture)
        n_limbs = ((~fol).sum() - 12) // 8
        assert n_limbs in (3, 4)                                                   # crossed strips, seen from every side
        assert V[fol][:, 2].max() <= 4.2 + 0.45 and V[fol][:, 2].min() >= 0.3
        assert 1.2 <= np.hypot(V[fol][:, 0], V[fol][:, 1]).max() <= 1.95 * 1.7
    assert forms == set(ST.ORCHARD_FORMS) and len(ST.ORCHARD_FORMS) == 4


def test_garden_trees_vary_scale_tint_and_species_branch_height():
    """agy-garden-var-s24: neighboring identical orthophoto crowns get varied 0.7-1.3x scale and distinct UV1 tints,
    while birch/ash attach first branches higher than maple/chestnut."""
    from types import SimpleNamespace
    from shapely.geometry import box
    parts = [SimpleNamespace(layer=ly, mat="plot_kit",
                             V=np.array([[-15.0, 2.0, 0.0], [18.0, 2.0, 0.0], [18.0, 15.0, 0.0], [-15.0, 15.0, 0.0]]),
                             T=np.array([[0, 1, 2], [0, 2, 3]])) for ly in ("plots", "plots_low")]
    buf = SimpleNamespace(parts=parts, add=lambda l, m, V, UV, T, **k: parts.append(
        SimpleNamespace(layer=l, mat=m, V=np.asarray(V), T=np.asarray(T), kw=k)))
    plot = {"id": "p", "key": "p", "poly": box(-15, -15, 15, 15),
            "foot": box(-4, -4, 4, 4),
            "lay": {"runs": [], "gate": None, "wicket": None, "wickets": []}}
    crowns = [{"plot": "p", "key": ("c", i), "p": np.array([-10.0 + i * 2.5, 8.0]), "r": 1.35,
               "in_plot": True, "near": True, "kind": "broadleaf"} for i in range(12)]
    rep = PG.garden_trees(buf, {"plots": [plot], "garden_trees": crowns}, lambda q: 0.0, {})
    hs = [t["h_m"] for t in rep["list"] if t["species"] != "fruit"]
    assert len(hs) >= 6 and max(hs) / min(hs) >= 1.35, hs                          # 0.7-1.3x scale spread across same r
    assert any("UV1" in p.kw for p in parts[1:] if p.layer == "plots")
    assert PG.tree_dims(1.4, "birch", "k")[1] > PG.tree_dims(1.4, "maple", "k")[1]  # birch attaches higher than maple


def test_crown_cards_have_a_rounded_underside():
    """The crown cards ended in a straight cut a third of their width long (the flat underside of the "lollipop")."""
    N = PK.N
    for name in ("crown_ovoid", "crown_round"):
        u0, u1, v0, v1 = PK.sprite(name)
        a = np.asarray(PK.atlas().crop((int(u0 * N), int((1 - v1) * N), int(u1 * N), int((1 - v0) * N))))[..., 3] > 128
        h, w = a.shape
        foot = a[int(h * 0.985):].any(0).sum() / w
        low = a[int(h * 0.80):int(h * 0.97)].any(0).sum() / w
        assert foot <= 0.30 and low >= 0.5, (name, foot, low)
