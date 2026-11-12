"""Query GUGiK "Skorowidze" (sheet index) WFS services for a bbox in EPSG:2180.

GUGiK publishes, per data product and per year of data currency (akt_rok), a WFS index layer whose
features are map sheets with download URLs on opendata.geoportal.gov.pl. We use WFS 1.0.0 because it
takes the bbox in x(east),y(north) order for EPSG:2180 (WFS 1.1/2.0 would flip to northing,easting).

Usage (from repo root):
    uv run tools/worldgen/gugik_index.py --bbox 776971 595199 779019 597247 [--product NMT ...]

Only official GUGiK endpoints are used (ADR 0002). Requests are paced (POLITE_DELAY_S).
"""

from __future__ import annotations

import argparse
import json
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import requests

USER_AGENT = "truck-sim-pl-worldgen/0.1 (open-data ingest; low volume)"
POLITE_DELAY_S = 1.0
WSS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK"

# product -> (WFS endpoint, layer-name template with {year}, years to scan)
INDEX_SERVICES: dict[str, tuple[str, str, range]] = {
    "NMT": (f"{WSS}/NumerycznyModelTerenuEVRF2007/WFS/Skorowidze", "gugik:SkorowidzNMT{year}", range(2018, 2027)),
    "NMPT": (f"{WSS}/NumerycznyModelPokryciaTerenuEVRF2007/WFS/Skorowidze", "gugik:SkorowidzNMPT{year}", range(2019, 2027)),
    "LIDAR": (f"{WSS}/DanePomiaroweLidarEVRF2007/WFS/Skorowidze", "gugik:SkorowidzDanychPomiarowychLIDAR{year}", range(2018, 2027)),
    "ORTO": (f"{WSS}/ORTO/WFS/Skorowidze", "gugik:SkorowidzOrtofomapy{year}", range(2018, 2027)),
}

GML = "{http://www.opengis.net/gml}"
GUGIK = "{http://www.gugik.gov.pl}"


@dataclass
class Sheet:
    product: str
    layer: str
    fid: str
    attrs: dict[str, str]
    ring: list[tuple[float, float]] = field(default_factory=list)

    @property
    def url(self) -> str | None:
        return self.attrs.get("url_do_pobrania")

    @property
    def date(self) -> str | None:
        return self.attrs.get("akt_data")


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


def get_feature(session: requests.Session, endpoint: str, layer: str,
                bbox: tuple[float, float, float, float]) -> bytes:
    params = {
        "SERVICE": "WFS", "VERSION": "1.0.0", "REQUEST": "GetFeature", "TYPENAME": layer,
        "SRSNAME": "EPSG:2180", "BBOX": ",".join(f"{v:.2f}" for v in bbox),
    }
    r = session.get(endpoint, params=params, timeout=120)
    r.raise_for_status()
    time.sleep(POLITE_DELAY_S)
    return r.content


def parse_features(product: str, layer: str, xml: bytes) -> list[Sheet]:
    root = ET.fromstring(xml)
    out: list[Sheet] = []
    for member in root.iter(f"{GML}featureMember"):
        feat = next(iter(member))
        attrs: dict[str, str] = {}
        ring: list[tuple[float, float]] = []
        for child in feat:
            tag = child.tag.replace(GUGIK, "")
            if tag == "msGeometry":
                coords = child.find(f".//{GML}outerBoundaryIs//{GML}coordinates")
                if coords is not None and coords.text:
                    ring = [tuple(map(float, p.split(","))) for p in coords.text.split()]
            elif tag.startswith("{"):
                continue
            else:
                attrs[tag] = (child.text or "").strip()
        out.append(Sheet(product, layer, feat.get("fid", ""), attrs, ring))
    return out


def query(product: str, bbox: tuple[float, float, float, float],
          session: requests.Session | None = None) -> list[Sheet]:
    endpoint, tmpl, years = INDEX_SERVICES[product]
    session = session or _session()
    sheets: list[Sheet] = []
    for year in years:
        layer = tmpl.format(year=year)
        try:
            xml = get_feature(session, endpoint, layer, bbox)
        except requests.HTTPError as e:  # a missing year layer is not fatal; report it
            print(f"[gugik_index] {product} {layer}: {e}")
            continue
        sheets.extend(parse_features(product, layer, xml))
    return sheets


def summarise(sheets: list[Sheet]) -> list[dict]:
    keep = ("godlo", "akt_rok", "akt_data", "piksel", "char_przestrz", "format", "uklad_xy", "uklad_h",
            "blad_sr_wys", "blad_sr_syt", "kolor", "url_do_pobrania", "wlk_pliku_mb", "dt_pzgik",
            "modul_archiwizacji", "asortyment", "zrodlo_danych", "czy_ark_wypelniony")
    return [{"product": s.product, "layer": s.layer, **{k: s.attrs[k] for k in keep if k in s.attrs}}
            for s in sheets]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bbox", nargs=4, type=float, required=True, metavar=("XMIN", "YMIN", "XMAX", "YMAX"))
    ap.add_argument("--product", nargs="*", default=list(INDEX_SERVICES))
    ap.add_argument("--json", action="store_true", help="print full JSON instead of a table")
    a = ap.parse_args()
    s = _session()
    allrows = []
    for p in a.product:
        rows = summarise(query(p, tuple(a.bbox), s))
        allrows.extend(rows)
        if not a.json:
            for r in rows:
                print(p, r.get("akt_rok"), r.get("akt_data"), r.get("godlo"),
                      r.get("piksel") or r.get("char_przestrz"), r.get("format", ""), r.get("uklad_h", ""),
                      r.get("wlk_pliku_mb", ""), re.sub(r"^https://opendata\.geoportal\.gov\.pl", "",
                                                         r.get("url_do_pobrania", "")))
    if a.json:
        print(json.dumps(allrows, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
