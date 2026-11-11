"""The world tint API is globally linear; metric/weather metadata survives migration."""
from pathlib import Path
import sys
import numpy as np


ROOT = Path(__file__).resolve().parents[2]


def test_all_pbr_tint_writes_use_one_linear_encoder():
    source = (ROOT / "game/Assets/_Project/World/Import/WorldPbrMaterials.cs").read_text(encoding="utf-8")
    assert source.count('material.SetColor("_Tint"') == 1
    assert 'mat.SetVector("_Tint"' not in source
    assert 'mat.SetColor("_Tint"' not in source
    assert source.count('SetLinearTint(mat,') == 4
    assert 'if (def.Get("tint_linear")' not in source


def test_tint_migration_keeps_metric_and_weather_contracts():
    source = (ROOT / "game/Assets/_Project/World/Import/WorldPbrMaterials.cs").read_text(encoding="utf-8")
    assert '|| elementScan || isAtlasSet' in source
    for key in ('"weather"', '"runoff"', '"macro"', '"panel_m"', '"splash_h"'):
        assert key in source


def test_plaster_palette_change_cannot_recolour_roof_trim_or_glass(monkeypatch):
    sys.path.insert(0, str(ROOT / "art-source/world/materials/_src"))
    import sets_fire_station as station
    # Keep this a pure generator-contract test in a clean public clone: source
    # acquisition is covered separately, and no network/download is permitted.
    def scan(asset, context, mask, relief, *args, **kwargs):
        shape = (context.ny, context.nx)
        return np.ones(shape, np.float32), np.zeros(shape, np.float32), np.zeros(shape, np.float32), None, False
    monkeypatch.setattr(station, "_scan_fields", scan)
    first = station.fire_station(nx=128)
    pigment = station.LAYOUT["render_blue_linear"]
    monkeypatch.setitem(station.LAYOUT, "render_blue_linear", [x * .8 for x in pigment])
    second = station.fire_station(nx=128)
    x, y = first.c.xy()
    v = station.TILE[1] - y
    roof = (v > 4.2) & (v < 7.1)
    trim = (v > 11.5) & (v < 11.8)
    arch_glass = (x > 5.3) & (x < 7.8) & (v > 7.7) & (v < 9.1)
    round_glass = (x - 9.55) ** 2 + (v - 8.55) ** 2 < .3 ** 2
    protected = roof | trim | arch_glass | round_glass
    assert protected.any()
    assert np.array_equal(first.albedo[protected], second.albedo[protected])
    assert np.array_equal(first.height, second.height)
    assert np.array_equal(first.rough, second.rough)
    assert np.any(first.albedo[v < 3] != second.albedo[v < 3])
