"""Fetch and verify CC0 Poly Haven 4K PureSky HDRIs into ignored Data/raw/cc0/sky/."""
import hashlib, json, os, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "Data" / "raw" / "cc0" / "sky"
ASSETS = [
    "kloofendal_48d_partly_cloudy_puresky",
    "sunflowers_puresky",
    "kloofendal_38d_partly_cloudy_puresky",
    "kloppenheim_03_puresky",
]

for asset in ASSETS:
    d = RAW / asset
    d.mkdir(parents=True, exist_ok=True)
    fjson = d / "files.json"
    ijson = d / "info.json"
    if not fjson.exists():
        req = urllib.request.Request(f"https://api.polyhaven.com/files/{asset}", headers={"User-Agent": "kamion-sky/1.0"})
        fjson.write_bytes(urllib.request.urlopen(req, timeout=15).read())
    if not ijson.exists():
        req = urllib.request.Request(f"https://api.polyhaven.com/info/{asset}", headers={"User-Agent": "kamion-sky/1.0"})
        ijson.write_bytes(urllib.request.urlopen(req, timeout=15).read())
    files = json.loads(fjson.read_text(encoding="utf-8-sig"))
    info = json.loads(ijson.read_text(encoding="utf-8-sig"))
    hdr = files["hdri"]["4k"]["hdr"]
    out = d / f"{asset}_4k.hdr"
    if not out.exists() or out.stat().st_size != hdr["size"]:
        print(f"Downloading {asset} ({hdr['size']/1e6:.1f} MB)...")
        req = urllib.request.Request(hdr["url"], headers={"User-Agent": "kamion-sky/1.0"})
        data = urllib.request.urlopen(req, timeout=60).read()
        out.write_bytes(data)
    raw = out.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    sha = hashlib.sha256(raw).hexdigest()
    if md5 != hdr["md5"] or len(raw) != hdr["size"]:
        raise SystemExit(f"MD5/size mismatch for {asset}: got {md5} ({len(raw)}) expected {hdr['md5']} ({hdr['size']})")
    print(f"VERIFIED {asset}: size={len(raw)} md5={md5} sha256={sha} authors={info.get('authors')}")
