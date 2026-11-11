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


def test_reviewed_curtain_pigments_keep_s9_gpu_appearance_and_roughness():
    from streetscape.materials import M
    accepted = {
        "grey": ([.20,.21,.21], .82), "blue": ([.03,.06,.14], .82),
        "white": ([.55,.56,.55], .82), "red": ([.18,.045,.035], .82),
        "green": ([.045,.08,.06], .82), "silver": ([.36,.37,.37], .72),
    }
    for name, (old, rough) in accepted.items():
        value=M["trailer_curtain_"+name]
        old=np.asarray(old)
        effective=np.where(old <= .04045, old/12.92, ((old+.055)/1.055)**2.4)
        assert np.allclose(value["color"],effective,atol=1e-8)
        assert value["rough"] == rough
        assert value["texture_set"] == "curtain_folds"
    old=np.asarray([.60,.61,.60])
    assert np.allclose(M["trailer_box_white"]["color"], ((old+.055)/1.055)**2.4, atol=1e-8)
    assert M["trailer_box_white"]["rough"] == .45
