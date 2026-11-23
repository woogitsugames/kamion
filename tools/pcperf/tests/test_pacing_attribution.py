"""ADR 0333: pacing_attribution splits slow frames into clean / contended seconds."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pacing_attribution as pa  # noqa: E402


def _write(run: Path, frames, sysload_rows):
    (run / "frametimes.csv").write_text(
        "frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab\n"
        + "".join(f"{i},{t},{ms},5,7,1.00,2,\n" for i, (t, ms) in enumerate(frames)), encoding="utf-8")
    hdr = ("wall,t_game_s,cpu_total_pct,cpu_game_pct,cpu_other_pct,game_fg,fg_name,mem_avail_mb,gpu_util_pct,"
           "gpu_clock_mhz,mem_clock_mhz,gpu_pstate,gpu_power_w,gpu_temp_c,top_other\n")
    (run / "sysload.csv").write_text(hdr + "".join(
        f"x,{t},{o + 20},20,{o},{fg},Kamion,1000,50,1500,4000,P0,100,60,Unity:1={o};robocopy:2=1\n"
        for t, o, fg in sysload_rows), encoding="utf-8")


def test_clean_vs_contended(tmp_path):
    frames = [(10.0 + i * 0.5, 16.7) for i in range(40)] + [(12.2, 55.0), (20.2, 48.0), (25.2, 45.0)]
    frames.sort()
    rows = [(10.5 + i, 2.0, 1) for i in range(20)]
    rows[10] = (20.5, 35.0, 1)          # other process busy -> covers frame at 20.2
    rows[15] = (25.5, 1.0, 0)           # game not in foreground -> covers 25.2
    _write(tmp_path, frames, rows)
    r = pa.attribute(pa.read_frames(tmp_path), pa.read_sysload(tmp_path / "sysload.csv", 0.0))
    assert r.slow == 3
    assert r.slow_clean == 1 and r.clean_slow_list[0][0] == 12.2
    assert r.slow_contended == 2
    assert r.reasons["not_foreground"] == 1
    assert r.contenders["Unity"] == 2


def test_unsampled_and_exit_codes(tmp_path):
    _write(tmp_path, [(50.0, 80.0)], [(10.5, 0.0, 1)])
    r = pa.attribute(pa.read_frames(tmp_path), pa.read_sysload(tmp_path / "sysload.csv", 0.0))
    assert r.slow_unsampled == 1
    assert pa.main([str(tmp_path)]) == 0
    assert pa.main([str(tmp_path / "nope")]) == 2
