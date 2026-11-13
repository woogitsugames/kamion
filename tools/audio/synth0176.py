"""ADR 0176: procedural synthesis of the truck layers that no free recording covers.

Three independent research passes (G9, GPT P5, Mistral M55) found no usable free recordings of a
hydrodynamic retarder, an engine (exhaust-flap / compression-release) brake of a single vehicle,
the torque interruption of an AMT shift, or the cyclic purge of an air dryer. This module builds
those layers from simple physical models, so the sound follows the vehicle physics telemetry at
runtime (``LayerMath`` / ``DrivelineSfx`` in game/Assets/_Project/Audio).

Every number below is a WORKING_VALUE design choice for a fictional truck (no measurement of a
real product); the final judgement is the owner's ears (phone speaker + headphones).

Layers (exterior; cabin versions via ``sfx_layers.cab_filter``):

* ``retarder_tone_loop``  -- rotor blade-pass tone of the hydrodynamic retarder at the reference
  propshaft speed REF_SHAFT_RPM. Runtime pitch = shaft rpm / REF_SHAFT_RPM, gain ~ fill x tip speed.
* ``retarder_flow_loop``  -- turbulent oil flow / churning in the working chamber (broadband, its
  spectral centre scales with the shaft speed through the runtime pitch), gain ~ sqrt(dissipated
  power): with the hydrodynamic n^2 law the retarder is nearly silent at walking pace even at full fill.
* ``ebrake_engage``       -- exhaust-flap actuator: solenoid click, flap hitting its stop, manifold
  pressure building up (low "whump").
* ``ebrake_release``      -- flap opens: trapped exhaust back-pressure dumps through the exhaust pipe
  (pipe resonances of engine_synth.EXH_EXT) + actuator cylinder venting.
* ``amt_disengage``       -- AMT shift: solenoid valve, shift-cylinder exhaust, sliding sleeve leaving
  the dog teeth (played at the start of the neutral phase, after the torque ramp-down).
* ``amt_engage``/``_b``   -- dog clutch engagement clunk + backlash rattle in the gearbox housing.
* ``amt_clutch_chuff``    -- pneumatic clutch actuator venting when the clutch closes again.
* ``air_dryer_purge_v2``/``_v2b`` -- governor cut-out: blow-down of the dryer volume through the purge
  valve (choked then subsonic orifice flow integrated in time; jet-noise level ~ m_dot * U^5,
  peak frequency ~ 0.2 U / D falls as the pressure drops) followed by the quiet regeneration flow.

Loops are periodic by construction (integer numbers of rotor revolutions, periodic filtering);
one-shots have raised-cosine edges and a >= 1 ms attack (no digital click).
"""

from __future__ import annotations

import numpy as np
from scipy import signal

import dsp
import engine_synth as es
import sfx_layers as sl
import sfx_synth as sx
from dsp import FS, bp, chain, highshelf, hp, lowshelf, lp, peak, periodic_sosfilt

# --------------------------------------------------------------------------- retarder geometry
REF_SHAFT_RPM = 1000.0      # propshaft speed of the loops at runtime pitch 1.0
RETARDER_STEP_UP = 1.7      # rotor / propshaft speed ratio (WORKING_VALUE)
ROTOR_BLADES = 23           # rotor vanes; stator has 25 (unequal counts: no full-coincidence slam)
STATOR_BLADES = 25


def rotor_hz(shaft_rpm: float = REF_SHAFT_RPM) -> float:
    return shaft_rpm * RETARDER_STEP_UP / 60.0


def blade_pass_hz(shaft_rpm: float = REF_SHAFT_RPM) -> float:
    return ROTOR_BLADES * rotor_hz(shaft_rpm)


def _loop_seconds(target_s: float) -> tuple[float, int]:
    """Loop length holding an integer number of rotor revolutions at REF_SHAFT_RPM (and of samples)."""
    fr = rotor_hz()
    revs = max(1, int(round(target_s * fr)))
    return revs / fr, revs


def _periodic_phase(f_inst: np.ndarray) -> np.ndarray:
    """Phase of a slowly modulated tone, rescaled to an integer number of cycles over the buffer (seamless)."""
    ph = 2 * np.pi * np.cumsum(f_inst) / FS
    cyc = ph[-1] / (2 * np.pi)
    return ph * (np.round(cyc) / cyc)


def retarder_tone_loop(target_s: float = 3.0, seed: int = 1761) -> np.ndarray:
    """Rotor/stator interaction tone: blade-pass harmonics with shaft-order sidebands (rotor run-out)."""
    rng = np.random.default_rng(seed)
    secs, revs = _loop_seconds(target_s)
    n = int(round(secs * FS))
    t = np.arange(n) / FS
    fr = revs / (n / FS)                       # exact rotor frequency of this loop
    bpf = ROTOR_BLADES * fr
    # turbulent unsteadiness: tiny FM, slow AM (periodic)
    fm = 0.0025 * dsp.smooth_random_periodic(rng, n, max_cycles=int(4 * secs), n_terms=5)
    am = 1.0 + 0.12 * dsp.smooth_random_periodic(rng, n, max_cycles=int(9 * secs), n_terms=6)
    ph = _periodic_phase(bpf * (1 + fm))
    rev = 2 * np.pi * fr * t                    # rotor angle (integer revs per loop)
    run_out = 1.0 + 0.18 * np.cos(rev + 0.4) + 0.07 * np.cos(2 * rev + 1.9)  # shaft-order sidebands
    tone = (np.sin(ph) + 0.42 * np.sin(2 * ph + 0.9) + 0.16 * np.sin(3 * ph + 2.1)) * run_out * am
    # stator-count interaction: weak line at (N_S / N_R) x BPF (beat between vane rows)
    ph_s = _periodic_phase(np.full(n, STATOR_BLADES * fr))
    tone += 0.10 * np.sin(ph_s + 0.3) * am
    tone = periodic_sosfilt(tone, chain(hp(120.0, 0.7), lp(5000.0, 0.7)))
    return tone / (np.max(np.abs(tone)) + 1e-12)


def retarder_flow_loop(target_s: float = 6.0, seed: int = 1762) -> np.ndarray:
    """Oil flow in the working chamber: broadband rush centred around ~0.6 x BPF, churning that
    breathes once per rotor revolution, sparse vapour-bubble (cavitation) crackle."""
    rng = np.random.default_rng(seed)
    secs, revs = _loop_seconds(target_s)
    n = int(round(secs * FS))
    t = np.arange(n) / FS
    fr = revs / (n / FS)
    bpf = ROTOR_BLADES * fr
    rush = periodic_sosfilt(dsp.periodic_noise(rng, n),
                            chain(hp(90.0, 0.7), peak(0.6 * bpf, 0.8, 7.0), peak(1.6 * bpf, 1.2, 3.0), lp(4200.0, 0.7)))
    rush /= np.max(np.abs(rush)) + 1e-12
    breathe = 1.0 + 0.22 * np.cos(2 * np.pi * fr * t) + 0.08 * dsp.smooth_random_periodic(rng, n, int(13 * secs), 8)
    churn = periodic_sosfilt(dsp.periodic_noise(rng, n), chain(hp(35.0, 0.7), lp(260.0, 0.9), peak(95.0, 1.4, 4.0)))
    churn /= np.max(np.abs(churn)) + 1e-12
    crackle = np.zeros(n)
    k = sl._damped_sine(2600.0, 0.0007, 0.006)
    for _ in range(int(45 * secs)):
        sl._add_circ(crackle, int(rng.integers(0, n)), k, float(rng.uniform(0.2, 1.0)))
    crackle = periodic_sosfilt(crackle, chain(hp(1200.0, 0.7)))
    crackle /= np.max(np.abs(crackle)) + 1e-12
    x = 0.85 * rush * breathe + 0.55 * churn * (1.0 + 0.3 * np.cos(2 * np.pi * fr * t + 1.0)) + 0.08 * crackle
    return x / (np.max(np.abs(x)) + 1e-12)


# --------------------------------------------------------------------------- one-shot helpers
def _modes(n: int, at_s: float, modes, rng=None, jitter: float = 0.0) -> np.ndarray:
    """Sum of decaying modes (Hz, tau s, amp) starting at at_s with a 1 ms raised attack."""
    x = np.zeros(n)
    i0 = int(at_s * FS)
    t = np.arange(n - i0) / FS
    att = np.minimum(1.0, t / 0.001)
    for f, tau, a in modes:
        if rng is not None and jitter:
            f *= 1.0 + rng.normal(0, jitter)
        x[i0:] += a * np.sin(2 * np.pi * f * t + 0.3) * np.exp(-t / tau) * att
    return x


def _hiss(rng, n: int, at_s: float, sos, attack_s: float, tau_s: float, hold_s: float = 0.0) -> np.ndarray:
    x = np.zeros(n)
    i0 = int(at_s * FS)
    m = n - i0
    w = signal.sosfilt(sos, rng.standard_normal(m + 4096))[4096:]
    w /= np.max(np.abs(w)) + 1e-12
    x[i0:] = w * sx._env_attack_decay(m, attack_s, tau_s, hold_s)
    return x


def _finish(x: np.ndarray, fade_out_s: float = 0.05) -> np.ndarray:
    x = dsp.fade_edges(x, 0.0005, fade_out_s)
    return x / (np.max(np.abs(x)) + 1e-12)


# --------------------------------------------------------------------------- engine brake
def ebrake_engage(seed: int = 1771) -> np.ndarray:
    """Exhaust flap closes: solenoid click, flap knocks its stop, back-pressure builds (low whump)."""
    rng = np.random.default_rng(seed)
    n = int(0.75 * FS)
    t = np.arange(n) / FS
    click = _modes(n, 0.0, [(2600.0, 0.0018, 0.35), (4100.0, 0.0009, 0.2)])
    cyl = _hiss(rng, n, 0.004, chain(hp(1500.0), peak(3600.0, 1.4, 4.0), lp(8000.0)), 0.003, 0.03) * 0.18
    knock = _modes(n, 0.045, [(185.0, 0.035, 0.8), (430.0, 0.018, 0.55), (1150.0, 0.008, 0.35), (2300.0, 0.004, 0.15)], rng, 0.02)
    # manifold pressurisation: exhaust pulses suddenly back up -> slow low-frequency swell through the pipe system
    swell_env = np.clip((t - 0.05) / 0.12, 0, 1) ** 1.5 * np.exp(-np.maximum(t - 0.17, 0) / 0.22)
    f = 48.0 + 26.0 * np.clip((t - 0.05) / 0.3, 0, 1)
    swell = np.sin(2 * np.pi * np.cumsum(f) / FS) * swell_env
    rumble = signal.sosfilt(chain(hp(40.0), lp(320.0, 0.8)), rng.standard_normal(n)) * swell_env
    rumble /= np.max(np.abs(rumble)) + 1e-12
    x = click + cyl + knock + 0.65 * swell + 0.35 * rumble
    x = signal.sosfilt(es.EXH_EXT, np.concatenate([np.zeros(256), x]))[256:] * 0.6 + 0.4 * x
    return _finish(x, 0.15)


def ebrake_release(seed: int = 1772) -> np.ndarray:
    """Flap opens: the trapped back-pressure (a few bar in the manifold) dumps through the exhaust pipe
    ("whoomp" on the pipe resonances + exhaust rush), then the actuator cylinder vents."""
    rng = np.random.default_rng(seed)
    n = int(1.0 * FS)
    t = np.arange(n) / FS
    # pressure pulse: fast rise, ~60 ms decay; drives the pipe/muffler resonances
    pulse = np.where(t > 0.002, (1 - np.exp(-(t - 0.002) / 0.004)) * np.exp(-(t - 0.002) / 0.06), 0.0)
    rush = signal.sosfilt(chain(hp(150.0), peak(1100.0, 0.9, 5.0), lp(4800.0, 0.7)), rng.standard_normal(n))
    rush /= np.max(np.abs(rush)) + 1e-12
    rush_env = sx._env_attack_decay(n, 0.006, 0.11, hold_s=0.02)
    bright = np.exp(-t / 0.12)
    rush = rush * rush_env * (0.35 + 0.65 * bright)
    src = 1.4 * pulse + 0.55 * rush
    pipe = signal.sosfilt(es.EXH_EXT, np.concatenate([np.zeros(512), src]))[512:]
    pipe /= np.max(np.abs(pipe)) + 1e-12
    knock = _modes(n, 0.003, [(210.0, 0.02, 0.35), (980.0, 0.006, 0.25)], rng, 0.02)
    vent = _hiss(rng, n, 0.07, chain(hp(1800.0), peak(4200.0, 1.3, 4.0), lp(9500.0)), 0.004, 0.05, 0.02) * 0.22
    x = pipe + 0.6 * rush * 0.4 + knock + vent
    return _finish(x, 0.2)


# --------------------------------------------------------------------------- AMT
HOUSING = [(140.0, 0.045, 0.7), (310.0, 0.03, 0.6), (760.0, 0.016, 0.5), (1600.0, 0.008, 0.35), (3100.0, 0.004, 0.18)]


def amt_disengage(seed: int = 1781) -> np.ndarray:
    """Neutral phase starts: solenoid valve click, shift-cylinder exhaust 'pft', sleeve leaves the dog teeth."""
    rng = np.random.default_rng(seed)
    n = int(0.35 * FS)
    click = _modes(n, 0.0, [(3000.0, 0.0012, 0.4), (5200.0, 0.0006, 0.15)])
    pft = _hiss(rng, n, 0.012, chain(hp(1700.0), peak(4300.0, 1.5, 5.0), lp(9000.0)), 0.003, 0.035, 0.01) * 0.45
    clack = _modes(n, 0.038, [(900.0, 0.009, 0.4), (2300.0, 0.005, 0.3), (3700.0, 0.003, 0.15), (310.0, 0.02, 0.25)], rng, 0.03)
    return _finish(click + pft + clack, 0.06)


def amt_engage(seed: int = 1782, rattle: int = 3) -> np.ndarray:
    """Dog clutch engages: metallic clunk through the gearbox housing modes + backlash rattle + cylinder 'pft'."""
    rng = np.random.default_rng(seed)
    n = int(0.5 * FS)
    clunk = _modes(n, 0.004, HOUSING, rng, 0.03)
    thud = _modes(n, 0.004, [(62.0, 0.06, 0.6)])  # driveline wind-up through the frame
    rat = np.zeros(n)
    at = 0.004
    for k in range(rattle):
        at += float(rng.uniform(0.012, 0.022))
        rat += _modes(n, at, [(1250.0, 0.006, 0.25), (2650.0, 0.003, 0.18), (420.0, 0.012, 0.15)], rng, 0.05) * 0.6 ** (k + 1)
    pft = _hiss(rng, n, 0.03, chain(hp(1600.0), peak(4000.0, 1.4, 4.0), lp(8500.0)), 0.004, 0.05, 0.01) * 0.35
    return _finish(clunk + thud + rat + pft, 0.08)


def amt_clutch_chuff(seed: int = 1783) -> np.ndarray:
    """Pneumatic clutch actuator vents as the clutch closes: soft, darker 'chuff' with a valve click."""
    rng = np.random.default_rng(seed)
    n = int(0.45 * FS)
    t = np.arange(n) / FS
    bright = chain(hp(900.0, 0.7), peak(2600.0, 1.0, 4.0), lp(7000.0, 0.7))
    dark = chain(hp(400.0, 0.7), peak(1300.0, 1.0, 3.0), lp(3200.0, 0.7))
    hiss = sx._time_varying_hiss(rng, n, bright, dark, np.exp(-t / 0.08)) * sx._env_attack_decay(n, 0.006, 0.07, 0.02)
    click = _modes(n, 0.0, [(2400.0, 0.0015, 0.3)])
    body = _modes(n, 0.002, [(120.0, 0.03, 0.25)])
    return _finish(0.8 * hiss + click + body, 0.08)


# --------------------------------------------------------------------------- air dryer blow-down
GAMMA = 1.4
R_AIR = 287.05
P_AMB = 101_325.0


def blowdown(volume_l: float, p0_bar_g: float, d_mm: float, cd: float = 0.75, t0_k: float = 330.0,
             seconds: float = 2.0, dt: float = 1e-4) -> dict[str, np.ndarray]:
    """Adiabatic blow-down of a vessel through an orifice (choked, then subsonic isentropic flow).

    Returns time [s], vessel pressure [Pa abs], mass flow [kg/s], fully expanded jet velocity [m/s]."""
    v = volume_l * 1e-3
    a = cd * np.pi * (d_mm * 1e-3) ** 2 / 4
    p = (p0_bar_g * 1e5) + P_AMB
    m = p * v / (R_AIR * t0_k)
    s_ent = p / (m / v) ** GAMMA             # p / rho^gamma constant (adiabatic vessel)
    crit = (2 / (GAMMA + 1)) ** (GAMMA / (GAMMA - 1))
    k = int(seconds / dt)
    out = {k_: np.zeros(k) for k_ in ("t", "p", "mdot", "u")}
    for i in range(k):
        rho = m / v
        p = s_ent * rho ** GAMMA
        temp = p / (rho * R_AIR)
        pr = P_AMB / p
        if pr <= crit:   # choked
            mdot = a * p * np.sqrt(GAMMA / (R_AIR * temp)) * (2 / (GAMMA + 1)) ** ((GAMMA + 1) / (2 * (GAMMA - 1)))
        elif pr < 1.0:
            mdot = a * p * np.sqrt(2 * GAMMA / ((GAMMA - 1) * R_AIR * temp) * (pr ** (2 / GAMMA) - pr ** ((GAMMA + 1) / GAMMA)))
        else:
            mdot = 0.0
        u = np.sqrt(max(0.0, 2 * GAMMA / (GAMMA - 1) * R_AIR * temp * (1 - min(1.0, pr) ** ((GAMMA - 1) / GAMMA))))
        out["t"][i], out["p"][i], out["mdot"][i], out["u"][i] = i * dt, p, mdot, u
        m = max(m - mdot * dt, P_AMB * v / (R_AIR * temp) * 0.999)
    return out


def _jet_noise(rng, n: int, t_s: np.ndarray, amp: np.ndarray, fpeak: np.ndarray) -> np.ndarray:
    """Noise whose short-time spectrum follows a jet-noise similarity shape around fpeak(t)
    (log-normal-ish: -24 dB/decade^2 below the peak, -14 dB/decade^2 above), scaled by amp(t)."""
    nper = 1024
    hop = nper // 4
    w = rng.standard_normal(n + nper)
    f, tt, z = signal.stft(w, FS, nperseg=nper, noverlap=nper - hop)
    a_t = np.interp(tt, t_s, amp, right=0.0)
    fp_t = np.interp(tt, t_s, fpeak, right=fpeak[-1])
    lf = np.log10(np.maximum(f, 20.0))[:, None] - np.log10(fp_t)[None, :]
    k = np.where(lf < 0, 24.0, 14.0)
    shape_db = -k * lf ** 2
    z *= 10 ** (shape_db / 20) * a_t[None, :]
    _, y = signal.istft(z, FS, nperseg=nper, noverlap=nper - hop)
    return y[:n]


def air_dryer_purge_v2(seed: int = 1791, volume_l: float = 2.0, d_mm: float = 8.0, p0_bar_g: float = 12.5,
                       regen_s: float = 6.0) -> np.ndarray:
    """Governor cut-out: purge valve snaps open, the dryer volume blows down (physical envelope),
    then the regeneration air trickles back out through the desiccant (quiet hiss)."""
    rng = np.random.default_rng(seed)
    bd = blowdown(volume_l, p0_bar_g, d_mm, seconds=1.6)
    n = int((1.6 + regen_s) * FS)
    t = np.arange(n) / FS
    # Lighthill-like scaling: acoustic power ~ mdot * U^5 (amplitude = sqrt), relative to the start
    pw = bd["mdot"] * np.maximum(bd["u"], 1.0) ** 5
    amp = np.sqrt(pw / pw[0])
    d_j = d_mm * 1e-3 * np.maximum(1.0, (bd["p"] / P_AMB)) ** 0.25    # rough fully-expanded jet diameter
    fpk = np.clip(0.2 * bd["u"] / d_j, 900.0, 9000.0)
    jet = _jet_noise(rng, n, bd["t"], amp, fpk)
    jet /= np.max(np.abs(jet)) + 1e-12
    # regeneration: small orifice (~1.5 mm) from the regeneration volume, slow decay, much quieter
    reg_env = np.clip((t - 0.35) / 0.4, 0, 1) * np.exp(-np.maximum(t - 0.75, 0) / (regen_s / 3.0))
    reg = _jet_noise(rng, n, t, reg_env, np.full(n, 5200.0))
    reg /= np.max(np.abs(reg)) + 1e-12
    # purge valve piston snap + silencer body knock
    snap = _modes(n, 0.0, [(95.0, 0.05, 0.9), (610.0, 0.012, 0.45), (2100.0, 0.003, 0.25)], rng, 0.02)
    x = jet + 0.045 * reg + 0.55 * snap
    x = signal.sosfilt(chain(hp(40.0), highshelf(7000.0, -4.0)), x)   # purge silencer (sintered insert)
    return _finish(x, 0.6)


def air_dryer_purge_v2b(seed: int = 1792) -> np.ndarray:
    """Variant: smaller purge volume / orifice (shorter, a bit higher), no repetition between cycles."""
    return air_dryer_purge_v2(seed=seed, volume_l=1.6, d_mm=7.0, p0_bar_g=12.3, regen_s=5.0)


# --------------------------------------------------------------------------- registry
#  name: (function, is_loop, cab profile)
LAYERS = {
    "retarder_tone_loop": (retarder_tone_loop, True, "mech"),
    "retarder_flow_loop": (retarder_flow_loop, True, "mech"),
    "ebrake_engage": (ebrake_engage, False, "mech"),
    "ebrake_release": (ebrake_release, False, "mech"),
    "amt_disengage": (amt_disengage, False, "mech"),
    "amt_engage": (amt_engage, False, "mech"),
    "amt_engage_b": (lambda: amt_engage(seed=1784, rattle=2), False, "mech"),
    "amt_clutch_chuff": (amt_clutch_chuff, False, "pneu"),
    "air_dryer_purge_v2": (air_dryer_purge_v2, False, "pneu"),
    "air_dryer_purge_v2b": (air_dryer_purge_v2b, False, "pneu"),
}


def cab_name(name: str, is_loop: bool) -> str:
    return name.replace("_loop", "_cab_loop") if is_loop else name + "_cab"


if __name__ == "__main__":
    import soundfile as sf
    from pathlib import Path
    out = Path(__file__).resolve().parents[2] / "artifacts" / "audio-synth-0176" / "raw"
    out.mkdir(parents=True, exist_ok=True)
    for name, (fn, is_loop, prof) in LAYERS.items():
        x = fn()
        sf.write(out / f"{name}.wav", (x * 0.89).astype(np.float32), FS, subtype="PCM_16")
        print(f"{name}: {len(x) / FS:.2f} s, peak {dsp.db(np.max(np.abs(x))):.1f} dBFS, rms {dsp.db(dsp.rms(x)):.1f} dBFS")
    bd = blowdown(2.0, 12.5, 8.0)
    i = np.argmax(bd["p"] < P_AMB * 1.05)
    print(f"blowdown 2.0 L @12.5 bar, 8 mm: p<1.05 atm after {bd['t'][i]:.3f} s, mdot0 {bd['mdot'][0]:.3f} kg/s, U0 {bd['u'][0]:.0f} m/s")
    print(f"retarder: rotor {rotor_hz():.2f} Hz, BPF {blade_pass_hz():.1f} Hz at {REF_SHAFT_RPM:.0f} rpm shaft")
