"""Compare the measured full inventory, retaining only a pair of full PNGs in RAM."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
phase = sys.argv[1] if len(sys.argv) > 1 else "after"
base = sys.argv[2] if len(sys.argv) > 2 else "before"
focus = "--focus" in sys.argv[3:]
out = ROOT / "review" / f"{phase}-from-{base}"
out.mkdir(parents=True, exist_ok=True)
details = {c["id"] for c in json.loads((ROOT / "cameras.json").read_text(encoding="utf-8-sig"))["cameras"]}
baseline_inventory = json.loads((ROOT / 'baseline-result.json').read_text(encoding='utf-8-sig'))['camera_inventories']
rows, inventories = [], {}
for condition in ("Low-overcast", "Low-clear", "High-overcast", "High-clear"):
    before = {p.name: p for p in (ROOT / base / condition).glob("*.png")}
    after = {p.name: p for p in (ROOT / phase / condition).glob("*.png")}
    expected = set(baseline_inventory[condition])
    assert before.keys() == expected, (condition, expected - before.keys())
    if focus:
        assert after and after.keys() <= expected, condition
        before = {name: before[name] for name in after}
    assert before.keys() == after.keys(), (condition, before.keys() - after.keys(), after.keys() - before.keys())
    inventories[condition] = sorted(before)
    sheet = None
    for index, name in enumerate(sorted(before)):
        with Image.open(before[name]) as original_a, Image.open(after[name]) as original_b:
            a, b = original_a.convert("RGB"), original_b.convert("RGB")
        assert a.size == b.size, (condition, name, a.size, b.size)
        delta = np.abs(np.asarray(a).astype(np.int16) - np.asarray(b).astype(np.int16))
        rows.append(dict(condition=condition, camera=Path(name).stem,
                         mean_abs=float(delta.mean()), fraction_over_5=float((delta.max(axis=2) > 5).mean()),
                         exact=bool(not delta.any())))
        del delta
        page, row = divmod(index, 8)
        if row == 0:
            sheet = Image.new("RGB", (960, 246 * min(8, len(before) - index)), (24, 24, 24))
        draw = ImageDraw.Draw(sheet)
        draw.text((8, row * 246 + 5), f"{condition} {Path(name).stem} | {base} / {phase}", fill="white")
        for column, image in enumerate((a, b)):
            image.thumbnail((480, 222))
            sheet.paste(image, (480 * column + (480 - image.width) // 2,
                                row * 246 + 24 + (222 - image.height) // 2))
        a.close()
        b.close()
        if row == 7 or index == len(before) - 1:
            sheet.save(out / f"{condition}-{page + 1:02d}.jpg", quality=91)
            sheet.close()
result = dict(base=base, phase=phase, inventories=inventories, camera_conditions=len(rows),
              scope="diagnostic subset only" if focus else "all captured cameras",
              exact=sum(row["exact"] for row in rows), rows=rows)
(ROOT / f"pixel-diff-{phase}-from-{base}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"{len(rows)} camera conditions; {result['exact']} identical; sheets: {out}")
