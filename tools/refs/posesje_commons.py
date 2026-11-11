r"""Referencje posesji (ADR 0114), uzupelnienie: Wikimedia Commons (CC0/BY/BY-SA wg extmetadata) - ogrodzenia, bramy,
domy jednorodzinne w Bialymstoku i na Podlasiu. Pliki: Data/raw/refs/posesje/ (poza gitem) + manifest.jsonl.

  uv run --project tools/refs python tools/refs/posesje_commons.py [--list-only] [--per-query 6]
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refs_common as rc  # noqa: E402
import open_sources as os_  # noqa: E402

QUERIES = [
    "ogrodzenie dom jednorodzinny Białystok", "płot drewniany Białystok", "brama wjazdowa posesja Białystok",
    "Białystok ulica domy jednorodzinne", "Dojlidy Białystok dom", "Bacieczki Białystok", "Wysoki Stoczek Białystok",
    "Zawady Białystok", "Zaścianki Białystok", "Kleosin dom", "Wasilków ulica domy", "Podlasie płot sztachety",
    "Podlasie dom drewniany ogrodzenie", "ogrodzenie panelowe", "ogrodzenie z siatki dom", "furtka ogrodzenie Polska",
    "zjazd z drogi obniżony krawężnik", "podjazd kostka brukowa dom", "tuje żywopłot ogrodzenie", "skrzynka na listy ogrodzenie",
    "ogrodzenie betonowe prefabrykowane", "ogrodzenie z klinkieru słupki", "brama przesuwna posesja",
]


def search_cands(q, limit=15):
    def getter(http):
        body = http.get_json(os_.CM_API, {"action": "query", "format": "json", "list": "search", "srsearch": q,
                                          "srnamespace": 6, "srlimit": limit})
        titles = [h["title"] for h in (body.get("query") or {}).get("search", [])]
        infos = os_._commons_imageinfo(http, titles)
        out = []
        for t in titles:
            if t in infos:
                c = os_._commons_cand(t, infos[t])
                if c:
                    out.append(c)
        return out
    return getter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-only", action="store_true")
    ap.add_argument("--per-query", type=int, default=6)
    ap.add_argument("--max", type=int, default=120)
    ap.add_argument("--only", nargs="*", help="tylko zapytania zawierajace te frazy")
    a = ap.parse_args()
    outdir = rc.RAW_ROOT / "posesje"
    outdir.mkdir(parents=True, exist_ok=True)
    http = rc.Http(cache_dir=outdir / ".cache")
    items = [(q, search_cands(q)) for q in QUERIES if not a.only or any(o in q for o in a.only)]
    if a.list_only:
        for q, g in items:
            print("##", q)
            try:
                for c in g(http):
                    print("  ", c["id"], rc.normalize_license(c["license"]), c["title"][:90])
            except rc.SourceError as e:
                print("   ERR", e)
        return
    os_.fetch_text_source("commons-posesje", items, None, http, outdir, per_item=a.per_query, max_total=a.max)


main()
