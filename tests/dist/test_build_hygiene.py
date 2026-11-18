"""build-hygiene-s23: corridor / D3D12 opt-in launchers (D3D11 default since ADR 0291) (postbuild-windows.py), their way into the tester zip
(package-windows.py), the scene check before a full build (check-build-scenes.py) and the region catalog invariants of
the full build (d67-full). No Unity, no real build.

    uv run --no-project --with pytest pytest tests/dist -q
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / file)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


cbs = load("check_build_scenes_t", "check-build-scenes.py")
pw = cbs.pw          # package-windows.py (same module instance as check-build-scenes uses)
pb = pw.postbuild    # postbuild-windows.py
SHA = "e28533ca31"
W = "Assets/_Generated/World/"


def log_line(scenes: list[str]) -> str:
    return ("[BUILD] Windows x64 \u2192 C:/k/Kamion.exe (development=False, worldHigh=True) scenes=["
            + ", ".join(["Assets/_Project/Core/Scenes/Boot.unity"] + scenes) + "]\n")


def region_scenes(rid: str, tile: bool) -> list[str]:
    s = [f"{W}{rid}/World_{rid}.unity", f"{W}{rid}/World_{rid}_High.unity"]
    if tile:
        s += [f"{W}{rid}/World_{rid}_Tile.unity", f"{W}{rid}/World_{rid}_High_Tile.unity"]
    return s


CORRIDOR_LOG = log_line(region_scenes("knyszyn-s", True) + region_scenes("knyszyn", True) + region_scenes("dk65-11", False))
NO_TILE_LOG = log_line(region_scenes("knyszyn-s", False) + region_scenes("knyszyn", False))


def make_build(root: Path, log_text: str) -> Path:
    b = root / f"kamion-0.1.0-{SHA}-regions"
    for rel, data in {"Kamion.exe": b"MZ", "UnityPlayer.dll": b"MZ", "Kamion_Data/level0": b"s0",
                      "Kamion_Data/globalgamemanagers": b"g"}.items():
        p = b / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    log = root / "build-win.log"
    log.write_text(log_text, encoding="utf-8")
    (b / "build.json").write_text(json.dumps({"version": "0.1.0", "sha": SHA, "regions": "knyszyn-s,knyszyn,dk65-11",
                                              "worldHigh": True, "log": str(log)}), encoding="utf-8")
    return b


# ---------------------------------------------------------------- postbuild: tiles, corridor, D3D12 opt-in

def test_tile_regions_from_log():
    assert pb.tile_regions_from_log(CORRIDOR_LOG) == ["knyszyn-s", "knyszyn"]
    assert pb.tile_regions_from_log(NO_TILE_LOG) == []
    assert pb.tile_regions_from_log(log_line([f"{W}bialystok-industrial-c/WorldC_Tile.unity"])) == ["bialystok-industrial-c"]
    with pytest.raises(pb.PostBuildError):
        pb.tile_regions_from_log("BUILD_RESULT: Succeeded")


def test_corridor_needs_the_neighbour_tile_scene(tmp_path):
    a = tmp_path / "a"; a.mkdir()
    written, _ = pb.write_launchers(a, ["knyszyn-s", "knyszyn"], tiles=[])
    assert "Kamion-korytarz.cmd" not in written and "Kamion-korytarz-d3d12.cmd" not in written
    assert not (a / "Kamion-korytarz.cmd").exists()
    b = tmp_path / "b"; b.mkdir()
    written, _ = pb.write_launchers(b, ["knyszyn-s", "knyszyn"], tiles=["knyszyn-s"])
    assert written[-2:] == ["Kamion-korytarz.cmd", "Kamion-korytarz-d3d12.cmd"]


def test_d3d12_launchers_exact_text(tmp_path):
    pb.write_launchers(tmp_path, ["knyszyn-s", "knyszyn"], tiles=["knyszyn-s"])
    assert (tmp_path / "Kamion-d3d12.cmd").read_bytes() == b'@echo off\r\nstart "" "%~dp0Kamion.exe" -force-d3d12 %*\r\n'
    assert (tmp_path / "Kamion-korytarz-d3d12.cmd").read_bytes() == (
        b'@echo off\r\nstart "" "%~dp0Kamion.exe" -scene knyszyn -stream 1 -force-d3d12 %*\r\n')
    # the D3D12 opt-in forces no screen mode (StartupDisplayPolicy: only -screen-* / -window-mode / -popupwindow do)
    for n in ("Kamion-d3d12.cmd", "Kamion-korytarz-d3d12.cmd"):
        t = (tmp_path / n).read_text(encoding="ascii")
        assert "-screen-" not in t and "-window-mode" not in t and "-popupwindow" not in t
    # ADR 0291: Direct3D 11 is the default, so no -force-d3d11 launcher any more
    assert not (tmp_path / "Kamion-d3d11.cmd").exists() and not (tmp_path / "Kamion-korytarz-d3d11.cmd").exists()


def test_cli_warns_when_corridor_tiles_missing(tmp_path, capsys):
    b = make_build(tmp_path, NO_TILE_LOG)
    assert pb.main([str(b), "--log", str(tmp_path / "build-win.log"), "--git-sha", SHA]) == 0
    cap = capsys.readouterr()
    out = json.loads(cap.out)
    assert out["tileRegionIds"] == [] and "Kamion-korytarz.cmd" not in out["launchers"]
    assert "Kamion-d3d12.cmd" in out["launchers"]
    assert "Kamion-korytarz.cmd not written" in cap.err


# ---------------------------------------------------------------- postbuild -> package (zip plan)

def test_postbuild_launchers_reach_the_zip_with_readme(tmp_path, capsys):
    b = make_build(tmp_path, CORRIDOR_LOG)
    assert pb.main([str(b), "--log", str(tmp_path / "build-win.log"), "--git-sha", SHA]) == 0
    capsys.readouterr()
    plan = pw.plan_package(b)
    shipped = {f.as_posix() for f in plan.files}
    for n in ("Kamion-okno.cmd", "Kamion-d3d12.cmd", "Kamion-korytarz.cmd", "Kamion-korytarz-d3d12.cmd",
              "Kamion-knyszyn.cmd", "Kamion-knyszyn-s.cmd", "Kamion-dk65-11.cmd", "build-id.json"):
        assert n in shipped, n
    ex = pw.extras(plan)
    readme = ex["README.txt"].decode("utf-8-sig")
    for must in ("Kamion-korytarz.cmd", "Kamion-<region>.cmd", "Kamion-d3d12.cmd", "Kamion-korytarz-d3d12.cmd",
                 r"%LOCALAPPDATA%\CrashDumps"):
        assert must in readme, must
    assert "Zbierz-logi.cmd" in ex and "collect-logs.ps1" in ex


def test_corridor_launcher_left_out_of_zip_when_knyszyn_not_built(tmp_path, capsys):
    b = make_build(tmp_path, CORRIDOR_LOG)
    assert pb.main([str(b), "--log", str(tmp_path / "build-win.log"), "--git-sha", SHA]) == 0
    capsys.readouterr()
    (tmp_path / "build-win.log").write_text(log_line(region_scenes("dk65-11", False)), encoding="utf-8")
    plan = pw.plan_package(b)
    assert "Kamion-korytarz.cmd" in plan.excluded and "Kamion-korytarz-d3d12.cmd" in plan.excluded
    assert "Kamion-d3d12.cmd" in {f.as_posix() for f in plan.files}


def test_collect_logs_takes_wer_crash_dumps():
    ps = (REPO / "scripts/collect-logs.ps1").read_text(encoding="utf-8-sig")
    assert "CrashDumps" in ps and "'Kamion*.dmp'" in ps and "$MaxDumpMB" in ps and "$MaxDumps" in ps
    assert "if ($NoCrashes) { $notes.Add(\"skipped $DumpDir (-NoCrashes)\") }" in ps


# ---------------------------------------------------------------- check-build-scenes.py

def fake_project(root: Path, scenes: list[str]) -> Path:
    for s in scenes:
        p = root / s
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("%YAML", encoding="utf-8")
    return root


def fake_catalog(root: Path, ids: list[str], full: list[str]) -> Path:
    cat = {"schema": "truck-sim-pl/region-catalog/1", "regions": [{"id": i} for i in ids], "aliases": [],
           "sets": [{"name": "d67-full", "regions": full}]}
    p = root / "catalog.json"
    p.write_text(json.dumps(cat), encoding="utf-8")
    return p


def fake_regions_dir(root: Path, ids: list[str]) -> Path:
    for i in ids:
        (root / "Regions" / i).mkdir(parents=True, exist_ok=True)
        (root / "Regions" / i / "route_start.json").write_text("{}", encoding="utf-8")
    return root / "Regions"


def test_scene_check_missing_low_tile_high(tmp_path):
    proj = fake_project(tmp_path / "game", region_scenes("a-1", True) + [f"{W}b-2/World_b-2.unity"])
    cat = fake_catalog(tmp_path, ["a-1", "b-2", "c-3"], ["a-1", "b-2", "c-3"])
    rd = fake_regions_dir(tmp_path, ["a-1", "b-2", "c-3"])
    res = cbs.check("d67-full", proj, cat, rd, require_tiles=False, require_high=False)
    assert res["counts"] == {"low": 2, "lowTile": 1, "high": 1, "highTile": 1}
    assert [f.split(":")[0] for f in res["failures"]] == ["c-3"]          # Low missing = the build would fail
    # RegionBuildList.ComposeScenes order: Low, Low tile, High, High tile; a missing region is left out
    assert res["expectedRegionScenes"] == [f"{W}a-1/World_a-1.unity", f"{W}a-1/World_a-1_Tile.unity",
                                           f"{W}a-1/World_a-1_High.unity", f"{W}a-1/World_a-1_High_Tile.unity",
                                           f"{W}b-2/World_b-2.unity"]
    strict = cbs.check("d67-full", proj, cat, rd, require_tiles=True, require_high=True)
    assert sum(f.startswith("b-2: tile") for f in strict["failures"]) == 1
    assert sum(f.startswith("b-2: High") for f in strict["failures"]) == 1


def test_scene_check_d86_low_tile_needs_high_tile(tmp_path):
    """D86: dk65-04 imported with only a Low tile forced FALLBACK Low in every PC build (INTEGRATION int-ui-s23)."""
    only_low_tile = [f"{W}dk65-04/World_dk65-04.unity", f"{W}dk65-04/World_dk65-04_Tile.unity"]
    proj = fake_project(tmp_path / "game", region_scenes("a-1", True) + only_low_tile)
    cat = fake_catalog(tmp_path, ["a-1", "dk65-04"], ["a-1", "dk65-04"])
    rd = fake_regions_dir(tmp_path, ["a-1", "dk65-04"])
    fails = cbs.check("d67-full", proj, cat, rd, False, False)["failures"]
    assert len(fails) == 1 and fails[0].startswith("dk65-04: D86")
    assert cbs.check("d67-full", proj, cat, rd, False, False, with_high=False)["failures"] == []   # -WorldLow build


def test_scene_check_catalog_coverage(tmp_path):
    proj = fake_project(tmp_path / "game", region_scenes("a-1", False) + region_scenes("b-2", False))
    cat = fake_catalog(tmp_path, ["a-1", "b-2"], ["a-1"])                 # b-2 in the catalog, not in d67-full
    rd = fake_regions_dir(tmp_path, ["a-1", "b-2", "ring-9"])             # ring-9 has data, no catalog entry
    res = cbs.check("d67-full", proj, cat, rd, False, False)
    assert len(res["failures"]) == 1 and "ring-9" in res["failures"][0] and "not in the catalog" in res["failures"][0]
    assert res["warnings"] == ["catalog region b-2 is not in set d67-full"]      # warning only (no owner rule)
    assert cbs.check("a-1", proj, cat, rd, False, False)["warnings"] == []


def test_scene_check_against_a_build_log(tmp_path):
    proj = fake_project(tmp_path / "game", region_scenes("a-1", True) + region_scenes("b-2", False))
    cat = fake_catalog(tmp_path, ["a-1", "b-2"], ["a-1", "b-2"])
    rd = fake_regions_dir(tmp_path, ["a-1", "b-2"])
    good = cbs.check("d67-full", proj, cat, rd, False, False, log_text=log_line(region_scenes("a-1", True) + region_scenes("b-2", False)))
    assert good["failures"] == [] and good["log"]["tileRegionsInLog"] == ["a-1"]
    old = cbs.check("d67-full", proj, cat, rd, False, False, log_text=log_line(region_scenes("a-1", False) + region_scenes("b-2", False)))
    assert len(old["log"]["missingInLog"]) == 2                            # tiles imported after the build


def test_scene_check_cli_exit_codes(tmp_path, capsys):
    proj = fake_project(tmp_path / "game", region_scenes("a-1", False))
    cat = fake_catalog(tmp_path, ["a-1"], ["a-1"])
    rd = fake_regions_dir(tmp_path, ["a-1"])
    args = ["--project", str(proj), "--catalog", str(cat), "--regions-dir", str(rd)]
    assert cbs.main(args) == 0
    assert cbs.main(args + ["--require-tiles"]) == 1
    assert cbs.main(args + ["--regions", "nope"]) == 1
    assert cbs.main(args + ["--log", str(tmp_path / "missing.log")]) == 2
    capsys.readouterr()


# ---------------------------------------------------------------- the real catalog (data-driven, no hard-coded counts)

def test_real_catalog_resolves_and_covers_region_data():
    cat = json.loads(pw.REGION_CATALOG.read_text(encoding="utf-8-sig"))
    errors: list[str] = []
    full = pw.resolve_regions(cat, cbs.FULL_SET, errors)
    assert errors == []
    assert cbs.catalog_problems(cat, REPO / "Data/Regions") == []
    # the regions this task was asked about by name
    assert {"dk65-03", "dk65-04"} <= set(full)
