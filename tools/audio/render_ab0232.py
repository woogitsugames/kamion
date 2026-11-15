"""ADR 0232: owner A/B scenes. A = synthesis model on main, B = model 0232, same physics telemetry.

    uv run python render_ab0232.py            # banks (if missing) + scenes + spectrograms + README
    uv run python render_ab0232.py --rebuild  # force both banks to be re-rendered first

Output: ``artifacts/audio-0232/`` -- ``<scene>_<ext|cab>_<A|B>.flac`` (48 kHz mono 16 bit, lossless),
``spec/*.jpg`` (A over B with the event markers), ``metrics.json``, ``README.md`` (what to listen for, with
the time stamps of the events that the runtime detectors fired on the telemetry).

Both versions go through the same offline mirror of the game's mixing code: ``runtime_sim.LayerGrid``
(EngineLayerGrid.cs) for the rpm x load grids and the laws of EngineAudio.cs / TruckAudioController.cs /
LayerMath.cs / DrivelineSfx.cs below. No runtime law differs between A and B; only the clips do
(engine + engine-brake grids, turbo whistle, lift-off, service-brake release, parking-brake set).
Tyres, wind, compressor, retarder, AMT phases, dryer and parking-brake release are the same clips in A and B.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

import physics_params as pp
import runtime_sim as rs
import telemetry0232 as tel
from dsp import FS
from el_analyze import lufs

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "artifacts" / "audio-0232"
BANKS = {"A": "main", "B": "0232"}
PERSPECTIVES = ("ext", "cab")
FRAME = int(FS / rs.FRAME_HZ)   # 800 samples: one 60 Hz game frame
DT = FRAME / FS

# ---- EngineAudio.cs (serialized defaults) ----
RPM_TAU, LOAD_TAU, BRAKE_TAU, BOOST_TAU = 0.035, 0.05, 0.08, 0.05
MIX = {  # PerspectiveMix.Exterior / .Cab
    "ext": {"engine": 1.0, "engine_brake": 1.0, "turbo": 0.11, "liftoff": 0.30},
    "cab": {"engine": 1.0, "engine_brake": 0.85, "turbo": 0.045, "liftoff": 0.10},
}
TURBO_PITCH_BASE, TURBO_PITCH_RANGE = 0.6, 0.85
LIFTOFF_MIN_BOOST, LIFTOFF_COOLDOWN = 0.35, 1.0
# ---- TruckAudioController.cs (serialized defaults) ----
PNEUMATICS_VOLUME, CAB_PNEUMATICS = 0.55, 0.6
ROAD_VOLUME, CAB_ROAD = 0.45, 0.55
WIND_VOLUME, CAB_WIND = 0.30, 0.35
RETARDER_VOLUME, CAB_RETARDER = 0.50, 0.85
COMPRESSOR_VOLUME, CAB_COMPRESSOR = 0.06, 0.75
EBRAKE_EVENT_VOLUME, CAB_EBRAKE_EVENT = 0.5, 0.7
# ---- LayerMath.cs ----
RET_TONE_MIX, RET_FLOW_MIX, RET_TONE_FULL_RPM, RET_REF_SHAFT_RPM = 0.35, 0.65, 1600.0, 1000.0
# ---- DrivelineSfx.cs ----
ENGAGE_RISE, RELEASE_RATIO = 0.12, 0.88


def smooth(cur: float, target: float, tau: float, dt: float) -> float:
    return target if tau <= 0 else cur + (target - cur) * (1.0 - math.exp(-dt / tau))


def exp_step(cur: float, target: float, dt: float, tau_up: float, tau_down: float) -> float:
    return smooth(cur, target, tau_up if target > cur else tau_down, dt)


# --------------------------------------------------------------------------- banks
def bank_dir(model: str) -> Path:
    return OUT / "_bank" / model


def ensure_bank(model: str, rebuild: bool = False) -> dict:
    man = bank_dir(model) / "manifest.json"
    if rebuild or not man.exists() or json.loads(man.read_text(encoding="utf-8")).get("synthesis_model") != model:
        subprocess.run([sys.executable, str(HERE / "render_all.py"), "--model", model, "--out", str(bank_dir(model))],
                       check=True, cwd=HERE)
    return json.loads(man.read_text(encoding="utf-8"))


class Bank:
    def __init__(self, model: str, manifest: dict):
        self.model, self.manifest = model, manifest
        self._sfx: dict[str, np.ndarray] = {}

    def sfx(self, name: str) -> np.ndarray:
        if name not in self._sfx:
            self._sfx[name] = rs.load_sfx(self.manifest, name)
        return self._sfx[name]

    def pair(self, name: str, persp: str, loop: bool = False) -> np.ndarray:
        """Exterior clip or its prerendered cabin version (PerspectiveLoop / Play(ext, cab, cabView))."""
        if persp == "ext":
            return self.sfx(name)
        return self.sfx(name.replace("_loop", "_cab_loop") if loop else name + "_cab")


# --------------------------------------------------------------------------- scene render
class DrivelineSfx:
    """Mirror of DrivelineSfx.Step."""
    DISENGAGE, ENGAGE, CLUTCH_CLOSED, EB_ENGAGE, EB_RELEASE = 1, 2, 4, 8, 16

    def __init__(self):
        self.init = False
        self.prev = 0
        self.on = self.was_shifting = False
        self.mn = self.mx = 0.0
        self.depth = 0.0

    def step(self, amt: int, state: float, requested: bool) -> int:
        s = min(1.0, max(0.0, state))
        if not self.init:
            self.init, self.prev, self.on, self.mn, self.mx = True, amt, s > 0.5, s, s
            return 0
        ev = 0
        shifting = 3 <= amt <= 6
        if amt != self.prev:
            if amt == 4:
                ev |= self.DISENGAGE
            if amt == 6:
                ev |= self.ENGAGE
            if self.prev == 6 and not shifting:
                ev |= self.CLUTCH_CLOSED
            self.prev = amt
        if shifting:
            self.was_shifting = True
            return ev
        if self.was_shifting:
            self.was_shifting = False
            if self.on and not requested:
                self.on = False
            self.mn = self.mx = s
            return ev
        if not self.on:
            self.mn = min(self.mn, s)
            if s > self.mn + ENGAGE_RISE:
                self.on, self.mx = True, s
                ev |= self.EB_ENGAGE
        else:
            self.mx = max(self.mx, s)
            if s < self.mx * RELEASE_RATIO:
                self.on, self.mn, self.depth = False, s, self.mx
                ev |= self.EB_RELEASE
        return ev


def render_scene(bank: Bank, name: str, persp: str) -> tuple[np.ndarray, list[tuple[float, str]]]:
    """One scene through the runtime mirror. Returns the mix (Unity volume units) and the fired events."""
    f = tel.load(name)
    cab = persp == "cab"
    mix = MIX[persp]
    n_frames = int(len(f) * tel.DT / DT)
    out = np.zeros(n_frames * FRAME)
    events: list[tuple[float, str]] = []

    eng = rs.load_grid(bank.manifest, "engine", persp, pool=6)
    brk = rs.load_grid(bank.manifest, "ebrake", persp, pool=3)
    whistle = rs.LoopVoice(bank.sfx("turbo_whistle_loop"))
    road = rs.LoopVoice(bank.pair("road_roll_loop", persp, True))
    wind = rs.LoopVoice(bank.pair("wind_loop", persp, True))
    comp = rs.LoopVoice(bank.pair("compressor_loop", persp, True))
    ret_tone = rs.LoopVoice(bank.pair("retarder_tone_loop", persp, True))
    ret_flow = rs.LoopVoice(bank.pair("retarder_flow_loop", persp, True))

    def one_shot(clip: np.ndarray, frame: int, gain: float, label: str) -> None:
        i0 = frame * FRAME
        m = min(len(clip), len(out) - i0)
        out[i0:i0 + m] += gain * clip[:m]
        events.append((frame * DT, label))

    pv = PNEUMATICS_VOLUME * (CAB_PNEUMATICS if cab else 1.0)
    ebv = EBRAKE_EVENT_VOLUME * (CAB_EBRAKE_EVENT if cab else 1.0)
    cab_ret = CAB_RETARDER if cab else 1.0
    wheel_r, final = pp.wheel_radius(), pp.vehicle()["driveline"]["finalDriveRatio"]
    ret_max_p = pp.vehicle()["retarder"]["maxPowerKW"] * 1000.0

    rpm = load = brake = boost = 0.0
    throttle_hold = liftoff_timer = 0.0
    brake_peak = brake_held = 0.0
    tone_g = flow_g = comp_g = 0.0
    prev_park = prev_comp = False
    has_prev = purge_alt = engage_alt = False
    drive = DrivelineSfx()

    for k in range(n_frames):
        i = min(len(f) - 1, int(round(k * DT / tel.DT)))
        # ---- EngineAudio.Update ----
        if k == 0:
            rpm, load, brake, boost = f.rpm[i], f.load[i], f.engine_brake[i], f.boost[i]
        rpm = smooth(rpm, max(0.0, f.rpm[i]), RPM_TAU, DT)
        load = smooth(load, f.load[i], LOAD_TAU, DT)
        brake = smooth(brake, f.engine_brake[i], BRAKE_TAU, DT)
        boost = smooth(boost, f.boost[i], BOOST_TAU, DT)
        throttle = float(f.throttle[i])
        run_gain = min(1.0, max(0.0, (rpm - 80.0) / 300.0))
        eng.update(rpm, load, mix["engine"] * run_gain)
        brk.update(rpm, 0.0, mix["engine_brake"] * brake * run_gain)
        seg = eng.render(FRAME, FS) + brk.render(FRAME, FS)
        # turbo whistle + lift-off (EngineAudio.UpdateTurbo)
        vol = mix["turbo"] * boost ** 1.5 * (0.35 + 0.65 * throttle)
        seg += whistle.render(FRAME, TURBO_PITCH_BASE + TURBO_PITCH_RANGE * boost, vol if vol > 1e-4 else 0.0, FS)
        throttle_hold = max(throttle, throttle_hold - 2.0 * DT)
        liftoff_timer = max(0.0, liftoff_timer - DT)
        if liftoff_timer <= 0 and throttle_hold - throttle > 0.5 and boost > LIFTOFF_MIN_BOOST:
            # the procedural set has no cabin lift-off clip (turboLiftoffCab = null): the exterior clip plays
            one_shot(bank.sfx("turbo_liftoff"), k, mix["liftoff"] * boost, f"turbo: odpuszczenie gazu przy doładowaniu {boost:.2f}")
            liftoff_timer = LIFTOFF_COOLDOWN

        # ---- TruckAudioController.AudioStep ----
        v = float(f.speed[i])
        vn = min(1.0, v / 25.0)
        seg += road.render(FRAME, 0.75 + 0.6 * vn, ROAD_VOLUME * vn ** 1.6 * (CAB_ROAD if cab else 1.0), FS)
        seg += wind.render(FRAME, 1.0, WIND_VOLUME * (CAB_WIND if cab else 1.0) * vn ** 2.2, FS)
        # retarder tone + flow (ADR 0176), compressor
        shaft = abs(v) / max(wheel_r, 0.1) * final * 60.0 / (2 * math.pi)
        fill = float(f.retarder_fill[i])
        tg = RETARDER_VOLUME * RET_TONE_MIX * fill ** 0.8 * min(1.0, shaft / RET_TONE_FULL_RPM) ** 1.5
        fg = RETARDER_VOLUME * RET_FLOW_MIX * math.sqrt(min(1.0, max(0.0, f.retarder_power[i] / ret_max_p)))
        tone_g = exp_step(tone_g, tg, DT, 0.08, 0.25)
        flow_g = exp_step(flow_g, fg, DT, 0.08, 0.25)
        pitch = min(2.5, max(0.2, shaft / RET_REF_SHAFT_RPM))
        seg += ret_tone.render(FRAME, pitch, tone_g * cab_ret, FS) + ret_flow.render(FRAME, pitch, flow_g * cab_ret, FS)
        comp_on = bool(f.compressor[i])
        comp_g = exp_step(comp_g, COMPRESSOR_VOLUME if (rpm > 300.0 and comp_on) else 0.0, DT, 0.15, 0.12)
        seg += comp.render(FRAME, min(1.8, max(0.5, rpm / 1000.0)), comp_g * (CAB_COMPRESSOR if cab else 1.0), FS)
        out[k * FRAME:(k + 1) * FRAME] += seg

        # pneumatic events
        b = float(f.brake[i])
        if b > 0.08:
            brake_peak, brake_held = max(brake_peak, b), brake_held + DT
        elif brake_peak > 0:
            if brake_held > 0.25:
                one_shot(bank.pair("air_brake_release", persp), k, pv * (0.35 + 0.65 * brake_peak),
                         f"zwolnienie hamulca roboczego (szczyt {brake_peak:.2f})")
            brake_peak = brake_held = 0.0
        park = bool(f.park[i])
        amt = int(f.amt[i])
        if has_prev:
            if park and not prev_park:
                one_shot(bank.pair("parking_brake_set", persp), k, pv, "hamulec postojowy: zaciągnięcie")
            if not park and prev_park:
                one_shot(bank.pair("parking_brake_release", persp), k, pv * 0.8, "hamulec postojowy: zwolnienie")
            if prev_comp and not comp_on:
                purge_alt = not purge_alt
                one_shot(bank.pair("air_dryer_purge_v2b" if purge_alt else "air_dryer_purge_v2", persp), k, pv * 0.85,
                         f"odcięcie regulatora przy {f.air_supply[i]:.1f} bar: wydmuch osuszacza")
        prev_park, prev_comp, has_prev = park, comp_on, True
        ev = drive.step(amt, float(f.ebrake_state[i]), bool(f.ebrake_cmd[i]))
        if ev & DrivelineSfx.DISENGAGE:
            one_shot(bank.pair("amt_disengage", persp), k, pv * 0.55, "AMT: wysprzęglenie, bieg neutralny")
        if ev & DrivelineSfx.ENGAGE:
            engage_alt = not engage_alt
            one_shot(bank.pair("amt_engage" if engage_alt else "amt_engage_b", persp), k, pv * 0.6,
                     f"AMT: włączenie biegu {int(f.gear[min(len(f) - 1, i + 30)])}")
        if ev & DrivelineSfx.CLUTCH_CLOSED:
            one_shot(bank.pair("amt_clutch_chuff", persp), k, pv * 0.45, "AMT: sprzęgło zamknięte")
        if ev & DrivelineSfx.EB_ENGAGE:
            one_shot(bank.pair("ebrake_engage", persp), k, ebv * 0.7, "hamulec silnikowy: włączenie")
        if ev & DrivelineSfx.EB_RELEASE:
            lvl = ebv * (0.4 + 0.6 * min(1.0, max(0.0, (f.rpm[i] - 900.0) / 1100.0))) * drive.depth
            one_shot(bank.pair("ebrake_release", persp), k, lvl, "hamulec silnikowy: wyłączenie")
    return out, events


# --------------------------------------------------------------------------- telemetry markers (README)
def telemetry_markers(name: str) -> list[tuple[float, str]]:
    """What the driver and the physics did, from the telemetry (not from the audio events)."""
    f = tel.load(name)
    marks: list[tuple[float, str]] = []
    drv = np.genfromtxt(tel.TELE_DIR / f"{tel.scene(name).scenario.replace('@', '_')}.csv", delimiter=",", names=True)
    sel = (drv["t"] >= tel.scene(name).window[0] - 1e-9) & (drv["t"] < tel.scene(name).window[1] + tel.DT - 1e-9)
    thr_in = drv["throttle_in"][sel]
    for i in range(1, len(f)):
        t = float(f.t[i])
        if abs(thr_in[i] - thr_in[i - 1]) > 0.04:
            marks.append((t, f"pedał gazu {thr_in[i - 1] * 100:.0f} % → {thr_in[i] * 100:.0f} %"))
        if f.lever[i] != f.lever[i - 1]:
            marks.append((t, f"dźwignia hamulców długotrwałych {f.lever[i - 1]} → {f.lever[i]}"))
        if f.amt[i] == tel.AMT_TORQUE_RAMP and f.amt[i - 1] != tel.AMT_TORQUE_RAMP:
            marks.append((t, f"AMT: początek zmiany biegu z {f.gear[i - 1]} ({f.rpm[i]:.0f} obr/min)"))
        if f.amt[i - 1] == tel.AMT_ENGAGE and f.amt[i] not in tel.SHIFT_STATES:
            marks.append((t, f"AMT: bieg {f.gear[i]} włączony ({f.rpm[i]:.0f} obr/min)"))
        if f.compressor[i] != f.compressor[i - 1]:
            marks.append((t, "sprężarka: " + ("start" if f.compressor[i] else "odcięcie") + f" ({f.air_supply[i]:.1f} bar)"))
    return marks


# --------------------------------------------------------------------------- output
def click_ratio(x: np.ndarray) -> float:
    """Largest sample-to-sample step relative to the 99.99th percentile step (a splice click sticks out)."""
    d = np.abs(np.diff(x))
    return float(d.max() / (np.percentile(d, 99.99) + 1e-12))


def spectrogram_jpg(path: Path, a: np.ndarray, b: np.ndarray, title: str, events, f: tel.Frames) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import io

    import matplotlib.pyplot as plt
    from PIL import Image

    fig, ax = plt.subplots(5, 1, figsize=(13, 13), gridspec_kw={"height_ratios": [1.1, 2, 2, 2, 2]})
    ax[0].plot(f.t, f.rpm / 2000.0, label="obr/min / 2000", lw=1)
    ax[0].plot(f.t, f.load, label="obciążenie", lw=1)
    ax[0].plot(f.t, f.boost, label="doładowanie", lw=1)
    ax[0].plot(f.t, f.engine_brake, label="hamulec silnikowy", lw=1)
    ax[0].plot(f.t, f.retarder_fill, label="retarder", lw=1)
    ax[0].set_xlim(0, len(a) / FS)
    ax[0].legend(ncol=5, fontsize=7, loc="upper right")
    ax[0].set_title(title, fontsize=9)
    for row, (x, lab) in enumerate(((a, "A (main)"), (b, "B (0232)"))):
        for col, (fmax, nfft) in enumerate(((600, 16384), (9000, 2048))):
            axx = ax[1 + row + 2 * col]
            axx.specgram(x, NFFT=nfft, Fs=FS, noverlap=nfft * 3 // 4, vmin=-115, vmax=-35, cmap="magma")
            axx.set_ylim(0, fmax)
            axx.set_xlim(0, len(a) / FS)
            axx.set_ylabel(f"{lab}\nHz", fontsize=8)
            if col == 0:
                axx.plot(f.t, f.rpm / 20.0, color="cyan", lw=0.5, alpha=0.6)   # firing frequency (order 3)
            for t, _ in events:
                axx.axvline(t, color="white", lw=0.4, alpha=0.5)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=80)
    plt.close(fig)
    img = Image.open(buf).convert("RGB")
    img = img.resize((960, round(img.height * 960 / img.width)), Image.LANCZOS)
    img.save(path, quality=80, optimize=True)


def _times(items, needle: str) -> str:
    ts = [t for t, label in items if needle in label]
    return ", ".join(f"{t:.1f}".replace(".", ",") for t in ts) + " s" if ts else "brak"


def _cell_lufs(bank: "Bank", kind: str, persp: str, rpm: int, layer: str | None) -> float:
    c = next(c for c in bank.manifest["clips"] if c["kind"] == kind and c["perspective"] == persp
             and c["rpm"] == rpm and c["layer"] == layer)
    x, _ = sf.read(ROOT / c["file"])
    return lufs(x, FS)


GUIDE = {
    "1_ruszanie_40t": [
        "Bieg jałowy 0–1,5 s: w B słychać spalanie na biegu jałowym (klekot, więcej harmonicznych zapłonu do ~600 Hz); "
        "w A komórka „bez obciążenia” to silnik bez wtrysku, więc jałowy jest gładszy i bardziej pusty.",
        "Zwolnienie hamulca roboczego ({brake}): B = wypływ z komór przez zawory (dwa strumienie, przód i tył), A = szum z obwiednią.",
        "Pełny gaz pod obciążeniem (np. 2–5,5 s i 13–18,5 s): w B ostrzejszy, bardziej „warczący” wydech (stromy front impulsu), "
        "gwizd turbo siedzi w szumie przepływu i ma wstęgi boczne; w A gwizd to prawie czysty ton 3,2–4,6 kHz.",
        "Zmiany biegów AMT (wysprzęglenie: {neutral}; bieg włączony: {closed}): przerwa w momencie i spadek obrotów "
        "pochodzą z fizyki i są takie same w A i B; w B wyraźniej zmienia się barwa silnika w przerwie (obciążenie → 0 → 1). "
        "Stuki skrzyni i „pft” są te same (ADR 0176).",
        "„Pssst” turbo przy odjęciu momentu ({liftoff}): B = upust powietrza doładowującego (ok. 0,3 s) + wybieg sprężarki, "
        "A = krótszy syk z opadającym tonem. Ostatnie ({liftoff_last}) to odpuszczenie pedału przez kierowcę.",
        "Wybieg 21–24 s i częściowy gaz od 24 s: B na wybiegu ciemniejszy i bardziej „mechaniczny”, po dodaniu gazu 50 % wraca wydech.",
    ],
    "2_biegi_pusty": [
        "Gaz 55 % (1–10 s), zmiany co ~1,5 s (wysprzęglenie: {neutral}): słuchaj, czy silnik w B przy częściowym gazie "
        "brzmi inaczej niż przy pełnym (10–18 s), a nie tylko ciszej. W A warstwy różnią się głównie poziomem.",
        "Pełny gaz 10–18 s: gwizd turbo narasta z doładowaniem; „pssst” przy zmianach ({liftoff}).",
        "Odpuszczenie gazu przy 18 s i powrót 70 % od 20,5 s: przejście wybieg → obciążenie (crossfade warstw off → on).",
    ],
    "3_zjazd_hamulce_dlugotrwale": [
        "Wybieg 0–3 s na 12. biegu (~1050 obr/min): tło to głównie opony i wiatr przy 75–80 km/h (te same w A i B).",
        "Dźwignia na 2 przy 3 s: redukcja 12 → 10 z przegazówką, hamulec silnikowy od {eb_on} (~1840 obr/min). "
        "W B poziom hamulca silnikowego wynika z krzywej momentu hamującego z fizyki: przy wysokich obrotach prawie jak w A, "
        "przy niskich wyraźnie ciszej (1000 obr/min: różnica w tabeli niżej).",
        "Dźwignia na maksimum od 9 s: retarder (ton łopatek + szum oleju) — te same pliki w A i B (ADR 0176), "
        "różnica A/B tylko w warstwie silnika pod spodem.",
        "Zwolnienie przy 19 s (zmiana 10 → 12; zdarzenie zwolnienia przepustnicy jest tu celowo nieme, bo trwa zmiana biegu), "
        "gaz 60 % od 21,5 s: wraca wydech i gwizd turbo.",
    ],
    "4_postoj_pneumatyka": [
        "0–8 s: postój na podwyższonych obrotach (~1900 obr/min, kierowca dopompowuje układ), sprężarka pracuje cicho pod silnikiem (ten sam plik w A i B).",
        "Odcięcie regulatora i wydmuch osuszacza ({purge}): ten sam plik w A i B (ADR 0176).",
        "8–11 s: obroty spadają do jałowych; od ~11 s bieg jałowy — tu różnica silnika A/B jest największa (klekot spalania w B).",
        "Zwolnienie hamulca postojowego ({park_off}): ten sam plik w A i B.",
        "Zwolnienie hamulca roboczego ({brake}): B = model wypływu z komór; drugie zwolnienie jest cichsze (słabsze hamowanie).",
        "Ruszenie 14–19 s, hamowanie do zatrzymania 19–21 s (fizyka dokłada hamulec silnikowy: {eb_on}).",
        "Zaciągnięcie hamulca postojowego ({park_on}): B = wypływ z komór sprężynowych, stuk sprężyn ok. 0,45 s po otwarciu zaworu "
        "(ciśnienie spada do progu sprężyn z definicji pojazdu); A = długi szum z kliknięciem po 1,75 s.",
    ],
}


def readme(metrics: dict, banks: dict) -> str:
    out = ["# audio-0232 — odsłuch A/B (ADR 0232)", "",
           "A = synteza z `origin/main`, B = model 0232. Te same przebiegi z fizyki (physics-runner, 100 Hz), to samo lustro "
           "miksu gry, te same prawa głośności; różnią się tylko pliki: siatka silnika i hamulca silnikowego, gwizd turbo, "
           "„pssst” turbo, zwolnienie hamulca roboczego, zaciągnięcie postojowego. Opony, wiatr, sprężarka, retarder, fazy AMT, "
           "osuszacz i zwolnienie postojowego to te same pliki w A i B.", "",
           "Pliki: FLAC 48 kHz mono 16 bit (bezstratne; WAV to LFS w tym repo). `ext` = kamera zewnętrzna, `cab` = kabina. "
           "W obrębie pary A i B mają to samo wzmocnienie (głośniejszy z dwóch ma szczyt −1 dBFS), więc różnice poziomu są prawdziwe. "
           "Sceny mają różne wzmocnienia — kolumna „wzmocnienie sceny”.", "",
           "Odsłuch: telefon (głośnik) i słuchawki, najlepiej na przemian A → B → A ten sam fragment. "
           "Spektrogramy z zaznaczonymi zdarzeniami: `spec/<scena>_<ext|cab>.jpg` (góra: telemetria; 0–600 Hz i 0–9 kHz, A nad B).", "",
           "Agent nie słyszy: poniżej jest to, co wynika z pomiaru i z konstrukcji dźwięku; ocena brzmienia należy do właściciela.", ""]
    for name, e in metrics["scenes"].items():
        ev = e["events_ext"]
        mk = e["markers"]
        lift = [t for t, label in ev if "turbo" in label]
        fmt = {
            "brake": _times(ev, "hamulca roboczego"), "neutral": _times(ev, "wysprzęglenie"), "closed": _times(ev, "sprzęgło zamknięte"),
            "liftoff": _times(ev, "turbo"), "liftoff_last": (f"{lift[-1]:.1f}".replace(".", ",") + " s") if lift else "brak",
            "eb_on": _times(ev, "hamulec silnikowy: włączenie"), "purge": _times(ev, "osuszacza"),
            "park_off": _times(ev, "postojowy: zwolnienie"), "park_on": _times(ev, "postojowy: zaciągnięcie"),
        }
        out += [f"## {name}", "", e["title"] + f". Fizyka: `{e['scenario']}`, okno {e['window_s'][0]:.0f}–{e['window_s'][1]:.0f} s przebiegu.", "",
                "| plik | LUFS | szczyt dBFS | wzmocnienie sceny dB |", "|---|---|---|---|"]
        for fn, m in e["files"].items():
            out.append(f"| `{fn}` | {m['lufs']:.1f} | {m['peak_dbfs']:.1f} | {m['scene_gain_db']:+.1f} |")
        out += ["", "Czego słuchać:", ""] + [f"- {g.format(**fmt)}" for g in GUIDE[name]]
        out += ["", "Znaczniki czasu (T = telemetria fizyki, D = zdarzenie dźwiękowe wykryte przez lustro gry):", ""]
        rows = sorted([(t, "T", label) for t, label in mk] + [(t, "D", label) for t, label in ev])
        out += [f"- {t:5.2f} s  {k}  {label}" for t, k, label in rows] + [""]
    a, b = banks["A"], banks["B"]
    out += ["## Pomiary banków (A = main, B = 0232)", "",
            "| komórka | A LUFS | B LUFS |", "|---|---|---|"]
    for kind, persp, rpm, layer in (("engine", "ext", 600, "off"), ("engine", "ext", 600, "on"), ("engine", "ext", 1300, "off"),
                                    ("engine", "ext", 1300, "mid"), ("engine", "ext", 1300, "on"), ("engine", "cab", 1300, "on"),
                                    ("engine", "ext", 2100, "on"), ("ebrake", "ext", 1000, None), ("ebrake", "ext", 1500, None),
                                    ("ebrake", "ext", 2000, None)):
        label = f"{'silnik' if kind == 'engine' else 'hamulec silnikowy'} {persp} {layer or ''} {rpm} obr/min".replace("  ", " ")
        out.append(f"| {label} | {_cell_lufs(a, kind, persp, rpm, layer):.1f} | {_cell_lufs(b, kind, persp, rpm, layer):.1f} |")
    out += ["", "| warstwa | A LUFS | B LUFS |", "|---|---|---|"]
    for sname, v in b.manifest["sfx_0232"].items():
        out.append(f"| `{sname}` | {v['main_lufs']:.1f} | {v['lufs']:.1f} |")
    out += ["", "Odtworzenie: `cd tools/audio; uv run python render_ab0232.py --rebuild` (telemetria: `uv run python telemetry0232.py --refresh`, wymaga .NET 8).", ""]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--no-plots", action="store_true")
    args = ap.parse_args()
    banks = {v: Bank(m, ensure_bank(m, args.rebuild)) for v, m in BANKS.items()}
    (OUT / "spec").mkdir(parents=True, exist_ok=True)
    metrics: dict = {"sample_rate": FS, "banks": BANKS, "scenes": {}}
    for sc in tel.SCENES:
        entry = {"title": sc.title, "scenario": sc.scenario, "window_s": list(sc.window), "files": {},
                 "markers": telemetry_markers(sc.name)}
        for persp in PERSPECTIVES:
            rendered = {v: render_scene(banks[v], sc.name, persp) for v in BANKS}
            peak = max(np.max(np.abs(x)) for x, _ in rendered.values())
            gain = 10 ** (-1.0 / 20) / peak      # one gain for A and B: the louder of the two peaks at -1 dBFS
            for v, (x, events) in rendered.items():
                y = x * gain
                fn = f"{sc.name}_{persp}_{v}.flac"
                sf.write(OUT / fn, y, FS, format="FLAC", subtype="PCM_16")
                entry["files"][fn] = {"lufs": lufs(y, FS), "peak_dbfs": 20 * math.log10(np.max(np.abs(y))),
                                      "scene_gain_db": 20 * math.log10(gain), "click_ratio": click_ratio(y),
                                      "seconds": len(y) / FS}
            entry[f"events_{persp}"] = rendered["B"][1]
            assert [e[1] for e in rendered["A"][1]] == [e[1] for e in rendered["B"][1]]  # same detectors, same telemetry
            if not args.no_plots:
                gain_a = rendered["A"][0] * gain
                spectrogram_jpg(OUT / "spec" / f"{sc.name}_{persp}.jpg", gain_a, rendered["B"][0] * gain,
                                f"{sc.name} ({persp}): {sc.title}", rendered["B"][1], tel.load(sc.name))
            print(sc.name, persp, {k: round(v["lufs"], 1) for k, v in entry["files"].items() if f"_{persp}_" in k})
        metrics["scenes"][sc.name] = entry
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / "README.md").write_text(readme(metrics, banks), encoding="utf-8")


if __name__ == "__main__":
    main()
