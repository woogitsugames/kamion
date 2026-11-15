"""Download Commons thumbs (<=1600 px) for titles in list file; write photos/<id>.jpg (q82, <=1600) + view/<id>.jpg (<=960) + photos_meta.json"""
import json, sys, time, hashlib, io, os, requests, re
from PIL import Image
UA = {"User-Agent": "research-client/1.0 (generic)"}
pool = {}
for f in sys.argv[3:]:
    j = json.load(open(f)); pool.update(j.get("files", j))
lst = [l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]
od = sys.argv[2]; os.makedirs(od + "/files", exist_ok=True); os.makedirs(od + "/view", exist_ok=True)
metaf = od + "/photos_meta.json"
meta = json.load(open(metaf)) if os.path.exists(metaf) else {}
for line in lst:
    pid, title = line.split("|", 1)
    if pid in meta: continue
    f = pool.get(title)
    if not f: print("MISSING", title); continue
    import urllib.parse
    url = "https://commons.wikimedia.org/w/thumb.php?f=" + urllib.parse.quote(title[5:].replace(" ", "_")) + "&w=1600"
    ok = False
    for a in range(8):
        r = requests.get(url, headers=UA, timeout=120)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"): ok = True; break
        print("  retry", r.status_code, flush=True); time.sleep(15 * (a + 1))
    if not ok: print("FAIL", pid); continue
    im = Image.open(io.BytesIO(r.content)).convert("RGB"); im.thumbnail((1600, 1600))
    p = f"{od}/files/{pid}.jpg"; im.save(p, quality=82)
    v = im.copy(); v.thumbnail((960, 960)); v.save(f"{od}/view/{pid}.jpg", quality=85)
    sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
    artist = re.sub("<[^>]+>", "", f.get("artist") or "").strip()
    meta[pid] = {"title": title, "page": f.get("page"), "file_url": f.get("url"), "thumb_url": url, "sha256": sha, "commons_sha1": f.get("sha1"), "license": f.get("license"), "artist": artist,
                 "date": f.get("date"), "coords": f.get("coords"), "size": im.size}
    print(pid, im.size, f.get("license"), title[:70], flush=True)
    json.dump(meta, open(metaf, "w"), ensure_ascii=False, indent=1)
    time.sleep(4)
json.dump(meta, open(metaf, "w"), ensure_ascii=False, indent=1)
