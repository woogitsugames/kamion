import sys
from pathlib import Path
R = Path(sys.argv[1])


def sub(path, old, new, count=1):
    p = R / path
    s = p.read_text(encoding="utf-8")
    assert s.count(old) >= 1, (path, old[:60])
    s = s.replace(old, new, count)
    p.write_text(s, encoding="utf-8", newline="\n")


A = "art-source/world/materials/_src/sets_fire_station.py"
sub(A, '"arch": {"w": 4.7, "spring": 3.3, "rise": 1.3, "trim": 0.24, "col": 1.175, "row": 1.5, "bar": 0.07},',
       '"arch": {"w": 4.7, "spring": 3.3, "rise": 1.3, "trim": 0.24, "col": 1.5667, "row": 1.5, "bar": 0.07},      # r4: 3 lights (2 mullions) as on photo 7197')
sub(A, '    "ochre": _r(10.35, 12.60, 1.6, 1.35),\n',
       '    "ochre": _r(10.35, 12.60, 1.6, 1.35),\n    "thuja_far": _r(12.15, 12.60, 1.75, 1.35),     # r4: far-LOD thuja body (LOD1/2 have no leaf shell)\n')
sub(A, "    tone = det ** 0.9 * (1 + 0.03 * n_mid + 0.06 * n_big - 0.035 * ss(0.2, 1.4, n_run))",
       "    # r4: the scan detail is damped (0.9 -> 0.5) and the big tone noise halved: photo 7197 shows an even matt paint\n"
       "    tone = det ** 0.5 * (1 + 0.02 * n_mid + 0.03 * n_big - 0.03 * ss(0.2, 1.4, n_run))")
sub(A, "    tone *= 1 + 0.035 * ss(0.6, 1.1, n_pat) - 0.03 * ss(0.7, 1.3, -n_pat)",
       "    tone *= 1 + 0.02 * ss(0.6, 1.1, n_pat) - 0.02 * ss(0.7, 1.3, -n_pat)")
sub(A, "                blind_seed=0):", "                blind_seed=0, glass=None):")
sub(A, "        gcol = np.where((hsh > 0.62)[..., None], blind * 0.35 + glass_col * 0.65, glass_col * dark_in)",
       "        if glass is not None:                      # big hall glazing: grey daylight reflection, no blinds (photo 7197)\n"
       "            gcol = glass[None, None, :] * (0.85 + 0.3 * K.hash01(pane, 19))[..., None] * (1 + 0.10 * n_big)[..., None]\n"
       "        else:\n"
       "            gcol = np.where((hsh > 0.62)[..., None], blind * 0.35 + glass_col * 0.65, glass_col * dark_in)")
sub(A, "trim=(trim_m, tblue * 1.0), blind_seed=3)", "trim=(trim_m, tblue * 1.0), blind_seed=3, glass=hall_glass)")
sub(A, "    # arched window 3.4 x 3.4:",
       "    # r4: the hall windows read mid grey on the overcast CC0 photo 7197 (sky reflection + light interior), far lighter\n"
       "    # than the office glazing. Linear albedo WORKING_VALUE by eye.\n"
       "    hall_glass = np.array([0.085, 0.090, 0.095], np.float32)\n"
       "    # arched window 3.4 x 3.4:")
sub(A, "    cross = in_circ & ((np.abs(ru) < gr[\"cross\"] / 2) | (np.abs(rv2) < gr[\"cross\"] / 2))\n"
       "    glazing(in_rw, ru + R0, rv2 + R0, 9.0, 9.0, shape=in_circ, trim=(ring | cross, tblue), blind_seed=5)\n",
       "    # r4 (photo 7197): one wide blue vertical post; the horizontal member is a thin white transom\n"
       "    cross = in_circ & (np.abs(ru) < gr[\"cross\"] / 2)\n"
       "    glazing(in_rw, ru + R0, rv2 + R0, 9.0, 9.0, shape=in_circ, trim=(ring | cross, tblue), blind_seed=5, glass=hall_glass)\n"
       "    transom = in_rw & in_circ & ~ring & ~cross & (np.abs(rv2) < 0.035)\n"
       "    alb = np.where(transom[..., None], pvc, alb)\n"
       "    rough = np.where(transom, 0.45, rough)\n"
       "    h = np.where(transom, 0.0, h)\n")
sub(A, "    alb = np.clip(alb, 0.012, 0.9).astype(np.float32)",
       "    # far-LOD thuja body: leaf green of the shell texture seen from a distance (core albedo x ~2.5, materials.py\n"
       "    # hedge_thuja note 'core ~0.4 x leaf'), mottled so the cone is not a flat colour\n"
       "    Tf = L[\"thuja_far\"]\n"
       "    in_tf = _gut(X, v, Tf)\n"
       "    tcol = np.array([0.040, 0.068, 0.030], np.float32) * (1 + 0.30 * n_mid + 0.15 * n_big + 0.25 * n_fine).clip(0.4, 1.8)[..., None]\n"
       "    alb = np.where(in_tf[..., None], tcol, alb)\n"
       "    rough = np.where(in_tf, 0.9, rough)\n"
       "    h = np.where(in_tf, 0.004 * n_mid, h)\n\n"
       "    alb = np.clip(alb, 0.012, 0.9).astype(np.float32)")
sub(A, '"number": {"u": [0.0, 0.30], "v": [0.02, 0.25], "size_m": [2.3, 0.88]},',
       '"number": {"u": [0.0, 0.34], "v": [0.02, 0.25], "size_m": [2.4, 0.80]},     # r4: roundel + digits 0.6 m (photo 7197)')
sub(A, "        m4 = np.asarray(im, np.float32) / 255\n",
       "        if key == \"number\":                        # r4: digits right of a generic handset roundel (ring + receiver arc)\n"
       "            im = Image.new(\"L\", (w4, h4), 0)\n"
       "            dr = ImageDraw.Draw(im)\n"
       "            f = _font(int(h4 * 0.98))\n"
       "            bb = dr.textbbox((0, 0), text, font=f)\n"
       "            sc = min(1.0, (w4 * 0.70) / (bb[2] - bb[0]), (h4 * 0.76) / (bb[3] - bb[1]))\n"
       "            f = _font(int(h4 * 0.98 * sc))\n"
       "            bb = dr.textbbox((0, 0), text, font=f)\n"
       "            dr.text((w4 - (bb[2] - bb[0]) - bb[0] - w4 * 0.01, (h4 - (bb[3] - bb[1])) / 2 - bb[1]), text, fill=255, font=f)\n"
       "            rr_ = h4 * 0.30\n"
       "            cx_, cy_ = w4 * 0.02 + rr_, h4 / 2\n"
       "            lw = max(2, int(h4 * 0.055))\n"
       "            dr.ellipse((cx_ - rr_, cy_ - rr_, cx_ + rr_, cy_ + rr_), outline=255, width=lw)\n"
       "            dr.arc((cx_ - rr_ * 0.55, cy_ - rr_ * 0.55, cx_ + rr_ * 0.55, cy_ + rr_ * 0.55), 110, 250, fill=255, width=int(lw * 1.6))\n"
       "        m4 = np.asarray(im, np.float32) / 255\n")

D = "art-source/world/landmarks/fire_station_jrg2/dims.json"
sub(D, '"lettering": {"u": [38.1, 46.7], "z": [9.2, 10.0]}, "number": {"u": [38.9, 40.9], "z": [8.05, 8.85]},',
       '"lettering": {"u": [37.9, 46.55], "z": [9.2, 10.0]}, "number": {"u": [37.9, 40.3], "z": [8.05, 8.85]},\n'
       '          "vents": {"u": [37.77, 40.62, 43.62, 46.7], "z": 10.5, "size": 0.2},')
sub(D, "WORKING_VALUE +-0.2 m (sill hidden by the thujas)\"",
       "WORKING_VALUE +-0.2 m (sill hidden by the thujas). r4 (same photo, 67 px/m at full size): arched windows have 3 lights; round window = one wide blue post + thin white transom; lettering spans 1.5-10.15 m and the handset roundel + '998' 1.57-3.84 m from the W corner, digits 0.6 m; four ochre vent squares ~0.2 m at 1.37 / 4.22 / 7.22 / 10.3 m, 0.9 m above the lettering centre\"")

M = "tools/blender/world/landmarks/make_fire_station.py"
sub(M, "    _bar(mb, W, back, nout, (R0 - ri, R0), (R0 + ri, R0), g[\"cross\"] / 2, 0.07, bl)\n",
       "    _bar(mb, W, back, nout, (R0 - ri, R0), (R0 + ri, R0), 0.035, 0.05, white)      # r4: thin white transom (photo 7197)\n")
sub(M, "    downpipe(mb, (u1, v0 + 0.4), (1, 0), PL_H, ze - 0.5, lod)\n",
       "    if lod == 0 and \"vents\" in h:               # r4: ochre vent squares under the verge (photo 7197), 2 cm proud\n"
       "        oc, vt = LAY[\"ochre\"], h[\"vents\"]\n"
       "        hs_ = vt[\"size\"] / 2\n"
       "        for uu in vt[\"u\"]:\n"
       "            q = [P3((uu - hs_, v0 - 0.02), zl(vt[\"z\"]) - hs_), P3((uu + hs_, v0 - 0.02), zl(vt[\"z\"]) - hs_),\n"
       "                 P3((uu + hs_, v0 - 0.02), zl(vt[\"z\"]) + hs_), P3((uu - hs_, v0 - 0.02), zl(vt[\"z\"]) + hs_)]\n"
       "            ou, ov = oc[\"u\"][0] + 0.2, oc[\"v\"][0] + 0.9\n"
       "            mb.face(q, [(ou, ov), (ou + vt[\"size\"], ov), (ou + vt[\"size\"], ov + vt[\"size\"]), (ou, ov + vt[\"size\"])], MAT, np.array([0, -1.0, 0]))\n"
       "    downpipe(mb, (u1, v0 + 0.4), (1, 0), PL_H, ze - 0.5, lod)\n")
sub(M, "                    mb.face([a0, a1, b1, b0], [(u_a, v_a), (u_b, v_a), (u_b, v_b), (u_a, v_b)], mat,\n",
       "                    quv = [(u_a, v_a), (u_b, v_a), (u_b, v_b), (u_a, v_b)]\n"
       "                    if lod > 0:                 # r4: no leaf shell on LOD1/2 -> leaf-green atlas swatch instead of the\n"
       "                        tf = LAY[\"thuja_far\"]    # near-black core (black cones on the Low tier, r3 frames)\n"
       "                        fv = tf[\"v\"][1] - tf[\"v\"][0] - 0.1\n"
       "                        ya, yb = min(v_a * 0.25, fv), min(v_b * 0.25, fv)\n"
       "                        xa = tf[\"u\"][0] + 0.05 + (i % 2) * 0.8\n"
       "                        quv = [(xa, tf[\"v\"][0] + 0.05 + ya), (xa + 0.8, tf[\"v\"][0] + 0.05 + ya),\n"
       "                               (xa + 0.8, tf[\"v\"][0] + 0.05 + yb), (xa, tf[\"v\"][0] + 0.05 + yb)]\n"
       "                    mb.face([a0, a1, b1, b0], quv, mat if lod == 0 else MAT,\n")
print("patched")
