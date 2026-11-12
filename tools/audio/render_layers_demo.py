"""Layer demo: (1) a 'tour' of every new layer solo, (2) a 46 s yard-to-downhill drive that exercises them together.

    uv run python render_layers_demo.py

The drive is rendered through the runtime mirror (runtime_sim.py + render_demo.Controller for the engine/turbo) and a
Python port of the layer logic in TruckAudioController.cs / LayerMath.cs (same constants). Telemetry is scripted, not the
physics model: yard idle (parking-brake release, compressor, governor purge) -> pull away on asphalt -> concrete -> cobbles
-> gravel -> wet asphalt -> hard corner (squeal) -> downhill with engine brake + retarder -> service-brake stop.

Outputs
  art-source/audio/generated/demo/layers_tour_{ext,cab}.wav, layers_drive_{ext,cab}.wav   (gitignored, for the owner's ears)
  art-source/audio/demo/layers_tour_{ext,cab}.ogg, layers_drive_{ext,cab}.ogg              (small, committed)
  docs/reports/audio/layers_drive_{ext,cab}_spectrogram.png, layers_demo_analysis.json
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

import render_demo as rd  # noqa: E402
import runtime_sim as rs  # noqa: E402
from dsp import FS, save_png_small, write_ogg  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "art-source" / "audio" / "generated" / "demo"
DEMO = ROOT / "art-source" / "audio" / "demo"
REP = ROOT / "docs" / "reports" / "audio"
DUR = 46.0
FRAME = int(FS / rs.FRAME_HZ)

# ---- constants mirrored from LayerMath.cs / TruckAudioController.cs ----
SURF_LEVEL = [1.00, 1.15, 1.00, 1.35, 1.20, 0.80]
SURF_EXP = [1.6, 1.5, 1.6, 1.1, 1.2, 1.2]
SURF_SQUEAL = [1.0, 0.8, 1.0, 0.5, 0.0, 0.0]
TYRE = ["road_roll", "tyre_wet", "tyre_concrete", "tyre_cobbles", "tyre_gravel", "tyre_grass"]
VOL = dict(road=0.45, wind=0.30, squeal=0.55, retarder=0.50, compressor=0.35, relay=0.55, pneu=0.55,
           ambient_bed=0.30, forklift=0.16, bird=0.35)
CAB = dict(road=0.55, wind=0.35, squeal=1.0, retarder=0.85, compressor=0.75, pneu=0.6, ambient_bed=0.5,
           forklift=0.7, bird=0.4, relay_ext=0.25)


def lm_squeal(s, v):
    if v < 1.5:
        return 0.0
    g = min(max((s - 0.8) / 0.6, 0.0), 1.0)
    g = g * g * (3 - 2 * g)
    return g * min(max((v - 1.5) / 2.5, 0.0), 1.0)


def step(cur, tgt, dt, up, down):
    tau = up if tgt > cur else down
    return cur + (tgt - cur) * (1 - math.exp(-dt / max(tau, 1e-4)))


# --------------------------------------------------------------------------- scenario
SPEED = [(0, 0), (4.0, 0), (6, 9), (9, 22), (11, 34), (13.5, 38), (16, 38), (18, 22), (24, 24), (26, 19), (28, 20),
         (31, 38), (34, 48), (36, 50), (43, 46), (45.2, 0), (46, 0)]
SURFACE = [(0, 0), (12.0, 2), (18.0, 3), (24.0, 4), (28.0, 1), (34.0, 0)]  # (t, SurfaceKind)
SLIP = [(0, 0.0), (8.6, 0.0), (9.0, 1.45), (10.2, 1.45), (10.6, 0.0), (30.8, 0.0), (31.3, 1.2), (32.3, 1.2), (32.8, 0.0)]
RETARDER = [(0, 0.0), (36.0, 0.0), (36.6, 0.7), (39.0, 1.0), (42.6, 1.0), (43.0, 0.0)]
BRAKE = [(0, 0.0), (43.3, 0.0), (43.6, 0.6), (45.1, 0.6), (45.2, 0.0)]
COMPRESSOR = [(0, 0.0), (0.8, 1.0), (3.6, 0.0), (21.0, 0.0), (21.3, 1.0), (24.3, 0.0), (39.5, 0.0), (39.7, 1.0), (41.8, 0.0)]
GEARS = [(0, 150.0), (10.0, 87.0), (18.0, 56.0), (28.0, 40.0), (40.0, 30.0), (55.0, 21.0)]  # (upshift km/h, rpm per km/h)
EVENTS = [(2.2, "park_release"), (45.4, "park_set")]
BIRDS = [(0.6, "bird_tit", -0.6), (5.2, "bird_sparrow", 0.7), (13.0, "bird_crow_caw", -0.3)]  # fade out with speed anyway
INDICATOR = (7.5, 12.2)


def seg(t, pts):
    return rd._seg(t, pts)


def step_seg(t, pts):  # piecewise constant
    v = pts[0][1]
    for tt, val in pts:
        if t >= tt:
            v = val
    return v


def gear_at(v_kmh):
    g = 0
    for i, (vmin, _) in enumerate(GEARS):
        if v_kmh >= vmin:
            g = i
    return g


class Layers:
    def __init__(self, manifest, persp):
        self.p = persp
        cab = persp == "cab"
        sfx = lambda n: rs.load_sfx(manifest, n)  # noqa: E731
        nm = lambda base: base.replace("_loop", "_cab_loop") if cab else base  # noqa: E731
        self.tyre = [rs.LoopVoice(sfx(nm(f"{b}_loop"))) for b in TYRE]
        self.wind = rs.LoopVoice(sfx(nm("wind_loop")))
        self.squeal = rs.LoopVoice(sfx(nm("tyre_squeal_loop")))
        self.retarder = rs.LoopVoice(sfx(nm("retarder_loop")))
        self.compressor = rs.LoopVoice(sfx(nm("compressor_loop")))
        self.bed = rs.LoopVoice(sfx(nm("ambient_bed_loop")))
        self.fork = rs.LoopVoice(sfx(nm("forklift_loop")))
        sfxs = lambda n, cn=None: sfx((cn or n + "_cab") if cab else n)  # noqa: E731
        self.one = {"park_release": sfxs("parking_brake_release"), "park_set": sfxs("parking_brake_set"),
                    "purge": sfxs("air_dryer_purge"), "purge_b": sfxs("air_dryer_purge_b"),
                    "tick": sfxs("indicator_tick"), "tock": sfxs("indicator_tock"),
                    "bird_crow_caw": sfxs("bird_crow_caw"), "air_brake": sfxs("air_brake_release")}
        if not cab:
            self.one["bird_sparrow"] = sfx("bird_sparrow")
            self.one["bird_tit"] = sfx("bird_tit")
        self.w = [0.0] * 6
        self.w[0] = 1.0
        self.sq = self.rt = self.cp = 0.0
        self.pending: list[tuple[int, str, float, float]] = []  # (sample, name, gain, pan unused for mono)
        self.purge_alt = False
        self.prev_comp = False
        self.relay_phase = None
        self.relay_last = 0
        self.alpha = 0.0

    def frame(self, t, dt, i0, tel):
        cab = self.p == "cab"
        v = tel["speed"] / 3.6
        surf = int(step_seg(t, SURFACE))
        k = 1 - math.exp(-dt / 0.15)
        for i in range(6):
            self.w[i] += ((1.0 if i == surf else 0.0) - self.w[i]) * k
        vn = min(v / 25.0, 1.0)
        pitch = 0.75 + 0.6 * vn
        self.tyre_params = []
        sq_ok = 0.0
        for i in range(6):
            g = VOL["road"] * SURF_LEVEL[i] * vn ** SURF_EXP[i] * self.w[i] * (CAB["road"] if cab else 1.0)
            self.tyre_params.append((pitch, g))
            sq_ok += self.w[i] * SURF_SQUEAL[i]
        slip = seg(t, SLIP)
        self.sq = step(self.sq, lm_squeal(slip, v) * sq_ok, dt, 0.05, 0.15)
        self.sq_pitch = 0.9 + 0.3 * min(max(slip - 0.8, 0.0), 1.0)
        self.wind_g = VOL["wind"] * (CAB["wind"] if cab else 1.0) * vn ** 2.2
        rt = seg(t, RETARDER)
        self.rt = step(self.rt, VOL["retarder"] * max(rt, 0.0) ** 0.9, dt, 0.08, 0.25)
        comp = step_seg(t, COMPRESSOR) > 0.5
        self.cp = step(self.cp, VOL["compressor"] if comp else 0.0, dt, 0.15, 0.12)
        if self.prev_comp and not comp:
            self.purge_alt = not self.purge_alt
            name = "purge_b" if self.purge_alt else "purge"
            self.pending.append((i0, name, VOL["pneu"] * (CAB["pneu"] if cab else 1.0) * (0.9 if self.purge_alt else 0.8), 0))
        self.prev_comp = comp
        self.rpm = tel["rpm"]
        self.rt_pitch = 0.5 + 1.0 * min(v / 22.0, 1.0)
        masked = 1 - 0.55 * min(v / 20.0, 1.0)
        self.bed_g = VOL["ambient_bed"] * masked * (CAB["ambient_bed"] if cab else 1.0)
        swell = 0.55 + 0.45 * math.sin(t * 0.11 * 0.7 + 1.3)
        self.fork_g = VOL["forklift"] * swell * masked * (CAB["forklift"] if cab else 1.0)
        # flasher relay: 90/min, tick at contact close, tock half a period later
        if INDICATOR[0] <= t < INDICATOR[1]:
            if self.relay_phase is None:
                self.relay_phase, self.relay_last = 0.0, 1
                self.pending.append((i0, "tick", self._relay_gain(cab), 0))
            else:
                self.relay_phase = (self.relay_phase + dt) % 0.667
                want = 1 if self.relay_phase < 0.3335 else 2
                if want != self.relay_last:
                    self.relay_last = want
                    self.pending.append((i0, "tick" if want == 1 else "tock", self._relay_gain(cab), 0))
        else:
            self.relay_phase = None

    @staticmethod
    def _relay_gain(cab):
        return VOL["relay"] * (1.0 if cab else CAB["relay_ext"])

    def render(self, n):
        y = np.zeros(n)
        for i in range(6):
            p, g = self.tyre_params[i]
            if g > 1e-5:
                y += self.tyre[i].render(n, p, g, FS)
            else:
                self.tyre[i].render(0, p, 0.0, FS)
        y += self.wind.render(n, 1.0, self.wind_g, FS)
        y += self.squeal.render(n, self.sq_pitch, VOL["squeal"] * self.sq * (CAB["squeal"] if self.p == "cab" else 1.0), FS)
        y += self.retarder.render(n, self.rt_pitch, self.rt * (CAB["retarder"] if self.p == "cab" else 1.0), FS)
        y += self.compressor.render(n, min(max(self.rpm / 1000.0, 0.5), 1.8), self.cp * (CAB["compressor"] if self.p == "cab" else 1.0), FS)
        y += self.bed.render(n, 1.0, self.bed_g, FS)
        y += self.fork.render(n, 1.0, self.fork_g, FS)
        return y


def telemetry(t):
    v = seg(t, SPEED)
    g = gear_at(v)
    rpm = max(650.0, v * GEARS[g][1])
    accel = (seg(t + 0.3, SPEED) - seg(t - 0.3, SPEED)) / 0.6 / 3.6
    retarding = seg(t, RETARDER) > 0.05
    load = float(np.clip(0.35 + 0.25 * accel, 0.1, 1.0)) if v > 1 else 0.12
    if retarding or accel < -0.8:
        load = 0.0
    if 4.0 < t < 5.0:
        load = 0.85
    thr = 0.0 if load < 0.05 else min(1.0, load * 1.1)
    eb = 1.0 if (retarding or accel < -0.8) else 0.0
    return {"rpm": rpm, "load": load, "throttle": thr, "ebrake": eb, "speed": v, "gear": g}


def render_drive(persp, manifest):
    eng = rd.Controller(manifest, persp)
    eng.mix = dict(eng.mix, road=0.0, wind=0.0, air_brake=0.0)  # layers below own those
    eng.oneshots["air_brake"] = np.zeros(10)
    lay = Layers(manifest, persp)
    turbo = rd.TurboModel()
    n_total = int(DUR * FS)
    out = np.zeros(n_total + 3 * FS)
    dt = FRAME / FS
    ev = list(EVENTS)
    birds = list(BIRDS)
    prev_gear = 0
    prev_brake = 0.0
    tel_log = []
    for i0 in range(0, n_total, FRAME):
        t = i0 / FS
        x = telemetry(t)
        x["boost"] = turbo.step(x["rpm"], x["load"], dt)
        if x["gear"] > prev_gear:
            eng.pending.append((i0, "shift_air", eng.mix["shift_air"]))
        prev_gear = x["gear"]
        brake = seg(t, BRAKE)
        if prev_brake > 0.08 and brake <= 0.08:
            lay.pending.append((i0, "air_brake", VOL["pneu"] * (CAB["pneu"] if persp == "cab" else 1.0) * 0.8, 0))
        prev_brake = brake
        while ev and ev[0][0] <= t:
            _, name = ev.pop(0)
            g = VOL["pneu"] * (CAB["pneu"] if persp == "cab" else 1.0)
            lay.pending.append((i0, name, g * (0.8 if name == "park_release" else 1.0), 0))
        while birds and birds[0][0] <= t:
            _, name, _ = birds.pop(0)
            v = x["speed"] / 3.6
            vol = VOL["bird"] * max(0.0, 1 - v / 10.0) * (CAB["bird"] if persp == "cab" else 1.0)
            if name in lay.one and vol > 0.02:
                lay.pending.append((i0, name, vol, 0))
        eng.frame(x, dt, i0)
        lay.frame(t, dt, i0, x)
        out[i0:i0 + FRAME] += eng.render(FRAME) + lay.render(FRAME)
        tel_log.append((t, x["rpm"], x["speed"], lay.sq, lay.rt, lay.cp))
    for i0, name, g in eng.pending:
        clip = eng.oneshots[name]
        out[i0:i0 + len(clip)] += g * clip[: len(out) - i0]
    for i0, name, g, _ in lay.pending:
        clip = lay.one[name]
        out[i0:i0 + len(clip)] += g * clip[: len(out) - i0]
    out = out[:n_total]
    fi, fo = int(0.3 * FS), int(0.8 * FS)
    out[:fi] *= np.linspace(0, 1, fi)
    out[-fo:] *= np.linspace(1, 0, fo)
    return out, np.array(tel_log), len(lay.pending)


# --------------------------------------------------------------------------- tour
TOUR = [  # (name, label, loop?, repeat seconds)
    ("road_roll", "tyres: dry asphalt", True), ("tyre_wet", "tyres: wet asphalt", True), ("tyre_concrete", "tyres: concrete slabs", True),
    ("tyre_cobbles", "tyres: cobbles", True), ("tyre_gravel", "tyres: gravel", True), ("tyre_grass", "tyres: grass", True),
    ("tyre_squeal", "tyre squeal", True), ("retarder", "retarder", True), ("compressor", "air compressor", True),
    ("parking_brake_release", "parking brake release", False), ("air_dryer_purge_b", "air dryer psst", False),
    ("indicator_tick", "relay tick", False), ("indicator_tock", "relay tock", False),
    ("ambient_bed", "yard ambience bed", True), ("forklift", "forklift", True),
    ("bird_sparrow", "sparrow", False), ("bird_tit", "tit", False), ("bird_crow_caw", "crow", False),
]


def render_tour(persp, manifest):
    cab = persp == "cab"
    parts, marks = [], []
    t = 0.0
    gap = np.zeros(int(0.6 * FS))
    for name, label, loop in TOUR:
        if loop:
            cname = name + "_cab_loop" if cab else name + "_loop"
            x = rs.load_sfx(manifest, cname)
            n = int(5.0 * FS)
            x = np.tile(x, int(math.ceil(n / len(x))))[:n]
            x = x * np.hanning(n) ** 0.2  # soft ends
        else:
            cname = name + "_cab" if cab else name
            if cab and name in ("bird_sparrow", "bird_tit"):
                continue
            x = rs.load_sfx(manifest, cname)
            if name.startswith("indicator"):
                x = np.concatenate([x, np.zeros(int(0.45 * FS))])
                x = np.tile(x, 3)
        if name == "indicator_tick":
            pass
        marks.append((t, label))
        parts += [x, gap]
        t += (len(x) + len(gap)) / FS
    return np.concatenate(parts), marks


def normalise(x, target_lufs=-18.0):
    lufs = rd.integrated_lufs(x)
    g = 10 ** ((target_lufs - lufs) / 20)
    pk = np.max(np.abs(x)) * g
    if pk > 10 ** (-1 / 20):
        g *= 10 ** (-1 / 20) / pk
    return x * g, lufs


def plot(x, tel, path, title):
    fig, axes = plt.subplots(3, 1, figsize=(13, 10), gridspec_kw={"height_ratios": [3, 3, 1.5]})
    f, t, S = signal.spectrogram(x, FS, nperseg=2048, noverlap=1536)
    S = 10 * np.log10(S + 1e-16)
    for ax, fmax in zip(axes[:2], (1500, 9000)):
        ax.pcolormesh(t, f, S, shading="auto", vmin=S.max() - 85, vmax=S.max(), cmap="magma")
        ax.set_ylim(0, fmax)
        ax.set_ylabel("Hz")
    axes[0].set_title(f"{title}: 0-1.5 kHz (engine orders, retarder blade-pass 340 Hz x pitch, compressor, hum)")
    axes[1].set_title("0-9 kHz (squeal harmonics ~0.9/1.8/2.7 kHz, hiss of pneumatics, wet spray, gravel grains, birds)")
    for tt, label in ((2.2, "park rel."), (3.6, "purge"), (7.5, "indicator on"), (9.0, "squeal"), (12, "concrete"), (18, "cobbles"),
                      (24, "gravel"), (28, "wet"), (31, "squeal"), (36.6, "retarder"), (43.6, "brake"), (45.4, "park set")):
        axes[1].axvline(tt, color="cyan", lw=0.5, alpha=0.6)
        axes[1].text(tt + 0.1, 8300, label, color="cyan", fontsize=7, rotation=90, va="top")
    ax = axes[2]
    ax.plot(tel[:, 0], tel[:, 2] / 60, label="speed/60 km/h")
    ax.plot(tel[:, 0], tel[:, 3], label="squeal gain")
    ax.plot(tel[:, 0], tel[:, 4] / 0.5, label="retarder gain/0.5")
    ax.plot(tel[:, 0], tel[:, 5] / 0.35, label="compressor gain/0.35")
    ax.set_xlim(0, DUR)
    ax.legend(fontsize=7, ncol=4, loc="upper left")
    ax.grid(alpha=0.3)
    ax.set_xlabel("s")
    fig.tight_layout()
    save_png_small(fig, path, dpi=72, colors=64)
    plt.close(fig)


def main():
    manifest = rs.load_manifest()
    GEN.mkdir(parents=True, exist_ok=True)
    DEMO.mkdir(parents=True, exist_ok=True)
    report = {}
    for persp in ("ext", "cab"):
        x, tel, n_ev = render_drive(persp, manifest)
        x, lufs0 = normalise(x)
        sf.write(GEN / f"layers_drive_{persp}.wav", x.astype(np.float32), FS, subtype="PCM_16")
        write_ogg(DEMO / f"layers_drive_{persp}.ogg", x, compression_level=1.0)
        plot(x, tel, REP / f"layers_drive_{persp}_spectrogram.png", f"layers_drive_{persp}")
        # clicks: largest sample step vs a typical level (a hard discontinuity would stand out >> 0.5)
        step_max = float(np.max(np.abs(np.diff(x))))
        report[f"layers_drive_{persp}"] = {"integrated_lufs_after_norm": rd.integrated_lufs(x), "peak_dbfs": float(20 * np.log10(np.max(np.abs(x)))),
                                           "max_sample_step": step_max, "one_shot_events": n_ev,
                                           "ogg_bytes": (DEMO / f"layers_drive_{persp}.ogg").stat().st_size}
        tx, marks = render_tour(persp, manifest)
        tx, _ = normalise(tx, -20.0)
        sf.write(GEN / f"layers_tour_{persp}.wav", tx.astype(np.float32), FS, subtype="PCM_16")
        write_ogg(DEMO / f"layers_tour_{persp}.ogg", tx, compression_level=1.0)
        report[f"layers_tour_{persp}"] = {"seconds": len(tx) / FS, "index": [(round(t, 1), lbl) for t, lbl in marks],
                                           "ogg_bytes": (DEMO / f"layers_tour_{persp}.ogg").stat().st_size}
    (REP / "layers_demo_analysis.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
