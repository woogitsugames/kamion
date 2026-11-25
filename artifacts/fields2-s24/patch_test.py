from pathlib import Path
p = Path("tests/gis/test_fields_0334.py")
s = p.read_text(encoding="utf-8")
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:50]
    s = s.replace(a, b)
rep("    assert sp <= {n for n, _ in VG.BAULK_SPECIES} | {n for n, _ in VG.FALLOW_SPECIES}\n",
    "    assert sp <= {n for n, _ in VG.BAULK_SPECIES} | {n for n, _ in VG.FALLOW_SPECIES} | {n for n, _ in VG.CLUMP_SPECIES}\n")
rep("    assert all(t == \"baulk\" for _, _, _, t in pl)\n", "    assert all(t in (\"baulk\", \"clump\") for _, _, _, t in pl)\n")
s += '''

# ---------------------------------------------------------------- r2 (fields2-s24, critic build #8 P1#6 / P1#7)
def test_r2_wobble_constants_match_the_shader():
    for cell, amp, salt in VG.FIELD_WOBBLE:
        assert f"{salt}u" in HLSL
    (c47, a47, _), (_, a17, _), (_, a5, _) = VG.FIELD_WOBBLE
    assert f"#define KF_WOB_L_M {c47:.1f}" in HLSL
    for name, a in (("KF_WOB_A47", a47), ("KF_WOB_A17", a17), ("KF_WOB_A5", a5)):
        assert f"#define {name} {a}" in HLSL
    assert "float t = (dot(rel, dir) + wob) / w;" in HLSL
    assert "(n47 - 0.5) * KF_WOB_A47 + (n17 - 0.5) * KF_WOB_A17 + (n5 - 0.5) * KF_WOB_A5" in HLSL


def test_r2_strip_edges_meander_within_the_amplitude():
    rng = np.random.default_rng(3)
    P = rng.uniform(0, 6000, (40000, 2)) + np.array([758000.0, 609000.0])
    wob = VG.field_wobble(P[:, 0], P[:, 1])
    lim = 0.5 * sum(a for _, a, _ in VG.FIELD_WOBBLE)
    assert np.abs(wob).max() <= lim and np.abs(wob).max() > 0.5 * lim
    assert 0.3 < np.std(wob) < 1.0                       # an edge that visibly bows, not a ruled line, not a zigzag
    L = VG.field_layout(P[:, 0], P[:, 1])
    assert np.array_equal(L["wob"], wob)
    # the edge moves smoothly: 1 m along the strip changes the wobble by a few cm
    th = L["th"]
    w2 = VG.field_wobble(P[:, 0] - np.sin(th), P[:, 1] + np.cos(th))
    assert np.abs(w2 - wob).max() < 0.45


def test_r2_no_scrub_between_two_strips_of_one_holding_and_clumps_are_clumps():
    hf = _Hf()
    pl = VG.field_plants(_src("uprawa na gruntach ornych"), ORIGIN, hf)
    baulk = np.array([p for p, _, _, t in pl if t == "baulk"])
    L = VG.field_layout(baulk[:, 0] + ORIGIN[0], baulk[:, 1] + ORIGIN[1])
    kE = L["k"] + (L["across"] >= 0.5 * L["w"])
    zero = np.zeros(len(kE))
    own = lambda k: VG._u01(VG._h32(VG._h32(L["bid"].astype(np.float64), k, 929).astype(np.float64), zero, 931)) < VG.FIELD_OWN_SHARE_SHADER
    assert (own(kE - 1) | own(kE)).all()
    clump = np.array([p for p, _, _, t in pl if t == "clump"])
    assert len(clump) >= VG.CLUMP_SIZE[0]
    from scipy.spatial import cKDTree
    d, _ = cKDTree(clump).query(clump, k=2)
    assert np.median(d[:, 1]) < 6.0 and d[:, 1].max() < 25.0           # every clump plant has company
    # trees of the open field are few: clumps per km2 follow the lattice share
    n_cl = len(clump) / np.mean(VG.CLUMP_SIZE)
    assert n_cl / 1.44 < 1.6 * VG.CLUMP_SHARE * 1e6 / VG.CLUMP_CELL_M ** 2 + 3


def test_r2_no_lone_self_seeded_sapling_inside_a_strip_farm_polygon():
    import inspect
    src = inspect.getsource(VG.place)
    assert "inside = 0.0 if field_plants_on and poly.area >= FIELD_PLANT_MIN_M2 else SELF_SEED_FIELD_KEEP" in src
'''
p.write_text(s, encoding="utf-8", newline="\n")
