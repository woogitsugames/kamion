import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from perfgate.formats import FrameRow  # noqa: E402


def make_rows(ft_ms, start_t=0.0, dt=0.033333):
    """Wiersze FrameRow z podanych czasów klatek (t narastająco)."""
    rows = []
    t = start_t
    for i, ms in enumerate(ft_ms, start=1):
        rows.append(
            FrameRow(
                frame=i,
                t_s=t,
                frame_ms=ms,
                cpu_main_ms=0.0,
                gpu_ms=0.0,
                render_scale=0.75,
                mirror_n=0.0,
                ab="",
            )
        )
        t += ms / 1000.0
    return rows


def write_run_dir(path: Path, rows, diag_lines=None, battery=None, thermal=None, meminfo=None):
    path.mkdir(parents=True, exist_ok=True)
    header = "frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab"
    lines = [header]
    for r in rows:
        lines.append(
            f"{r.frame},{r.t_s:.4f},{r.frame_ms:.3f},{r.cpu_main_ms:.3f},{r.gpu_ms:.3f},"
            f"{r.render_scale},{r.mirror_n},{r.ab}"
        )
    (path / "frametimes.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if diag_lines is not None:
        (path / "diag-logcat.txt").write_text("\n".join(diag_lines) + "\n", encoding="utf-8")
    if battery is not None:
        (path / "battery.txt").write_text(battery, encoding="utf-8")
    if thermal is not None:
        (path / "thermal.txt").write_text(thermal, encoding="utf-8")
    if meminfo is not None:
        (path / "meminfo.txt").write_text(meminfo, encoding="utf-8")
    return path


def diag_line(t_s, temp=27.5, thermal=0, pss=900.0, scale=0.75, fps=30.0, headroom=0.5):
    return (
        f"11-11 12:00:{int(t_s) % 60:02d}.000 11949 11965 I Unity   : "
        f"[DIAG] t={int(t_s)}s tier=Low target=30 fps={fps} p50=33.33 p95=33.40 p99=33.50 "
        f"max=33.50ms temp={temp}C thermal={thermal} headroom={headroom} pss={pss}MB "
        f"scale={scale} fallback=none mir=1.00/f cpu=3.30 gpu=28.00 cap=0.10/f cpu=0.10 gpu=28.0 "
        f"shd_gpu=- main_cpu=6.60"
    )


@pytest.fixture
def run_dir_factory(tmp_path):
    def _factory(name="run", **kw):
        return write_run_dir(tmp_path / name, **kw)

    return _factory
