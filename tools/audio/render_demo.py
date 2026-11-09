"""30 s "drive" demo rendered through the runtime mirror (runtime_sim.py), plus checks.

    uv run python render_demo.py

Scenario: idle -> parking-brake release -> pull away under load -> 3 upshifts (AMT torque
cut, shift-cylinder 'pft') -> cruise 1300 rpm -> lift-off (turbo sigh) -> downshift ->
engine brake decel. Telemetry is scripted (not the physics model) but follows the same
interface the game will feed: rpm, load, throttle, engineBrake, turboBoost, speed.

Outputs
  art-source/audio/demo/drive_demo.ogg           cab perspective (main camera)
  art-source/audio/demo/drive_demo_exterior.ogg  exterior perspective
  docs/reports/audio/demo_spectrogram.png        spectrogram with rpm/20 overlay
  docs/reports/audio/crossfade_sweep.png         slow rpm sweep: level vs loop levels
  docs/reports/audio/demo_analysis.json
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy import signal  # noqa: E402

import runtime_sim as rs  # noqa: E402
from dsp import FS, save_png_small, write_ogg  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "art-source" / "audio" / "demo"
REP = ROOT / "docs" / "reports" / "audio"
DUR = 30.0
FRAME = int(FS / rs.FRAME_HZ)  # 800 samples

# Mix constants (mirror EngineAudio.cs defaults). Linear gains.
MIX = {
    "cab": {"engine": 1.0, "ebrake": 0.85, "turbo": 0.045, "liftoff": 0.10, "road": 0.16, "wind": 0.10,
            "shift_air": 0.10, "air_brake": 0.22},
    "ext": {"engine": 1.0, "ebrake": 1.0, "turbo": 0.11, "liftoff": 0.30, "road": 0.22, "wind": 0.05,
            "shift_air": 0.22, "air_brake": 0.55},
}
TAU = {"rpm": 0.035, "load": 0.05, "ebrake": 0.08, "boost": 0.05}


# --------------------------------------------------------------------------- scenario
def _seg(t, pts):
    """Piecewise smooth (cosine) interpolation through (time, value) keyframes."""
    ts = [p[0] for p in pts]
    if t <= ts[0]:
        return pts[0][1]
    if t >= ts[-1]:
        return pts[-1][1]
    i = int(np.searchsorted(ts, t, side="right") - 1)
    (t0, v0), (t1, v1) = pts[i], pts[i + 1]
    u = (t - t0) / (t1 - t0)
    u = 0.5 - 0.5 * math.cos(math.pi * u)
    return v0 + (v1 - v0) * u


RPM_KEYS = [(0, 600), (3.5, 600), (4.0, 565), (4.6, 640), (8.8, 1550), (9.0, 1540), (9.45, 1100), (9.7, 1110),
            (13.6, 1550), (13.8, 1540), (14.25, 1120), (14.5, 1130), (18.8, 1500), (19.0, 1490), (19.45, 1150),
            (21.5, 1300), (25.0, 1300), (25.35, 1290), (25.75, 1760), (26.0, 1750), (29.2, 1420), (30, 1380)]
LOAD_KEYS = [(0, 0.12), (3.5, 0.12), (4.1, 0.75), (4.6, 0.95), (8.8, 0.95), (8.85, 0.0), (9.45, 0.0), (9.75, 0.95),
             (13.6, 0.95), (13.65, 0.0), (14.25, 0.0), (14.55, 0.9), (18.8, 0.9), (18.85, 0.0), (19.45, 0.0),
             (19.8, 0.7), (21.5, 0.40), (25.0, 0.38), (25.08, 0.0), (30, 0.0)]
THR_KEYS = [(0, 0.0), (3.5, 0.0), (4.1, 0.6), (4.6, 1.0), (8.8, 1.0), (8.85, 0.0), (9.45, 0.0), (9.75, 1.0),
            (13.6, 1.0), (13.65, 0.0), (14.25, 0.0), (14.55, 1.0), (18.8, 1.0), (18.85, 0.0), (19.45, 0.0),
            (19.8, 0.75), (21.5, 0.42), (25.0, 0.4), (25.05, 0.0), (30, 0.0)]
EB_KEYS = [(0, 0.0), (25.8, 0.0), (26.05, 1.0), (29.2, 1.0), (29.45, 0.0), (30, 0.0)]
SPEED_KEYS = [(0, 0.0), (3.8, 0.0), (8.8, 11.0), (9.5, 10.6), (13.6, 22.0), (14.3, 21.6), (18.8, 33.0),
              (19.5, 32.6), (21.5, 46.0), (25.0, 48.0), (26.0, 47.0), (30, 38.0)]  # km/h
EVENTS = [(2.8, "air_brake"), (9.0, "shift_air"), (13.8, "shift_air"), (19.0, "shift_air"), (25.45, "shift_air")]


def telemetry(t: float) -> dict:
    return {"rpm": _seg(t, RPM_KEYS), "load": _seg(t, LOAD_KEYS), "throttle": _seg(t, THR_KEYS),
            "ebrake": _seg(t, EB_KEYS), "speed": _seg(t, SPEED_KEYS)}


class TurboModel:
    """'Physics side' stand-in: boost (0..1) lags its target (spool-up slower than blow-down)."""

    def __init__(self):
        self.b = 0.0

    def step(self, rpm, load, dt):
        target = load * float(np.clip((rpm - 750.0) / 650.0, 0.1, 1.0))
        tau = 0.9 if target > self.b else 0.35
        self.b += (target - self.b) * (1 - math.exp(-dt / tau))
        return self.b


# --------------------------------------------------------------------------- controller (mirror of EngineAudio.cs)
class Controller:
    def __init__(self, manifest, perspective: str):
        self.p = perspective
        self.mix = MIX[perspective]
        self.eng = rs.load_grid(manifest, "engine", perspective, pool=6)
        self.eb = rs.load_grid(manifest, "ebrake", perspective, pool=3)
        self.turbo = rs.LoopVoice(rs.load_sfx(manifest, "turbo_whistle_loop"))
        self.road = rs.LoopVoice(rs.load_sfx(manifest, "road_roll_loop"))
        self.wind = rs.LoopVoice(rs.load_sfx(manifest, "wind_loop"))
        self.oneshots = {"liftoff": rs.load_sfx(manifest, "turbo_liftoff"),
                         "shift_air": rs.load_sfx(manifest, "gearshift_air"),
                         "air_brake": rs.load_sfx(manifest, "air_brake_release")}
        self.s = None
        self.thr_hold = 0.0
        self.liftoff_cool = 0.0
        self.pending: list[tuple[int, str, float]] = []
        self.max_voices = 0

    def frame(self, x: dict, dt: float, sample_index: int) -> None:
        if self.s is None:
            self.s = dict(x)
        for k in ("rpm", "load", "ebrake", "boost"):
            self.s[k] += (x[k] - self.s[k]) * (1 - math.exp(-dt / TAU[k]))
        self.s["throttle"], self.s["speed"] = x["throttle"], x["speed"]
        # turbo lift-off detector: throttle peak-hold vs current
        self.thr_hold = max(x["throttle"], self.thr_hold - 2.0 * dt)
        self.liftoff_cool = max(0.0, self.liftoff_cool - dt)
        if self.thr_hold - x["throttle"] > 0.5 and self.s["boost"] > 0.35 and self.liftoff_cool == 0.0:
            self.pending.append((sample_index, "liftoff", self.mix["liftoff"] * self.s["boost"]))
            self.liftoff_cool = 1.0
        self.eng.update(self.s["rpm"], self.s["load"], self.mix["engine"])
        self.eb.update(self.s["rpm"], 0.0, self.mix["ebrake"] * self.s["ebrake"])
        self.max_voices = max(self.max_voices, self.eng.active_voices() + self.eb.active_voices())

    def render(self, n: int) -> np.ndarray:
        s = self.s
        y = self.eng.render(n, FS) + self.eb.render(n, FS)
        b = s["boost"]
        y += self.turbo.render(n, 0.6 + 0.85 * b, self.mix["turbo"] * b ** 1.5 * (0.35 + 0.65 * s["throttle"]), FS)
        v = s["speed"] / 80.0
        y += self.road.render(n, 0.75 + 0.5 * min(v, 1.2), self.mix["road"] * min(v, 1.3) ** 1.6, FS)
        y += self.wind.render(n, 0.8 + 0.4 * min(v, 1.2), self.mix["wind"] * min(v, 1.3) ** 2.2, FS)
        return y


def integrated_lufs(x: np.ndarray) -> float:
    """ITU-R BS.1770-4 integrated loudness (mono, 48 kHz coefficients)."""
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x))
    blk, hop = int(0.4 * FS), int(0.1 * FS)
    ms = np.array([np.mean(y[i:i + blk] ** 2) for i in range(0, len(y) - blk, hop)])
    lk = -0.691 + 10 * np.log10(ms + 1e-20)
    g = ms[lk > -70]
    rel = -0.691 + 10 * np.log10(np.mean(g)) - 10
    g = ms[(lk > -70) & (lk > rel)]
    return float(-0.691 + 10 * np.log10(np.mean(g)))


def render(perspective: str, manifest) -> tuple[np.ndarray, dict]:
    c = Controller(manifest, perspective)
    turbo = TurboModel()
    n_total = int(DUR * FS)
    out = np.zeros(n_total + FS)
    tel = []
    ev = list(EVENTS)
    dt = FRAME / FS
    for i0 in range(0, n_total, FRAME):
        t = i0 / FS
        x = telemetry(t)
        x["boost"] = turbo.step(x["rpm"], x["load"], dt)
        while ev and ev[0][0] <= t:
            _, name = ev.pop(0)
            c.pending.append((i0, name, c.mix[name]))
        c.frame(x, dt, i0)
        out[i0:i0 + FRAME] += c.render(FRAME)
        tel.append((t, x["rpm"], x["load"], x["throttle"], x["ebrake"], x["boost"], x["speed"]))
    for i0, name, g in c.pending:
        clip = c.oneshots[name]
        out[i0:i0 + len(clip)] += g * clip[: len(out) - i0]
    out = out[:n_total]
    # gentle fade-in from silence (engine already running) and fade-out
    fi, fo = int(0.25 * FS), int(0.6 * FS)
    out[:fi] *= np.linspace(0, 1, fi)
    out[-fo:] *= np.linspace(1, 0, fo)
    return out, {"telemetry": np.array(tel), "max_engine_voices": c.max_voices}


def sweep_test(manifest) -> dict:
    """Slow 600->2100 rpm sweep at constant load through the runtime: level smoothness + clicks."""
    res = {}
    fig, ax = plt.subplots(1, 1, figsize=(10, 4))
    for load, col in ((1.0, "tab:red"), (0.4, "tab:blue"), (0.0, "tab:green")):
        g = rs.load_grid(manifest, "engine", "ext", pool=6)
        dur = 24.0
        n = int(dur * FS)
        y = np.zeros(n)
        rpm_t = []
        for i0 in range(0, n, FRAME):
            rpm = 600 + 1500 * (i0 / n)
            g.update(rpm, load, 1.0)
            y[i0:i0 + FRAME] = g.render(FRAME, FS)[: len(y[i0:i0 + FRAME])]
            rpm_t.append(rpm)
        win = int(0.25 * FS)
        lev = np.array([10 * np.log10(np.mean(y[i:i + win] ** 2) + 1e-20) for i in range(0, n - win, win // 2)])
        rpm_l = 600 + 1500 * (np.arange(0, n - win, win // 2) + win / 2) / n
        layer = {0.0: "off", 0.4: "mid", 1.0: "on"}[load]
        pts = sorted((c["rpm"], c["rms_dbfs"]) for c in manifest["clips"]
                     if c["kind"] == "engine" and c["perspective"] == "ext" and c["layer"] == layer)
        expect = np.interp(rpm_l, [p[0] for p in pts], [p[1] for p in pts])
        dev = lev - expect
        # click check: largest sample-to-sample step vs the largest step inside the source loops
        src_max_step = max(np.max(np.abs(np.diff(cl.data))) for cl in g.clips[g.loads.index(load) * len(g.rpms):
                                                                                (g.loads.index(load) + 1) * len(g.rpms)])
        step_ratio = float(np.max(np.abs(np.diff(y))) / src_max_step)
        res[layer] = {"max_abs_level_dev_db": float(np.max(np.abs(dev[2:-2]))),
                      "mean_level_dev_db": float(np.mean(dev[2:-2])), "max_step_vs_source": step_ratio}
        ax.plot(rpm_l, lev, color=col, lw=1, label=f"runtime sweep, {layer}")
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "o", color=col, ms=3, label=f"loop RMS, {layer}")
    ax.set_xlabel("rpm")
    ax.set_ylabel("dBFS (250 ms RMS)")
    ax.set_title("Crossfade sweep 600→2100 rpm (ext bank, runtime mirror) vs individual loop levels")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, ncol=3)
    fig.tight_layout()
    save_png_small(fig, REP / "crossfade_sweep.png", dpi=80)
    plt.close(fig)
    return res


def plot_demo(x: np.ndarray, tel: np.ndarray, path: Path, title: str) -> dict:
    fig, axes = plt.subplots(3, 1, figsize=(13, 10), gridspec_kw={"height_ratios": [3, 3, 1.3]})
    f, t, S = signal.spectrogram(x, FS, nperseg=8192, noverlap=8192 - 1024, window="hann")
    SdB = 10 * np.log10(S + 1e-16)
    ax = axes[0]
    ax.pcolormesh(t, f, SdB, shading="auto", vmin=SdB.max() - 75, vmax=SdB.max(), cmap="magma")
    for h, ls in ((1, "-"), (2, "--"), (3, ":")):
        ax.plot(tel[:, 0], tel[:, 1] / 20.0 * h, color="cyan", lw=0.8, ls=ls, alpha=0.8,
                label=f"{h}× rpm/20" if h else None)
    ax.set_ylim(0, 400)
    ax.set_ylabel("Hz")
    ax.legend(loc="upper left", fontsize=8)
    ax.set_title(f"{title}: 0–400 Hz, cyan = expected firing harmonics from telemetry rpm")
    f2, t2, S2 = signal.spectrogram(x, FS, nperseg=1024, noverlap=768)
    S2dB = 10 * np.log10(S2 + 1e-16)
    axes[1].pcolormesh(t2, f2, S2dB, shading="auto", vmin=S2dB.max() - 80, vmax=S2dB.max(), cmap="magma")
    axes[1].set_ylim(0, 10000)
    axes[1].set_ylabel("Hz")
    axes[1].set_title("0–10 kHz (turbo whistle, clatter, pneumatics, road)")
    ax = axes[2]
    ax.plot(tel[:, 0], tel[:, 1] / 2100, label="rpm/2100")
    ax.plot(tel[:, 0], tel[:, 2], label="load")
    ax.plot(tel[:, 0], tel[:, 4], label="engine brake")
    ax.plot(tel[:, 0], tel[:, 5], label="boost")
    ax.set_xlim(0, DUR)
    ax.set_xlabel("s")
    ax.legend(fontsize=7, ncol=4, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    save_png_small(fig, path, dpi=72, colors=64)
    plt.close(fig)
    # firing-frequency tracking: peak of the smoothed spectrum near expected f_fire
    errs = []
    for j, tj in enumerate(t):
        rpm = np.interp(tj, tel[:, 0], tel[:, 1])
        ff = rpm / 20.0
        m = (f > 0.8 * ff) & (f < 1.2 * ff)
        idx = np.flatnonzero(m)
        k = idx[np.argmax(S[m, j])]
        # parabolic interpolation on log magnitude for sub-bin peak frequency
        a, b, c = np.log(S[k - 1:k + 2, j] + 1e-20)
        delta = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0
        fpk = f[k] + delta * (f[1] - f[0])
        errs.append(100 * (fpk - ff) / ff)
    errs = np.abs(np.array(errs))
    return {"firing_track_median_abs_err_pct": float(np.median(errs)),
            "firing_track_p90_abs_err_pct": float(np.percentile(errs, 90)),
            "freq_resolution_hz": float(FS / 8192)}


def main() -> None:
    manifest = rs.load_manifest()
    DEMO.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    report = {}
    for p, fname in (("cab", "drive_demo"), ("ext", "drive_demo_exterior")):
        x, info = render(p, manifest)
        lufs = integrated_lufs(x)
        gain = 10 ** ((-16.0 - lufs) / 20)
        peak = np.max(np.abs(x)) * gain
        if peak > 10 ** (-1 / 20):
            gain *= 10 ** (-1 / 20) / peak
        x *= gain
        final_lufs = integrated_lufs(x)
        ogg = DEMO / f"{fname}.ogg"
        write_ogg(ogg, x, compression_level=0.6 if p == "cab" else 1.0)  # keep each <= 300 KB
        track = plot_demo(x, info["telemetry"], REP / f"{fname}_spectrogram.png", fname)
        report[fname] = {"perspective": p, "integrated_lufs": final_lufs, "peak_dbfs": float(20 * np.log10(np.max(np.abs(x)))),
                         "ogg_bytes": ogg.stat().st_size, "max_engine_voices": info["max_engine_voices"], **track}
        if p == "cab":  # same scripted telemetry for both perspectives; 10 Hz is enough to read
            np.savetxt(DEMO / "drive_demo_telemetry.csv", info["telemetry"][::6], delimiter=",", fmt="%.3f",
                       header="t_s,rpm,load,throttle,engine_brake,boost,speed_kmh", comments="")
    report["crossfade_sweep_ext"] = sweep_test(manifest)
    (REP / "demo_analysis.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
