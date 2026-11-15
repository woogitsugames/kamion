"""verify-cloud-c: render top view | GUGiK orthophoto crop of the same footprint (QA only), + downsized driver views.
uv run --project tools/worldgen python artifacts/verify-cloud-c/tools/pairs.py <region> <render_dir> <out_dir>"""
import json, math, sys
from pathlib import Path
import rasterio
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
reg, rd, od = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]); od.mkdir(parents=True, exist_ok=True)
auth = json.loads((ROOT / "Data/Regions" / reg / "control_cameras_place.authored.json").read_text(encoding="utf-8"))["cameras"]
org = json.loads((ROOT / "Data/Regions" / reg / "generated/world_manifest.json").read_text(encoding="utf-8"))["origin_epsg2180"]
o = json.loads((ROOT / "Data/Regions" / reg / "ortho.json").read_text(encoding="utf-8")); ds = rasterio.open(ROOT / o["file"])
for c in auth:
    cands = [p for p in rd.glob("*.png") if p.stem.replace("-", "_") == c["id"]]
    if not cands:
        print("no render", c["id"]); continue
    r = Image.open(cands[0]).convert("RGB")
    if c["id"].startswith("top_"):
        hh = c["eye_m"] * math.tan(math.radians(c["fov_deg"] / 2)); hw = hh * r.width / r.height
        x, y = org["x"] + c["pos_en"][0], org["y"] + c["pos_en"][1]
        a = ds.read(window=from_bounds(x - hw, y - hh, x + hw, y + hh, ds.transform), boundless=True)[:3].transpose(1, 2, 0)
        b = Image.fromarray(a).resize((960, 540), Image.LANCZOS)
        M = Image.new("RGB", (1920, 540)); M.paste(r.resize((960, 540), Image.LANCZOS), (0, 0)); M.paste(b, (960, 0))
        d = ImageDraw.Draw(M); d.text((8, 8), f"{reg} Low render: {c['id']}  ({2*hw:.0f} x {2*hh:.0f} m, centre {x:.0f},{y:.0f})", fill=(255, 255, 0))
        d.text((968, 8), f"GUGiK orto {o.get('date', '2024-05-27')} 0.25 m (QA only)", fill=(255, 255, 0))
        M.save(od / f"pair-{c['id']}.jpg", quality=88)
    else:
        r.resize((960, 540), Image.LANCZOS).save(od / f"view-{c['id']}.jpg", quality=88)
print("ok", reg)
