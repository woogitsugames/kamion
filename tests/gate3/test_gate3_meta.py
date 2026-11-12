"""APK identity + duplicate-frame checks of scripts/gate3_meta.py and gate3_evidence.py (r7 section 7 / 14 #1). Synthetic data only.

    uv run --project tools/worldgen --with pillow --with pytest pytest tests/gate3 -q
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


gm = load("gate3_meta")


def make_apk(d: Path, name: str, payload: bytes = b"apk") -> Path:
    p = d / name
    p.write_bytes(payload)
    return p


def test_parse_apk_name_variants():
    assert gm.parse_apk_name("kamion-0.1.0-e3671b4309-high.apk") == {"version": "0.1.0", "sha": "e3671b4309", "dirty": False, "high": True, "dev": False}
    i = gm.parse_apk_name("kamion-0.1.0-f6abb8b001-dirty.apk")
    assert i["dirty"] and not i["high"]
    i = gm.parse_apk_name("kamion-0.1.0-f6abb8b001-dirty-high-dev.apk")
    assert i["dirty"] and i["high"] and i["dev"]
    assert gm.parse_apk_name("something.apk") is None


def test_apk_meta_uses_name_sha_not_head(tmp_path):
    apk = make_apk(tmp_path, "kamion-0.1.0-e3671b4309-high.apk", b"hello")
    m = gm.apk_meta(apk, head="dcb9064a4a" + "0" * 30)
    assert m["gitSha"] == "e3671b4309"
    assert m["apkFile"] == apk.name
    assert m["apkSha256"] == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert any("NOT of HEAD" in w for w in m["warnings"])
    assert not m["dirty"] and m["high"]


def test_apk_meta_matching_head_no_warning(tmp_path):
    apk = make_apk(tmp_path, "kamion-0.1.0-e3671b4309.apk")
    m = gm.apk_meta(apk, head="e3671b4309" + "f" * 30)
    assert m["warnings"] == []


def test_apk_meta_dirty_warns(tmp_path):
    apk = make_apk(tmp_path, "kamion-0.1.0-e3671b4309-dirty.apk")
    m = gm.apk_meta(apk, head="e3671b4309" + "f" * 30)
    assert m["dirty"] is True
    assert any("-dirty" in w for w in m["warnings"])


def test_apk_meta_sidecar_mismatch(tmp_path):
    apk = make_apk(tmp_path, "kamion-0.1.0-e3671b4309.apk", b"x")
    (tmp_path / (apk.name + ".sha256")).write_text("0" * 64 + "  " + apk.name)
    m = gm.apk_meta(apk, head="e3671b4309aa")
    assert any("declares" in w for w in m["warnings"])


def test_pick_apk_separates_low_and_high(tmp_path):
    import os
    low = make_apk(tmp_path, "kamion-0.1.0-aaaaaaa111.apk")
    high = make_apk(tmp_path, "kamion-0.1.0-bbbbbbb222-high.apk")
    dev = make_apk(tmp_path, "kamion-0.1.0-ccccccc333-dev.apk")
    os.utime(low, (1, 1))
    os.utime(high, (2, 2))
    os.utime(dev, (3, 3))   # newest of all: must still not be picked
    assert gm.pick_apk(tmp_path, high=False) == low
    assert gm.pick_apk(tmp_path, high=True) == high
    assert gm.pick_apk(tmp_path, high=True, dev=True) is None


def test_duplicate_frames_detected(tmp_path):
    (tmp_path / "g3b_eye_s1482.png").write_bytes(b"same")
    (tmp_path / "g3b_eye_s1532.png").write_bytes(b"same")
    (tmp_path / "g3b_eye_s1582.png").write_bytes(b"other")
    assert gm.duplicate_frames(tmp_path) == [["g3b_eye_s1482.png", "g3b_eye_s1532.png"]]


def test_no_duplicates(tmp_path):
    (tmp_path / "a.png").write_bytes(b"1")
    (tmp_path / "b.png").write_bytes(b"2")
    assert gm.duplicate_frames(tmp_path) == []


def test_evidence_check_unique_frames(tmp_path):
    ge = load("gate3_evidence")
    a, b, c = tmp_path / "a.png", tmp_path / "b.png", tmp_path / "c.png"
    a.write_bytes(b"1"); b.write_bytes(b"1"); c.write_bytes(b"2")
    r = ge.check_unique_frames({"phone a": a, "phone b": b, "phone c": c})
    assert r["verdict"] == "FAIL" and r["duplicate_groups"] == 1
    assert ge.check_unique_frames({"phone a": a, "phone c": c})["verdict"] == "PASS"


def test_evidence_apk_info_from_results(tmp_path):
    ge = load("gate3_evidence")
    d = tmp_path / "run"
    d.mkdir()
    (d / "gate3-result.json").write_text(json.dumps({
        "gitSha": "dcb9064a4a", "apkFile": "kamion-0.1.0-e3671b4309-high.apk", "apkSha256": "ab" * 32}), encoding="utf-8")
    info = ge.discover_apk_info(tmp_path, None, tmp_path)
    assert info["git_sha"] == "e3671b4309"
    assert any("not the APK's build sha" in w for w in info["warnings"])
    assert info["apks"][0]["apkSha256"] == "ab" * 32


def test_evidence_apk_info_legacy_and_dirty(tmp_path):
    ge = load("gate3_evidence")
    (tmp_path / "gate3-result-G3-B.json").write_text(json.dumps({
        "gitSha": "c24042a", "apk": {"path": "C:\\x\\apk\\kamion-0.1.0-f6abb8b001-dirty.apk", "sha256": "cd" * 32}}), encoding="utf-8")
    info = ge.discover_apk_info(tmp_path, None, tmp_path)
    assert info["git_sha"] == "f6abb8b001"
    text = " ".join(info["warnings"])
    assert "-dirty" in text and "old format" in text


def test_evidence_apk_info_none(tmp_path):
    ge = load("gate3_evidence")
    info = ge.discover_apk_info(tmp_path, None, tmp_path)
    assert info["git_sha"] is None and info["warnings"]
