"""scripts/package-windows.py (ADR 0271) on a synthetic Windows player folder. No Unity, no real build.

    uv run --no-project --with pytest pytest tests/dist -q
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def load():
    spec = importlib.util.spec_from_file_location("package_windows", REPO / "scripts" / "package-windows.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m  # dataclasses resolve annotations through sys.modules
    spec.loader.exec_module(m)
    return m


pw = load()
SHA = "4ee3e02626"


def make_build(root: Path, name: str = f"kamion-0.1.0-{SHA}-regions", dev: bool = False, build_json: dict | None = None) -> Path:
    """Folder shaped like build-windows.ps1 output (ADR 0261) incl. the files that must not ship."""
    b = root / name
    files = {
        "Kamion.exe": b"MZ exe",
        "UnityPlayer.dll": b"MZ player",
        "UnityCrashHandler64.exe": b"MZ crash",
        "Kamion_Data/globalgamemanagers": b"ggm",
        "Kamion_Data/data.unity3d": b"x" * 4096,
        "Kamion_Data/Managed/Assembly-CSharp.dll": b"MZ managed",
        "Kamion_Data/Plugins/x86_64/lib_burst_generated.dll": b"MZ burst",
        "MonoBleedingEdge/EmbedRuntime/mono-2.0-bdwgc.dll": b"MZ mono",
        "Kamion-okno.cmd": b"@echo off\r\n",
        # must not ship
        "Kamion_BurstDebugInformation_DoNotShip/Data/Plugins/lib_burst_generated.txt": b"dbg",
        "Kamion_BackUpThisFolder_ButDontShipItWithYourGame/il2cppOutput/a.cpp": b"cpp",
        "UnityPlayer.pdb": b"pdb",
        "Kamion_Data/Plugins/x86_64/something.PDB": b"pdb2",
        "build.json": json.dumps(build_json if build_json is not None else
                                 {"version": "0.1.0", "sha": SHA, "worldHigh": True, "development": dev}).encode("utf-8-sig"),
        "Kamion.exe.sha256": b"abc  Kamion.exe\n",
        "Kamion.content.json": b"{}",
        "Kamion.top.txt": b"top",
        "Kamion.variants.txt": b"v",
        "Kamion-knyszyn.cmd": b"@echo off\r\n",
        "Kamion-knyszyn-w.cmd": b"@echo off\r\n",          # ADR 0276: every region launcher stays out
        "Kamion_Data.sha256": b"manifest\n",
    }
    if dev:
        files["WinPixEventRuntime.dll"] = b"MZ pix"
    for rel, data in files.items():
        p = b / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return b


def content(b: Path) -> str:
    """Content hash (ADR 0276) of a synthetic build, as package-windows.py computes it."""
    return pw.postbuild.build_id(pw.postbuild.data_manifest(b), SHA)["contentHash"]


def zname(b: Path, flags: str = "-regions") -> str:
    return f"kamion-0.1.0-{SHA}{flags}-{content(b)}-win64"


def names(zip_path: Path) -> set[str]:
    with zipfile.ZipFile(zip_path) as z:
        return set(z.namelist())


def test_package_excludes_debug_and_metadata(tmp_path):
    b = make_build(tmp_path)
    out = tmp_path / "dist"
    assert pw.main([str(b), "--out-dir", str(out)]) == 0
    zp = out / f"{zname(b)}.zip"
    assert zp.is_file()
    root = f"{zname(b)}/"
    got = names(zp)
    for must in ("Kamion.exe", "UnityPlayer.dll", "UnityCrashHandler64.exe", "Kamion_Data/data.unity3d",
                 "MonoBleedingEdge/EmbedRuntime/mono-2.0-bdwgc.dll", "Kamion-okno.cmd", "build-id.json",
                 "THIRD_PARTY_NOTICES.txt", "README.txt", "SHA256SUMS.txt", "collect-logs.ps1", "Zbierz-logi.cmd"):
        assert root + must in got, must
    for n in got:
        assert n.startswith(root)
        low = n.lower()
        assert "donotship" not in low and "dontship" not in low and not low.endswith(".pdb"), n
    for meta in ("build.json", "Kamion.exe.sha256", "Kamion.content.json", "Kamion.top.txt", "Kamion.variants.txt",
                 "Kamion-knyszyn.cmd", "Kamion-knyszyn-w.cmd", "Kamion_Data.sha256"):
        assert root + meta not in got


def test_sha256_sidecar_and_sums(tmp_path):
    b = make_build(tmp_path)
    out = tmp_path / "dist"
    assert pw.main([str(b), "--out-dir", str(out)]) == 0
    zp = out / f"{zname(b)}.zip"
    side = (out / (zp.name + ".sha256")).read_text(encoding="ascii")
    assert side == f"{hashlib.sha256(zp.read_bytes()).hexdigest()}  {zp.name}\n"
    with zipfile.ZipFile(zp) as z:
        root = f"{zname(b)}/"
        sums = z.read(root + "SHA256SUMS.txt").decode()
        lines = dict(reversed(l.split("  ", 1)) for l in sums.splitlines())
        assert hashlib.sha256(z.read(root + "Kamion.exe")).hexdigest() == lines["Kamion.exe"]
        assert z.testzip() is None
    manifest = json.loads((out / f"{zname(b)}.json").read_text(encoding="utf-8"))
    assert manifest["contentHash"] == content(b) and manifest["regions"] is True
    assert manifest["zipSha256"] in side
    assert "Kamion_BurstDebugInformation_DoNotShip/" in manifest["excluded"]
    assert "Kamion_BackUpThisFolder_ButDontShipItWithYourGame/" in manifest["excluded"]
    assert "UnityPlayer.pdb" in manifest["excluded"]


def test_reproducible(tmp_path):
    b = make_build(tmp_path)
    a, c = tmp_path / "a", tmp_path / "c"
    assert pw.main([str(b), "--out-dir", str(a)]) == 0
    assert pw.main([str(b), "--out-dir", str(c)]) == 0
    za = (a / f"{zname(b)}.zip").read_bytes()
    zc = (c / f"{zname(b)}.zip").read_bytes()
    assert za == zc  # README carries today's date only; same day = identical bytes


def test_dev_build_refused_unless_allowed(tmp_path):
    b = make_build(tmp_path, name=f"kamion-0.1.0-{SHA}-regions-dev", dev=True)
    assert pw.main([str(b), "--out-dir", str(tmp_path / "d")]) == 2
    assert pw.main([str(b), "--out-dir", str(tmp_path / "d"), "--allow-dev"]) == 0
    assert (tmp_path / "d" / f"{zname(b, '-regions-dev')}.zip").is_file()


def test_pix_dll_marks_dev_even_without_flag(tmp_path):
    b = make_build(tmp_path, build_json={"version": "0.1.0", "sha": SHA})
    (b / "WinPixEventRuntime.dll").write_bytes(b"MZ")
    with pytest.raises(pw.PackageError):
        pw.plan_package(b)


def test_dirty_refused_unless_allowed(tmp_path):
    b = make_build(tmp_path, name=f"kamion-0.1.0-{SHA}-dirty-regions", build_json={})
    assert pw.main([str(b), "--out-dir", str(tmp_path / "d")]) == 2
    assert pw.main([str(b), "--out-dir", str(tmp_path / "d"), "--allow-dirty"]) == 0
    assert (tmp_path / "d" / f"{zname(b, '-regions-dirty')}.zip").is_file()


def test_low_variant_name(tmp_path):
    b = make_build(tmp_path, name=f"kamion-0.1.0-{SHA}-low",
                   build_json={"version": "0.1.0", "sha": SHA, "worldHigh": False, "development": False})
    assert pw.plan_package(b).name == zname(b, "-low")


def test_missing_exe_or_data(tmp_path):
    b = make_build(tmp_path)
    (b / "Kamion.exe").unlink()
    assert pw.main([str(b), "--dry-run"]) == 2
    b2 = make_build(tmp_path / "x")
    import shutil
    shutil.rmtree(b2 / "Kamion_Data")
    assert pw.main([str(b2), "--dry-run"]) == 2


def test_bad_sha_rejected(tmp_path):
    b = make_build(tmp_path, name="player", build_json={})
    with pytest.raises(pw.PackageError):
        pw.plan_package(b)  # no build.json data, folder name not kamion-<ver>-<sha>
    assert pw.plan_package(b, version="0.2.0", sha="abcdef1").name == f"kamion-0.2.0-abcdef1-{content(b)}-win64"
    with pytest.raises(pw.PackageError):
        pw.plan_package(b, version="0.2.0", sha="not-a-sha")


def test_dry_run_writes_nothing(tmp_path):
    b = make_build(tmp_path)
    out = tmp_path / "dist"
    assert pw.main([str(b), "--out-dir", str(out), "--dry-run"]) == 0
    assert not out.exists()


def test_notices_from_attributions(tmp_path):
    res = tmp_path / "Resources"
    (res / "About").mkdir(parents=True)
    (res / "Fonts").mkdir()
    (res / "Fonts/Lic.txt").write_text("LICENCE BODY\nline 2\n", encoding="utf-8")
    src = res / "About/attributions.txt"
    src.write_text("# hidden comment R-P0-2\n= Mapy\n\n== OSM\n© OpenStreetMap contributors\n\n== Font\n@include Fonts/Lic\n",
                   encoding="utf-8")
    text = pw.render_notices(src, res)
    assert "hidden comment" not in text
    assert "MAPY\n====" in text and "OSM\n---" in text
    assert "© OpenStreetMap contributors" in text and "LICENCE BODY\nline 2" in text
    assert pw.licence_blockers(src)  # R-P0-2 note still present


def test_real_notices_render_and_have_core_attributions():
    text = pw.render_notices()
    for must in ("OpenStreetMap", "ODbL", "Główny Urząd Geodezji i Kartografii", "SIL Open Font License", "Apache License"):
        assert must in text, must
    assert "UNVERIFIED" not in text  # '#' comment lines stay out of the shipped notices


def test_release_mode_blocks_on_open_licence_items(tmp_path):
    b = make_build(tmp_path)
    expected = 3 if pw.licence_blockers() else 0
    assert pw.main([str(b), "--out-dir", str(tmp_path / "r"), "--release", "--dry-run"]) == expected
    assert pw.main([str(b), "--release", "--allow-dev", "--dry-run"]) == 2


def test_readme_has_requirements_and_no_placeholders(tmp_path):
    plan = pw.plan_package(make_build(tmp_path))
    text = pw.render_readme(plan)
    assert "{" not in text
    for must in ("i5-6400", "Ryzen 3 1200", "GTX 660", "RX 460", "HD 630", "8 GB", "i5-9600", "Ryzen 5 3600",
                 "GTX 1660", "RX 590", "12 GB", "25 GB", "WORKING_VALUE", zname(make_build(tmp_path / "n")),
                 f"dane {content(make_build(tmp_path / 'n2'))}", "-NoCrashes",
                 r"AppData\LocalLow\woogitsugames\Kamion\Player.log"):
        assert must in text, must
    assert "\r\n" in text


# ---------------------------------------------------------------- region launchers (Kamion-<region>.cmd)

def _launcher(scene: str) -> bytes:
    """Same text as build-windows.ps1 writes."""
    return (f'@echo off\r\nstart "" "%~dp0Kamion.exe" -screen-fullscreen 0 -screen-width 1600 -screen-height 900 '
            f'-scene {scene} %*\r\n').encode("ascii")


def _with_launchers(b: Path) -> Path:
    (b / "Kamion-okno.cmd").write_bytes(b'@echo off\r\nstart "" "%~dp0Kamion.exe" -screen-fullscreen 0 %*\r\n')
    (b / "Kamion-knyszyn.cmd").write_bytes(_launcher("knyszyn"))
    (b / "Kamion-knyszyn-w.cmd").write_bytes(_launcher("knyszyn-w"))
    return b


def _plan_names(b: Path) -> tuple[set[str], list[str]]:
    plan = pw.plan_package(b)
    return {f.as_posix() for f in plan.files}, plan.excluded


def test_region_launcher_left_out_when_region_not_in_build(tmp_path):
    # default build (no -Regions): Boot + DrivingLab + WorldC only -> no knyszyn-w scene
    b = _with_launchers(make_build(tmp_path, name=f"kamion-0.1.0-{SHA}",
                                   build_json={"version": "0.1.0", "sha": SHA, "regions": "", "regionsFile": ""}))
    shipped, excluded = _plan_names(b)
    assert "Kamion-okno.cmd" in shipped
    assert "Kamion-knyszyn-w.cmd" in excluded and "Kamion-knyszyn-w.cmd" not in shipped
    assert "Kamion-knyszyn.cmd" in excluded


def test_region_launcher_set_d67_has_no_knyszyn_w(tmp_path):
    # Data/build_regions.json style: set d67 (region_catalog.json) holds knyszyn but not knyszyn-w
    b = _with_launchers(make_build(tmp_path, build_json={"version": "0.1.0", "sha": SHA, "regions": "d67", "regionsFile": ""}))
    shipped, excluded = _plan_names(b)
    assert "Kamion-knyszyn-w.cmd" in excluded
    assert "Kamion-knyszyn.cmd" in excluded          # developer shortcut (ADR 0271 §2) even with knyszyn in the build


def test_region_launcher_kamion_prefix_never_ships(tmp_path):
    # ADR 0276 (int-h3-s23): every Kamion-<region>.cmd is a developer shortcut, even with its region in the build;
    # the tester picks the region in the start menu, only Kamion-okno.cmd ships.
    b = _with_launchers(make_build(tmp_path, build_json={"version": "0.1.0", "sha": SHA, "regions": "d67,knyszyn-w"}))
    shipped, excluded = _plan_names(b)
    assert "Kamion-okno.cmd" in shipped
    assert "Kamion-knyszyn-w.cmd" in excluded and "Kamion-knyszyn.cmd" in excluded


def test_other_scene_launcher_ships_only_when_region_in_build(tmp_path):
    # ADR 0271 s23 rule still guards any other root *.cmd with -scene <x>.
    b = make_build(tmp_path / "in", build_json={"version": "0.1.0", "sha": SHA, "regions": "d67,knyszyn-w"})
    (b / "Start-knyszyn-w.cmd").write_bytes(_launcher("knyszyn-w"))
    shipped, _ = _plan_names(b)
    assert "Start-knyszyn-w.cmd" in shipped
    c = make_build(tmp_path / "out", build_json={"version": "0.1.0", "sha": SHA, "regions": "d67"})
    (c / "Start-knyszyn-w.cmd").write_bytes(_launcher("knyszyn-w"))
    shipped, excluded = _plan_names(c)
    assert "Start-knyszyn-w.cmd" in excluded and "Start-knyszyn-w.cmd" not in shipped


def test_region_launcher_build_log_wins(tmp_path):
    # -RegionsAllowMissing: knyszyn-w asked for but not imported -> the build log's scene list is the truth
    log = tmp_path / "build-win.log"
    log.write_text("[BUILD] Windows x64 → C:/a/Kamion.exe (development=False, worldHigh=True) scenes=["
                   "Assets/_Project/Core/Scenes/Boot.unity, Assets/_Generated/World/knyszyn/World_knyszyn.unity]\n",
                   encoding="utf-8")
    b = _with_launchers(make_build(tmp_path, build_json={"version": "0.1.0", "sha": SHA, "regions": "knyszyn,knyszyn-w",
                                                         "log": str(log)}))
    shipped, excluded = _plan_names(b)
    assert "Kamion-knyszyn-w.cmd" in excluded


def test_region_launcher_unknown_build_content(tmp_path):
    b = _with_launchers(make_build(tmp_path, build_json={"version": "0.1.0", "sha": SHA}))
    (b / "build.json").unlink()
    plan = pw.plan_package(b)
    shipped = {f.as_posix() for f in plan.files}
    assert "Kamion-okno.cmd" in shipped and "Kamion-knyszyn-w.cmd" not in shipped
    assert any("scene launchers" in w for w in plan.warnings)


def test_resolve_regions_matches_catalog_rules():
    cat = pw._catalog()
    errs: list[str] = []
    assert pw.resolve_regions(cat, "c, dojlidy", errs) == ["bialystok-industrial-c", "bialystok-dojlidy"]
    assert pw.resolve_regions(cat, "dk65-01..dk65-03", errs) == ["dk65-01", "dk65-02", "dk65-03"]
    assert pw.resolve_regions(cat, "dk65-03 ... dk65-01", errs) == ["dk65-03", "dk65-02", "dk65-01"]
    assert "knyszyn-w" not in pw.resolve_regions(cat, "d67", errs)
    assert errs == []
    pw.resolve_regions(cat, "nie-ma-takiego", errs)
    assert errs


# ---------------------------------------------------------------- ADR 0276: build identity, -regions in the name


def test_regions_flag_from_build_json_and_folder(tmp_path):
    """Review #134 P2-1: the regions build and the default build of one commit must not share a zip name."""
    plain = make_build(tmp_path / "a", name=f"kamion-0.1.0-{SHA}", build_json={"version": "0.1.0", "sha": SHA, "regions": ""})
    reg = make_build(tmp_path / "b", name=f"kamion-0.1.0-{SHA}", build_json={"version": "0.1.0", "sha": SHA, "regions": "d67-full"})
    assert pw.plan_package(plain).name == zname(plain, "")
    assert pw.plan_package(reg).name == zname(reg, "-regions")
    assert pw.plan_package(plain).name != pw.plan_package(reg).name


def test_two_builds_of_one_commit_get_different_names(tmp_path):
    """INTEGRATION s23 §8: Kamion.exe (the Unity stub) is identical, Kamion_Data is not."""
    a = make_build(tmp_path / "a")
    b = make_build(tmp_path / "b")
    (b / "Kamion_Data/data.unity3d").write_bytes(b"y" * 4096)
    assert (a / "Kamion.exe").read_bytes() == (b / "Kamion.exe").read_bytes()
    na, nb = pw.plan_package(a).name, pw.plan_package(b).name
    assert na != nb and na.endswith("-win64") and na[:-6].rsplit("-", 1)[1] == content(a)


def test_recorded_build_id_must_match_data(tmp_path):
    b = make_build(tmp_path)
    pb = pw.postbuild
    doc = pb.write_build_id(b, pb.data_manifest(b), SHA)
    plan = pw.plan_package(b)
    assert plan.content == doc["contentHash"] and plan.build_id is None   # shipped as built, not regenerated
    assert not any("build-id.json missing" in w for w in plan.warnings)
    (b / "Kamion_Data/globalgamemanagers").write_bytes(b"changed after the build")
    with pytest.raises(pw.PackageError, match="changed after the build"):
        pw.plan_package(b)


def test_missing_build_id_generated_and_shipped(tmp_path):
    b = make_build(tmp_path)
    out = tmp_path / "dist"
    assert pw.main([str(b), "--out-dir", str(out)]) == 0
    with zipfile.ZipFile(out / f"{zname(b)}.zip") as z:
        doc = json.loads(z.read(f"{zname(b)}/build-id.json"))
    assert doc["contentHash"] == content(b) and doc["gitSha"] == SHA and doc["schema"] == "kamion/build-id/1"


def test_zbierz_logi_warns_about_crash_dumps(tmp_path):
    plan = pw.plan_package(make_build(tmp_path))
    cmd = pw.extras(plan)["Zbierz-logi.cmd"].decode("ascii")
    assert "*.dmp" in cmd and "-NoCrashes" in cmd and "%*" in cmd
