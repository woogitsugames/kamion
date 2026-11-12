import numpy as np
import pytest

from perfgate.cli import main
from perfgate.report import generate_report

from conftest import diag_line, make_rows, write_run_dir


def test_report_end_to_end(tmp_path):
    ft = [33.333] * 2000 + [50.1] * 20  # trochę klatek > 1.5x
    lines = [diag_line(t, temp=28.0 + t / 200.0, pss=850 + t / 20.0) for t in range(0, 91, 5)]
    d = write_run_dir(
        tmp_path / "run1",
        make_rows(ft),
        diag_lines=lines,
        battery="  level: 80\n  temperature: 276\n",
        thermal="Thermal Status: 0\n\tTemperature{mValue=30.0, mType=0, mName=AP, mStatus=0}\n",
        meminfo="        TOTAL   870000   736515\n",
    )
    out = tmp_path / "out"
    rp = generate_report(d, out_dir=out, warmup_s=0.0, target_fps=30)
    md = rp.read_text(encoding="utf-8")
    assert "Raport bramki wydajności" in md
    assert "VALID" in md
    assert "naprzemienność" in md
    assert "throttling: nie wykryto" in md
    for png in ("frametimes.png", "windows.png", "thermal_pss.png"):
        assert (out / png).exists() and (out / png).stat().st_size > 1000


def test_cli_report_and_check(tmp_path):
    d = write_run_dir(tmp_path / "run2", make_rows([33.333] * 500), battery="  level: 80\n  temperature: 276\n")
    assert main(["report", str(d), "--out", str(tmp_path / "rep"), "--warmup-s", "0"]) == 0
    assert (tmp_path / "rep" / "report.md").exists()
    assert main(["check", str(d)]) == 0
    d2 = write_run_dir(tmp_path / "run3", make_rows([33.333] * 500), battery="  level: 10\n  temperature: 276\n")
    assert main(["check", str(d2)]) == 1


def test_cli_compare(tmp_path):
    rng = np.random.default_rng(5)
    a = rng.normal(33.33, 0.2, 1500)
    b = rng.normal(36.0, 0.2, 1500)
    da = write_run_dir(tmp_path / "A", make_rows(list(a)))
    db = write_run_dir(tmp_path / "B", make_rows(list(b)))
    assert main(["compare", str(da), str(db), "--boot", "1000", "--warmup-s", "0"]) == 0


def test_cli_history(tmp_path):
    root = tmp_path / "hist"
    write_run_dir(root / "r1", make_rows([33.333] * 300))
    write_run_dir(root / "r2", make_rows([40.0] * 300))
    out = tmp_path / "hist.md"
    assert main(["history", str(root), "--out", str(out), "--warmup-s", "0"]) == 0
    txt = out.read_text(encoding="utf-8")
    assert "r1" in txt and "r2" in txt and "p95" in txt


def test_cli_unknown_column_exit_code(tmp_path):
    d = tmp_path / "bad"
    d.mkdir()
    (d / "frametimes.csv").write_text(
        "frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab,extra\n1,0,33,0,0,0.75,0,,x\n",
        encoding="utf-8",
    )
    assert main(["report", str(d)]) == 2
