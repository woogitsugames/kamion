"""Open reference sources (D43, ADR 0066): mocked HTTP, no network, no keys.

Run: uv run --project tools/refs pytest tests/refs -q
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "refs"))

import bialystok_open_data as bod  # noqa: E402
import gugik_ortho as go  # noqa: E402
import open_sources as osrc  # noqa: E402
import refs_common as rc  # noqa: E402


def jpg_bytes(color=(90, 120, 90)):
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", (64, 48), color).save(b, "JPEG")
    return b.getvalue()


class Resp:
    def __init__(self, status=200, body=None, content=b"", headers=None):
        self.status_code, self._body, self.content, self.headers = status, body, content, headers or {}

    def json(self):
        return self._body


class Session:
    """Routes by URL substring: handlers return a Resp or a JSON-able body."""

    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def _route(self, method, url, params, data, headers):
        self.calls.append((method, url, params, data, dict(headers or {})))
        for key, h in self.routes:
            if key in url:
                r = h(params, data) if callable(h) else h
                return r if isinstance(r, Resp) else Resp(200, r)
        return Resp(404)

    def get(self, url, params=None, headers=None, timeout=None):
        return self._route("GET", url, params, None, headers)

    def post(self, url, data=None, headers=None, timeout=None):
        return self._route("POST", url, None, data, headers)


def http_for(routes, tmp_path, retries=2):
    return rc.Http(cache_dir=tmp_path / "cache", session=Session(routes), sleep=lambda s: None, min_interval=0, retries=retries)


POINT = {"nr": 7, "type": "kadr gate3", "place": "test", "lat": 53.1545, "lon": 23.1702, "s_m": 0, "azimuth": 209.0}


# ---------------------------------------------------------------- licence policy / route

@pytest.mark.parametrize("text,key", [
    ("CC0 1.0", "cc0"), ("CC0", "cc0"), ("Public domain", "pdm"), ("pdm", "pdm"), ("PD-self", "pdm"),
    ("CC BY 4.0", "by"), ("by", "by"), ("CC-BY-4.0", "by"), ("CC BY-SA 4.0", "by-sa"), ("CC-BY-SA-4.0", "by-sa"),
    ("by-sa", "by-sa"), ("CC BY-NC 2.0", None), ("by-nc-sa", None), ("CC BY-ND 4.0", None), ("by-nd", None),
    ("All rights reserved", None), ("", None), (None, None), ("restricted Personality rights", None),
])
def test_normalize_license(text, key):
    assert rc.normalize_license(text) == key


def test_usage_classes():
    assert rc.usage_class("cc0") == rc.usage_class("by") == "texture_ok"
    assert rc.usage_class("by-sa").startswith("reference_only")
    assert rc.usage_class(None) == "rejected"


def test_photo_list_parses_55_shots_in_route_order():
    pts = rc.parse_photo_list()
    assert len(pts) == 55
    assert [p["nr"] for p in pts] == list(range(1, 56))
    assert all(53.1 < p["lat"] < 53.2 and 23.1 < p["lon"] < 23.2 for p in pts)
    assert [p["s_m"] for p in pts] == sorted(p["s_m"] for p in pts)


def test_weak_shots(tmp_path):
    f = tmp_path / "coverage.json"
    assert rc.weak_shots(tmp_path / "none.json") is None
    f.write_text(json.dumps({"1": "DOBRE", "2": "SŁABE", "3": "BRAK"}), encoding="utf-8")
    assert rc.weak_shots(f) == {2, 3}
    f.write_text(json.dumps([{"nr": 4, "status": "brak"}, {"nr": 5, "status": "OK"}]), encoding="utf-8")
    assert rc.weak_shots(f) == {4}


# ---------------------------------------------------------------- HTTP client

def test_http_retries_429_and_caches(tmp_path):
    n = {"c": 0}

    def h(params, data):
        n["c"] += 1
        return Resp(429, headers={"Retry-After": "1"}) if n["c"] == 1 else {"ok": True}

    http = http_for([("x.test", h)], tmp_path)
    assert http.get_json("https://x.test/a", {"q": 1}) == {"ok": True}
    assert n["c"] == 2
    assert http.get_json("https://x.test/a", {"q": 1}) == {"ok": True}  # cached
    assert n["c"] == 2


def test_http_gives_up_after_retries(tmp_path):
    http = http_for([("x.test", Resp(503))], tmp_path, retries=1)
    with pytest.raises(rc.SourceError):
        http.get_json("https://x.test/a")
    assert http.requests_made == 2


def test_http_retries_network_error_then_gives_up(tmp_path):
    n = {"c": 0}

    def h(params, data):
        n["c"] += 1
        if n["c"] == 1:
            raise ConnectionResetError("reset")
        return {"ok": True}

    http = http_for([("x.test", h)], tmp_path)
    assert http.get_json("https://x.test/a") == {"ok": True}
    assert n["c"] == 2

    def always(params, data):
        raise TimeoutError("slow")

    http = http_for([("y.test", always)], tmp_path, retries=1)
    with pytest.raises(rc.SourceError):
        http.get_json("https://y.test/a")
    assert http.requests_made == 2


def test_http_does_not_swallow_programming_errors(tmp_path):
    def h(params, data):
        raise ValueError("bug")

    with pytest.raises(ValueError):
        http_for([("x.test", h)], tmp_path).get_json("https://x.test/a")


# ---------------------------------------------------------------- KartaView

KV1 = {"currentPageItems": [
    {"id": "11", "sequence_id": "5", "sequence_index": "3", "lat": "53.15451", "lng": "23.17021", "heading": "205.0",
     "name": "storage13/files/photo/2021/6/24/proc/a.jpg", "shot_date": "2021-06-23 10:33:51.000", "username": "alice", "projection": "PLANE"},
    {"id": "12", "sequence_id": "5", "sequence_index": "4", "lat": "53.15452", "lng": "23.17022", "heading": "30.0",
     "name": "storage13/files/photo/2021/6/24/proc/b.jpg", "shot_date": "2021-06-23", "username": "bob", "projection": "PLANE"},
    {"id": "13", "sequence_id": "5", "sequence_index": "5", "lat": "53.15450", "lng": "23.17020", "heading": "205.0",
     "name": "storage13/files/photo/2021/6/24/proc/c.jpg", "projection": "SPHERE"},
]}


def test_kartaview_v1_parses_and_filters(tmp_path):
    http = http_for([("1.0/list/nearby-photos", KV1)], tmp_path)
    c = osrc.kartaview_v1_candidates(POINT, http)
    assert [x["id"] for x in c] == ["kv11", "kv12"]  # spherical dropped
    assert c[0]["file_url"] == "https://storage13.openstreetcam.org/files/photo/2021/6/24/proc/a.jpg"
    assert c[0]["author"] == "alice" and c[0]["date"] == "2021-06-23"


def test_kartaview_pipeline_manifest_and_idempotent(tmp_path):
    img = jpg_bytes()
    routes = [("1.0/list/nearby-photos", KV1), ("2.0/photo", {"result": {"data": []}}),
              ("openstreetcam.org/files", Resp(200, content=img))]
    http = http_for(routes, tmp_path)
    out = tmp_path / "raw"
    e, st = rc.fetch_for_points("kartaview", [POINT], osrc.kartaview_all, http, out, per_point=4, azimuth_tol=40)
    assert set(e) == {"kv11"}  # heading 30 deg is > 40 deg from azimuth 209
    m = e["kv11"]
    assert m["sha256"] == hashlib.sha256(img).hexdigest()
    assert m["license_key"] == "by-sa" and m["usage"].startswith("reference_only")
    assert m["author"] == "alice" and m["page_url"].startswith("https://kartaview.org/details/")
    assert m["shots"] == [7] and (out / "kv11.jpg").read_bytes() == img
    first = (out / "manifest.jsonl").read_bytes()
    _, st2 = rc.fetch_for_points("kartaview", [POINT], osrc.kartaview_all, http, out, per_point=4, azimuth_tol=40)
    assert st2["downloaded"] == 0 and (out / "manifest.jsonl").read_bytes() == first


def test_download_404_is_skipped_not_fatal(tmp_path):
    routes = [("1.0/list/nearby-photos", KV1), ("2.0/photo", {"result": {"data": []}}), ("openstreetcam.org/files", Resp(404))]
    e, st = rc.fetch_for_points("kartaview", [POINT], osrc.kartaview_all, http_for(routes, tmp_path), tmp_path / "raw")
    assert e == {} and st["failed"] == 2


# ---------------------------------------------------------------- Panoramax

def px_feature(fid, lic, az=209):
    return {"id": fid, "geometry": {"type": "Point", "coordinates": [23.1702, 53.1545]}, "properties": {
        "license": lic, "datetime": "2019-08-15T15:32:28+00:00", "view:azimuth": az},
        "links": [{"rel": "license", "href": "https://creativecommons.org/licenses/by-sa/4.0/"},
                  {"rel": "via", "href": "https://panoramax.openstreetmap.fr"}],
        "providers": [{"name": "stanton", "roles": ["producer"]}],
        "assets": {"sd": {"href": f"https://px.test/{fid}/sd.jpg"}}}


def test_panoramax_license_per_feature(tmp_path):
    img = jpg_bytes()
    routes = [("api.panoramax.xyz/api/search", {"features": [px_feature("a", "CC-BY-SA-4.0"), px_feature("b", "CC-BY-NC-4.0")]}),
              ("px.test", Resp(200, content=img))]
    e, st = rc.fetch_for_points("panoramax", [POINT], osrc.panoramax_candidates, http_for(routes, tmp_path), tmp_path / "raw")
    assert set(e) == {"pxa"} and st["rejected_license"] == 1
    assert e["pxa"]["author"] == "stanton" and "panoramax.openstreetmap.fr" in e["pxa"]["page_url"]


# ---------------------------------------------------------------- Commons

def commons_routes(img):
    geos = {"query": {"geosearch": [
        {"pageid": 1, "title": "File:Good.jpg", "lat": 53.1546, "lon": 23.1703},
        {"pageid": 2, "title": "File:NC.jpg", "lat": 53.1547, "lon": 23.1703},
        {"pageid": 3, "title": "File:PD.jpg", "lat": 53.1548, "lon": 23.1703}]}}

    def ii(lic, artist, url="https://upload.test/x.jpg"):
        return {"mime": "image/jpeg", "url": url, "thumburl": url, "descriptionurl": "https://commons.test/wiki/File:x",
                "extmetadata": {"LicenseShortName": {"value": lic}, "Artist": {"value": f'<a href="u">{artist}</a>'},
                                "DateTimeOriginal": {"value": "2020-11-05 16:13:05"}}}

    info = {"query": {"pages": {
        "1": {"title": "File:Good.jpg", "imageinfo": [ii("CC BY-SA 4.0", "Rakoon")]},
        "2": {"title": "File:NC.jpg", "imageinfo": [ii("CC BY-NC 2.0", "Eve")]},
        "3": {"title": "File:PD.jpg", "imageinfo": [ii("Public domain", "John Harvey")]}}}}

    def api(params, data):
        return geos if params.get("list") == "geosearch" else info

    return [("commons.wikimedia.org/w/api.php", api), ("upload.test", Resp(200, content=img))]


def test_commons_geosearch_extmetadata_and_licence_gate(tmp_path):
    img = jpg_bytes()
    e, st = rc.fetch_for_points("commons", [POINT], osrc.commons_candidates, http_for(commons_routes(img), tmp_path), tmp_path / "raw")
    assert set(e) == {"cm1", "cm3"} and st["rejected_license"] == 1
    assert e["cm1"]["author"] == "Rakoon" and e["cm1"]["captured_at"] == "2020-11-05"  # HTML stripped
    assert e["cm1"]["usage"].startswith("reference_only") and e["cm3"]["usage"] == "texture_ok"
    assert e["cm1"]["sha256"] == hashlib.sha256(img).hexdigest()


def test_commons_category_missing_reports_not_exists(tmp_path):
    routes = [("commons.wikimedia.org/w/api.php", {"query": {}})]
    ok, c = osrc.commons_category_candidates(http_for(routes, tmp_path), "Nope")
    assert ok is False and c == []


# ---------------------------------------------------------------- Openverse

def test_openverse_rejects_nc_nd_even_if_server_returns_them(tmp_path):
    img = jpg_bytes()
    results = [
        {"id": "a", "title": "A", "creator": "x", "license": "by", "license_version": "2.0", "license_url": "u", "url": "https://ov.test/a.jpg", "foreign_landing_url": "p"},
        {"id": "b", "title": "B", "creator": "y", "license": "by-nc", "license_version": "2.0", "license_url": "u", "url": "https://ov.test/b.jpg", "foreign_landing_url": "p"},
        {"id": "c", "title": "C", "creator": "z", "license": "cc0", "license_version": "1.0", "license_url": "u", "url": "https://ov.test/c.jpg", "foreign_landing_url": "p"},
        {"id": "d", "title": "D", "creator": "w", "license": "by-nd", "license_version": "2.0", "license_url": "u", "url": "https://ov.test/d.jpg", "foreign_landing_url": "p"},
    ]
    sess = Session([("api.openverse.org", {"results": results}), ("ov.test", Resp(200, content=img))])
    http = rc.Http(cache_dir=tmp_path / "c", session=sess, sleep=lambda s: None, min_interval=0)
    items = [("Białystok rondo", lambda h: osrc.openverse_candidates_for_query(h, "Białystok rondo"))]
    e, _ = osrc.fetch_text_source("openverse", items, None, http, tmp_path / "raw")
    assert set(e) == {"ova", "ovc"}
    assert e["ova"]["license_key"] == "by" and e["ovc"]["license_key"] == "cc0"
    assert sess.calls[0][2]["license"] == "cc0,pdm,by,by-sa"  # server-side filter also asks for CC only


# ---------------------------------------------------------------- GUGiK ortho

def test_ortho_bbox_is_epsg2180_and_params(tmp_path):
    bb, (x, y) = go.shot_bbox_2180(23.1702, 53.1545, 160)
    assert 770000 < x < 790000 and 590000 < y < 600000  # region sheets lie at ~777-779k / 595-597k
    assert pytest.approx(bb[2] - bb[0]) == 160 and pytest.approx(bb[3] - bb[1]) == 160
    p = go.wms_params(bb, 640)
    assert p["SRS"] == "EPSG:2180" and p["VERSION"] == "1.1.1" and p["WIDTH"] == 640


def test_ortho_retries_blank_tiles(tmp_path):
    from PIL import Image
    blank = io.BytesIO()
    Image.new("RGB", (32, 32), (255, 255, 255)).save(blank, "PNG")
    good = io.BytesIO()
    Image.new("RGB", (32, 32), (60, 90, 50)).save(good, "PNG")
    seq = [blank.getvalue(), blank.getvalue(), good.getvalue()]

    def h(params, data):
        return Resp(200, content=seq.pop(0) if len(seq) > 1 else seq[0])

    http = http_for([("geoportal.gov.pl", h)], tmp_path)
    e = go.fetch([POINT], http, tmp_path / "raw", log=lambda *_: None)
    assert "ortho7" in e and e["ortho7"]["crs"] == "EPSG:2180" and "Główny Urząd Geodezji" in e["ortho7"]["attribution"]
    assert not go.is_blank(tmp_path / "raw" / "shot_07.png")


# ---------------------------------------------------------------- Białystok open data

def test_bialystok_layers_queried_by_route_bbox(tmp_path):
    fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"a": 1}, "geometry": None}]}
    sess = Session([("services6.arcgis.com", fc)])
    http = rc.Http(cache_dir=tmp_path / "c", session=sess, sleep=lambda s: None, min_interval=0)
    e = bod.fetch([POINT, dict(POINT, nr=8, lon=23.18, lat=53.16)], http, tmp_path / "raw", log=lambda *_: None)
    assert len(e) == len(bod.LAYERS) and e["parki"]["feature_count"] == 1
    assert e["parki"]["license_key"] == "unspecified" and "LEGAL_REVIEW_REQUIRED" in e["parki"]["license"]
    params = sess.calls[0][2]
    assert params["inSR"] == 4326 and params["f"] == "geojson"
    x0, y0, x1, y1 = (float(v) for v in params["geometry"].split(","))
    assert x0 < 23.1702 and x1 > 23.18 and y0 < 53.1545 and y1 > 53.16
    # idempotent bytes
    before = (tmp_path / "raw" / "parki.geojson").read_bytes()
    bod.fetch([POINT, dict(POINT, nr=8, lon=23.18, lat=53.16)], http, tmp_path / "raw", log=lambda *_: None)
    assert (tmp_path / "raw" / "parki.geojson").read_bytes() == before


def test_montage_is_made_from_manifest(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.jpg").write_bytes(jpg_bytes())
    ent = {"a": {"id": "a", "file": "a.jpg", "shots": [7], "license": "CC BY-SA 4.0", "author": "x", "captured_at": "2020-01-01"}}
    assert rc.montages_for("test", [POINT], ent, raw, tmp_path / "art") == 1
    assert (tmp_path / "art" / "shot_07.jpg").stat().st_size > 0
