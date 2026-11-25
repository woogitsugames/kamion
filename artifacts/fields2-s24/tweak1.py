from pathlib import Path
def sub(path, pairs):
    p = Path(path); s = p.read_text(encoding="utf-8")
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:60])
        s = s.replace(a, b)
    p.write_text(s, encoding="utf-8", newline="\n")
sub("artifacts/fields2-s24/patch_hlsl.py", [("#define KF_WOB_A47 2.4\n#define KF_WOB_A17 1.4\n#define KF_WOB_A5 0.5", "#define KF_WOB_A47 2.6\n#define KF_WOB_A17 1.0\n#define KF_WOB_A5 0.2")])
sub("tools/worldgen/streetscape/vegetation.py", [("FIELD_WOBBLE = ((47.0, 2.4, 983), (17.0, 1.4, 953), (5.0, 0.5, 951))", "FIELD_WOBBLE = ((47.0, 2.6, 983), (17.0, 1.0, 953), (5.0, 0.2, 951))")])
sub("artifacts/fields2-s24/mosaic_body.hlsl", [
 ("meanders by up to +-2.15 m (gentle 47 m bows, 17 m\n    // and 5 m wiggles)", "meanders by up to +-1.9 m (gentle 47 m bows, a little\n    // 17 m and 5 m wiggle - furrows stay near-straight)"),
 ("        stA1 = 0.10h; stA2 = 0.16h;\n    }\n    else if (u <= KF_RAPE_STUBBLE)", "        stA1 = 0.06h; stA2 = 0.16h;\n    }\n    else if (u <= KF_RAPE_STUBBLE)"),
 ("""        float am = frac(across / P) * P - 0.5 * P;
        float dr = length(float2(am, blockEdge - (Hd - 0.6)));
        float ring = abs(abs(dr - 0.4 * P) - 0.9);
        half arc = (half)(saturate((0.22 - ring) / fp + 0.5) * saturate(0.9 / fp - 0.5)) * (blockEdge < Hd - 0.6 ? 1.0h : 0.0h);
        col = lerp(col, lerp(col * 0.72h, half3(0.150h, 0.112h, 0.072h), 0.40h), arc * 0.7h);""",
  """        float ac = floor(across / P);
        float am = (across / P - ac) * P - 0.5 * P;
        float ua = KFU01(KFHash((int)fid, (int)ac, 997u));           // per loop: there or worked over, wider or tighter
        float dr = length(float2(am, blockEdge - (Hd - 0.6)));
        float ring = abs(abs(dr - (0.30 + 0.12 * ua) * P) - 0.9);
        half arc = (half)(saturate((0.22 - ring) / fp + 0.5) * saturate(0.9 / fp - 0.5)) * (blockEdge < Hd - 0.6 && ua < 0.7 ? 1.0h : 0.0h);
        arc *= 0.35h + 0.65h * n5;
        col = lerp(col, lerp(col * 0.72h, half3(0.150h, 0.112h, 0.072h), 0.40h), arc * 0.6h);"""),
 ("    half thin = hasBaulk ? (half)saturate(1.0 - (e - hw) / (1.0 + 3.0 * n17)) : 0.0h;", "    half thin = hasBaulk ? (half)saturate(1.0 - (e - hw) / (0.6 + 2.2 * n17)) : 0.0h;"),
 ("    thin = max(thin, (half)saturate(1.0 - (blockEdge - hb) / (1.0 + 3.0 * n17)));", "    thin = max(thin, (half)saturate(1.0 - (blockEdge - hb) / (0.6 + 2.2 * n17)));"),
 ("    col = lerp(col, lerp(col, bc, 0.55h), thin * thin * 0.75h);", "    col = lerp(col, lerp(col, bc, 0.55h), thin * thin * (0.25h + 0.70h * n5));"),
])
sub("artifacts/fields2-s24/preview_r2.py", [
 ("wob = (n47 - 0.5) * 2.4 + (n17 - 0.5) * 1.4 + (n5 - 0.5) * 0.5", "wob = (n47 - 0.5) * 2.6 + (n17 - 0.5) * 1.0 + (n5 - 0.5) * 0.2"),
 ("""am = np.mod(across / P, 1.0) * P - 0.5 * P
dr = np.hypot(am, block_edge - (Hd - 0.6))
ring = np.abs(np.abs(dr - 0.4 * P) - 0.9)
arc = np.clip((0.22 - ring) / fp + 0.5, 0, 1) * np.clip(0.9 / fp - 0.5, 0, 1) * (block_edge < Hd - 0.6)
c2 = lerp(c2, lerp(c2 * 0.72, SOIL, 0.40), arc * 0.7)""",
  """ac = np.floor(across / P)
am = (across / P - ac) * P - 0.5 * P
ua = u01(h32(i32(fid), ac, 997))
dr = np.hypot(am, block_edge - (Hd - 0.6))
ring = np.abs(np.abs(dr - (0.30 + 0.12 * ua) * P) - 0.9)
arc = np.clip((0.22 - ring) / fp + 0.5, 0, 1) * np.clip(0.9 / fp - 0.5, 0, 1) * ((block_edge < Hd - 0.6) & (ua < 0.7))
arc = arc * (0.35 + 0.65 * n5)
c2 = lerp(c2, lerp(c2 * 0.72, SOIL, 0.40), arc * 0.6)"""),
 ("thin = np.where(has, np.clip(1.0 - (e - hw) / (1.0 + 3.0 * n17), 0, 1), 0.0)", "thin = np.where(has, np.clip(1.0 - (e - hw) / (0.6 + 2.2 * n17), 0, 1), 0.0)"),
 ("thin = np.maximum(thin, np.clip(1.0 - (block_edge - hb) / (1.0 + 3.0 * n17), 0, 1))", "thin = np.maximum(thin, np.clip(1.0 - (block_edge - hb) / (0.6 + 2.2 * n17), 0, 1))"),
 ("(thin * thin * 0.75)[..., None]", "(thin * thin * (0.25 + 0.70 * n5))[..., None]"),
 ("stA1[m], stA2[m] = 0.10, 0.16", "stA1[m], stA2[m] = 0.06, 0.16"),
])
print("ok")
