"""ADR 0241: parser sesji A/B GPU (perfgate.gpuab) i katalog wariantów. Wyłącznie dane SYNTETYCZNE
(generator niżej + tests/data/gpuab/frametimes_synthetic.csv) - to nie są pomiary telefonu.

    uv run --project tools/perf pytest tools/perf/tests/test_gpuab.py -q
"""
from __future__ import annotations

import csv
import json
import random
import zlib
from pathlib import Path

import pytest

from perfgate import gpuab
from perfgate.formats import parse_frametimes_csv

REPO = Path(__file__).resolve().parents[3]
DATA = Path(__file__).resolve().parent / "data" / "gpuab"
SAMPLE = DATA / "frametimes_synthetic.csv"
HEADER = "frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab"


def synth_csv(path: Path, gpu_ms: float, seconds: float = 60.0, seed: int = 1, jitter: float = 0.4, scale: float = 0.75,
              spikes: int = 0, ab_period: float = 0.0, ab_delta: float = 0.0, gpu_zero: bool = False) -> Path:
    """Syntetyczny frametimes.csv v1: limit 30 FPS (klatka 33,33 ms), GPU = gpu_ms +- jitter, opcjonalne okna rq_ab."""
    rng = random.Random(seed)
    lines, t, i = [HEADER], 0.0, 0
    while t < seconds:
        i += 1
        ab = ""
        g = gpu_ms + rng.uniform(-jitter, jitter)
        if ab_period > 0:
            state = int(t // ab_period) % 2
            ab = str(state)
            g += ab_delta * state
        frame = 50.0 if spikes and i % max(1, int(seconds * 30 / spikes)) == 0 and t > 30 else 33.333
        lines.append(f"{i},{t:.4f},{frame:.3f},{21.0 + rng.uniform(-1, 1):.3f},{0.0 if gpu_zero else g:.3f},{scale},1,{ab}")
        t += frame / 1000.0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def make_run(session: Path, variant: str, segment: str, repeat: int, gpu_ms: float, valid: bool = True, reason: str = "",
             extras: dict | None = None, pss: float = 900.0, temp: float = 30.0, **kw) -> Path:
    d = session / "runs" / f"r{repeat}-{variant}-{segment}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "run.json").write_text(json.dumps({
        "variant": variant, "segment": segment, "repeat": repeat, "extras": extras or {}, "valid": valid,
        "rejectReason": reason, "batteryTempBeforeC": temp, "warmupSeconds": 25}), encoding="utf-8")
    if valid:
        synth_csv(d / "frametimes.csv", gpu_ms, seed=zlib.crc32(f"{variant}/{segment}/{repeat}".encode()) % 10_000, **kw)
        (d / "metrics.json").write_text(json.dumps({"serial": "SYNTH", "timestamp": "x", "pssMb": pss, "batteryTempC": temp + 1.5,
                                                    "thermalStatus": 0}), encoding="utf-8")
    return d


@pytest.fixture
def session(tmp_path):
    s = tmp_path / "gpu-ab" / "20990101-000000"
    for rep, drift in ((1, 0.0), (2, 0.2), (3, 0.4)):      # dryf termiczny między rundami
        make_run(s, "baseline", "G3-A", rep, 32.0 + drift)
        make_run(s, "scale-070", "G3-A", rep, 30.0 + drift, extras={"rq_scale": "0.7"})
        make_run(s, "msaa-1", "G3-A", rep, 32.0 + drift + (0.05 if rep != 2 else -0.05), extras={"rq_msaa": "1"})
    (s / "session.json").write_text(json.dumps({"timestamp": "20990101-000000", "serial": "SYNTH", "tier": "Low", "fps": 30,
                                                "mode": "Drive", "repeats": 3, "warmupSeconds": 25,
                                                "apk": {"file": "synthetic.apk", "sha256": "0" * 64}}), encoding="utf-8")
    return s


# ---------------------------------------------------------------- katalog
def test_shipped_catalogue_is_valid():
    cat = gpuab.load_catalog()
    assert cat["baseline"] == "baseline"
    ids = [v["id"] for v in cat["variants"]]
    assert len(ids) == len(set(ids))
    assert next(v for v in cat["variants"] if v["id"] == "baseline")["extras"] == {}


def test_catalogue_covers_the_requested_switch_families():
    keys = {k for v in gpuab.load_catalog()["variants"] for k in v["extras"]}
    # skala, MSAA, kopia głębi / koloru, post, cienie, LOD bias, las / impostory
    for k in ("rq_scale", "rq_msaa", "rq_depthtex", "rq_opaquetex", "rq_post", "rq_shadow", "rq_lod", "rq_impostors",
              "rq_hlodpart", "rq_thin", "rq_trees"):
        assert k in keys, k
    by = {v["id"]: v for v in gpuab.load_catalog()["variants"]}
    assert by["shadows-off"]["extras"] == {"rq_shadow": "0"}


def test_every_catalogue_key_is_read_by_the_game_sources():
    src = REPO / "game" / "Assets" / "_Project"
    assert gpuab.unknown_catalog_keys(gpuab.load_catalog(), src) == []


def test_every_estimate_has_status_and_source():
    for v in gpuab.load_catalog()["variants"]:
        assert v["est_status"] in gpuab.EST_STATUSES, v["id"]
        assert len(v["est_source"]) > 20, v["id"]
        if v["est_gpu_ms"] is None:
            assert v["est_status"] == "UNVERIFIED", v["id"]


def test_validate_catalogue_reports_problems():
    cat = {"schema": gpuab.SCHEMA_CATALOG, "baseline": "baseline", "variants": [
        {"id": "baseline", "extras": {"rq_scale": "0.7"}, "role": "baseline", "default": True, "est_status": "REFERENCE", "est_source": "x"},
        {"id": "Bad Id", "extras": {"tier": "Low"}, "role": "nope", "default": "yes", "est_status": "MEASURED", "est_source": ""},
        {"id": "comma", "extras": {"rq_x": "1,2"}, "role": "lever", "default": False, "est_status": "UNVERIFIED", "est_source": "x"},
    ]}
    text = " | ".join(gpuab.validate_catalog(cat))
    for needle in ("puste extras", "zły id", "nie jest przełącznikiem", "rola", "est_status", "est_source", "default", "rq_x='1,2'"):
        assert needle in text, needle


def test_format_estimate():
    assert gpuab.format_estimate({"est_gpu_ms": [-2.0, -2.0], "est_status": "ESTIMATED"}) == "-2.00 ms (ESTIMATED)"
    assert gpuab.format_estimate({"est_gpu_ms": [-1.4, 0], "est_status": "ESTIMATED"}) == "-1.40 … 0 ms (ESTIMATED)"
    assert gpuab.format_estimate({"est_gpu_ms": [0.36, None], "est_status": "UNVERIFIED"}) == "+0.36 … ? ms (UNVERIFIED)"
    assert gpuab.format_estimate({"est_gpu_ms": None, "est_status": "UNVERIFIED"}) == "brak liczby (UNVERIFIED)"


# ---------------------------------------------------------------- przebieg
def test_committed_synthetic_csv_parses_and_matches_the_generator(tmp_path):
    rows = parse_frametimes_csv(SAMPLE)
    again = synth_csv(tmp_path / "again.csv", 32.0, seconds=40.0, seed=241, spikes=3)
    assert SAMPLE.read_text(encoding="utf-8") == again.read_text(encoding="utf-8"), "plik próbki nie pochodzi z generatora"
    a = gpuab.analyse_frames(rows, warmup_s=25.0)
    assert a["samples"] > gpuab.MIN_SAMPLES
    assert a["p50_ms"] == pytest.approx(33.333)
    assert a["max_ms"] == pytest.approx(50.0)
    assert a["over40"] >= 1 and a["over33"] == a["over40"]
    assert 31.6 <= a["gpu_p50_ms"] <= 32.4
    assert a["gpu_p50_ms"] <= a["gpu_p95_ms"] <= a["gpu_p99_ms"] <= 32.4
    assert a["render_scale_min"] == a["render_scale_max"] == 0.75


def test_warmup_is_cut_like_device_metrics(tmp_path):
    p = tmp_path / "f.csv"
    lines = [HEADER] + [f"{i},{i * 0.1:.4f},{99.0 if i < 250 else 33.333},20,{50.0 if i < 250 else 30.0},0.75,1," for i in range(1, 601)]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    a = gpuab.analyse_frames(parse_frametimes_csv(p), warmup_s=25.0)
    assert a["samples"] == 351 and a["max_ms"] == pytest.approx(33.333) and a["gpu_p99_ms"] == 30.0


def test_gpu_zero_samples_are_not_percentiles(tmp_path):
    rows = parse_frametimes_csv(synth_csv(tmp_path / "z.csv", 30.0, gpu_zero=True))
    a = gpuab.analyse_frames(rows, 25.0)
    assert a["gpu_samples"] == 0 and "gpu_p50_ms" not in a


def test_interleaved_rq_ab_windows(tmp_path):
    rows = parse_frametimes_csv(synth_csv(tmp_path / "ab.csv", 30.0, seconds=90, ab_period=4.0, ab_delta=-1.5, jitter=0.2))
    ab = gpuab.split_ab([r for r in rows if r.t_s >= 25])
    assert ab is not None and ab.n_a > 100 and ab.n_b > 100
    assert ab.delta_gpu_p50 == pytest.approx(-1.5, abs=0.15)
    assert gpuab.split_ab(parse_frametimes_csv(SAMPLE)) is None


def test_ab_settle_frames_are_dropped(tmp_path):
    # klatki tuż po przełączeniu niosą stan poprzedni: bez odcięcia 0,75 s zaniżyłyby różnicę
    lines = [HEADER]
    for i in range(1, 1201):
        t = i / 30.0
        state = int(t // 4) % 2
        in_settle = (t % 4) < 0.5
        g = 30.0 if (state == 0) != in_settle else 28.0   # w oknie przejściowym wartość poprzedniego stanu
        lines.append(f"{i},{t:.4f},33.333,20,{g},0.75,1,{state}")
    p = tmp_path / "s.csv"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ab = gpuab.split_ab(parse_frametimes_csv(p))
    assert ab.gpu_p50_a == 30.0 and ab.gpu_p50_b == 28.0


def test_load_run_rejections(tmp_path):
    s = tmp_path / "s"
    locked = make_run(s, "baseline", "G3-A", 1, 32.0, valid=False, reason="keyguard after the run")
    r = gpuab.load_run(locked)
    assert not r.valid and "keyguard" in r.reject_reason
    short = make_run(s, "baseline", "G3-A", 2, 32.0, seconds=26.0)
    r = gpuab.load_run(short)
    assert not r.valid and "za mało klatek" in r.reject_reason
    nocsv = make_run(s, "baseline", "G3-A", 3, 32.0)
    (nocsv / "frametimes.csv").unlink()
    assert "brak frametimes.csv" in gpuab.load_run(nocsv).reject_reason
    bad = make_run(s, "baseline", "G3-B", 1, 32.0)
    (bad / "frametimes.csv").write_text("frame,t_s,frame_ms,bogus\n1,0,33,1\n", encoding="utf-8")
    assert "nieznane kolumny" in gpuab.load_run(bad).reject_reason
    with pytest.raises(gpuab.GpuAbError):
        gpuab.load_run(tmp_path / "missing")


# ---------------------------------------------------------------- zestawienie
def test_summary_pairs_with_the_baseline_of_the_same_repeat(session):
    rows = {(r.variant, r.segment): r for r in gpuab.summarise(gpuab.load_session(session), gpuab.load_catalog())}
    base, scale, msaa = rows[("baseline", "G3-A")], rows[("scale-070", "G3-A")], rows[("msaa-1", "G3-A")]
    assert base.runs == 3 and base.d_gpu_p50_ms is None and base.significant == ""
    assert base.baseline_spread_gpu_p50 == pytest.approx(0.4, abs=0.15)
    # dryf 0,4 ms między rundami nie psuje różnicy liczonej w parach
    assert scale.pairs == 3
    assert scale.d_gpu_p50_ms == pytest.approx(-2.0, abs=0.15)
    assert scale.d_gpu_p50_max < 0 and scale.significant == "TAK"
    assert scale.estimate == "-2.00 ms (ESTIMATED)" and scale.role == "lever"
    assert abs(msaa.d_gpu_p50_ms) < 0.2 and msaa.significant == "NIE (szum)"
    assert base.gpu_p95_within_budget == "TAK" and base.pss_mb == 900.0
    assert base.battery_before_c == 30.0 and base.battery_after_c == 31.5 and base.thermal_max == 0


def test_summary_needs_three_pairs_and_counts_rejected(tmp_path):
    s = tmp_path / "s"
    for rep in (1, 2, 3):
        make_run(s, "baseline", "G3-B", rep, 34.6)
    make_run(s, "lod-030", "G3-B", 1, 33.0)
    make_run(s, "lod-030", "G3-B", 2, 33.0)
    make_run(s, "lod-030", "G3-B", 3, 33.0, valid=False, reason="battery 37.2 C >= 36 C after 20 min")
    rows = {r.variant: r for r in gpuab.summarise(gpuab.load_session(s), gpuab.load_catalog())}
    assert rows["lod-030"].runs == 2 and rows["lod-030"].rejected == 1
    assert rows["lod-030"].significant == "ZA MAŁO PAR"
    assert rows["baseline"].gpu_p95_within_budget == "NIE"     # 34,6 + jitter > 33,3


def test_report_writes_csv_and_markdown(session):
    make_run(session, "depthtex-on", "G3-A", 1, 33.0, valid=False, reason="keyguard")
    out = gpuab.report(session)
    assert out == {"runs": 10, "valid": 9, "rows": 4}
    with (session / "results.csv").open(encoding="utf-8") as f:
        res = list(csv.DictReader(f))
    assert len(res) == 10 and res[0].keys() == set(gpuab.RESULT_COLUMNS)
    one = next(r for r in res if r["variant"] == "scale-070" and r["repeat"] == "2")
    assert one["extras"] == "rq_scale=0.7" and one["valid"] == "1" and float(one["gpu_p50_ms"]) < 31
    with (session / "summary.csv").open(encoding="utf-8") as f:
        summ = {r["variant"]: r for r in csv.DictReader(f)}
    assert float(summ["scale-070"]["d_gpu_p50_ms"]) == pytest.approx(-2.0, abs=0.15)
    assert summ["depthtex-on"]["runs"] == "0" and summ["depthtex-on"]["rejected"] == "1"
    md = (session / "REPORT.md").read_text(encoding="utf-8")
    assert "## Odcinek / kamera G3-A" in md and "| scale-070 | lever | 3 |" in md
    assert "synthetic.apk" in md and "## Odrzucone przebiegi" in md and "keyguard" in md
    assert "-2.00 ms (ESTIMATED)" in md


def test_report_flags_adaptive_scale_and_missing_gpu(tmp_path):
    s = tmp_path / "s"
    d = make_run(s, "baseline", "G3-A", 1, 32.0)
    text = (d / "frametimes.csv").read_text(encoding="utf-8").splitlines()
    text[-1] = text[-1].replace(",0.75,", ",0.7,")
    (d / "frametimes.csv").write_text("\n".join(text) + "\n", encoding="utf-8")
    make_run(s, "msaa-1", "G3-A", 1, 32.0, gpu_zero=True)
    gpuab.report(s)
    md = (s / "REPORT.md").read_text(encoding="utf-8")
    assert "skala renderu zmieniała się" in md and "brak próbek GPU" in md


def test_cli(session, capsys):
    assert gpuab.main(["report", str(session)]) == 0
    assert gpuab.main(["catalog", "--sources", str(REPO / "game" / "Assets" / "_Project")]) == 0
    assert "baseline" in capsys.readouterr().out
    assert gpuab.main(["report", str(session / "nope")]) == 2
