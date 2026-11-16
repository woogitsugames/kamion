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
    }
    if dev:
        files["WinPixEventRuntime.dll"] = b"MZ pix"
    for rel, data in files.items():
        p = b / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return b


def names(zip_path: Path) -> set[str]:
    with zipfile.ZipFile(zip_path) as z:
        return set(z.namelist())


def test_package_excludes_debug_and_metadata(tmp_path):
    b = make_build(tmp_path)
    out = tmp_path / "dist"
    assert pw.main([str(b), "--out-dir", str(out)]) == 0
    zp = out / f"kamion-0.1.0-{SHA}-win64.zip"
    assert zp.is_file()
    root = f"kamion-0.1.0-{SHA}-win64/"
    got = names(zp)
    for must in ("Kamion.exe", "UnityPlayer.dll", "UnityCrashHandler64.exe", "Kamion_Data/data.unity3d",
                 "MonoBleedingEdge/EmbedRuntime/mono-2.0-bdwgc.dll", "Kamion-okno.cmd",
                 "THIRD_PARTY_NOTICES.txt", "README.txt", "SHA256SUMS.txt", "collect-logs.ps1", "Zbierz-logi.cmd"):
        assert root + must in got, must
    for n in got:
        assert n.startswith(root)
        low = n.lower()
        assert "donotship" not in low and "dontship" not in low and not low.endswith(".pdb"), n
    for meta in ("build.json", "Kamion.exe.sha256", "Kamion.content.json", "Kamion.top.txt", "Kamion.variants.txt",
                 "Kamion-knyszyn.cmd"):
        assert root + meta not in got


def test_sha256_sidecar_and_sums(tmp_path):
    b = make_build(tmp_path)
    out = tmp_path / "dist"
    assert pw.main([str(b), "--out-dir", str(out)]) == 0
    zp = out / f"kamion-0.1.0-{SHA}-win64.zip"
    side = (out / (zp.name + ".sha256")).read_text(encoding="ascii")
    assert side == f"{hashlib.sha256(zp.read_bytes()).hexdigest()}  {zp.name}\n"
    with zipfile.ZipFile(zp) as z:
        root = f"kamion-0.1.0-{SHA}-win64/"
        sums = z.read(root + "SHA256SUMS.txt").decode()
        lines = dict(reversed(l.split("  ", 1)) for l in sums.splitlines())
        assert hashlib.sha256(z.read(root + "Kamion.exe")).hexdigest() == lines["Kamion.exe"]
        assert z.testzip() is None
    manifest = json.loads((out / f"kamion-0.1.0-{SHA}-win64.json").read_text(encoding="utf-8"))
    assert manifest["zipSha256"] in side
    assert "Kamion_BurstDebugInformation_DoNotShip/" in manifest["excluded"]
    assert "Kamion_BackUpThisFolder_ButDontShipItWithYourGame/" in manifest["excluded"]
    assert "UnityPlayer.pdb" in manifest["excluded"]


def test_reproducible(tmp_path):
    b = make_build(tmp_path)
    a, c = tmp_path / "a", tmp_path / "c"
    assert pw.main([str(b), "--out-dir", str(a)]) == 0
    assert pw.main([str(b), "--out-dir", str(c)]) == 0
    za = (a / f"kamion-0.1.0-{SHA}-win64.zip").read_bytes()
    zc = (c / f"kamion-0.1.0-{SHA}-win64.zip").read_bytes()
    assert za == zc  # README carries today's date only; same day = identical bytes


def test_dev_build_refused_unless_allowed(tmp_path):
    b = make_build(tmp_path, name=f"kamion-0.1.0-{SHA}-regions-dev", dev=True)
    assert pw.main([str(b), "--out-dir", str(tmp_path / "d")]) == 2
    assert pw.main([str(b), "--out-dir", str(tmp_path / "d"), "--allow-dev"]) == 0
    assert (tmp_path / "d" / f"kamion-0.1.0-{SHA}-dev-win64.zip").is_file()


def test_pix_dll_marks_dev_even_without_flag(tmp_path):
    b = make_build(tmp_path, build_json={"version": "0.1.0", "sha": SHA})
    (b / "WinPixEventRuntime.dll").write_bytes(b"MZ")
    with pytest.raises(pw.PackageError):
        pw.plan_package(b)


def test_dirty_refused_unless_allowed(tmp_path):
    b = make_build(tmp_path, name=f"kamion-0.1.0-{SHA}-dirty-regions", build_json={})
    assert pw.main([str(b), "--out-dir", str(tmp_path / "d")]) == 2
    assert pw.main([str(b), "--out-dir", str(tmp_path / "d"), "--allow-dirty"]) == 0
    assert (tmp_path / "d" / f"kamion-0.1.0-{SHA}-dirty-win64.zip").is_file()


def test_low_variant_name(tmp_path):
    b = make_build(tmp_path, name=f"kamion-0.1.0-{SHA}-low",
                   build_json={"version": "0.1.0", "sha": SHA, "worldHigh": False, "development": False})
    assert pw.plan_package(b).name == f"kamion-0.1.0-{SHA}-low-win64"


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
    assert pw.plan_package(b, version="0.2.0", sha="abcdef1").name == "kamion-0.2.0-abcdef1-win64"
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
                 "GTX 1660", "RX 590", "12 GB", "25 GB", "WORKING_VALUE", f"kamion-0.1.0-{SHA}-win64",
                 r"AppData\LocalLow\woogitsugames\Kamion\Player.log"):
        assert must in text, must
    assert "\r\n" in text
