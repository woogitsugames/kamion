"""Prepare the ElevenLabs effects of sections B-G (gearbox, pneumatics, tyres, cab, ambience) as game layers (ADR 0142).

    uv run python el_fx.py [--src <dir>]

Input : the owner's raw files (<src>/<ID> (n).wav, 48 kHz stereo; default main repo art-source/audio/elevenlabs, not in git)
        and the procedural reference set (main repo art-source/audio/generated/manifest.json) for loudness matching.
Output: game/Assets/_Project/Audio/ElevenLabs/Clips/sfx/el_*.wav (48 kHz mono 16-bit, git LFS), entries with
        "group": "fx" in game/Assets/_Project/Audio/ElevenLabs/el_manifest.json (replaced on every run; el_prepare.py keeps
        them), artifacts/audio-fx/fx.txt|fx.json (measurements) and artifacts/audio-fx/verify/fx_sheet.png (spectrograms).

Choices are authored below after reviewing artifacts/audio-el/analysis/sheets/*.png, artifacts/audio-regen01/analysis
and the probe numbers in the comments (onsets = 2-6 kHz envelope peaks, periods = envelope autocorrelation).
Processing per clip:
  one-shot: mono, 25 Hz high-pass, optional cut / extra high-pass / spectral gate, 3 ms fade-in, fade-out,
            loudness matched (BS.1770) to the procedural clip it replaces (so the mix constants of TruckAudioController
            keep their meaning) or to an authored LUFS (new sounds, WORKING_VALUE); peak <= -1.5 dBFS (gain reduced if a
            short transient would exceed it, reported).
  loop    : mono, 25 Hz high-pass (circular), seam = last 40 ms crossfaded equal-power into the first (el_prepare);
            loops with a period (beeper, horn) are cut to an integer number of periods with the seam in a gap / steady
            part; tyre loops are resampled periodically so that the runtime pitch LayerMath.TyrePitch(v) gives 1.0 at the
            recorded speed (procedural tyre loops: pitch 1 at 10.4 m/s).
  perspective: exterior recordings get a prerendered cabin clip (sfx_layers.cab_filter, same profiles as the synthesis,
            ADR 0017); cabin recordings are used as the cabin clip only (exterior keeps the procedural clip) unless marked
            "both" (sounds that are the same inside and outside the shell: relay, actuator, door).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy import signal  # noqa: E402

from el_analyze import MAIN, lufs, seam  # noqa: E402
from el_prepare import FS, OUT, ROOT, circular_hp, fade, mono, resample_periodic, seam_loop, soft_limit, synth_lufs, write  # noqa: E402
from el_regen01 import REGEN01, prompt_entry  # noqa: E402
import el_regen03  # noqa: E402
from sfx_layers import cab_filter  # noqa: E402
import turbo2  # noqa: E402

ART = ROOT / "artifacts" / "audio-fx"


def tyre_pitch(v: float) -> float:
    """Mirror of LayerMath.TyrePitch (C#)."""
    return 0.75 + 0.6 * min(max(v / 25.0, 0.0), 1.0)


# ---------------------------------------------------------------------------------------------------------------
# Authored choices. persp: "ext" -> + cabin clip with cab profile; "cab" -> cabin clip only; "both" -> one clip for both.
# target: float LUFS | "syn:<procedural clip name>" | "syn:<name>:<dB offset>".
FX: list[dict] = [
    # C. gearbox -------------------------------------------------------------------------------------------------
    # REGEN-01 GEAR_UPSHIFT_CAB (6) (ADR 0138: click 20.3 dB over the HF floor). The take carries the engine drone the
    # whole time, which would double the runtime engine: only the actuator click + clunk (HF peaks 0.52 / 0.60 s) is cut,
    # high-passed at 320 Hz and spectrally gated against the drone before the click (0.05-0.45 s).
    {"name": "el_gearshift_up", "src": "GEAR_UPSHIFT_CAB (6).wav", "kind": "oneshot", "persp": "both",
     "cut": (0.47, 1.05), "hp": 320.0, "gate": (0.05, 0.45), "fade_out": 0.25, "target": "syn:gearshift_air_cab"},
    # GEAR_DOWNSHIFT_CAB (3): clean transient at 0.454 s + 0.9 s pneumatic hiss, no engine (peak -5.8 dBFS, no clip).
    {"name": "el_gearshift_down", "src": "GEAR_DOWNSHIFT_CAB (3).wav", "kind": "oneshot", "persp": "both",
     "cut": (0.44, 1.30), "fade_out": 0.30, "target": "syn:gearshift_air_cab"},
    # GEARBOX_WHINE_LOOP (4): faint gear-mesh lines over a cab floor; seam 0.23, level drift 0.07 dB. New layer
    # (the procedural gear_whine_loop was never wired), only in the ElevenLabs set.
    {"name": "el_gear_whine_cab_loop", "src": "GEARBOX_WHINE_LOOP (4).wav", "kind": "loop", "persp": "cab",
     "target": "syn:gear_whine_loop:-3"},
    # D. pneumatics and brakes -------------------------------------------------------------------------------------
    # REGEN-01 BRAKE_SERVICE_HISS (7): attack 0 ms, 94 % energy > 2 kHz, -20 dB after 0.18 s, one burst (ADR 0138).
    {"name": "el_air_brake_release", "src": "BRAKE_SERVICE_HISS (7).wav", "kind": "oneshot", "persp": "ext",
     "cab": "pneu", "fade_out": 0.25, "target": "syn:air_brake_release"},
    # AIR_PARKING_APPLY (4): the only take with a natural attack/decay; (1)-(3) are hard-gated noise blocks.
    {"name": "el_parking_brake_set", "src": "AIR_PARKING_APPLY (4).wav", "kind": "oneshot", "persp": "ext",
     "cab": "pneu", "fade_out": 0.3, "target": "syn:parking_brake_set"},
    # AIR_PARKING_RELEASE (4): sharp burst with decay, -16.6 LUFS raw; (1)-(3) are 20-30 dB quieter, mostly floor.
    {"name": "el_parking_brake_release", "src": "AIR_PARKING_RELEASE (4).wav", "kind": "oneshot", "persp": "ext",
     "cab": "pneu", "fade_out": 0.3, "target": "syn:parking_brake_release"},
    # AIR_DRYER_PURGE (4) loud blast + tail; (1) shorter, with faint tonal lines -> the two alternate (as the synthesis A/B).
    # (2) clips (peak 0.0 dBFS, HF spike 36 dB) and is not used.
    {"name": "el_air_dryer_purge", "src": "AIR_DRYER_PURGE (4).wav", "kind": "oneshot", "persp": "ext",
     "cab": "pneu", "fade_out": 0.4, "target": "syn:air_dryer_purge"},
    {"name": "el_air_dryer_purge_b", "src": "AIR_DRYER_PURGE (1).wav", "kind": "oneshot", "persp": "ext",
     "cab": "pneu", "fade_out": 0.4, "target": "syn:air_dryer_purge_b"},
    # AIR_COMPRESSOR_LOOP (2): the only take with a measurable stroke rhythm (envelope ACF 0.39 at 6.6 Hz; others < 0.13).
    # Not resampled: runtime pitch rpm/1000 then gives 6.6 strokes/s at 1000 rpm (procedural: 14) - WORKING_VALUE.
    {"name": "el_compressor_loop", "src": "AIR_COMPRESSOR_LOOP (2).wav", "kind": "loop", "persp": "ext",
     "cab": "mech", "target": "syn:compressor_loop"},
    # TRAILER_COUPLE (1): kingpin clunk at 1.73 s + jaw 1.86 s, then the air-line hiss; cut so the clunk lands at 20 ms.
    {"name": "el_trailer_couple", "src": "TRAILER_COUPLE (1).wav", "kind": "oneshot", "persp": "ext",
     "cab": "mech", "cut": (1.70, 4.0), "fade_out": 0.5, "target": -24.0},
    # E. tyres, suspension -----------------------------------------------------------------------------------------
    # TYRE_ASPHALT_50: cabin perspective (roll-off ~3 kHz). (1): seam 0.06, drift -0.7 dB; resampled to the procedural
    # pitch reference (recorded 13.9 m/s). Exterior keeps the procedural road roll.
    {"name": "el_tyre_dry_cab_loop", "src": "TYRE_ASPHALT_50 (1).wav", "kind": "loop", "persp": "cab",
     "speed_ms": 50 / 3.6, "target": "syn:road_roll_cab_loop"},
    # TYRE_WET_60 (4): steady full-band spray (exterior); (1) has a passing burst at 3.6 s.
    {"name": "el_tyre_wet_loop", "src": "TYRE_WET_60 (4).wav", "kind": "loop", "persp": "ext", "cab": "road",
     "speed_ms": 60 / 3.6, "target": "syn:tyre_wet_loop"},
    # TYRE_PAVERS_20 (2) -> concrete slabs: even joint thumps; (4) has isolated clicks (peak -2.7 dBFS spikes).
    {"name": "el_tyre_concrete_loop", "src": "TYRE_PAVERS_20 (2).wav", "kind": "loop", "persp": "ext", "cab": "road",
     "speed_ms": 20 / 3.6, "target": "syn:tyre_concrete_loop"},
    # TYRE_GRAVEL_15 (3): steadiest of the four (2/4 swell by 6-8 dB).
    {"name": "el_tyre_gravel_loop", "src": "TYRE_GRAVEL_15 (3).wav", "kind": "loop", "persp": "ext", "cab": "road",
     "speed_ms": 15 / 3.6, "target": "syn:tyre_gravel_loop"},
    # SUSP_BUMP (4): single thump at 0.40 s with a short rattle.
    {"name": "el_susp_bump", "src": "SUSP_BUMP (4).wav", "kind": "oneshot", "persp": "ext", "cab": "mech",
     "cut": (0.38, 1.48), "fade_out": 0.3, "target": -30.0},
    # F. cab ------------------------------------------------------------------------------------------------------
    # CAB_INDICATOR_LOOP (3): alternating strong/weak relay clicks, strong ones every 0.66 s (= IndicatorClock 90/min).
    # Tick = strong click at 1.609 s, tock = weak click at 1.919 s (-8.9 dB), level ratio kept.
    {"name": "el_indicator_tick", "src": "CAB_INDICATOR_LOOP (3).wav", "kind": "oneshot", "persp": "both",
     "cut": (1.590, 1.760), "fade_out": 0.06, "target": "syn:indicator_tick_cab"},
    {"name": "el_indicator_tock", "src": "CAB_INDICATOR_LOOP (3).wav", "kind": "oneshot", "persp": "both",
     "cut": (1.900, 2.070), "fade_out": 0.06, "gain_of": "el_indicator_tick"},
    # CAB_SWITCH (2): the only audible take ((1)(3)(4) are -60 LUFS).
    {"name": "el_cab_switch", "src": "CAB_SWITCH (2).wav", "kind": "oneshot", "persp": "both",
     "cut": (0.13, 0.45), "fade_out": 0.08, "target": "syn:indicator_tick_cab:3"},
    # REGEN-01 CAB_DOOR_OPEN (7): latch at 0.06 s, air layer +14.2 dB (ADR 0138). CAB_DOOR_CLOSE (1): one thud at 0.22 s.
    {"name": "el_door_open", "src": "CAB_DOOR_OPEN (7).wav", "kind": "oneshot", "persp": "both",
     "fade_out": 0.3, "target": -28.0},
    {"name": "el_door_close", "src": "CAB_DOOR_CLOSE (1).wav", "kind": "oneshot", "persp": "both",
     "cut": (0.20, 1.48), "fade_out": 0.3, "target": -26.0},
    # HORN_AIR (2): steady 627-633 Hz, 250 ms level std 0.24 dB; sustain loop cut from 0.35-1.35 s at the best
    # autocorrelation lag near 0.8 s, seam in the steady part. Released by a runtime fade.
    {"name": "el_horn_loop", "src": "HORN_AIR (2).wav", "kind": "loop", "persp": "ext", "cab": "pneu",
     "period_loop": (0.35, 0.80, 0.08), "target": -20.0},
    # REVERSE_BEEPER_LOOP (4): 1.00 s period (ACF 0.70), beeps at 0.82/1.83/2.82/3.84 s; one period, seam in the gap.
    {"name": "el_reverse_beeper_loop", "src": "REVERSE_BEEPER_LOOP (4).wav", "kind": "loop", "persp": "ext",
     "cab": "ambient", "segment": (1.675, 1.000), "target": -26.0},
    # REGEN-02 ENG_STOP_CAB (7): run-down to silence, tail -33.9 dB vs head (el_regen02.py PASS; ADR 0138 had no take).
    # Replaces the filtered exterior stop for the cab (runtime slot el_engine_stop_cab; own file so el_prepare.py reruns
    # cannot overwrite it; the fx entry comes later in the manifest and wins in the importer). Level = previous cab stop.
    {"name": "el_engine_stop_cab", "file_name": "el_engine_stop_cab_r02", "src": "ENG_STOP_CAB (7).wav", "kind": "oneshot",
     "persp": "both", "fade_out": 0.3, "target": -34.5},
    # G. ambience -------------------------------------------------------------------------------------------------
    # AMB_WIND_CAB_80 (3): cabin perspective, steady (drift small); (1) is a broadband roar at -17 LUFS.
    {"name": "el_wind_cab_loop", "src": "AMB_WIND_CAB_80 (3).wav", "kind": "loop", "persp": "cab",
     "target": "syn:wind_cab_loop"},
    # AMB_INDUSTRIAL_DAY (2): steady 20 s bed, no distinctive events (a recognisable event would mark the loop).
    {"name": "el_ambient_bed_loop", "src": "AMB_INDUSTRIAL_DAY (2).wav", "kind": "loop", "persp": "ext",
     "cab": "ambient", "target": "syn:ambient_bed_loop"},
]
# Turbo layer (ADR 0142, owner feedback on APK 0138): procedural v2 (turbo2.py) until a REGEN-02 recording passes.
# REGEN-02 swap: put "<ID> (n).wav" instead of None -> the take is prepared like any loop (seam, loudness) into the same
# runtime slot. LUFS targets: full-boost exterior turbo ~10 dB under the full-load engine cell at the EngineAudio mix
# (WORKING_VALUE).
# REGEN-02 (ADR 0142): TURBO_WHISTLE_LOOP (6) PASS - line 2757 Hz, 13.8 dB over the floor, span 1.7 % (el_regen02.py);
# resampled so the line sits at turbo2.WHINE_REF_HZ (runtime pitch mapping unchanged). Rush stays procedural.
TURBO: dict[str, str | None] = {"whine": "TURBO_WHISTLE_LOOP (6).wav", "rush": None}
TURBO_LINE_HZ = {"TURBO_WHISTLE_LOOP (6).wav": 2757.0}
TURBO_LUFS = {"whine": -14.0, "rush": -12.0}
# Not wired (ADR 0142 table): CAB_WIPERS_LOOP (no take keeps the asked rhythm, ADR 0138), CAB_RAIN_ROOF_LOOP (no weather
# state), BRAKE_SQUEAL_STOP (no squeal line except (4) faintly at 5.3 kHz), BRAKE_ROLL_LOOP (every take has a burst),
# TRAILER_RATTLE_LOOP (no trailer load / road roughness signal), AMB_PASSING_CAR (no traffic), AMB_YARD_LOGISTICS
# (procedural forklift kept), TURBO_SPOOL / TURBO_WHISTLE_LOOP (no tonal whistle, ADR 0137/0138).
# ---------------------------------------------------------------------------------------------------------------

# REGEN-02 prompts (docs/owner/ELEVENLABS-REGEN-02.md); provenance key "<ID> REGEN-02" keeps the REGEN-01 entry intact.
REGEN02 = {
    "ENG_STOP_CAB REGEN-02": {"id": "ENG_STOP_CAB", "batch": "REGEN-02", "duration": 5, "influence": 70, "loop": False,
                              "prompt": "Inside a heavy truck cab: the idling diesel engine is switched off after half a second, the engine speed sinks quickly, the cab gives one heavy shudder and the engine stops completely within two seconds, then quiet cab with only a faint tick of cooling metal, no music, no voices"},
    "TURBO_WHISTLE_LOOP REGEN-02": {"id": "TURBO_WHISTLE_LOOP", "batch": "REGEN-02", "duration": 5, "influence": 90, "loop": True,
                                    "prompt": "A single pure steady high-pitched whine, like a small turbine spinning at constant speed, one clean tone with almost no noise, no engine, no rumble, no air rush, no pitch change, seamless loop, no music, no voices"},
}
REGEN02_FILES = {"ENG_STOP_CAB (7).wav", "TURBO_WHISTLE_LOOP (6).wav"}

# REGEN-03 (ADR 0145): tyre scrub (tight slow turn, trailer axles dragged sideways) and hard squeal, exterior + cabin.
# Takes are picked automatically by el_regen03.select (6 s steadiest window, no whistle line, no regular creak train,
# seam); an ID without a passing take (or without files) is skipped and the runtime keeps the procedural loop.
# Levels: the same clip LUFS as the procedural placeholders (render_all.TYRE_SLIP_LUFS), so LayerMath / the runtime
# volumes mean the same in both sets; the loudness at the listener lives in TruckAudioController (scrub/squealVolume).
# Cabin takes carry a diesel idle (prompt): 100 Hz high-pass so the runtime engine is not doubled.
REGEN03_SLOTS = [  # (prompt id, runtime name, perspective, target)
    ("TYRE_SCRUB_TIGHT_TURN", "el_tyre_scrub_loop", "ext", -18.0),
    ("TYRE_SCRUB_TIGHT_TURN_CAB", "el_tyre_scrub_cab_loop", "cab", -22.0),
    ("TYRE_SQUEAL_HARD", "el_tyre_squeal_loop", "ext", -16.0),
    ("TYRE_SQUEAL_HARD_CAB", "el_tyre_squeal_cab_loop", "cab", -20.0),
]


def regen03_fx(src: Path) -> list[dict]:
    picks = el_regen03.select(src)
    out = []
    for pid, name, persp, target in REGEN03_SLOTS:
        f = picks.get(pid)
        if not f:
            print(f"REGEN-03 {pid}: no passing take in {src} - procedural loop stays")
            continue
        t0 = el_regen03.best_window(circular_hp(mono(src / f)))
        c = {"name": name, "src": f, "kind": "loop", "persp": persp, "segment": (t0, el_regen03.WIN_S), "target": target,
             "regen": "REGEN-03"}
        if persp == "cab":
            c["hp_loop"] = 100.0
        else:
            cab_pid = pid + "_CAB"
            if picks.get(cab_pid):
                c["no_cab"] = True       # the cabin take is its own clip
            else:
                c["cab"] = "road"        # fallback: prerendered cabin perspective of the exterior take
        out.append(c)
    return out


HP25 = signal.butter(2, 25, "hp", fs=FS, output="sos")


def spectral_gate(x: np.ndarray, ref: np.ndarray, over: float = 1.6, floor: float = 0.12) -> np.ndarray:
    nper = 1024
    _, _, R = signal.stft(ref, FS, nperseg=nper, noverlap=nper * 3 // 4)
    noise = np.median(np.abs(R), axis=1, keepdims=True)
    _, _, Z = signal.stft(x, FS, nperseg=nper, noverlap=nper * 3 // 4)
    m = np.abs(Z)
    g = np.maximum(1.0 - over * noise / (m + 1e-12), floor)
    _, y = signal.istft(Z * g, FS, nperseg=nper, noverlap=nper * 3 // 4)
    return y[: len(x)]


def lead_trim(x: np.ndarray, thr_db: float = -40.0, pre_s: float = 0.005) -> np.ndarray:
    """Drops leading near-silence so the sound starts with its event (5 ms kept before the 1 ms envelope crosses
    thr_db below its maximum)."""
    env = np.convolve(np.abs(x), np.ones(48) / 48, "same")
    i = int(np.argmax(env > env.max() * 10 ** (thr_db / 20)))
    return x[max(0, i - int(pre_s * FS)):]


def best_period(x: np.ndarray, t0: float, approx: float, cf: float) -> tuple[int, int]:
    """Start index and loop length (samples) maximising the waveform correlation across the seam near `approx` s."""
    a = int(t0 * FS)
    w = int(cf * FS)
    best, best_l = -2.0, int(approx * FS)
    for lag in range(int(approx * 0.9 * FS), int(approx * 1.1 * FS)):
        u, v = x[a:a + w], x[a + lag:a + lag + w]
        c = float(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-12))
        if c > best:
            best, best_l = c, lag
    return a, best_l


def process(src: Path, c: dict) -> tuple[np.ndarray, dict]:
    x = mono(src / c["src"])
    info: dict = {}
    if c["kind"] == "loop":
        x = circular_hp(x, c.get("hp_loop", 25.0))
        if "period_loop" in c:
            t0, approx, cf = c["period_loop"]
            a, L = best_period(x, t0, approx, cf)
            x = seam_loop(x[a:a + L + int(cf * FS)], cf)
            info["loop_s"] = L / FS
        elif "segment" in c:
            t0, length = c["segment"]
            a, L = int(t0 * FS), int(length * FS)
            x = seam_loop(x[a:a + L + int(0.04 * FS)])
        else:
            x = seam_loop(x)
        if "speed_ms" in c:
            ratio = 1.0 / tyre_pitch(c["speed_ms"])  # play the recorded speed at runtime pitch tyre_pitch(v_rec)
            x, exact = resample_periodic(x, ratio)
            info["pitch_ratio"] = exact
    else:
        x = signal.sosfiltfilt(HP25, x)
        if "gate" in c:
            g0, g1 = c["gate"]
            ref = x[int(g0 * FS):int(g1 * FS)]
        if "hp" in c:
            x = signal.sosfiltfilt(signal.butter(4, c["hp"], "hp", fs=FS, output="sos"), x)
            if "gate" in c:
                ref = signal.sosfiltfilt(signal.butter(4, c["hp"], "hp", fs=FS, output="sos"), ref)
        if "cut" in c:
            t0, t1 = c["cut"]
            x = x[int(t0 * FS):int(t1 * FS)]
        if "gate" in c:
            x = spectral_gate(x, ref)
        x = lead_trim(x)
        x = fade(x, 0.003, c.get("fade_out", 0.08))
    return x, info


def limit(y: np.ndarray, loop: bool) -> tuple[np.ndarray, float, float]:
    """Peak <= -1.5 dBFS. Loops: memoryless soft knee (seam-safe) takes up to 4 dB of peak reduction, the rest is gain.
    One-shots: gain only (the attack is the sound). Returns (y, gain change dB, soft-limit peak reduction dB)."""
    ceil = 10 ** (-1.5 / 20)
    lim, soft = 0.0, 0.0
    pk = np.abs(y).max()
    if loop and pk > ceil:
        allowed = ceil * 10 ** (4 / 20)  # peak the soft knee may still bring down to the ceiling
        if pk > allowed:
            lim = 20 * math.log10(allowed / pk)
            y = y * (allowed / pk)
        y, soft = soft_limit(y, -1.5)
        pk = np.abs(y).max()
    if pk > ceil:
        lim += 20 * math.log10(ceil / pk)
        y = y * (ceil / pk)
    return y, lim, soft


def resolve_target(t, ref: dict) -> float:
    if isinstance(t, (int, float)):
        return float(t)
    parts = t.split(":")
    v = ref[("sfx", parts[1])]
    return v + (float(parts[2]) if len(parts) > 2 else 0.0)


def check(y: np.ndarray, loop: bool) -> dict:
    r = {"peak_dbfs": 20 * math.log10(np.abs(y).max() + 1e-12), "lufs": lufs(y, FS), "dur_s": len(y) / FS,
         "clipped": int(np.sum(np.abs(y) >= 0.999))}
    if loop:
        r.update(seam(y, FS))
        r["ok"] = r["seam_jump_ratio"] < 1.0 and r["seam_hf_spike_db"] < 6.0 and r["peak_dbfs"] <= -1.0
    else:
        edge = int(0.002 * FS)
        r["edge_start"] = float(np.abs(y[:8]).max())
        r["edge_end"] = float(np.abs(y[-edge:]).max())
        r["ok"] = r["edge_start"] < 0.01 and r["edge_end"] < 0.002 and r["peak_dbfs"] <= -1.0
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(MAIN / "art-source" / "audio" / "elevenlabs"))
    a = ap.parse_args()
    src = Path(a.src)
    ref = synth_lufs()
    gains: dict[str, float] = {}
    entries, rows, report = [], [], []
    sheet: list[tuple[str, np.ndarray]] = []
    for c in FX + regen03_fx(src):
        x, info = process(src, c)
        loop = c["kind"] == "loop"
        if "gain_of" in c:
            gain = gains[c["gain_of"]]
            y = x * 10 ** (gain / 20)
            target = None
        else:
            target = resolve_target(c["target"], ref)
            gain = target - lufs(x, FS)
            y = x * 10 ** (gain / 20)
        y, lim, soft = limit(y, loop)
        gain += lim
        gains[c["name"]] = gain
        outs = [(c["name"], y, None, target, lim, soft)]
        if c["persp"] == "ext" and not c.get("no_cab"):
            cab_name = c["name"].replace("_loop", "_cab_loop") if loop else c["name"] + "_cab"
            z = cab_filter(y, loop, c["cab"])
            # the cabin clip is matched to the procedural cabin clip as well (both perspectives keep the synthesis balance)
            ctarget = None
            syn = c.get("target")
            if isinstance(syn, str) and syn.startswith("syn:"):
                sname = syn.split(":")[1]
                key = sname.replace("_loop", "_cab_loop") if sname.endswith("_loop") else sname + "_cab"
                if ("sfx", key) in ref:
                    ctarget = ref[("sfx", key)]
            if ctarget is not None:
                z = z * 10 ** ((ctarget - lufs(z, FS)) / 20)
            z, clim, csoft = limit(z, loop)
            outs.append((cab_name, z, c["cab"], ctarget, clim, csoft))
        for name, z, prof, tgt, lim, soft in outs:
            f = write(c.get("file_name", name) if prof is None else name, "sfx", z)
            chk = check(z, loop)
            e = {"name": name, "file": f, "loop": loop, "samples": len(z), "source": c["src"], "gain_db": gain,
                 "lufs": chk["lufs"], "source_prompt_id": c["src"].split(" (")[0], "group": "fx",
                 "perspective": "cab" if (prof or c["persp"] == "cab") else c["persp"]}
            if prof:
                e["cab_filter"] = prof
            if tgt is not None:
                e["target_lufs"] = tgt
            if lim:
                e["peak_limited_db"] = lim
            if soft:
                e["soft_limit_db"] = soft
            e.update({k: v for k, v in info.items()})
            entries.append(e)
            rows.append({"name": name, **chk, **info, "gain_db": gain, "target_lufs": tgt, "limited_db": lim, "soft_limit_db": soft})
            sheet.append((name, z))
            extra = (f"seam {chk['seam_jump_ratio']:.2f} hf {chk['seam_hf_spike_db']:+.1f} dB" if loop
                     else f"edges {chk['edge_start']:.4f}/{chk['edge_end']:.5f}")
            report.append(f"{name:28s} <- {c['src']:30s} {chk['dur_s']:5.2f} s {chk['lufs']:6.1f} LUFS pk {chk['peak_dbfs']:5.1f} "
                          f"{extra}{'' if not lim else f'  gain-limited {lim:.1f} dB'}{'' if not soft else f'  soft-limit {soft:.1f} dB'}  {'OK' if chk['ok'] else 'FAIL'}")
    for part in ("whine", "rush"):
        srcf = TURBO[part]
        if srcf:
            x, _ = process(src, {"src": srcf, "kind": "loop"})
            if srcf in TURBO_LINE_HZ:
                x, _ = resample_periodic(x, turbo2.WHINE_REF_HZ / TURBO_LINE_HZ[srcf])
        else:
            x = getattr(turbo2, part + "_loop")()
        y = x * 10 ** ((TURBO_LUFS[part] - lufs(x, FS)) / 20)
        y, lim, soft = limit(y, True)
        z = cab_filter(y, True, "mech")
        z, _, _ = limit(z, True)
        for name, w, prof in ((f"el_turbo_{part}_loop", y, None), (f"el_turbo_{part}_cab_loop", z, "mech")):
            f = write(name, "sfx", w)
            chk = check(w, True)
            e = {"name": name, "file": f, "loop": True, "samples": len(w), "source": srcf or f"procedural turbo2.{part}_loop",
                 "gain_db": 0.0, "lufs": chk["lufs"], "source_prompt_id": (srcf or "PROCEDURAL").split(" (")[0], "group": "fx",
                 "perspective": "cab" if prof else "ext"}
            if prof:
                e["cab_filter"] = prof
            entries.append(e)
            rows.append({"name": name, **chk})
            sheet.append((name, w))
            report.append(f"{name:28s} <- {e['source']:30s} {chk['dur_s']:5.2f} s {chk['lufs']:6.1f} LUFS pk {chk['peak_dbfs']:5.1f} "
                          f"seam {chk['seam_jump_ratio']:.2f} hf {chk['seam_hf_spike_db']:+.1f} dB  {'OK' if chk['ok'] else 'FAIL'}")
    # manifest: replace the fx group, keep the engine set from el_prepare.py
    mp = OUT / "el_manifest.json"
    man = json.loads(mp.read_text(encoding="utf-8"))
    man["sfx"] = [s for s in man["sfx"] if s.get("group") != "fx"] + entries
    gen = {g["id"]: g for g in json.loads((src / "generation-manifest.json").read_text(encoding="utf-8"))}
    gen.update({k: prompt_entry(k) for k in REGEN01})
    gen.update(REGEN02)
    gen.update({pid: el_regen03.prompt_entry(pid) for pid in el_regen03.PROMPTS})
    for e in entries:
        pid = e["source_prompt_id"]
        key = pid + " REGEN-02" if e["source"] in REGEN02_FILES else pid
        if key in gen:
            man["prompts"][key] = gen[key]
    man["fx_generator"] = "tools/audio/el_fx.py (ADR 0142)"
    mp.write_text(json.dumps(man, indent=1), encoding="utf-8")
    ART.mkdir(parents=True, exist_ok=True)
    (ART / "fx.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (ART / "fx.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    render_sheet(sheet, ART / "verify" / "fx_sheet.png")
    print("\n".join(report))
    bad = [r["name"] for r in rows if not r["ok"]]
    print(f"{len(rows)} clips, {len(bad)} FAIL {bad}")


def render_sheet(items: list[tuple[str, np.ndarray]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = 4
    rows = math.ceil(len(items) / cols)
    fig, axs = plt.subplots(rows, cols, figsize=(16, 2.4 * rows))
    for ax in axs.flat:
        ax.axis("off")
    for ax, (name, z) in zip(axs.flat, items):
        ax.axis("on")
        f, t, S = signal.spectrogram(z, FS, nperseg=1024, noverlap=768)
        ax.pcolormesh(t, f / 1000, 10 * np.log10(S + 1e-14), vmin=-130, vmax=-40, shading="auto", cmap="magma")
        ax.set_ylim(0, 12)
        ax.set_title(f"{name} ({len(z) / FS:.2f} s)", fontsize=8)
        ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(out, dpi=60)
    plt.close(fig)


if __name__ == "__main__":
    main()
