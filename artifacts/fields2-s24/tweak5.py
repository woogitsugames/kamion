from pathlib import Path
p = Path("game/Assets/_Project/Environment/Shaders/KamionFieldMosaic.hlsl"); s = p.read_text(encoding="utf-8")
for a, b in [
 ("    float hw = max(0.5 * bw * (0.55 + 0.9 * n5) + (n1 - 0.5) * 0.35, 0.12);", "    float hw = max(0.5 * bw * (0.55 + 0.9 * n5) + (n1 - 0.5) * 0.60, 0.12);"),
 ("    fb = lerp(fb, 0.50h, baulk * bstr);", "    fb = lerp(fb, 0.32h, baulk * bstr);     // r2: 0.50 browned the baulk into a dirt track beside a green crop"),
 ("    half3 bc = lerp(half3(0.072h, 0.112h, 0.036h), half3(0.150h, 0.140h, 0.072h), smoothstep(0.45h, 0.8h, n5));", "    half3 bc = lerp(half3(0.078h, 0.122h, 0.038h), half3(0.150h, 0.140h, 0.072h), smoothstep(0.50h, 0.85h, n5));"),
]:
    assert s.count(a) == 1, a[:50]
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
