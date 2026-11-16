"""Testy parsera pomiaru PC (ADR 0266). Uruchomienie: uv run --with pytest pytest tools/pcperf/tests -q"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pc_metrics as pm  # noqa: E402

BUDGET = Path(__file__).resolve().parents[1] / "budgets" / "pc-budgets.json"
MACHINES = Path(__file__).resolve().parents[1] / "budgets" / "pc-machines.json"


# ---------------------------------------------------------------- dane syntetyczne


def make_run(tmp: Path, frame_ms: list[float], *, fps_dt: float | None = None, width=1920, height=1080, tier="High",
             target_fps=60, warmup=5.0, editor=False, focus_lost=0, end="duration", draws=1500, tris=2_000_000,
             gc_step_at: list[int] | None = None, loads=None, memory=True, process=True, private_peak=4000.0,
             vram_peak=3000.0, gpu="Synthetic GPU", cpu="Synthetic CPU", dropped=0, vsync=0,
             fullscreen="FullScreenWindow", gpu_vendor="X") -> Path:
    d = tmp / "run"
    d.mkdir(parents=True, exist_ok=True)
    lines = [",".join(pm.FRAMES_HEADER)]
    t = 0.0
    gc = 10
    for i, ms in enumerate(frame_ms):
        if gc_step_at and i in gc_step_at:
            gc += 1
        lines.append(f"{i + 100},{t:.4f},{ms:.3f},{ms * 0.6:.3f},{ms * 0.8:.3f},{draws},{draws // 2},{draws // 10},{tris},{gc},1")
        t += (fps_dt if fps_dt is not None else ms / 1000.0)
    (d / "frames.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if memory:
        mem = [",".join(pm.MEMORY_HEADER)]
        for k in range(40):
            mem.append(f"{k * 0.5:.3f},{1000 + k:.1f},{1500 + 2 * k:.1f},50.0,64.0,-1.0,{gc}")
        (d / "memory.csv").write_text("\n".join(mem) + "\n", encoding="utf-8")
    if process:
        pr = [",".join(pm.PROCESS_HEADER)]
        pr.append(f"0.0,1000.0,1200.0,500.0,10.0,,")
        pr.append(f"2.0,3000.0,{private_peak},{vram_peak},12.0,61,95")
        pr.append(f"4.0,2900.0,{private_peak - 100},{vram_peak - 10},12.0,62,96")
        (d / "process.csv").write_text("\n".join(pr) + "\n", encoding="utf-8")
    run = {
        "format": pm.RUN_FORMAT, "label": "test", "endReason": end, "isEditor": editor, "platform": "WindowsPlayer",
        "unityVersion": "6000.3.28f1", "appVersion": "0.1.0", "development": False, "buildLabel": "0.1.0 (abc)",
        "commandLine": "Kamion.exe -metrics x",
        "system": {"os": "Windows 11", "cpu": cpu, "gpu": gpu, "gpuVendor": gpu_vendor, "graphicsApi": "Direct3D 12",
                   "deviceModel": "PC", "cpuCores": 12, "cpuFrequencyMHz": 3600, "systemMemoryMb": 32768, "gpuMemoryMb": 12000},
        "display": {"width": width, "height": height, "vSyncCount": vsync, "targetFrameRate": target_fps, "qualityLevel": 2,
                    "refreshRateHz": 144.0, "fullScreenMode": fullscreen, "qualityName": tier},
        "options": {"seconds": 90.0, "warmupSeconds": warmup, "start": "region", "vsyncOverride": -1, "maxFps": 1000},
        "recording": {"windowStartRealtime_s": 12.0, "drivingReadyRealtime_s": -1.0, "frames": len(frame_ms),
                      "droppedFrames": dropped, "focusLost": focus_lost, "gcAtStart": 10, "gcAtEnd": gc, "memorySamples": 40,
                      "countersAvailable": True},
        "loads": loads if loads is not None else [
            {"scene": "Region_knyszyn", "loadStart_s": 3.0, "firstFrameEnd_s": 11.5, "seconds": 8.5, "startSource": "frame"}],
        "inGame": {"samples": 0, "over33Ms": 0, "over50Ms": 0, "over100Ms": 0, "meanFps": 0, "p50Ms": 0, "p95Ms": 0, "p99Ms": 0, "maxMs": 0},
    }
    (d / "run.json").write_text(json.dumps(run), encoding="utf-8")
    return d


def steady(n: int, ms: float) -> list[float]:
    return [ms] * n


# ---------------------------------------------------------------- percentyle (te same przypadki co PcMetricsMathTests)


def test_nearest_rank_one_to_hundred():
    a = [float(i) for i in range(1, 101)]
    assert pm.nearest_rank(a, 0.50) == 50
    assert pm.nearest_rank(a, 0.95) == 95
    assert pm.nearest_rank(a, 0.99) == 99
    assert pm.nearest_rank(a, 1.0) == 100
    assert pm.nearest_rank(a, 0.0) == 1


def test_nearest_rank_small_and_empty():
    assert pm.nearest_rank([10.0, 20.0, 30.0], 0.50) == 20
    assert pm.nearest_rank([10.0, 20.0, 30.0], 0.95) == 30
    assert pm.nearest_rank([10.0], 0.99) == 10
    assert pm.nearest_rank([], 0.5) is None


def test_nearest_rank_integer_product_not_rounded_up():
    a = [float(i) for i in range(1, 21)]
    assert pm.nearest_rank(a, 0.95) == 19


def test_summarize_unsorted():
    s = pm.summarize([5.0, 1.0, 3.0, 2.0, 4.0])
    assert s["p50"] == 3 and s["max"] == 5 and s["samples"] == 5 and s["mean"] == 3


def test_slope_per_minute():
    ts = [0.0, 30.0, 60.0, 90.0]
    assert pm.slope_per_minute(ts, [100.0, 110.0, 120.0, 130.0]) == pytest.approx(20.0)
    assert pm.slope_per_minute([0.0, 1.0], [1.0, 2.0]) is None


# ---------------------------------------------------------------- analiza i budżet


def test_pass_recommended_class(tmp_path):
    d = make_run(tmp_path, steady(6000, 15.0))
    rep = pm.evaluate(pm.load_run(d), pm.load_budget(BUDGET), "zalecany")
    assert rep["verdict"] == "PASS", rep["checks"]
    assert rep["gate_eligible"] is False          # brak maszyny referencyjnej w budżecie
    assert rep["reference_machine"] is False
    m = rep["metrics"]
    assert m["frame_ms"]["p99"] == pytest.approx(15.0)
    assert m["region_load_s"]["max"] == pytest.approx(8.5)
    assert m["process"]["private_mb"]["peak"] == pytest.approx(4000.0)
    assert m["unity_memory"]["reserved_mb_per_min"] == pytest.approx(240.0)   # 2 MB / 0,5 s
    assert all(c["value_status"] == "WORKING_VALUE" for c in rep["checks"])
    assert pm.exit_code(rep) == 0


def test_warmup_frames_excluded(tmp_path):
    # 5 s rozgrzewki po 100 ms (50 klatek), potem 15 ms — nie mogą wpłynąć na p99 ani na liczbę > 100 ms.
    frames = steady(50, 100.5) + steady(6000, 15.0)
    d = make_run(tmp_path, frames)
    rep = pm.evaluate(pm.load_run(d), pm.load_budget(BUDGET), "zalecany")
    assert rep["metrics"]["frames_window"] == 6000
    assert rep["metrics"]["frames_over"]["100"]["count"] == 0
    assert rep["verdict"] == "PASS"


def test_spikes_fail_and_counts(tmp_path):
    frames = steady(6000, 15.0)
    for i in range(1000, 1100):      # 100 klatek po 40 ms = 1,6 % > 33,3 ms -> FAIL (limit 0,5 %)
        frames[i] = 40.0
    frames[3000] = 120.0             # 1 przycięcie > 100 ms -> FAIL (limit 0)
    d = make_run(tmp_path, frames)
    rep = pm.evaluate(pm.load_run(d), pm.load_budget(BUDGET), "zalecany")
    st = {c["metric"]: c for c in rep["checks"]}
    assert st["frames_over_pct>33.3ms"]["status"] == "FAIL"
    assert st["frames_over_count>100ms"]["value"] == 1
    assert st["frames_over_count>100ms"]["status"] == "FAIL"
    assert rep["verdict"] == "FAIL"
    assert pm.exit_code(rep) == 1


def test_memory_and_load_over_budget(tmp_path):
    d = make_run(tmp_path, steady(6000, 15.0), private_peak=9000.0,
                 loads=[{"scene": "A", "seconds": 25.0, "startSource": "marked"}, {"scene": "B", "seconds": -1}])
    rep = pm.evaluate(pm.load_run(d), pm.load_budget(BUDGET), "zalecany")
    st = {c["metric"]: c["status"] for c in rep["checks"]}
    assert st["process.private_mb.peak"] == "FAIL"
    assert st["region_load_s.max"] == "FAIL"
    assert rep["metrics"]["region_load_s"]["loads"] == [{"scene": "A", "seconds": 25.0, "start": "marked"}]


def test_gc_collections_counted_in_window_only(tmp_path):
    frames = steady(6000, 15.0)
    d = make_run(tmp_path, frames, gc_step_at=[10, 1000, 2000, 3000])   # 10 = w rozgrzewce
    rep = pm.evaluate(pm.load_run(d), pm.load_budget(BUDGET), "zalecany")
    assert rep["metrics"]["gc"]["collections_in_window"] == 3
    st = {c["metric"]: c["status"] for c in rep["checks"]}
    assert st["gc.collections_in_window"] == "FAIL"


def test_missing_process_csv_is_incomplete_not_fail(tmp_path):
    d = make_run(tmp_path, steady(6000, 15.0), process=False)
    rep = pm.evaluate(pm.load_run(d), pm.load_budget(BUDGET), "zalecany")
    assert rep["verdict"] == "INCOMPLETE"
    assert pm.exit_code(rep) == 0
    st = {c["metric"]: c["status"] for c in rep["checks"]}
    assert st["process.private_mb.peak"] == "NO_DATA"


def test_counters_unavailable_are_no_data(tmp_path):
    d = make_run(tmp_path, steady(6000, 15.0), draws=-1, tris=-1)
    rep = pm.evaluate(pm.load_run(d), pm.load_budget(BUDGET), "zalecany")
    assert rep["metrics"]["draw_calls"] is None
    st = {c["metric"]: c["status"] for c in rep["checks"]}
    assert st["draw_calls.p95"] == "NO_DATA" and st["tris.p95"] == "NO_DATA"


@pytest.mark.parametrize("kw,needle", [
    ({"editor": True}, "edytorze"),
    ({"focus_lost": 1}, "fokus"),
    ({"end": "quit"}, "endReason"),
    ({"dropped": 5}, "bufor"),
])
def test_invalid_runs(tmp_path, kw, needle):
    d = make_run(tmp_path, steady(6000, 15.0), **kw)
    rep = pm.evaluate(pm.load_run(d), pm.load_budget(BUDGET), "zalecany")
    assert rep["verdict"] == "INVALID"
    assert any(needle in r for r in rep["invalid_reasons"])
    assert pm.exit_code(rep) == 2


def test_too_few_frames_invalid(tmp_path):
    d = make_run(tmp_path, steady(400, 15.0), warmup=0.0)
    rep = pm.evaluate(pm.load_run(d), pm.load_budget(BUDGET), "zalecany")
    assert rep["verdict"] == "INVALID"


def test_context_mismatch_invalid_unless_allowed(tmp_path):
    d = make_run(tmp_path, steady(6000, 15.0), width=2560, height=1440, tier="Ultra")
    budget = pm.load_budget(BUDGET)
    rep = pm.evaluate(pm.load_run(d), budget, "zalecany")
    assert rep["verdict"] == "INVALID"
    assert len(rep["class"]["context_mismatch"]) == 2
    rep2 = pm.evaluate(pm.load_run(d), budget, "zalecany", allow_mismatch=True)
    assert rep2["verdict"] == "PASS"
    rep3 = pm.evaluate(pm.load_run(d), budget, "wysoki")
    assert rep3["class"]["context_mismatch"] == []


def test_reference_machine_makes_gate_eligible(tmp_path):
    d = make_run(tmp_path, steady(6000, 15.0), gpu="Ref GPU", cpu="Ref CPU")
    budget = pm.load_budget(BUDGET)
    budget["referenceMachines"] = [{"gpu": "Ref GPU", "cpu": "Ref CPU", "class": "zalecany"}]
    rep = pm.evaluate(pm.load_run(d), budget, "zalecany")
    assert rep["reference_machine"] is True and rep["gate_eligible"] is True


def test_unknown_frames_column_rejected(tmp_path):
    d = make_run(tmp_path, steady(10, 15.0))
    p = d / "frames.csv"
    p.write_text(p.read_text().replace("scene", "scene_x", 1))
    with pytest.raises(pm.FormatError):
        pm.load_run(d)


def test_wrong_run_format_rejected(tmp_path):
    d = make_run(tmp_path, steady(10, 15.0))
    j = json.loads((d / "run.json").read_text())
    j["format"] = "something/else"
    (d / "run.json").write_text(json.dumps(j))
    with pytest.raises(pm.FormatError):
        pm.load_run(d)


def test_unknown_class_raises(tmp_path):
    d = make_run(tmp_path, steady(6000, 15.0))
    with pytest.raises(KeyError):
        pm.evaluate(pm.load_run(d), pm.load_budget(BUDGET), "ultra-max")


def test_no_budget_reports_numbers_only(tmp_path):
    d = make_run(tmp_path, steady(6000, 15.0))
    rep = pm.evaluate(pm.load_run(d), None, None)
    assert rep["verdict"] == "NO_BUDGET" and rep["checks"] == []
    assert pm.exit_code(rep) == 0


def test_cli_writes_reports_and_exit_codes(tmp_path, capsys):
    d = make_run(tmp_path, steady(6000, 15.0))
    assert pm.main([str(d), "--class", "zalecany"]) == 0
    rep = json.loads((d / "pc-report.json").read_text(encoding="utf-8"))
    assert rep["verdict"] == "PASS"
    md = (d / "pc-report.md").read_text(encoding="utf-8")
    assert "WORKING_VALUE" in md and "Werdykt budżetu: PASS" in md and "informacyjny" in md
    assert "_ms_window" not in json.dumps(rep)
    assert pm.main([str(tmp_path / "nope"), "--class", "zalecany"]) == 2


def test_budget_file_all_working_value_and_classes():
    b = pm.load_budget(BUDGET)
    assert b["status"] == "WORKING_VALUE"
    assert set(b["classes"]) == {"min", "zalecany", "wysoki"}
    assert b["referenceMachines"] == []          # referencyjny PC nieustalony (ADR 0260)
    for name, c in b["classes"].items():
        assert c["status"] == "WORKING_VALUE", name
        metrics = {ch["metric"] for ch in c["checks"]}
        for required in ("frame_ms.p50", "frame_ms.p95", "frame_ms.p99", "frames_over_pct", "process.private_mb.peak",
                         "process.gpu_dedicated_mb.peak", "region_load_s.max", "draw_calls.p95", "tris.p95"):
            assert required in metrics, (name, required)
        # p50 zgodny z limitem FPS klasy
        p50 = next(ch["max"] for ch in c["checks"] if ch["metric"] == "frame_ms.p50")
        assert p50 == pytest.approx(1000.0 / c["targetFps"], abs=0.05)
    # zabezpieczenie mobilne zachowane (< 2 M tris Ultra / 1,5 M High)
    assert b["mobileSafeguard"]["trisInView"]["Ultra"] == 2_000_000


def test_docs03_table_matches_budget_file():
    """Tabela w docs/03 i plik budżetu muszą mówić to samo (p50/p95/p99 per klasa)."""
    doc = (Path(__file__).resolve().parents[3] / "docs" / "03_ETAPY_I_BRAMKI.md").read_text(encoding="utf-8")
    b = pm.load_budget(BUDGET)
    for key, row in (("frame_ms.p50", "Czas klatki p50"), ("frame_ms.p95", "Czas klatki p95"), ("frame_ms.p99", "Czas klatki p99")):
        line = next(l for l in doc.splitlines() if l.startswith(f"| {row} "))
        for cls in ("min", "zalecany", "wysoki"):
            v = next(ch["max"] for ch in b["classes"][cls]["checks"] if ch["metric"] == key)
            assert f"{v:.1f}".replace(".", ",") in line, (row, cls, v)


def test_cross_check_with_in_game_percentiles(tmp_path):
    d = make_run(tmp_path, steady(6000, 15.0))
    rep0 = pm.evaluate(pm.load_run(d), None, None)
    assert rep0["cross_check"] is None                 # inGame.samples == 0 -> brak kontroli
    n = rep0["metrics"]["frames_window"]
    j = json.loads((d / "run.json").read_text())
    j["inGame"].update({"samples": n, "p50Ms": 15.0, "p95Ms": 15.0, "p99Ms": 15.0})
    (d / "run.json").write_text(json.dumps(j))
    cc = pm.evaluate(pm.load_run(d), None, None)["cross_check"]
    assert cc["ok"] is True and cc["samples_game"] == n
    j["inGame"]["p99Ms"] = 16.0
    (d / "run.json").write_text(json.dumps(j))
    cc2 = pm.evaluate(pm.load_run(d), None, None)["cross_check"]
    assert cc2["ok"] is False and cc2["max_diff_ms"] == pytest.approx(1.0)


# ---------------------------------------------------------------- D76: emulacja klas na maszynie deweloperskiej

DEV_GPU = dict(gpu="NVIDIA GeForce RTX 5070", gpu_vendor="NVIDIA", cpu="Intel(R) Core(TM) Ultra 7 270K Plus")
MIN_EMU = dict(width=1920, height=1080, tier="Low", target_fps=30, vram_peak=1500.0)   # VRAM min <= 1792 MB
REC_EMU = dict(width=1920, height=1080, tier="High", target_fps=60)


def _eval(d, cls, machines=None, **kw):
    return pm.evaluate(pm.load_run(d), pm.load_budget(BUDGET), cls,
                       machines=pm.load_machines(MACHINES) if machines is None else machines, **kw)


@pytest.mark.parametrize("cls,cond,ms", [("min", MIN_EMU, 30.0), ("zalecany", REC_EMU, 15.0)])
def test_emulation_matching_config_is_gate_eligible(tmp_path, cls, cond, ms):
    d = make_run(tmp_path, steady(6000, ms), **DEV_GPU, **cond)
    rep = _eval(d, cls)
    assert rep["verdict"] == "PASS", rep["checks"]
    assert rep["measurement_kind"] == "emulation"
    assert rep["gate_eligible"] is True
    assert rep["reference_machine"] is False
    assert rep["measurement"]["machine"] == "dev-rtx5070" and rep["measurement"]["decision"] == "D76"
    ann = rep["measurement"]["annotation"]
    assert ann.startswith("EMULACJA (D76)") and f"klasy {cls}" in ann and "przed obietnicą wymagań" in ann
    md = pm.render_md(rep)
    assert "EMULACJA (D76) — nie zastępuje pomiaru na sprzęcie klasy " + cls in md
    assert "Zalicza bramkę: **TAK**" in md


def test_emulation_fail_verdict_not_eligible(tmp_path):
    frames = steady(6000, 15.0)
    frames[3000] = 120.0
    d = make_run(tmp_path, frames, **DEV_GPU, **REC_EMU)
    rep = _eval(d, "zalecany")
    assert rep["verdict"] == "FAIL" and rep["measurement_kind"] == "emulation" and rep["gate_eligible"] is False
    assert pm.exit_code(rep) == 1


@pytest.mark.parametrize("cls,kw,needle", [
    ("zalecany", dict(REC_EMU, width=2560, height=1440), "rozdzielczość"),
    ("zalecany", dict(REC_EMU, tier="Ultra"), "tier"),
    ("min", dict(MIN_EMU, target_fps=60), "limit FPS"),
    ("zalecany", dict(REC_EMU, vsync=1), "VSync"),
    ("zalecany", dict(REC_EMU, fullscreen="Windowed"), "tryb ekranu"),
])
def test_emulation_config_mismatch_is_informational(tmp_path, cls, kw, needle):
    d = make_run(tmp_path, steady(6000, 15.0), **DEV_GPU, **kw)
    rep = _eval(d, cls, allow_mismatch=True)       # nawet PASS przy --allow-context-mismatch nie zalicza
    assert rep["measurement_kind"] == "informational"
    assert rep["gate_eligible"] is False
    assert rep["measurement"]["machine"] == "dev-rtx5070"
    assert any(needle in r for r in rep["measurement"]["reasons"]), rep["measurement"]["reasons"]
    assert rep["measurement"]["annotation"] is None
    assert "Dlaczego nie zalicza" in pm.render_md(rep)


def test_vsync_mismatch_alone_keeps_verdict_but_not_gate(tmp_path):
    # VSync nie jest warunkiem klasy w budżecie -> werdykt PASS, ale emulacja wymaga VSync 0
    d = make_run(tmp_path, steady(6000, 15.0), **DEV_GPU, **REC_EMU, vsync=1)
    rep = _eval(d, "zalecany")
    assert rep["verdict"] == "PASS" and rep["gate_eligible"] is False and rep["measurement_kind"] == "informational"
    assert pm.exit_code(rep) == 0


@pytest.mark.parametrize("gpu,vendor", [("NVIDIA GeForce RTX 4070", "NVIDIA"), ("NVIDIA GeForce RTX 5070 Ti", "NVIDIA"),
                                        ("Synthetic GPU", "X")])
def test_unmatched_gpu_is_informational(tmp_path, gpu, vendor):
    d = make_run(tmp_path, steady(6000, 15.0), gpu=gpu, gpu_vendor=vendor, **REC_EMU)
    rep = _eval(d, "zalecany")
    assert rep["verdict"] == "PASS"
    assert rep["measurement_kind"] == "informational" and rep["gate_eligible"] is False
    assert "nie jest w pc-machines.json" in rep["measurement"]["reasons"][0]


def test_dev_machine_class_without_emulation_is_informational(tmp_path):
    d = make_run(tmp_path, steady(6000, 15.0), **DEV_GPU, width=2560, height=1440, tier="Ultra", target_fps=60)
    rep = _eval(d, "wysoki")
    assert rep["verdict"] == "PASS" and rep["measurement_kind"] == "informational"
    assert "nie emuluje klasy wysoki" in rep["measurement"]["reasons"][0]


def test_reference_entry_in_machines_file_is_gate_eligible(tmp_path):
    d = make_run(tmp_path, steady(6000, 30.0), gpu="NVIDIA GeForce GTX 660", gpu_vendor="NVIDIA",
                 cpu="Intel(R) Core(TM) i5-6400 CPU @ 2.70GHz", **MIN_EMU, vsync=1, fullscreen="Windowed")
    machines = pm.load_machines(MACHINES)
    machines["reference"] = [{"id": "test-gtx660", "classes": ["min"],
                              "match": {"gpuContains": ["GTX 660"], "cpuContains": ["i5-6400"]}}]
    rep = _eval(d, "min", machines=machines)
    assert rep["measurement_kind"] == "reference" and rep["gate_eligible"] is True
    assert rep["measurement"]["annotation"] is None
    assert "EMULACJA" not in pm.render_md(rep)
    rep2 = _eval(d, "zalecany", machines=machines, allow_mismatch=True)   # wpis tylko dla klasy min
    assert rep2["measurement_kind"] == "informational"


def test_legacy_reference_machines_in_budget_still_work(tmp_path):
    d = make_run(tmp_path, steady(6000, 15.0), gpu="Ref GPU", cpu="Ref CPU")
    budget = pm.load_budget(BUDGET)
    budget["referenceMachines"] = [{"gpu": "Ref GPU", "cpu": "Ref CPU", "class": "zalecany"}]
    rep = pm.evaluate(pm.load_run(d), budget, "zalecany")      # bez pliku maszyn (stare wywołanie)
    assert rep["measurement_kind"] == "reference" and rep["gate_eligible"] is True


def test_old_run_json_without_display_fields(tmp_path):
    """Stary / niepełny run.json: brak vSyncCount, fullScreenMode i gpuVendor -> nie wywraca się, emulacja niepotwierdzona."""
    d = make_run(tmp_path, steady(6000, 15.0), **DEV_GPU, **REC_EMU)
    j = json.loads((d / "run.json").read_text())
    del j["display"]["vSyncCount"], j["display"]["fullScreenMode"], j["system"]["gpuVendor"]
    (d / "run.json").write_text(json.dumps(j))
    rep = _eval(d, "zalecany")
    assert rep["verdict"] == "PASS"
    assert rep["measurement_kind"] == "informational" and rep["gate_eligible"] is False
    j.pop("system")
    (d / "run.json").write_text(json.dumps(j))
    rep2 = _eval(d, "zalecany")
    assert rep2["measurement_kind"] == "informational"
    pm.render_md(rep2)


def test_no_class_is_informational(tmp_path):
    d = make_run(tmp_path, steady(6000, 15.0), **DEV_GPU, **REC_EMU)
    rep = pm.evaluate(pm.load_run(d), None, None, machines=pm.load_machines(MACHINES))
    assert rep["measurement_kind"] == "informational" and rep["gate_eligible"] is False


def test_cli_emulation_default_machines_file(tmp_path, capsys):
    d = make_run(tmp_path, steady(6000, 30.0), **DEV_GPU, **MIN_EMU)
    assert pm.main([str(d), "--class", "min"]) == 0
    rep = json.loads((d / "pc-report.json").read_text(encoding="utf-8"))
    assert rep["measurement_kind"] == "emulation" and rep["gate_eligible"] is True
    assert "EMULACJA (D76)" in (d / "pc-report.md").read_text(encoding="utf-8")
    out = capsys.readouterr().out
    assert out.startswith("verdict=PASS ") and "kind=emulation gate_eligible=true" in out
    empty = tmp_path / "m.json"
    empty.write_text(json.dumps({"format": pm.MACHINES_FORMAT, "reference": [], "emulation": []}))
    assert pm.main([str(d), "--class", "min", "--machines", str(empty)]) == 0
    assert json.loads((d / "pc-report.json").read_text(encoding="utf-8"))["measurement_kind"] == "informational"
    assert pm.main([str(d), "--class", "min", "--machines", str(tmp_path / "brak.json")]) == 2
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"format": "x"}))
    assert pm.main([str(d), "--class", "min", "--machines", str(bad)]) == 2


def test_machines_file_schema_and_consistency_with_budget():
    m = pm.load_machines(MACHINES)
    b = pm.load_budget(BUDGET)
    assert m["format"] == "kamion/pc-machines/1" and m["decision"] == "D76"
    assert m["reference"] == []                     # prawdziwy sprzęt klas jeszcze nie wskazany
    ids = [e["id"] for e in m["reference"] + m["emulation"]]
    assert len(ids) == len(set(ids))
    dev = next(e for e in m["emulation"] if e["id"] == "dev-rtx5070")
    assert set(dev["classes"]) == {"min", "zalecany"}      # D76: tylko min i zalecany
    assert pm.machine_matches({"gpu": "NVIDIA GeForce RTX 5070", "gpuVendor": "NVIDIA"}, dev["match"])
    assert not pm.machine_matches({"gpu": "NVIDIA GeForce RTX 5070 Ti", "gpuVendor": "NVIDIA"}, dev["match"])
    for e in m["emulation"]:
        assert e.get("method") and e.get("decision") == "D76"
        for cname, cfg in e["classes"].items():
            assert cname in b["classes"], cname
            bc = b["classes"][cname]
            # metoda emulacji = warunki klasy z budżetu (rozdzielczość, tier, limit FPS) + VSync wył.
            assert list(cfg["resolution"]) == list(bc["resolution"]), cname
            assert cfg["tier"] == bc["tier"] and cfg["targetFps"] == bc["targetFps"], cname
            assert cfg["vSyncCount"] == 0
            assert set(cfg["fullScreenModes"]) <= {"FullScreenWindow", "ExclusiveFullScreen", "MaximizedWindow", "Windowed"}
            assert cfg.get("realHardware")


@pytest.mark.parametrize("mutate", [
    lambda m: m.update(format="kamion/pc-machines/0"),
    lambda m: m.update(reference=None),
    lambda m: m["emulation"][0]["match"].update(gpuNameIs="x"),
    lambda m: m["emulation"][0]["classes"]["min"].pop("vSyncCount"),
    lambda m: m["emulation"][0].update(classes=["min"]),
])
def test_machines_file_validation_rejects_bad_entries(tmp_path, mutate):
    m = json.loads(MACHINES.read_text(encoding="utf-8"))
    mutate(m)
    p = tmp_path / "pc-machines.json"
    p.write_text(json.dumps(m), encoding="utf-8")
    with pytest.raises(pm.FormatError):
        pm.load_machines(p)
