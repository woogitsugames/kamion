"""scripts/postbuild-windows.py (ADR 0276): content hash of Kamion_Data, build-id.json, region launchers. No Unity.

    uv run --no-project --with pytest pytest tests/dist -q
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def load():
    spec = importlib.util.spec_from_file_location("postbuild_windows_t", REPO / "scripts" / "postbuild-windows.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


pb = load()
SHA = "e28533ca31"

# The real line of BuildCommands.BuildWindowsPlayer (d67-full build of INTEGRATION-2026-11-15-int-pc-s23, shortened).
LOG_LINE = ("[BUILD] Windows x64 \u2192 C:/kamion/artifacts/win/kamion-0.1.0-e28533ca31-regions/Kamion.exe "
            "(development=False, worldHigh=True) scenes=[Assets/_Project/Scenes/Boot.unity, "
            "Assets/_Project/Scenes/DrivingLab.unity, Assets/_Generated/World/bialystok-industrial-c/WorldC.unity, "
            "Assets/_Generated/World/bialystok-industrial-c/WorldC_High.unity, "
            "Assets/_Generated/World/dk65-01/World_dk65-01.unity, Assets/_Generated/World/dk65-01/World_dk65-01_High.unity, "
            "Assets/_Generated/World/knyszyn/World_knyszyn.unity, Assets/_Generated/World/knyszyn/World_knyszyn_High.unity, "
            "Assets/_Generated/World/knyszyn-w/World_knyszyn-w.unity]")


def make_build(root: Path, data: dict[str, bytes] | None = None) -> Path:
    b = root / f"kamion-0.1.0-{SHA}-regions"
    files = {
        "Kamion.exe": b"MZ stub",
        "UnityPlayer.dll": b"MZ player",
        "Kamion_Data/globalgamemanagers": b"ggm",
        "Kamion_Data/level0": b"scene0",
        "Kamion_Data/Managed/Assembly-CSharp.dll": b"MZ managed",
        "Kamion_Data/Plugins/x86_64/x.pdb": b"pdb in data - not hashed (not shipped)",
        "Kamion_Data/StreamingAssets/a b/\u017c\u00f3\u0142w.txt": b"unicode path",
        "Kamion_BurstDebugInformation_DoNotShip/Data/x.txt": b"dbg",
    }
    files.update(data or {})
    for rel, d in files.items():
        p = b / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(d)
    return b


def test_manifest_scope_sorted_and_hash_definition(tmp_path):
    b = make_build(tmp_path)
    entries = pb.data_manifest(b)
    paths = [e[0] for e in entries]
    assert all(p.startswith("Kamion_Data/") for p in paths)
    assert not any(p.endswith(".pdb") for p in paths)
    assert paths == sorted(paths, key=lambda p: p.encode("utf-8"))
    assert len(paths) == 4
    text = "".join(f"{hashlib.sha256((b / p).read_bytes()).hexdigest()}  {p}\n" for p in paths)
    full = hashlib.sha256(text.encode("utf-8")).hexdigest()
    doc = pb.build_id(entries, SHA)
    assert doc["contentSha256"] == full and doc["contentHash"] == full[:12]
    assert doc["contentFiles"] == 4 and doc["gitSha"] == SHA and doc["schema"] == "kamion/build-id/1"


def test_hash_ignores_root_files_and_its_own_output(tmp_path):
    """build-id.json / launchers / the manifest live next to the exe: writing them never changes the hash."""
    b = make_build(tmp_path)
    before = pb.build_id(pb.data_manifest(b), SHA)["contentSha256"]
    pb.write_build_id(b, pb.data_manifest(b), SHA)
    pb.write_launchers(b, ["knyszyn"])
    (b / "build.json").write_text("{}")
    (b / "Kamion.exe").write_bytes(b"MZ another stub")
    assert pb.build_id(pb.data_manifest(b), SHA)["contentSha256"] == before
    assert (b / "Kamion_Data.sha256").read_text().count("\n") == 4


def test_any_data_change_changes_the_hash(tmp_path):
    a = pb.build_id(pb.data_manifest(make_build(tmp_path / "a")), SHA)["contentHash"]
    b = pb.build_id(pb.data_manifest(make_build(tmp_path / "b", {"Kamion_Data/level0": b"scene0 "})), SHA)["contentHash"]
    c = pb.build_id(pb.data_manifest(make_build(tmp_path / "c", {"Kamion_Data/level1": b"new"})), SHA)["contentHash"]
    d_dir = make_build(tmp_path / "d")
    (d_dir / "Kamion_Data/level0").rename(d_dir / "Kamion_Data/level9")       # same bytes, other name
    d = pb.build_id(pb.data_manifest(d_dir), SHA)["contentHash"]
    assert len({a, b, c, d}) == 4


def test_regions_from_log_expanded_low_scenes_in_order(tmp_path):
    log = "noise\n[BUILD] regions (3/4 in the APK): dk65-01, knyszyn, knyszyn-w, missing-one\n" + LOG_LINE + "\nmore\n"
    assert pb.regions_from_log(log) == ["bialystok-industrial-c", "dk65-01", "knyszyn", "knyszyn-w"]
    no_regions = "[BUILD] Windows x64 \u2192 x/Kamion.exe (development=False, worldHigh=True) scenes=[Assets/_Project/Scenes/Boot.unity]"
    assert pb.regions_from_log(no_regions) == []
    with pytest.raises(pb.PostBuildError):
        pb.regions_from_log("BUILD_RESULT: Succeeded")


def test_launchers_window_and_one_per_region(tmp_path):
    b = make_build(tmp_path)
    written, skipped = pb.write_launchers(b, ["knyszyn", "dk65-01", "bad id & del *", "okno"])
    assert written == ["Kamion-okno.cmd", "Kamion-knyszyn.cmd", "Kamion-dk65-01.cmd"]
    assert skipped == ["bad id & del *", "okno"]
    k = (b / "Kamion-knyszyn.cmd").read_bytes().decode("ascii")
    assert k == '@echo off\r\nstart "" "%~dp0Kamion.exe" -screen-fullscreen 0 -screen-width 1600 -screen-height 900 -scene knyszyn %*\r\n'
    w = (b / "Kamion-okno.cmd").read_bytes().decode("ascii")
    assert "-scene" not in w and w.endswith(" %*\r\n")


def test_cli_writes_build_id_and_check(tmp_path, capsys):
    b = make_build(tmp_path)
    log = tmp_path / "build.log"
    log.write_text(LOG_LINE + "\n", encoding="utf-8")
    assert pb.main([str(b), "--log", str(log), "--git-sha", SHA]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["regionIds"] == ["bialystok-industrial-c", "dk65-01", "knyszyn", "knyszyn-w"]
    assert "Kamion-knyszyn-w.cmd" in out["launchers"] and (b / "Kamion-knyszyn-w.cmd").is_file()
    doc = json.loads((b / "build-id.json").read_text(encoding="utf-8"))
    assert doc["contentHash"] == out["contentHash"] and len(doc["contentHash"]) == 12
    assert pb.main([str(b), "--check"]) == 0
    capsys.readouterr()
    (b / "Kamion_Data/level0").write_bytes(b"patched")
    assert pb.main([str(b), "--check"]) == 1


def test_missing_data_is_an_error(tmp_path):
    b = tmp_path / "empty"
    b.mkdir()
    assert pb.main([str(b)]) == 2


def test_csharp_reader_agrees_with_the_writer():
    """Game.Core.BuildInfo reads exactly what this script writes (file name, key, 12 hex digits)."""
    cs = (REPO / "game/Assets/_Project/Core/BuildInfo.cs").read_text(encoding="utf-8")
    assert f'BuildIdFileName = "{pb.BUILD_ID}"' in cs
    assert f"ContentHashLength = {pb.SHORT}" in cs
    assert '\\"contentHash\\"' in cs


def test_corridor_launcher_only_with_knyszyn_and_knyszyn_s(tmp_path):
    """int-stream-s23: Kamion-korytarz.cmd = knyszyn + streaming, borderless full screen."""
    b = tmp_path / "a"; b.mkdir()
    written, _ = pb.write_launchers(b, ["knyszyn", "dk65-11"])
    assert "Kamion-korytarz.cmd" not in written
    b2 = tmp_path / "b"; b2.mkdir()
    written, _ = pb.write_launchers(b2, ["knyszyn-s", "knyszyn"])
    assert written[-1] == "Kamion-korytarz.cmd"
    k = (b2 / "Kamion-korytarz.cmd").read_bytes().decode("ascii")
    assert k.startswith("@echo off\r\n") and "-scene knyszyn -stream 1 %*" in k and "-window-mode borderless" in k
