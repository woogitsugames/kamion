"""ADR 0145 listening A/B: tyre slip layers before (squeal v1: 930 Hz synthesis, onset 0.8 on the worst wheel at any
speed > 1.5 m/s) and after (scrub from the trailer slip angle at low speed + squeal from combined slip at speed, REGEN-03
recordings), driven by physics-runner telemetry of the 40 t combination.

    uv run python tyre_scrub_ab.py            # needs artifacts/tyre-scrub/runner/*.csv (see tyre_slip_scan.py)

Timeline (28 s): tight turn R 12 m at 10 km/h (12 s) -> straight 80 km/h (4 s) -> curve R 30 m at 35 km/h (6 s) ->
wet curve, 0.5 brake without ABS from 58 km/h, wheels lock (6 s, the hard-squeal case).
Context layers in both versions: dry road roll (procedural, TyreGain) and an approximate engine bed (ElevenLabs grid
cell nearest the telemetry rpm, equal-power on/off by throttle, pitched to the rpm; not the full EngineAudio mix).
Outputs: artifacts/tyre-scrub/ab/tyre_{before,after}_{ext,cab}.ogg, tyre_ab_{ext,cab}.ogg (A then B), ab_spectrogram.png,
ab_layers_solo.ogg (each new loop 4 s: scrub rec ext/cab, squeal rec ext/cab, scrub synth, squeal synth v2, squeal v1).
"""
from __future__ import annotations

import csv
import math
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy import signal  # noqa: E402

import runtime_sim as rs  # noqa: E402
from dsp import FS, write_ogg  # noqa: E402
import tyre_slip_scan as ts  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "artifacts" / "tyre-scrub" / "runner"
OUT = ROOT / "artifacts" / "tyre-scrub" / "ab"
GEN = ROOT / "game" / "Assets" / "_Project" / "Audio" / "Generated" / "Clips" / "sfx"
ART_GEN = ROOT / "art-source" / "audio" / "generated" / "sfx"
EL = ROOT / "game" / "Assets" / "_Project" / "Audio" / "ElevenLabs" / "Clips"
SEGMENTS = [  # csv, t0, t1, label
    ("scrub_r12_10kmh@laden40.csv", 0.0, 12.0, "tight turn R12 10 km/h"),
    ("lane_change_80@laden40.csv", 0.0, 4.0, "straight 80 km/h"),
    ("scrub_r30_35kmh@laden40.csv", 20.0, 26.0, "curve R30 35 km/h"),
    ("jackknife_wet_curve_noabs@laden40.csv", 5.0, 11.0, "wet curve, brake 0.5 no ABS (lock)"),
]
HZ = 100  # telemetry rate (runner dt 0.01)
ROAD_VOL, CAB_ROAD_EL = 0.45, 1.35
OLD = dict(vol=0.55, cab=1.0)
NEW = dict(squeal=0.60, scrub=0.25, cab_squeal=1.0, cab_scrub=1.0)
SQUEALABLE = {"dry_asphalt": 1.0, "wet": 0.8}
SCRUBBABLE = {"dry_asphalt": 1.0, "wet": 0.7}


def git_old(path: str) -> np.ndarray:
    """A clip as committed on main before ADR 0145 (squeal v1)."""
    ptr = subprocess.run(["git", "show", f"main:{path}"], cwd=ROOT, capture_output=True, check=True).stdout
    data = subprocess.run(["git", "lfs", "smudge", path], cwd=ROOT, input=ptr, capture_output=True, check=True).stdout
    tmp = OUT / "_tmp_old.wav"
    tmp.write_bytes(data)
    x, _ = sf.read(tmp)
    tmp.unlink()
    return x


def clip(p: Path) -> np.ndarray:
    x, fs = sf.read(p)
    assert fs == FS
    return x


def telemetry() -> list[dict]:
    rows = []
    for f, t0, t1, label in SEGMENTS:
        surface = "wet" if "wet" in f else "dry_asphalt"
        for r in csv.DictReader((RUN / f).open(newline="")):
            t = float(r["t"])
            if t < t0 or t >= t1:
                continue
            names = [k[:-len("_alpha_deg")] for k in r if k.endswith("_alpha_deg")]
            s_all, a_trl = 0.0, 0.0
            for nm in names:
                if float(r[nm + "_contact"]) < 0.5 or float(r[nm + "_fz"]) <= 0:
                    continue
                a = math.radians(abs(float(r[nm + "_alpha_deg"])))
                s_all = max(s_all, ts.combined(abs(float(r[nm + "_slip"])), a))
                if nm.startswith("T_"):
                    a_trl = max(a_trl, a)
            rows.append({"v": abs(float(r["v_fwd"])), "slip": s_all, "alpha": a_trl, "rpm": float(r["rpm"]),
                         "thr": float(r["throttle_eff"]), "surface": surface, "label": label})
    return rows


def step(cur: float, tgt: float, dt: float, up: float, down: float) -> float:
    tau = up if tgt > cur else down
    return cur + (tgt - cur) * (1 - math.exp(-dt / tau))


def render(rows: list[dict], version: str, persp: str, clips: dict) -> tuple[np.ndarray, np.ndarray]:
    n = int(FS / HZ)
    road = rs.LoopVoice(clips["road_" + persp])
    eng = {k: rs.LoopVoice(v) for k, v in clips["engine_" + persp].items()}
    if version == "before":
        sq = rs.LoopVoice(clips["squeal_v1_" + persp])
    else:
        sq = rs.LoopVoice(clips["squeal_" + persp])
        sc = rs.LoopVoice(clips["scrub_" + persp])
    g_sq = g_sc = 0.0
    out, gains = [], []
    dt = 1.0 / HZ
    for r in rows:
        v = r["v"]
        y = road.render(n, 0.75 + 0.6 * min(v / 25, 1), ROAD_VOL * (min(v / 25, 1) ** 1.6) * (CAB_ROAD_EL if persp == "cab" else 1.0), FS)
        # engine bed: nearest grid rpm, pitched, equal-power load blend (approximation)
        rpm = max(r["rpm"], 550.0)
        cell = min(clips["engine_rpms"], key=lambda c: abs(c - rpm))
        a = min(max(r["thr"], 0.1), 1.0) * math.pi / 2
        for (c, layer), voice in eng.items():
            w = (math.cos(a) if layer == "off" else math.sin(a)) if c == cell else 0.0
            y = y + voice.render(n, rpm / c, w * (0.7 if persp == "cab" else 1.0), FS)
        if version == "before":
            g_sq = step(g_sq, ts.squeal_gain_v1(r["slip"], v) * SQUEALABLE[r["surface"]], dt, 0.05, 0.15)
            y = y + sq.render(n, 0.9 + 0.3 * min(max(r["slip"] - 0.8, 0.0), 1.0), OLD["vol"] * g_sq, FS)
            gains.append((g_sq, 0.0))
        else:
            g_sq = step(g_sq, ts.squeal_gain_v2(r["slip"], v) * SQUEALABLE[r["surface"]], dt, 0.05, 0.15)
            g_sc = step(g_sc, ts.scrub_gain(math.degrees(r["alpha"]), v) * SCRUBBABLE[r["surface"]], dt, 0.12, 0.25)
            y = y + sq.render(n, 0.9 + 0.25 * min(max(r["slip"] - 1.3, 0.0), 1.0), NEW["squeal"] * g_sq, FS)
            pitch = 0.85 + 0.3 * min(v * math.sin(r["alpha"]) / 1.0, 1.0)
            y = y + sc.render(n, pitch, NEW["scrub"] * g_sc, FS)
            gains.append((g_sq, g_sc))
        out.append(y)
    return np.concatenate(out), np.array(gains)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    clips = {
        "road_ext": clip(GEN / "road_roll_loop.wav"), "road_cab": clip(GEN / "road_roll_cab_loop.wav"),
        "squeal_v1_ext": git_old("game/Assets/_Project/Audio/Generated/Clips/sfx/tyre_squeal_loop.wav"),
        "squeal_v1_cab": git_old("game/Assets/_Project/Audio/Generated/Clips/sfx/tyre_squeal_cab_loop.wav"),
        "squeal_ext": clip(EL / "sfx" / "el_tyre_squeal_loop.wav"), "squeal_cab": clip(EL / "sfx" / "el_tyre_squeal_cab_loop.wav"),
        "scrub_ext": clip(EL / "sfx" / "el_tyre_scrub_loop.wav"), "scrub_cab": clip(EL / "sfx" / "el_tyre_scrub_cab_loop.wav"),
        "engine_rpms": [600, 900, 1200, 1500],
    }
    for p in ("ext", "cab"):
        clips["engine_" + p] = {(c, layer): clip(EL / "engine" / p / f"el_engine_{p}_{layer}_{c:04d}.wav")
                                for c in clips["engine_rpms"] for layer in ("off", "on")}
    rows = telemetry()
    res = {}
    for persp in ("ext", "cab"):
        a, ga = render(rows, "before", persp, clips)
        b, gb = render(rows, "after", persp, clips)
        pk = max(np.abs(a).max(), np.abs(b).max())
        a, b = a * (0.89 / pk), b * (0.89 / pk)       # one common gain: A and B keep their level difference
        write_ogg(OUT / f"tyre_before_{persp}.ogg", a)
        write_ogg(OUT / f"tyre_after_{persp}.ogg", b)
        gap = np.zeros(int(1.0 * FS))
        write_ogg(OUT / f"tyre_ab_{persp}.ogg", np.concatenate([a, gap, b]))
        res[persp] = (a, b, ga, gb)
    # solo loops (4 s each, 0.3 s gaps): what each new clip sounds like on its own
    solo = []
    for x in (clips["scrub_ext"], clips["scrub_cab"], clips["squeal_ext"], clips["squeal_cab"],
              clip(ART_GEN / "tyre_scrub_loop.wav"), clip(ART_GEN / "tyre_squeal_loop.wav"), clips["squeal_v1_ext"]):
        y = np.tile(x, 2)[: 4 * FS]
        y = y / (np.abs(y).max() + 1e-9) * 0.7
        y[: 480] *= np.linspace(0, 1, 480)
        y[-480:] *= np.linspace(1, 0, 480)
        solo += [y, np.zeros(int(0.3 * FS))]
    write_ogg(OUT / "ab_layers_solo.ogg", np.concatenate(solo))
    # spectrogram + gains
    a, b, ga, gb = res["ext"]
    fig, axs = plt.subplots(4, 1, figsize=(14, 11), sharex=True)
    for ax, x, title in ((axs[0], a, "BEFORE (ext): squeal v1 930 Hz synthesis, old mapping"),
                         (axs[1], b, "AFTER (ext): REGEN-03 scrub + squeal, ADR 0145 mapping")):
        f, t, S = signal.spectrogram(x, FS, nperseg=2048, noverlap=1536)
        ax.pcolormesh(t, f / 1000, 10 * np.log10(S + 1e-14), vmin=-120, vmax=-40, shading="auto", cmap="magma")
        ax.set_ylim(0, 6)
        ax.set_ylabel("kHz")
        ax.set_title(title, fontsize=9)
    tt = np.arange(len(rows)) / HZ
    axs[2].plot(tt, ga[:, 0], label="squeal before")
    axs[2].plot(tt, gb[:, 0], label="squeal after")
    axs[2].plot(tt, gb[:, 1], label="scrub after")
    axs[2].legend(fontsize=8)
    axs[2].set_ylabel("gain")
    axs[3].plot(tt, [r["v"] * 3.6 for r in rows], label="speed km/h")
    axs[3].plot(tt, [math.degrees(r["alpha"]) for r in rows], label="trailer max slip angle deg")
    axs[3].plot(tt, [10 * r["slip"] for r in rows], label="10 x worst combined slip (norm.)")
    axs[3].legend(fontsize=8)
    t0 = 0.0
    for f_, s0, s1, label in SEGMENTS:
        for ax in axs:
            ax.axvline(t0, color="cyan", lw=0.6)
        axs[0].text(t0 + 0.1, 5.5, label, color="w", fontsize=7)
        t0 += s1 - s0
    axs[3].set_xlabel("s")
    fig.tight_layout()
    fig.savefig(OUT / "ab_spectrogram.png", dpi=70)
    plt.close(fig)
    # level summary per segment (dB RMS, after vs before)
    lines = []
    t0 = 0.0
    for f_, s0, s1, label in SEGMENTS:
        i0, i1 = int(t0 * FS), int((t0 + s1 - s0) * FS)
        for persp in ("ext", "cab"):
            a, b, _, _ = res[persp]
            ra, rb = (20 * math.log10(np.sqrt(np.mean(z[i0:i1] ** 2)) + 1e-9) for z in (a, b))
            lines.append(f"{label:38s} {persp}: before {ra:6.1f} dBFS  after {rb:6.1f} dBFS")
        t0 += s1 - s0
    (OUT / "ab_levels.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
