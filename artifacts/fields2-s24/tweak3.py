from pathlib import Path
def sub(path, pairs):
    p = Path(path); s = p.read_text(encoding="utf-8")
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:70])
        s = s.replace(a, b)
    p.write_text(s, encoding="utf-8", newline="\n")
H = "game/Assets/_Project/Environment/Shaders/KamionFieldMosaic.hlsl"
sub(H, [
 ("""// driftN: 0..1 low-frequency noise (macro map).""", """// mbD: (ddx, ddy) of the farmland flag m.b - with enDx / enDy it gives the flag's ground gradient: the ramp between a
// field polygon and its neighbour (1 m of mesh beside the roads, 8 m elsewhere) becomes a ragged rough-grass margin.
// driftN: 0..1 low-frequency noise (macro map)."""),
 ("""void KamionFieldMosaic(float2 local, float2 origin, float footprint, float2 enDx, float2 enDy, half driftN,
                       inout half4 m, out half4 field, out half2 slopeEN)""", """void KamionFieldMosaic(float2 local, float2 origin, float footprint, float2 enDx, float2 enDy, half2 mbD, half driftN,
                       inout half4 m, out half4 field, out half2 slopeEN)"""),
 ("""    if (farm <= 0.0h) return;
    bool arable = m.b > 0.95h;
""", """    if (farm <= 0.0h) return;
    // r2: ground gradient of the flag (1 / m); > 0 only on the mesh cells that straddle a polygon border
    float det = enDx.x * enDy.y - enDx.y * enDy.x;
    float2 gB = abs(det) > 1e-12 ? float2(enDy.y * mbD.x - enDx.y * mbD.y, enDx.x * mbD.y - enDy.x * mbD.x) / det : float2(0.0, 0.0);
    float gl = length(gB);
    bool ramp = gl > 0.002;
"""),
 ("""    float wob = (nL - 0.5) * KF_WOB_AL""", """    // r2 polygon border: the flag passes 0.90 (the grassland code) on its way from arable 1.00 to the verge - that used
    // to draw a ruler-straight band of vivid meadow green around every arable polygon. Now the ramp below the arable
    // threshold is a margin of rough grass, and the threshold wanders by ~+-0.5 m of ground (ragged crop edge).
    float thA = 0.95 + (ramp ? clamp(((n1 - 0.5) + (n5 - 0.5) * 0.8) * 1.6 * gl, -0.04, 0.04) : 0.0);
    bool arable = m.b > thA;
    float dA = max(0.3 * gl, 0.004);
    half margin = ramp ? (half)saturate((thA + dA - m.b) / (2.0 * dA)) : 0.0h;
    float wob = (nL - 0.5) * KF_WOB_AL"""),
 ("""    baulk = max(baulk, bblock);
""", """    baulk = max(baulk, max(bblock, margin));
    if (ramp && arable) thin = max(thin, (half)saturate(1.0 - (m.b - thA) / max(2.5 * gl, 1e-3)));
"""),
 ("""    col = lerp(col, bc, baulk * (arable ? 0.92h : 0.60h));     // between two meadows the baulk is only rougher grass""", """    col = lerp(col, bc, baulk * lerp(arable ? 0.92h : 0.60h, 0.92h, margin));     // between two meadows the baulk is only rougher grass"""),
])
W = "game/Assets/_Project/Environment/Shaders/WorldPBR.shader"
sub(W, [
 ("""                    float2 enDx = ddx(i.posEN), enDy = ddy(i.posEN);     // outside the branch (gradients)
                    if (_RegionOriginEN.z > 0.5)
                        KamionFieldMosaic(i.posEN, _RegionOriginEN.xy, footprint, enDx, enDy, macro.g, i.masks, fieldAlb, fieldSlope);""",
  """                    float2 enDx = ddx(i.posEN), enDy = ddy(i.posEN);     // outside the branch (gradients)
                    half2 mbD = half2(ddx(i.masks.b), ddy(i.masks.b));
                    if (_RegionOriginEN.z > 0.5)
                        KamionFieldMosaic(i.posEN, _RegionOriginEN.xy, footprint, enDx, enDy, mbD, macro.g, i.masks, fieldAlb, fieldSlope);"""),
])
print("ok")
