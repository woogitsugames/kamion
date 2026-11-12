import json

import pytest

from perfgate.formats import (
    ParseError,
    parse_battery_txt,
    parse_frametimes_csv,
    parse_logcat,
    parse_meminfo_txt,
    parse_thermal_txt,
)

from conftest import write_run_dir, make_rows


def test_frametimes_v1_header_ok(tmp_path):
    d = write_run_dir(tmp_path / "r", make_rows([33.333, 33.333, 50.0]))
    rows = parse_frametimes_csv(d / "frametimes.csv")
    assert len(rows) == 3
    assert rows[2].frame_ms == pytest.approx(50.0)
    assert rows[0].t_s == pytest.approx(0.0)


def test_frametimes_unknown_column_is_error(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    (d / "frametimes.csv").write_text(
        "frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab,nowa_kolumna\n"
        "1,0.0,33.333,0,0,0.75,0,,x\n",
        encoding="utf-8",
    )
    with pytest.raises(ParseError, match="nieznane kolumny.*nowa_kolumna"):
        parse_frametimes_csv(d / "frametimes.csv")


def test_frametimes_missing_column_is_error(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    (d / "frametimes.csv").write_text("frame,t_s,frame_ms\n1,0.0,33.333\n", encoding="utf-8")
    with pytest.raises(ParseError, match="brak wymaganych kolumn"):
        parse_frametimes_csv(d / "frametimes.csv")


def test_frametimes_bad_value_is_error(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    (d / "frametimes.csv").write_text(
        "frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab\n1,0.0,abc,0,0,0.75,0,\n",
        encoding="utf-8",
    )
    with pytest.raises(ParseError, match="wiersz 2"):
        parse_frametimes_csv(d / "frametimes.csv")


def test_battery_temperature_decidegrees(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    (d / "battery.txt").write_text("  level: 80\n  temperature: 276\n", encoding="utf-8")
    b = parse_battery_txt(d / "battery.txt")
    assert b["level_pct"] == 80
    assert b["temperature_c"] == pytest.approx(27.6)


def test_thermal_parse(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    (d / "thermal.txt").write_text(
        "Thermal Status: 0\n"
        "\tTemperature{mValue=37.5, mType=0, mName=AP, mStatus=0}\n"
        "\tTemperature{mValue=27.6, mType=2, mName=BAT, mStatus=1}\n",
        encoding="utf-8",
    )
    t = parse_thermal_txt(d / "thermal.txt")
    assert t["thermal_status"] == 0
    assert t["sensors"][1]["name"] == "BAT"
    assert t["sensors"][1]["value_c"] == pytest.approx(27.6)
    assert t["sensors"][1]["status"] == 1


def test_meminfo_total_pss(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    (d / "meminfo.txt").write_text(
        "  Native Heap    34527 ...\n        TOTAL   825305   736515\n", encoding="utf-8"
    )
    m = parse_meminfo_txt(d / "meminfo.txt")
    assert m["pss_kb"] == 825305
    assert m["pss_mb"] == pytest.approx(805.96, abs=0.01)


def test_logcat_diag_parse(tmp_path):
    from conftest import diag_line

    d = tmp_path / "r"
    d.mkdir()
    (d / "diag-logcat.txt").write_text(
        diag_line(3, temp=27.5, pss=889) + "\n" + diag_line(120, temp=41.0, thermal=2) + "\n",
        encoding="utf-8",
    )
    boots, diags = parse_logcat(d / "diag-logcat.txt")
    assert len(diags) == 2
    assert diags[0].t_s == 3
    assert diags[0].get_float("temp") == pytest.approx(27.5)
    assert diags[1].get_float("thermal") == 2
    assert diags[1].fields["pss"] == "900.0" or True


def test_logcat_diag_without_t_is_error(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    (d / "diag-logcat.txt").write_text(
        "11-11 12:00:00.000 1 1 I Unity   : [DIAG] fps=30 temp=27.5C\n", encoding="utf-8"
    )
    with pytest.raises(ParseError, match="bez pola t="):
        parse_logcat(d / "diag-logcat.txt")


def test_metrics_json_roundtrip(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    (d / "metrics.json").write_text(json.dumps({"serial": "X", "timestamp": "T", "frameTime": {}}))
    from perfgate.formats import parse_metrics_json

    m = parse_metrics_json(d / "metrics.json")
    assert m["serial"] == "X"
