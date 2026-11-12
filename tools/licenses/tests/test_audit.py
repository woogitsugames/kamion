"""M31: license audit tests (CLAUDE.md rule 8).

- no tracked asset comes from Fab/Megascans/Quixel (names, paths, model metadata)
- no tracked file names/paths indicate Google Maps/Street View/Earth/3D Tiles
- every git-tracked asset is covered by an entry (path or pattern) in docs/LICENSES.md;
  assets with only an UNVERIFIED-section entry are reported as xfail with the count
"""

from __future__ import annotations

from pathlib import Path

import pytest

import audit as A

REPO = A.REPO


def test_generated_paths_excluded_from_assets():
    """Reguła: ścieżki z segmentem `generated`/`_Generated` to wyniki kodu i nie są audytowane."""
    assets = A.list_assets()
    assert assets, "asset list must not be empty"
    assert not [a.path for a in assets if A.is_code_generated(a.path)]
    tracked = A.tracked_files()
    generated_tracked = [p for p in tracked if A.is_code_generated(p) and A.category_of(p)]
    assert generated_tracked, "expected some code-generated tracked assets to exist (sanity check)"
    assert not [p for p in generated_tracked if p in {a.path for a in assets}]


def test_no_fab_megascans_quixel_in_tracked_asset_names():
    assets = A.list_assets()
    hits = []
    for a in assets:
        for tok in A.FAB_NAME_TOKENS:
            if tok.search(a.path):
                hits.append((a.path, tok.pattern))
    assert not hits, f"Fab/Megascans/Quixel w nazwach/ścieżkach zasobów: {hits}"


def test_no_fab_megascans_quixel_in_model_metadata():
    """GLB/FBX mogą zawierać nazwę producenta w nagłówku JSON — skan treści (LFS pointer = skip)."""
    hits = []
    for a in A.list_assets():
        if Path(a.path).suffix.lower() not in {".glb", ".fbx", ".obj"}:
            continue
        p = REPO / a.path
        if not p.is_file() or A._is_lfs_pointer(p):
            continue
        blob = p.read_bytes().lower()
        for tok in A.FAB_CONTENT_TOKENS:
            if tok in blob:
                hits.append((a.path, tok.decode()))
    assert not hits, f"Fab/Megascans/Quixel w metadanych modeli: {hits}"


def test_no_google_sources_in_tracked_paths():
    # ADR 0002 to sam zakaz źródeł Google — jego nazwa zawiera „google”, ale to nie zasób Google.
    allow = {"docs/adr/0002-data-sources-no-google.md"}
    hits = []
    for p in A.tracked_files():
        if p in allow:
            continue
        for tok in A.GOOGLE_NAME_TOKENS:
            if tok.search(p):
                hits.append((p, tok.pattern))
    assert not hits, f"ścieżki wskazujące na źródła Google: {hits}"


def test_no_google_in_model_metadata():
    hits = []
    for a in A.list_assets():
        if Path(a.path).suffix.lower() not in {".glb", ".fbx", ".obj"}:
            continue
        p = REPO / a.path
        if not p.is_file() or A._is_lfs_pointer(p):
            continue
        blob = p.read_bytes().lower()
        for tok in A.GOOGLE_CONTENT_TOKENS:
            if tok in blob:
                hits.append((a.path, tok.decode()))
    assert not hits, f"Google w metadanych modeli: {hits}"


def test_all_tracked_assets_covered_in_licenses_md():
    rep = A.audit()
    assert not rep["suspicious"], f"podejrzane zasoby: {rep['suspicious']}"
    # Integracja r5: dziś 0 niepokrytych (2383/2383), więc twardy fail zamiast xfail - nowy zasób bez wpisu
    # w docs/LICENSES.md (albo tylko z wpisem w sekcji UNVERIFIED) ma zatrzymać testy, a nie zniknąć w xfail.
    assert not rep["unverified"], (f"{len(rep['unverified'])} śledzonych zasobów bez potwierdzonego wpisu w "
                                   f"docs/LICENSES.md: {rep['unverified'][:20]}")
    assert rep["covered"], "asset list must not be empty"


def test_pattern_matching_braces_dir_suffix():
    assert A.pattern_matches("art-source/world/vegetation/{leaves,bark}_*.png", "art-source/world/vegetation/leaves_pine.png")
    assert A.pattern_matches("art-source/world/vegetation/{leaves,bark}_*.png", "art-source/world/vegetation/bark_birch.png")
    assert not A.pattern_matches("art-source/world/vegetation/{leaves,bark}_*.png", "art-source/world/vegetation/grass_tuft.png")
    assert A.pattern_matches("art-source/world/materials/_renders/", "art-source/world/materials/_renders/tiling_asphalt_worn.jpg")
    assert A.pattern_matches("Environment/DrivingLab/Textures/T_*.png", "game/Assets/_Project/Environment/DrivingLab/Textures/T_Asphalt.png")
    assert A.pattern_matches("T_ClearClouds.png", "game/Assets/_Project/Rendering/Resources/Sky/T_ClearClouds.png")
    assert not A.pattern_matches("docs/reports/map/*.png", "docs/reports/visual/world-c/x.png")


def test_unverified_section_patterns_do_not_cover(tmp_path, monkeypatch):
    lic = tmp_path / "LICENSES.md"
    lic.write_text(
        "# LICENSES\n\n| `x` | `art-source/a.png` | own |\n\n"
        "## UNVERIFIED — do uzupełnienia przez lidera\n\n| `y` | `art-source/b.png` | ? |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(A, "LICENSES", lic)
    pats = A.load_patterns()
    by_raw = {p.raw: p.unverified_only for p in pats}
    assert by_raw["art-source/a.png"] is False
    assert by_raw["art-source/b.png"] is True
    a = A.Asset(path="art-source/a.png", category="texture/photo/hdri")
    b = A.Asset(path="art-source/b.png", category="texture/photo/hdri")
    for asset, pats_ in ((a, pats), (b, pats)):
        for pat in pats_:
            if A.pattern_matches(pat.raw, asset.path):
                (asset.unverified_by if pat.unverified_only else asset.covered_by).append(pat.raw)
    assert a.status == "covered"
    assert b.status == "unverified"


def test_leading_wildcard_patterns_do_not_cover_shipped_assets():
    """Integracja r5: wzorzec bez katalogu zaczynający się od `*` (np. `*photo*`) dopasowuje się do dowolnego sufiksu
    ścieżki, więc „pokrywałby” każdy przyszły zasób gry o takiej nazwie i przypisywał mu cudzą licencję. Takie wzorce
    mogą pokrywać tylko robocze `artifacts/` i `docs/reports/`."""
    shipped = [a.path for a in A.list_assets() if not a.path.startswith(("artifacts/", "docs/reports/"))]
    bad = []
    for pat in A.load_patterns():
        if "/" in pat.raw or not pat.raw.startswith("*"):
            continue
        bad += [(pat.raw, p) for p in shipped if A.pattern_matches(pat.raw, p)]
    assert not bad, f"zbyt szerokie wzorce w docs/LICENSES.md pokrywają zasoby gry: {bad[:10]}"
