"""fields2-s24: one-off patch of WorldPBR.shader for the r2 field mosaic signature (ADR 0334 r2), kept as evidence."""
from pathlib import Path

p = Path("game/Assets/_Project/Environment/Shaders/WorldPBR.shader")
raw = p.read_bytes()
crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:70])
    s = s.replace(a, b)


rep('''                half4 fieldAlb = half4(0.0h, 0.0h, 0.0h, 0.0h);
            #if defined(_GROUNDMASKS)
                if (_RegionOriginEN.z > 0.5)
                    KamionFieldMosaic(i.posEN, _RegionOriginEN.xy, footprint, macro.g, i.masks, fieldAlb);
            #endif
''', '''                half4 fieldAlb = half4(0.0h, 0.0h, 0.0h, 0.0h);
                half2 fieldSlope = half2(0.0h, 0.0h);     // ADR 0334 r2: furrows / rows of the field (dE, dN)
            #if defined(_GROUNDMASKS)
                {
                    float2 enDx = ddx(i.posEN), enDy = ddy(i.posEN);     // outside the branch (gradients)
                    if (_RegionOriginEN.z > 0.5)
                        KamionFieldMosaic(i.posEN, _RegionOriginEN.xy, footprint, enDx, enDy, macro.g, i.masks, fieldAlb, fieldSlope);
                }
            #endif
''')
rep('''                half3 nw = normalize(tn.x * T + tn.y * B + tn.z * n);
''', '''                half3 nw = normalize(tn.x * T + tn.y * B + tn.z * n);
            #if defined(_GROUNDMASKS)
                // ADR 0334 r2: furrows and drill rows tilt the ground normal (region-local E / N = world X / Z)
                nw = normalize(nw + half3(fieldSlope.x, 0.0h, fieldSlope.y));
            #endif
''')
out = s.replace("\n", "\r\n") if crlf else s
p.write_bytes(out.encode("utf-8"))
print("ok crlf=", crlf)
