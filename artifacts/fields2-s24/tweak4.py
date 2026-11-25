from pathlib import Path
p = Path("game/Assets/_Project/Environment/Shaders/KamionFieldMosaic.hlsl"); s = p.read_text(encoding="utf-8")
for a, b in [
 ("    col = lerp(col, bc, baulk * lerp(arable ? 0.92h : 0.60h, 0.92h, margin));     // between two meadows the baulk is only rougher grass",
  "    half bstr = lerp(arable ? 0.92h : 0.35h, 0.92h, margin);     // between two meadows the baulk is only rougher grass\n    col = lerp(col, bc, baulk * bstr);"),
 ("    fb = lerp(fb, 0.50h, baulk);", "    fb = lerp(fb, 0.50h, baulk * bstr);"),
]:
    assert s.count(a) == 1, a[:50]
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
