"""ADR 0352 addendum (garden-trees-s24): small garden trees of the plot kit as lobes / clumps on limbs."""
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
    for sp, r, H, cb in (("linden", 1.25, 4.7, 1.6), ("maple", 1.5, 4.6, 1.3), ("birch", 1.2, 5.6, 1.3), ("ash", 1.0, 4.0, 1.3)):
        for k in range(12):
            kit = PLT.Kit()
            forms.add(ST.young_tree(kit, np.zeros(2), 0.0, r, H, cb, sp, PG.HABIT[sp], (sp, k)))
            assert _tris(kit) <= 1.5 * OLD_YOUNG_TRIS                              # + 50 % at most
            V, UV, T, C, fol = _split(kit)
            rad = np.hypot(V[fol][:, 0], V[fol][:, 1])
            assert rad.max() <= 1.45 * r + 0.25, (sp, k, rad.max())                # quad corners; the painted crown ends inside
            assert V[fol][:, 2].max() <= H * 1.06 and V[fol][:, 2].min() >= cb - 0.12 * (H - cb) - 0.05
            assert (~fol).sum() >= 12 + 6                                          # 3-sided stem + boughs
            u0, u1, v0, v1 = PK.sprite(PG.HABIT[sp])                               # species crown card of ADR 0352, same atlas
            assert (UV[fol][:, 0] >= min(u0, u1) - 1e-6).all() and (UV[fol][:, 0] <= max(u0, u1) + 1e-6).all()
            occ = np.linalg.norm(C[fol, :3] * 2 - 1, axis=1)
            assert occ.min() >= 0.6                                                # no dark body
            shapes.append(np.round(np.ptp(V[fol], axis=0) / r, 2).tolist())
    assert forms == set(ST.YOUNG_FORMS)
    assert len({tuple(s) for s in shapes}) == len(shapes)                          # no two trees alike


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
    for k in range(16):
        kit = PLT.Kit()
        forms.add(PLT.fruit_tree(kit, np.zeros(2), 0.0, 4.2, ("f", k), r=1.7))
        assert _tris(kit) <= 1.5 * OLD_ORCHARD_TRIS and _tris(kit) in (40, 50)
        V, UV, T, C, fol = _split(kit)
        occ = np.linalg.norm(C[fol, :3] * 2 - 1, axis=1)
        assert occ.min() >= 0.6                                                    # the old _core had 0.22-0.26
        hv0, hv1 = PK.row("hedge")
        assert not ((UV[fol][:, 1] >= hv0) & (UV[fol][:, 1] <= hv1)).any()         # no dense hedge row (= the core's texture)
        n_limbs = ((~fol).sum() - 12) // 8
        assert n_limbs in (3, 4)                                                   # crossed strips, seen from every side
        assert V[fol][:, 2].max() <= 4.2 + 0.4 and V[fol][:, 2].min() >= 0.3
        assert 1.2 <= np.hypot(V[fol][:, 0], V[fol][:, 1]).max() <= 1.9 * 1.7
    assert forms == set(ST.ORCHARD_FORMS)


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
