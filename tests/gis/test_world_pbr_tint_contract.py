"""The world tint API is globally linear; metric/weather metadata survives migration."""
from pathlib import Path


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
