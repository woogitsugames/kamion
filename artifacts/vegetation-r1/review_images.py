"""Offline evidence: every camera, separate static/instance costs, fixed grass ROIs."""
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
ROIS = {
    "route-onramp-andersa-above": (.82, .62, .97, .80),
    "route-onramp-andersa-above:grass-only": (.87, .85, .95, .97),
    "r10_fence_2": (.10, .72, .85, .93),
}
FOCUS = ("dk8-dk19-exit", "driver-andersa-to-putry", "route-putry-approach",
         "g3a-rondo-bie-approach", "photo-biezenstwa-ground", "route-onramp-andersa-above",
         "r10_fence_2", "fire-station-ref7197")


def stats(path):
    result = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        m = re.match(r"([^:]+): objects=\d+ drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)", line)
        if m:
            result[m[1]] = dict(static_draws=int(m[2]), shadow_draws=int(m[3]), static_triangles_k=int(m[4]))
        m = re.match(r"\s+(.+?) instanced .*?: draws (\d+), instances (\d+), triangles (\d+)k", line)
        if m and m[1] in result:
            result[m[1]].update(instance_draws=int(m[2]), instances=int(m[3]), instance_triangles_k=int(m[4]))
    for r in result.values():
        r["total_draws"] = r["static_draws"] + r.get("instance_draws", 0)
        r["total_triangles_k"] = r["static_triangles_k"] + r.get("instance_triangles_k", 0)
    return result


def grass(path, box):
    a = np.array(Image.open(path).convert("RGB"), dtype=float)
    h, w = a.shape[:2]
    x0, y0, x1, y1 = box
    a = a[round(h*y0):round(h*y1), round(w*x0):round(w*x1)]
    luma = a @ np.array([.2126, .7152, .0722])
    blocks = [luma[y:y+32, x:x+32].mean()
              for y in range(0, luma.shape[0]-31, 32)
              for x in range(0, luma.shape[1]-31, 32)]
    return dict(roi=box, rgb_mean=a.mean((0, 1)).tolist(),
                luma_p10_p50_p90=np.percentile(luma, [10, 50, 90]).tolist(),
                block32_mean_std=float(np.std(blocks)),
                block_count=len(blocks), method="sRGB8 Rec709, original resolution; fixed rectangle, no semantic mask")


def main():
    output = ROOT / "contacts"
    output.mkdir(exist_ok=True)
    measurements, comparisons = {}, {}
    for stage in ("before", "after"):
        for folder in sorted((ROOT/stage).glob("*")):
            if not folder.is_dir():
                continue
            images = sorted(p for p in folder.glob("*.png") if not p.stem.endswith("_mask"))
            for offset in range(0, len(images), 12):
                sheet = Image.new("RGB", (960, 3*142), "#222222")
                draw = ImageDraw.Draw(sheet)
                for i, path in enumerate(images[offset:offset+12]):
                    im = Image.open(path).convert("RGB")
                    im.thumbnail((238, 115))
                    x, y = (i % 4)*240, (i//4)*142
                    sheet.paste(im, (x, y+24))
                    draw.text((x+2, y+3), path.stem[:34], fill="white")
                sheet.save(output/f"{stage}-{folder.name}-{offset//12+1}.jpg", quality=90)
            key = stage+"/"+folder.name
            measurements[key] = {camera: grass(folder/(camera.split(':')[0]+".png"), box)
                                 for camera, box in ROIS.items() if (folder/(camera.split(':')[0]+".png")).exists()}
            if (folder/"stats.txt").exists():
                measurements[key]["all_camera_stats"] = stats(folder/"stats.txt")
            if stage == "after" and (ROOT/"before"/folder.name/"stats.txt").exists():
                before, after = stats(ROOT/"before"/folder.name/"stats.txt"), stats(folder/"stats.txt")
                if before.keys() != after.keys():
                    raise ValueError("Camera sets differ: "+folder.name)
                comparisons[folder.name] = {camera: dict(before=before[camera], after=after[camera],
                    delta_draws=after[camera]["total_draws"]-before[camera]["total_draws"],
                    delta_triangles_percent=100*(after[camera]["total_triangles_k"]/
                                                max(before[camera]["total_triangles_k"], 1)-1)) for camera in before}
                for camera in FOCUS:
                    paths = [ROOT/stage/folder.name/(camera+".png") for stage in ("before", "after")]
                    if not all(p.exists() for p in paths):
                        continue
                    frames = [Image.open(p).convert("RGB") for p in paths]
                    for frame in frames:
                        frame.thumbnail((960, 960))
                    sheet = Image.new("RGB", (960, sum(f.height+24 for f in frames)), "#222222")
                    draw = ImageDraw.Draw(sheet)
                    y = 0
                    for label, frame in zip(("PRZED", "PO"), frames):
                        draw.text((6, y+5), label+" "+folder.name+" "+camera, fill="white")
                        sheet.paste(frame, (0, y+24))
                        y += frame.height+24
                    sheet.save(output/("focus-"+folder.name+"-"+camera+".jpg"), quality=92)
    ref_file = ROOT/"photo-references.json"
    if ref_file.exists():
        repo = ROOT.parents[1]
        pairs = ROOT/"photo-pairs"
        pairs.mkdir(exist_ok=True)
        for ref in json.loads(ref_file.read_text(encoding="utf-8-sig"))["references"]:
            for folder in sorted((ROOT/"after").glob("*-photo-*")):
                before, after = ROOT/"before"/folder.name/(ref["camera"]+".png"), folder/(ref["camera"]+".png")
                if not before.exists() or not after.exists():
                    continue
                photo = Image.open(repo/ref["local_photo"]).convert("RGB")
                old, new = Image.open(before).convert("RGB"), Image.open(after).convert("RGB")
                if photo.width*new.height != new.width*photo.height:
                    raise ValueError("Photo/render aspect mismatch: "+ref["camera"])
                height = round(470*photo.height/photo.width)
                sheet = Image.new("RGB", (960, 2*(height+25)+90), "#222222")
                draw = ImageDraw.Draw(sheet)
                for row, render in enumerate((old, new)):
                    y = row*(height+25)
                    draw.text((4, y+4), "ZDJECIE", fill="white")
                    draw.text((494, y+4), ("PRZED" if row == 0 else "PO")+" "+folder.name, fill="white")
                    sheet.paste(photo.resize((470, height)), (0, y+23))
                    sheet.paste(render.resize((470, height)), (490, y+23))
                y = 2*(height+25)+4
                for i, line in enumerate((ref["camera"], f'{ref["author"]} | {ref["license"]} | {ref["captured_at"]}',
                                          ref["page_url"], "Poza UNVERIFIED; roznice oswietlenia i sezonu nie sa wynikiem zmiany.")):
                    draw.text((5, y+18*i), line, fill="white")
                sheet.save(pairs/(folder.name+"-"+ref["camera"]+".jpg"), quality=92)
    (ROOT/"measurements.json").write_text(json.dumps(measurements, indent=2)+"\n", encoding="utf-8")
    (ROOT/"stats-comparison.json").write_text(json.dumps(comparisons, indent=2)+"\n", encoding="utf-8")
    print("Contact sheets:", len(list(output.glob("*.jpg"))))
    for key, rows in comparisons.items():
        print(key, len(rows), "max draws delta", max(r["delta_draws"] for r in rows.values()),
              "max triangle delta percent", max(r["delta_triangles_percent"] for r in rows.values()))


if __name__ == "__main__":
    main()
