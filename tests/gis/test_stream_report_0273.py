"""ADR 0273 §7: the run report parses the streamer / pack / safety log lines exactly as the C# code prints them."""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("stream_report", REPO / "scripts" / "stream-report.py")
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)

LOG = """\
[STREAM] on: start bialystok-industrial-c, 1/1 neighbour tile scenes available (0 from packs), load radius 400 m, unload +300 m, max 4 tiles, budget 1450 MB (High content, desktop)
[STREAM] pinned bialystok-industrial-c (start tile: no safe pose yet)
[STREAM] load World_bialystok-maczka_High_Tile (resident 1 tiles)
[STREAM] ready World_bialystok-maczka_High_Tile: load 1830 ms, activation 412 ms (96 chunks), vehicle 212 m from the tile, resident 2 tiles / 687 MB (ESTIMATED)
[STREAM] pinned bialystok-maczka (newest safe pose)
[PACKS] acquire dk65-06 set=0.1.0-abc scene=World_dk65-06 tile=World_dk65-06_Tile loaded 2 bundle(s), held regions 1, bundles 2
[STREAM] ready World_dk65-06_Tile: load 900 ms, activation 300 ms (40 chunks), vehicle 0 m from the tile, resident 3 tiles / 900 MB (ESTIMATED)
[STREAM] over budget: resident 1500 MB (ESTIMATED) > 1450 MB, loading the tile ahead anyway (ADR 0235 §4)
[STREAM] unload World_bialystok-maczka_High_Tile
[PACKS] release dk65-06|Low: unloaded [dk65-06,common], held regions 0
[SAFETY] reset #1 reason=Fell from=(1.0,2.0,3.0) speed=40 km/h -> safe pose (1,2,3) yaw=0 age=3.0 s
"""


def test_parse_log_counts_every_kind():
    r = sr.parse_log(LOG)
    assert r["on"].startswith("start bialystok-industrial-c")
    assert r["loads"] == 1 and r["unloads"] == 1 and r["over_budget"] == 1
    assert [p["tile"] for p in r["pins"]] == ["bialystok-industrial-c", "bialystok-maczka"]
    assert [x["load_ms"] for x in r["ready"]] == [1830, 900]
    assert r["ready"][1]["vehicle_m"] == 0
    assert r["packs_acquire"] == 1 and r["packs_release"] == 1
    assert [x["reason"] for x in r["resets"]] == ["Fell"]


def test_gate_flags_reset_late_tile_spikes_and_memory(tmp_path):
    frames = tmp_path / "frametimes.csv"
    frames.write_text("frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab\n" +
                      "".join(f"{i},{i / 60:.3f},{40.0 if i % 10 == 0 else 16.6},0,0,1,0,0\n" for i in range(200)), encoding="utf-8")
    mem = tmp_path / "mem.csv"
    mem.write_text("t_s,working_set_mb,private_mb\n0,3000,2900\n1,6500,6000\n", encoding="utf-8")
    f = sr.parse_frames(frames, 33.3)
    assert f["frames"] == 200 and f["over_threshold"] == 20 and f["max"] == 40.0
    m = sr.parse_memory(mem)
    assert m["peak_working_set_mb"] == 6500
    fails = sr.gate(sr.parse_log(LOG), f, m, 12, 6144)
    assert len(fails) == 4, fails
    ok = sr.gate(sr.parse_log(LOG.replace("vehicle 0 m", "vehicle 50 m").replace("[SAFETY] reset #1", "[SAFETY] x")), None, None, 12, None)
    assert ok == []


def test_gate_off_when_streaming_was_not_on():
    assert sr.gate(sr.parse_log("[STREAM] off: no neighbour tile scene"), None, None, 12, None)[0].startswith("streaming was not on")
