from pathlib import Path
def sub(path, pairs):
    p = Path(path); s = p.read_text(encoding="utf-8")
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:70])
        s = s.replace(a, b)
    p.write_text(s, encoding="utf-8", newline="\n")
H = "game/Assets/_Project/Environment/Shaders/KamionFieldMosaic.hlsl"
sub(H, [
 ("#define KF_WOB_L_M 47.0\n#define KF_WOB_A47 2.6\n#define KF_WOB_A17 1.0\n#define KF_WOB_A5 0.2", "#define KF_WOB_L_M 71.0\n#define KF_WOB_AL 1.8\n#define KF_WOB_A17 0.5\n#define KF_WOB_A5 0.12"),
 ("value noise of 47 / 17 / 5 m cells", "value noise of 71 / 17 / 5 m cells"),
 ("half n47 = KFNoise(local, origin, KF_WOB_L_M, 983u);", "half nL = KFNoise(local, origin, KF_WOB_L_M, 983u);"),
 ("meanders by up to +-1.9 m (gentle 47 m bows, a little\n    // 17 m and 5 m wiggle - furrows stay near-straight)", "meanders by up to +-1.2 m (gentle 71 m bows, a little\n    // 17 m and 5 m wiggle - seen end-on from the cab the furrows must stay near-straight, r2 render review)"),
 ("float wob = (n47 - 0.5) * KF_WOB_A47 + (n17 - 0.5) * KF_WOB_A17 + (n5 - 0.5) * KF_WOB_A5;", "float wob = (nL - 0.5) * KF_WOB_AL + (n17 - 0.5) * KF_WOB_A17 + (n5 - 0.5) * KF_WOB_A5;"),
 ("        rowD = 0.26h; rowS = 0.30h;\n        stA1 = 0.26h; stA2 = 0.20h;", "        rowD = 0.15h; rowS = 0.20h;\n        stA1 = 0.26h; stA2 = 0.20h;"),
 ("            col *= 1.0h + 0.10h * (KFBand(rc, 1.6, 0.8, fpr) - 0.5h);", "            col *= 1.0h + 0.06h * (KFBand(rc, 1.6, 0.8, fpr) - 0.5h);"),
 ("            rowP = 0.40; rowD = 0.42h; rowS = 0.75h;\n            stA1 = 0.30h; stA2 = 0.22h;", "            rowP = 0.40; rowD = 0.30h; rowS = 0.55h;\n            stA1 = 0.30h; stA2 = 0.12h;"),
 ("            rowP = 0.22; rowD = 0.20h; rowS = 0.25h;", "            rowP = 0.22; rowD = 0.12h; rowS = 0.15h;"),
 ("""        float ph = frac(rc / rowP) * 6.2831853;
        half fr = (half)saturate(rowP / (3.0 * fpr) - 0.5);
        half sn, cs;
        sincos((half)ph, sn, cs);""", """        // (render review r2: a pure sine read as corduroy - the furrow depth breaks up in 1.7 m / 5 m patches and the
        // line wanders by a fraction of its period, like clods and a hand on the wheel)
        float ph = frac(rc / rowP + (n1 - 0.5) * 0.25 + (n5 - 0.5) * 0.15) * 6.2831853;
        half fr = (half)saturate(rowP / (2.5 * fpr) - 0.8) * saturate(0.30h + 1.2h * n1) * (0.6h + 0.8h * n5);
        half sn, cs;
        sincos((half)ph, sn, cs);"""),
 ("    half baulk = hasBaulk ? (half)(saturate((hw - e) / fp + 0.5) * saturate(2.0 * hw / fp)) : 0.0h;", "    float fpe = max(fp, 0.30);     // a grass edge is never sharper than a few blades\n    half baulk = hasBaulk ? (half)(saturate((hw - e) / fpe + 0.5) * saturate(2.0 * hw / fp)) : 0.0h;"),
 ("    half bblock = (half)(saturate((hbw - blockEdge) / fp + 0.5) * saturate(2.0 * hbw / fp));", "    half bblock = (half)(saturate((hbw - blockEdge) / fpe + 0.5) * saturate(2.0 * hbw / fp));"),
 ("    col = lerp(col, bc, baulk * 0.92h);", "    col = lerp(col, bc, baulk * (arable ? 0.92h : 0.60h));     // between two meadows the baulk is only rougher grass"),
])
sub("tools/worldgen/streetscape/vegetation.py", [
 ("FIELD_WOBBLE = ((47.0, 2.6, 983), (17.0, 1.0, 953), (5.0, 0.2, 951))", "FIELD_WOBBLE = ((71.0, 1.8, 983), (17.0, 0.5, 953), (5.0, 0.12, 951))"),
 ("BAULK_THIN_KEEP = 0.35 ", "BAULK_THIN_KEEP = 0.12 "),
 ("BAULK_PAIR_SHARE = 0.40 ", "BAULK_PAIR_SHARE = 0.50 "),
 ("BAULK_LONE_KEEP = 0.004 ", "BAULK_LONE_KEEP = 0.002 "),
 ("""                inside = 0.0 if field_plants_on and poly.area >= FIELD_PLANT_MIN_M2 else SELF_SEED_FIELD_KEEP
                P = P[u < np.where(d_edge <= SELF_SEED_EDGE_M, SELF_SEED_EDGE_KEEP, inside)]""",
  """                inside, edge = SELF_SEED_FIELD_KEEP, SELF_SEED_EDGE_KEEP
                if field_plants_on and poly.area >= FIELD_PLANT_MIN_M2:
                    # ... and the margin scrub stands in patches (SELF_SEED_PATCH_M cells of EPSG:2180), not one
                    # sapling every 40 m of every polygon border
                    inside = 0.0
                    edge = np.where(_u01(_h32(np.floor((P[:, 0] + origin[0]) / SELF_SEED_PATCH_M),
                                              np.floor((P[:, 1] + origin[1]) / SELF_SEED_PATCH_M), 1008)) < SELF_SEED_PATCH_SHARE,
                                    SELF_SEED_PATCH_KEEP, 0.0)
                P = P[u < np.where(d_edge <= SELF_SEED_EDGE_M, edge, inside)]"""),
 ("SELF_SEED_FIELD_KEEP = 0.02\n", "SELF_SEED_FIELD_KEEP = 0.02\nSELF_SEED_PATCH_M = 60.0         # ADR 0334 r2 (rural strip farms): margin scrub in patches\nSELF_SEED_PATCH_SHARE = 0.25\nSELF_SEED_PATCH_KEEP = 0.90\n"),
])
sub("tests/gis/test_fields_0334.py", [
 ("""    (c47, a47, _), (_, a17, _), (_, a5, _) = VG.FIELD_WOBBLE
    assert f"#define KF_WOB_L_M {c47:.1f}" in HLSL
    for name, a in (("KF_WOB_A47", a47), ("KF_WOB_A17", a17), ("KF_WOB_A5", a5)):""", """    (cL, aL, _), (_, a17, _), (_, a5, _) = VG.FIELD_WOBBLE
    assert f"#define KF_WOB_L_M {cL:.1f}" in HLSL
    for name, a in (("KF_WOB_AL", aL), ("KF_WOB_A17", a17), ("KF_WOB_A5", a5)):"""),
 ('    assert "(n47 - 0.5) * KF_WOB_A47 + (n17 - 0.5) * KF_WOB_A17 + (n5 - 0.5) * KF_WOB_A5" in HLSL', '    assert "(nL - 0.5) * KF_WOB_AL + (n17 - 0.5) * KF_WOB_A17 + (n5 - 0.5) * KF_WOB_A5" in HLSL'),
 ("    assert 0.3 < np.std(wob) < 1.0 ", "    assert 0.15 < np.std(wob) < 0.6 "),
 ("    assert np.abs(w2 - wob).max() < 0.45", "    assert np.abs(w2 - wob).max() < 0.25"),
 ("    assert 'inside = 0.0 if field_plants_on and poly.area >= FIELD_PLANT_MIN_M2 else SELF_SEED_FIELD_KEEP' in src" if False else '    assert "inside = 0.0 if field_plants_on and poly.area >= FIELD_PLANT_MIN_M2 else SELF_SEED_FIELD_KEEP" in src', '    assert "if field_plants_on and poly.area >= FIELD_PLANT_MIN_M2:" in src and "inside = 0.0" in src'),
])
print("ok")
