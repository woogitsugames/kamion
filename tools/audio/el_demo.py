"""Owner listening demo for ADR 0137: the same scripted drive through the runtime mirror with the ElevenLabs set and
with the procedural set (A/B), cab and exterior.

    uv run python el_demo.py

Scenario (37.5 s): silence -> engine start (start one-shot, loops gated in after 1.2 + 1.0 s like EngineAudio) -> idle ->
pull away under load with 3 upshifts (AMT torque cut + shift-cylinder air) -> cruise -> lift-off (wastegate) ->
engine brake -> back to idle -> engine stop. Telemetry is scripted (render_demo.py keyframes, shifted by 3 s), not
the physics model.

Outputs (artifacts/audio-el/demo/): el_{cab,ext}.mp3, synth_{cab,ext}.mp3 (-16 LUFS, peak <= -1 dBFS),
el_cab_spectrogram.png, el_ext_spectrogram.png, demo.json (LUFS, max voices, rpm-tracking error of the result).
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
from dsp import FS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EL_MAN = ROOT / "game" / "Assets" / "_Project" / "Audio" / "ElevenLabs" / "el_manifest.json"
OUT = ROOT / "artifacts" / "audio-el" / "demo"
DUR = 37.5
SHIFT = 3.0
START_T, STOP_T = 0.5, 35.0
START_DELAY, START_FADE = 1.2, 1.0  # EngineAudio.startLoopDelay / startLoopFade
FRAME = int(FS / rs.FRAME_HZ)
CLIP_ROOT = ROOT  # repo root the el_manifest file paths resolve against (el_ab.py points it at main for the A/B)


def telemetry(t: float) -> dict:
    if t < START_T:
        return {"rpm": 0.0, "load": 0.0, "throttle": 0.0, "ebrake": 0.0, "speed": 0.0}
    if t < SHIFT:
        x = rd.telemetry(0.0)
    elif t <= SHIFT + 30.0:
        x = rd.telemetry(t - SHIFT)
    else:  # after the original 30 s: engine brake off, coast down to idle, stop
        x = dict(rd.telemetry(30.0))
        u = min(1.0, (t - SHIFT - 30.0) / 1.5)
        x["rpm"] = 1380 + (600 - 1380) * (0.5 - 0.5 * math.cos(math.pi * u))
        x["load"], x["ebrake"], x["throttle"] = 0.08, 0.0, 0.0
        x["speed"] = max(0.0, 38.0 - 8.0 * (t - SHIFT - 30.0))
    if t >= STOP_T:
        x["rpm"] = max(0.0, 600.0 - 900.0 * (t - STOP_T))  # stall/key off: run-down, the stop clip carries it
        x["load"] = 0.0
    return x


def load_grid_el(man: dict, kind: str, persp: str, pool: int) -> rs.LayerGrid:
    sel = [c for c in man["clips"] if c["kind"] == kind and c["perspective"] == persp]
    rpms = sorted({c["rpm"] for c in sel})
    loads = sorted({c["load"] for c in sel}) if kind == "engine" else [0.0]
    clips = []
    for ld in loads:
        for r in rpms:
            c = next(c for c in sel if c["rpm"] == r and (kind != "engine" or c["load"] == ld))
            clips.append(rs.Clip(sf.read(CLIP_ROOT / c["file"])[0].astype(np.float64), c["rpm_exact"], c["cycles"]))
    return rs.LayerGrid([float(r) for r in rpms], loads, clips, pool=pool)


def el_sfx(man: dict, name: str) -> np.ndarray:
    s = next(s for s in man["sfx"] if s["name"] == name)
    return sf.read(CLIP_ROOT / s["file"])[0].astype(np.float64)


class Ctrl(rd.Controller):
    """render_demo.Controller + the EngineAudio start/stop gate, clatter and the ElevenLabs banks."""

    def __init__(self, synth_man, el_man, persp: str, use_el: bool):
        super().__init__(synth_man, persp)
        self.use_el = use_el
        self.gate, self.hold, self.running = 1.0, 0.0, False
        self.events = []
        if use_el:
            self.eng = load_grid_el(el_man, "engine", persp, 6)
            self.eb = load_grid_el(el_man, "ebrake", persp, 3)
            self.oneshots["liftoff"] = el_sfx(el_man, "el_turbo_wastegate" + ("_cab" if persp == "cab" else ""))
            self.start = el_sfx(el_man, f"el_engine_start_{persp}")
            self.stop = el_sfx(el_man, f"el_engine_stop_{persp}")
            self.clatter = rs.LoopVoice(el_sfx(el_man, "el_idle_clatter_loop" if persp == "ext" else "el_idle_clatter_cab_loop"))

    def frame(self, x, dt, i0):
        rpm = x["rpm"]
        if not self.running and rpm > 400:
            self.running = True
            if self.use_el:
                self.events.append((i0, self.start))
                self.hold, self.gate = START_DELAY + START_FADE, 0.0
        elif self.running and rpm < 250:
            self.running = False
            if self.use_el:
                self.events.append((i0, self.stop))
        if self.use_el:
            self.hold = max(0.0, self.hold - dt)
            tgt = 1.0 - min(1.0, self.hold / START_FADE) if self.running else 0.0
            self.gate = tgt if tgt >= self.gate else max(tgt, self.gate - dt / 0.2)
        if self.s is None:
            self.s = dict(x)
        run = min(1.0, max(0.0, (self.s["rpm"] - 80) / 300)) * self.gate
        saved = dict(self.mix)
        self.mix = dict(self.mix, engine=saved["engine"] * run, ebrake=saved["ebrake"] * run)
        rs.XFADE_COHERENCE = 0.0 if self.use_el else 0.9  # EngineAudio: incoherent bank -> equal power
        super().frame(x, dt, i0)
        self.mix = saved
        self.run = run

    def render(self, n):
        y = super().render(n)
        if self.use_el:
            r = self.s["rpm"]
            idle = 1 - np.clip((r - 700) / 600, 0, 1)
            idle = idle * idle * (3 - 2 * idle)
            y += self.clatter.render(n, min(2.0, max(0.7, r / 600)), 0.6 * self.run * idle * (0.75 + 0.25 * self.s["load"]), FS)
        return y


def render(synth_man, el_man, persp, use_el):
    c = Ctrl(synth_man, el_man, persp, use_el)
    turbo = rd.TurboModel()
    n_total = int(DUR * FS)
    out = np.zeros(n_total + 6 * FS)
    tel = []
    ev = [(e[0] + SHIFT, e[1]) for e in rd.EVENTS]
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
    for i0, clip in c.events:
        out[i0:i0 + len(clip)] += clip[: len(out) - i0]
    out = out[:n_total]
    fo = int(0.3 * FS)
    out[-fo:] *= np.linspace(1, 0, fo)
    return out, np.array(tel), c.max_voices


def finish(x):
    g = 10 ** ((-16.0 - rd.integrated_lufs(x)) / 20)
    pk = np.abs(x).max() * g
    if pk > 10 ** (-1 / 20):
        g *= 10 ** (-1 / 20) / pk
    return x * g


def spectro(x, tel, path, title):
    fig, ax = plt.subplots(2, 1, figsize=(12, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    f, t, S = signal.spectrogram(x, FS, nperseg=8192, noverlap=8192 - 1024)
    k = f <= 400
    ax[0].pcolormesh(t, f[k], 10 * np.log10(S[k] + 1e-20), shading="auto", cmap="magma", vmin=10 * np.log10(S[k].max()) - 70)
    ax[0].plot(tel[:, 0], tel[:, 1] / 20, color="cyan", lw=0.7, ls="--", label="rpm/20 (firing) from telemetry")
    ax[0].legend(loc="upper right", fontsize=7)
    ax[0].set_ylabel("Hz")
    ax[0].set_title(title, fontsize=9)
    env = np.sqrt(np.convolve(x ** 2, np.ones(4800) / 4800, "same"))
    ax[1].plot(np.arange(len(x)) / FS, 20 * np.log10(env + 1e-9), lw=0.6)
    ax[1].set_ylim(-60, 0)
    ax[1].set_ylabel("dBFS (100 ms)")
    ax[1].set_xlabel("s")
    fig.tight_layout()
    fig.savefig(path, dpi=70)
    plt.close(fig)


def write_mp3(path, x):
    try:
        sf.write(path, x.astype(np.float32), FS, format="MP3", subtype="MPEG_LAYER_III")
    except Exception:
        path = path.with_suffix(".ogg")
        sf.write(path, x.astype(np.float32), FS, format="OGG", subtype="VORBIS")
    return path


def main():
    synth_man = rs.load_manifest()
    el_man = json.loads(EL_MAN.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    rep = {}
    for use_el, tag in ((True, "el"), (False, "synth")):
        for persp in ("cab", "ext"):
            x, tel, mv = render(synth_man, el_man, persp, use_el)
            x = finish(x)
            p = write_mp3(OUT / f"{tag}_{persp}.mp3", x)
            sf.write(OUT / f"{tag}_{persp}.wav", x.astype(np.float32), FS, subtype="PCM_16")
            if use_el or persp == "cab":
                spectro(x, tel, OUT / f"{tag}_{persp}_spectrogram.png", f"{tag} {persp}: start, idle, 3 upshifts, engine brake, stop")
            rep[f"{tag}_{persp}"] = {"file": p.name, "lufs": rd.integrated_lufs(x), "peak_dbfs": float(20 * np.log10(np.abs(x).max())),
                                     "max_engine_voices": mv, "bytes": p.stat().st_size}
            print(tag, persp, rep[f"{tag}_{persp}"])
    (OUT / "demo.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
