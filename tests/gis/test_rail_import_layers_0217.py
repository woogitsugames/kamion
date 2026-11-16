"""ADR 0217 (rail-0217, PR #96): Unity import of the rail layers.

The generator writes the GLB nodes rail_lod0 / rail_lod1 / rail_lod2 / rail_crossing (the Low GLB has no rail_lod0).
The importer bakes only the nodes named in RegionImporter.k_{Low,High}Layers and shows only those named in
WorldSceneBuilder.k_{Low,High}Lods, so a layer missing from either table is silently dropped (found by the local
verification of PR #96: the track was generated but never rendered). This contract test reads the C# tables.
It needs neither Unity nor Data/raw.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMPORT = ROOT / "game/Assets/_Project/World/Import"
RAIL_PY = ROOT / "tools/worldgen/streetscape/rail.py"

RAIL_ALL = {"rail_lod0", "rail_lod1", "rail_lod2", "rail_crossing"}
# ADR 0217 "Integracja z Unity": rail layers per LODGroup level 0..3
EXPECTED_LODS = {
    "Low": [{"rail_lod1", "rail_crossing"}, {"rail_lod1", "rail_crossing"}, {"rail_lod2", "rail_crossing"}, {"rail_lod2"}],
    "High": [{"rail_lod0", "rail_crossing"}, {"rail_lod1", "rail_crossing"}, {"rail_lod2", "rail_crossing"}, {"rail_lod2"}],
}


def _strings(text: str) -> list[str]:
    return re.findall(r'"([^"]+)"', text)


def _array(src: str, name: str) -> list[str]:
    m = re.search(r"static readonly string\[\] " + name + r"\s*=\s*\{([^}]*)\}", src)
    assert m, f"{name} not found"
    return _strings(m.group(1))


def _table(src: str, name: str) -> list[list[str]]:
    m = re.search(r"static readonly string\[\]\[\] " + name + r"\s*=\s*\{(.*?)\n\s*\};", src, re.S)
    assert m, f"{name} not found"
    rows = re.findall(r"new\[\]\s*\{([^}]*)\}", m.group(1))
    assert rows, f"{name} has no rows"
    return [_strings(r) for r in rows]


def _importer() -> str:
    return (IMPORT / "RegionImporter.cs").read_text(encoding="utf-8")


def _builder() -> str:
    return (IMPORT / "WorldSceneBuilder.cs").read_text(encoding="utf-8")


def _rail(names) -> set[str]:
    return {n for n in names if n.startswith("rail_")}


def test_importer_bakes_rail_layers():
    src = _importer()
    assert _rail(_array(src, "k_HighLayers")) == RAIL_ALL
    # the Low / Medium GLB carries no rail_lod0 (rail.py LOW_EXCLUDE)
    assert _rail(_array(src, "k_LowLayers")) == RAIL_ALL - {"rail_lod0"}


def test_scene_builder_lod_table_matches_adr():
    src = _builder()
    for tier, expected in EXPECTED_LODS.items():
        table = _table(src, f"k_{tier}Lods")
        assert len(table) == len(expected), tier
        assert [_rail(row) for row in table] == expected, tier


def test_every_shown_rail_layer_is_baked_and_every_baked_one_is_shown():
    imp, bld = _importer(), _builder()
    for tier in ("Low", "High"):
        baked = _rail(_array(imp, f"k_{tier}Layers"))
        shown = set().union(*(_rail(row) for row in _table(bld, f"k_{tier}Lods")))
        assert shown <= baked, f"{tier}: LOD table shows rail layers the importer never bakes: {sorted(shown - baked)}"
        assert baked <= shown, f"{tier}: baked rail layers never shown in any LOD: {sorted(baked - shown)}"


def test_one_track_representation_per_lod_level():
    # exactly one of rail_lod0/1/2 per level, otherwise two track meshes overlap (z-fight, double triangles)
    bld = _builder()
    for tier in ("Low", "High"):
        for i, row in enumerate(_table(bld, f"k_{tier}Lods")):
            tracks = [n for n in row if re.fullmatch(r"rail_lod\d", n)]
            assert len(tracks) == 1, f"{tier} LOD{i}: {tracks}"
            assert len(row) == len(set(row)), f"{tier} LOD{i}: duplicate layer"


def test_rail_casts_no_shadows():
    m = re.search(r"k_ShadowCasters\s*=\s*new HashSet<string>\s*\{([^}]*)\}", _builder())
    assert m, "k_ShadowCasters not found"
    assert not _rail(_strings(m.group(1)))


def test_tables_match_generator_layers():
    """After PR #96 is merged: the C# tables name exactly the generator's GLB nodes."""
    if not RAIL_PY.exists():
        import pytest

        pytest.skip("tools/worldgen/streetscape/rail.py not on this branch (PR #96 not merged)")
    consts = {}
    for node in ast.parse(RAIL_PY.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ("LAYERS", "LOW_EXCLUDE"):
            consts[node.targets[0].id] = set(ast.literal_eval(node.value))
    assert set(consts) == {"LAYERS", "LOW_EXCLUDE"}
    imp = _importer()
    assert _rail(_array(imp, "k_HighLayers")) == consts["LAYERS"]
    assert _rail(_array(imp, "k_LowLayers")) == consts["LAYERS"] - consts["LOW_EXCLUDE"]
