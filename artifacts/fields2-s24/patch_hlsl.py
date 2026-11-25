"""fields2-s24: splice the r2 body (mosaic_body.hlsl) into KamionFieldMosaic.hlsl (one-off helper, kept as evidence)."""
from pathlib import Path

p = Path("game/Assets/_Project/Environment/Shaders/KamionFieldMosaic.hlsl")
s = p.read_text(encoding="utf-8")
MARK = "// local: region-local E/N (m); origin: EPSG:2180 of the region origin (whole metres); footprint: metres per pixel;"
head = s.split(MARK)[0]
if "KF_WOB_L_M" not in head:
    head = head.replace("#define KF_BAULK_SPAN_M 1.6\n", """#define KF_BAULK_SPAN_M 1.6
// ADR 0334 r2 (fields2-s24, critic build #8 P1#6): the strip edges meander - value noise of 47 / 17 / 5 m cells added
// to the strip coordinate (metres peak-to-peak). Python mirror: vegetation.field_wobble (salts 983, 953, 951).
#define KF_WOB_L_M 47.0
#define KF_WOB_A47 2.4
#define KF_WOB_A17 1.4
#define KF_WOB_A5 0.5
""")
    head += """// value noise in the strip frame: cells sa (across the rows) x sl (along the rows) metres - streaks along the rows
half KFNoiseSF(float a, float l, float sa, float sl, uint salt)
{
    float2 p = float2(a / sa, l / sl);
    float2 g0 = floor(p);
    float2 f = p - g0;
    f = f * f * (3.0 - 2.0 * f);
    int2 g = int2(g0) + KF_BLOCK_HASH_OFS * 4;
    half a0 = (half)KFU01(KFHash(g.x, g.y, salt)), b0 = (half)KFU01(KFHash(g.x + 1, g.y, salt));
    half c0 = (half)KFU01(KFHash(g.x, g.y + 1, salt)), d0 = (half)KFU01(KFHash(g.x + 1, g.y + 1, salt));
    return lerp(lerp(a0, b0, (half)f.x), lerp(c0, d0, (half)f.x), (half)f.y);
}

"""
body = Path("artifacts/fields2-s24/mosaic_body.hlsl").read_text(encoding="utf-8")
p.write_text(head + body, encoding="utf-8", newline="\n")
print("ok", len(head + body))
