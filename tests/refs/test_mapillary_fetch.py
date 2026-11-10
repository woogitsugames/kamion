"""Mapillary fetcher tests: mocked HTTP, no network, no token.

Run: uv run --project tools/refs pytest tests/refs -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "refs"))

import mapillary_fetch as mf  # noqa: E402

REGION = "bialystok-industrial-c"
SECRET = "MLY|SECRET-TEST-TOKEN"
JPG = b"\xff\xd8fakejpegbytes"


class Resp:
    def __init__(self, status=200, body=None, content=b"", headers=None):
        self.status_code, self._body, self.content, self.headers = status, body, content, headers or {}

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, records, fail_first=0):
        self.records, self.fail_first, self.calls = records, fail_first, []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append((url, params, dict(headers or {})))
        if "graph.mapillary.com" in url:
            if self.fail_first > 0:
                self.fail_first -= 1
                return Resp(429, headers={"Retry-After": "2"})
            return Resp(200, {"data": self.records})
        return Resp(200, content=JPG)


def rec(iid, lon, lat, ang, pano=False, user="alice"):
    return {
        "id": iid, "captured_at": 1700000000000, "compass_angle": ang,
        "computed_geometry": {"type": "Point", "coordinates": [lon, lat]},
        "creator": {"username": user, "id": "u" + user}, "thumb_2048_url": f"https://cdn.example/{iid}.jpg",
        "is_pano": pano, "sequence": "seq1",
    }


@pytest.fixture
def origin_lonlat():
    from pyproj import Transformer
    o = mf._region_yaml(REGION)["origin"]
    return Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True).transform(o["x"], o["y"])


@pytest.fixture
def cams_file(tmp_path):
    f = tmp_path / "cams.json"
    f.write_text(json.dumps({"cameras": [
        {"id": "camN", "pos": [0.0, 0.0, 140.0], "look_at": [0.0, 40.0, 140.0]},   # looks north, azimuth 0
    ]}), encoding="utf-8")
    return f


def args(tmp_path, **kw):
    ns = mf.build_parser().parse_args(["--region", REGION])
    ns.out = str(tmp_path / "raw")
    ns.used_file = str(tmp_path / "used.json")
    ns.sheets_dir = str(tmp_path / "sheets")
    ns.attribution_out = str(tmp_path / "attr.md")
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def test_missing_token_is_readable_error(monkeypatch, tmp_path):
    monkeypatch.delenv("MAPILLARY_TOKEN", raising=False)
    monkeypatch.setattr(mf, "SECRETS_ENV", tmp_path / "absent.env")
    with pytest.raises(SystemExit) as e:
        mf.run(args(tmp_path))
    assert "MAPILLARY_TOKEN" in str(e.value) and "secrets.env" in str(e.value)
    with pytest.raises(mf.MapillaryError):
        mf.MapillaryClient("")


def test_tiling_respects_area_limit():
    box = (22.9, 53.0, 23.4, 53.3)
    tiles = mf.tile_bbox(box)
    assert len(tiles) > 1
    assert all((t[2] - t[0]) * (t[3] - t[1]) <= mf.MAX_TILE_DEG2 + 1e-12 for t in tiles)
    assert sum((t[2] - t[0]) * (t[3] - t[1]) for t in tiles) == pytest.approx(0.5 * 0.3)
    assert len(mf.tile_bbox((22.9, 53.1, 22.93, 53.12))) == 1


def test_region_bbox_is_bialystok():
    x0, y0, x1, y1 = mf.region_bbox_lonlat(REGION)
    assert 22.9 < x0 < x1 < 23.3 and 53.0 < y0 < y1 < 53.3
    assert (x1 - x0) * (y1 - y0) < mf.MAX_TILE_DEG2


def test_points_azimuth_and_selection(origin_lonlat, cams_file):
    cam = mf.load_points(cams_file, REGION)[0]
    assert cam["azimuth"] == pytest.approx(0.0)
    assert cam["lon"] == pytest.approx(origin_lonlat[0], abs=1e-6)
    lon, lat = cam["lon"], cam["lat"]
    dn = 10 / 111320.0
    records = [
        rec("1", lon, lat + dn, 350),                 # close, aligned (dev 10)
        rec("2", lon, lat + dn, 180),                 # wrong direction
        rec("3", lon, lat + dn, 10, pano=True),       # pano skipped
        rec("4", lon, lat + 100 / 111320.0, 0),       # 100 m away
        rec("5", lon, lat + 2 * dn, 41),              # just outside tolerance
        rec("6", lon, lat + 2 * dn, 39),              # inside
    ]
    got = [r["id"] for _, r in mf.select_for_camera(records, cam, 30, 40)]
    assert got == ["1", "6"]
    assert "3" in [r["id"] for _, r in mf.select_for_camera(records, cam, 30, 40, allow_pano=True)]


def test_fetch_points_manifest_cache_idempotence(tmp_path, origin_lonlat, cams_file, monkeypatch):
    monkeypatch.delenv("MAPILLARY_TOKEN", raising=False)
    lon, lat = origin_lonlat
    recs = [rec("111", lon, lat + 1e-4, 5, user="bob"), rec("222", lon, lat + 2e-4, 200)]
    sess = FakeSession(recs)
    client = mf.MapillaryClient(SECRET, session=sess, cache_dir=tmp_path / "raw" / ".cache", sleep=lambda s: None)
    a = args(tmp_path, points=str(cams_file))
    mf.run(a, client=client)
    man = tmp_path / "raw" / "manifest.jsonl"
    first = man.read_text(encoding="utf-8")
    e = json.loads(first.splitlines()[0])
    assert [json.loads(x)["id"] for x in first.splitlines()] == ["111"]
    assert e["author"] == "bob" and e["license"] == "CC BY-SA 4.0" and e["game_cameras"] == ["camN"]
    assert e["page_url"] == "https://www.mapillary.com/app/?pKey=111"
    import hashlib
    assert e["sha256"] == hashlib.sha256(JPG).hexdigest()
    assert (tmp_path / "raw" / "111.jpg").read_bytes() == JPG

    calls_before = len(sess.calls)
    mf.run(a, client=client)  # cached + already downloaded: no new HTTP at all
    assert len(sess.calls) == calls_before
    assert man.read_text(encoding="utf-8") == first


def test_token_only_in_header_never_in_params_or_download(tmp_path, origin_lonlat, cams_file):
    lon, lat = origin_lonlat
    sess = FakeSession([rec("9", lon, lat + 1e-4, 0)])
    client = mf.MapillaryClient(SECRET, session=sess, sleep=lambda s: None)
    mf.run(args(tmp_path, points=str(cams_file)), client=client)
    for url, params, headers in sess.calls:
        assert SECRET not in url and SECRET not in json.dumps(params or {})
        if "graph.mapillary.com" in url:
            assert headers["Authorization"] == f"OAuth {SECRET}"
        else:
            assert "Authorization" not in headers  # CDN download gets no token
    assert SECRET not in (tmp_path / "raw" / "manifest.jsonl").read_text(encoding="utf-8")


def test_backoff_on_429(tmp_path):
    sleeps = []
    sess = FakeSession([], fail_first=2)
    c = mf.MapillaryClient(SECRET, session=sess, sleep=sleeps.append)
    assert c.images_in_bbox((22.95, 53.12, 22.96, 53.13)) == []
    assert 2.0 in sleeps and len(sess.calls) == 3


def test_auth_error_is_clear():
    class S:
        def get(self, *a, **k):
            return Resp(401)
    c = mf.MapillaryClient(SECRET, session=S(), sleep=lambda s: None)
    with pytest.raises(mf.MapillaryError, match="rejected the token"):
        c.images_in_bbox((22.95, 53.12, 22.96, 53.13))


def test_region_mode_skips_pano_and_honours_max(tmp_path, origin_lonlat):
    lon, lat = origin_lonlat
    recs = [rec(str(i), lon, lat + i * 1e-5, 0) for i in range(1, 6)] + [rec("pano", lon, lat, 0, pano=True)]
    sess = FakeSession(recs)
    client = mf.MapillaryClient(SECRET, session=sess, sleep=lambda s: None)
    ents = mf.run(args(tmp_path, max=3), client=client)
    assert len(ents) == 3 and "pano" not in ents
    ents = mf.run(args(tmp_path / "p", max=10, pano=True), client=client)
    assert "pano" in ents


def test_paging_next_token_stripped():
    assert "access_token" not in mf._strip_query_param("https://graph.mapillary.com/images?after=x&access_token=T", "access_token")


def test_contact_sheet_and_attribution(tmp_path, origin_lonlat, cams_file):
    from PIL import Image
    lon, lat = origin_lonlat
    sess = FakeSession([rec("111", lon, lat + 1e-4, 0, user="carol")])
    client = mf.MapillaryClient(SECRET, session=sess, sleep=lambda s: None)
    mf.run(args(tmp_path, points=str(cams_file)), client=client)
    Image.new("RGB", (64, 48), (200, 50, 50)).save(tmp_path / "raw" / "111.jpg")  # make the fake jpg a real image
    mf.run(args(tmp_path, contact_sheet_only=True))
    sheet = tmp_path / "sheets" / "sheet_camN.jpg"
    assert sheet.exists() and Image.open(sheet).width >= 640
    mf.run(args(tmp_path, use=["111", "999"], attribution=True))
    txt = (tmp_path / "attr.md").read_text(encoding="utf-8")
    assert "carol" in txt and "pKey=111" in txt and "CC BY-SA 4.0" in txt and "999" in txt
    assert json.loads((tmp_path / "used.json").read_text()) == ["111", "999"]


def test_latest_game_frame(tmp_path):
    for ts in ("20260101", "20260102"):
        d = tmp_path / ts / "S24" / "cam"
        d.mkdir(parents=True)
        (d / "camN.png").write_bytes(b"x")
    import os
    os.utime(tmp_path / "20260101" / "S24" / "cam" / "camN.png", (1, 1))
    assert "20260102" in str(mf.latest_game_frame("camN", tmp_path))
    assert mf.latest_game_frame("nope", tmp_path) is None


def test_token_resolution_env_then_secrets_file(tmp_path):
    f = tmp_path / "secrets.env"
    f.write_text(chr(10).join(["# comment", "", "OTHER=1", 'MAPILLARY_TOKEN = "MLY|fromfile"', ""]), encoding="utf-8")
    assert mf.resolve_token({}, f) == "MLY|fromfile"
    assert mf.resolve_token({"MAPILLARY_TOKEN": "MLY|env"}, f) == "MLY|env"   # env wins
    f.write_text("MAPILLARY_TOKEN=" + chr(10), encoding="utf-8")                # empty value = none
    assert mf.resolve_token({}, f) == ""
    assert mf.resolve_token({}, tmp_path / "missing.env") == ""


def test_points_wgs84_format(tmp_path):
    f = tmp_path / "pts.json"
    f.write_text(json.dumps({"points": [
        {"id": "p01", "lat": 53.1, "lon": 23.1, "azimuth": 370.0},
        {"id": "p02", "lat": 53.2, "lon": 23.2, "azimuth": None},
    ]}), encoding="utf-8")
    pts = mf.load_points(f, REGION)
    assert pts == [{"id": "p01", "lon": 23.1, "lat": 53.1, "azimuth": pytest.approx(10.0)}]
