"""Text search of Wikimedia Commons for reference photos (CC0 / PD / CC BY / CC BY-SA only).

    uv run --no-project python tools/refs/commons_search.py --out Data/raw/refs/commons-trees --per 3 "query" ...

Writes <out>/cs<pageid>.jpg (1280 px thumbnail) and appends <out>/manifest.jsonl (title, author, licence, page url, query).
References only: never shipped in the build (docs/LICENSES.md, D43).
"""
import argparse, hashlib, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
UA = "refs-fetch/1.0 (reference photo research; python-urllib)"
OK = re.compile(r"^(cc0|pd|public domain|cc[ -]by([ -]sa)?[ -][0-9.]+)", re.I)


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    return data if binary else json.loads(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--per", type=int, default=3)
    ap.add_argument("queries", nargs="+")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    man = out / "manifest.jsonl"
    seen = {json.loads(l)["id"] for l in man.read_text(encoding="utf-8").splitlines()} if man.exists() else set()
    for q in a.queries:
        url = API + "?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "generator": "search", "gsrsearch": q + " filetype:bitmap",
            "gsrnamespace": 6, "gsrlimit": a.per * 3, "prop": "imageinfo", "iiprop": "url|extmetadata|size",
            "iiurlwidth": 1280})
        try:
            pages = get(url).get("query", {}).get("pages", {})
        except Exception as e:
            print("FAIL", q, e); continue
        n = 0
        for p in sorted(pages.values(), key=lambda p: p.get("index", 0)):
            if n >= a.per: break
            ii = (p.get("imageinfo") or [{}])[0]
            em = ii.get("extmetadata", {})
            lic = em.get("LicenseShortName", {}).get("value", "")
            pid = f"cs{p['pageid']}"
            if not OK.match(lic) or pid in seen or not ii.get("thumburl"): continue
            try:
                data = get(ii["thumburl"], True)
            except Exception as e:
                print("FAIL", p["title"], e); continue
            (out / f"{pid}.jpg").write_bytes(data)
            rec = {"id": pid, "file": f"{pid}.jpg", "title": p["title"], "query": q, "license": lic,
                   "license_url": em.get("LicenseUrl", {}).get("value", ""),
                   "author": re.sub(r"<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip()[:120],
                   "page_url": ii.get("descriptionurl", ""), "sha256": hashlib.sha256(data).hexdigest(),
                   "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            with man.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            seen.add(pid); n += 1
            print("OK", pid, lic, p["title"])
            time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
