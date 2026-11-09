"""Firing-order synthesis of a fictional modern EU ~13 l inline-six 4-stroke diesel.

Physical skeleton (all values are WORKING_VALUE design choices, not measurements of any
real engine):
  * 4-stroke R6, firing order 1-5-3-6-2-4, one firing every 120 deg crank angle (CA)
    -> 3 firings per crank revolution -> firing frequency f_fire = rpm / 20 Hz.
  * One engine cycle = 720 deg CA = 2 revolutions -> cycle frequency rpm / 120 Hz.
    Cylinder-to-cylinder differences put energy on these "half orders", which is what
    makes a big diesel sound lumpy instead of like a pure buzz.

Sources (each built periodic over the loop, see dsp.periodic_sosfilt):
  exhaust blowdown pulses  -> exhaust pipe/muffler resonances    (the body / growl)
  exhaust gas turbulence   -> noise amplitude-modulated by the blowdown pulses (breath)
  combustion pressure rise -> engine block structural modes      (diesel clatter / knock)
  low-frequency gas torque -> structure-borne drone in the cab    (cab boom)
  mechanics                -> timing-gear whine, valve-train and injector ticks
  intake                   -> band-limited intake roar, scaled with boost and rpm
  engine brake             -> compression-release "bark" pulses at TDC + raspy turbulence

Two listener perspectives are rendered from the same sources: ``ext`` (outside, a few
metres from the tractor) and ``cab`` (interior: transmission loss low-pass, cab boom).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

import dsp
from dsp import FS, bp, chain, highshelf, hp, lp, peak, periodic_sosfilt

FIRING_ORDER = (1, 5, 3, 6, 2, 4)
ENGINE_SEED = 13_062  # fixed engine "personality": identical across every loop of the set
RPM_MAX = 2100.0
LOOP_ORIGIN_DEG = 60.0  # crank angle of loop sample 0 is -60 deg rel. cyl-1 firing TDC


# --------------------------------------------------------------------------- engine personality
@dataclass(frozen=True)
class Personality:
    amp_bias: np.ndarray      # per cylinder (index = cylinder number - 1)
    timing_bias_deg: np.ndarray
    width_bias: np.ndarray
    exh_delay_ms: np.ndarray  # front bank (1-3) vs rear bank (4-6) manifold runner lengths
    clatter_bias: np.ndarray


def make_personality(seed: int = ENGINE_SEED) -> Personality:
    rng = np.random.default_rng(seed)
    return Personality(
        amp_bias=1.0 + rng.normal(0.0, 0.08, 6),
        timing_bias_deg=rng.normal(0.0, 1.2, 6),
        width_bias=1.0 + rng.normal(0.0, 0.08, 6),
        exh_delay_ms=np.array([0.05, 0.12, 0.20, 0.32, 0.40, 0.47]) + rng.normal(0, 0.02, 6),
        clatter_bias=1.0 + rng.normal(0.0, 0.18, 6),
    )


PERSONALITY = make_personality()


# --------------------------------------------------------------------------- loop geometry
@dataclass(frozen=True)
class LoopGeometry:
    rpm_nominal: float
    n_cycles: int       # whole engine cycles (720 deg) in the loop
    n_samples: int
    rpm_exact: float    # rpm that makes n_cycles fit n_samples exactly

    @property
    def seconds(self) -> float:
        return self.n_samples / FS

    @property
    def samples_per_cycle(self) -> float:
        return self.n_samples / self.n_cycles


def loop_geometry(rpm: float, target_s: float = 4.0) -> LoopGeometry:
    n_cycles = max(4, int(round(target_s * rpm / 120.0)))
    n_samples = int(round(n_cycles * 120.0 / rpm * FS))
    rpm_exact = n_cycles * 120.0 * FS / n_samples
    return LoopGeometry(rpm, n_cycles, n_samples, rpm_exact)


# --------------------------------------------------------------------------- kernels
def _deg_s(rpm: float) -> float:
    """Seconds per crank degree."""
    return 1.0 / (6.0 * rpm)


def k_blowdown(tau_r: float, tau_d: float, crack: float):
    """Exhaust blowdown pulse: fast valve-opening rise, CA-scaled decay, + a sharp crack."""
    def f(t):
        t = np.maximum(t, 0.0)
        body = (1.0 - np.exp(-t / tau_r)) * np.exp(-t / tau_d)
        snap = np.exp(-t / 0.00025) * (1.0 - np.exp(-t / 0.00004))
        return body + crack * snap
    return f


def k_alpha(tau_r: float, tau_d: float):
    def f(t):
        t = np.maximum(t, 0.0)
        return (1.0 - np.exp(-t / tau_r)) * np.exp(-t / tau_d)
    return f


def k_click(f0: float, tau: float):
    def f(t):
        t = np.maximum(t, 0.0)
        return np.sin(2 * np.pi * f0 * t) * np.exp(-t / tau) * (t > 0)
    return f


# --------------------------------------------------------------------------- crank timeline
class Crank:
    """Cumulative crank-cycle angle (deg) per sample, with periodic speed wobble."""

    def __init__(self, geo: LoopGeometry, rng: np.random.Generator, wobble_deg: float):
        self.geo = geo
        n = geo.n_samples
        span = 720.0 * geo.n_cycles
        i = np.arange(n + 1)
        max_c = max(1, int(1.6 * geo.seconds))  # governor / load hunting < ~1.6 Hz
        w = dsp.smooth_random_periodic(rng, n, max_c, n_terms=4)
        w = np.append(w, w[0])
        self.theta = span * i / n + wobble_deg * w
        self.span = span

    def sample_of(self, angle_deg: float) -> float:
        lo, hi = self.theta[0], self.theta[-1]
        a = angle_deg
        while a < lo:
            a += self.span
        while a >= hi:
            a -= self.span
        return float(np.interp(a, self.theta, np.arange(len(self.theta))))

    def revs(self) -> np.ndarray:
        return self.theta[:-1] / 360.0


# --------------------------------------------------------------------------- operating point
@dataclass
class OperatingPoint:
    rpm: float
    load: float               # 0 = motoring/overrun (no fuel), 1 = full load
    engine_brake: bool = False

    @property
    def fuel(self) -> float:
        return 0.0 if self.engine_brake else self.load

    @property
    def boost(self) -> float:
        """Steady-state boost fraction (0..1) used for intake/flow scaling."""
        spool = np.clip((self.rpm - 750.0) / 650.0, 0.15, 1.0)
        return float(self.fuel * spool)


@dataclass
class Sources:
    exhaust: np.ndarray          # exhaust-system output, exterior (already through pipe/muffler)
    exhaust_raw: np.ndarray      # pre-muffler (pulses + turbulence), used for the cab path
    block: np.ndarray            # structure-radiated combustion/clatter
    drone: np.ndarray            # low-frequency gas-torque structure-borne component
    mech: np.ndarray
    intake: np.ndarray
    meta: dict = field(default_factory=dict)


# Exterior exhaust system: tail-pipe / pipe quarter- and half-wave resonances + muffler.
EXH_EXT = chain(
    hp(24.0, 0.7),
    peak(58.0, 1.8, 3.0),     # muffler shell / tail-pipe low mode
    peak(104.0, 3.5, 5.0),    # down-pipe half-wave (~2.6 m hot gas)
    peak(212.0, 4.5, 3.5),
    peak(330.0, 5.0, 2.0),
    peak(520.0, 4.0, -3.0),   # expansion-chamber TL dip
    lp(1150.0, 0.62),
    lp(2600.0, 0.7),
)

# Engine block structural modes: (Hz, Q, gain)
BLOCK_MODES = (
    (190.0, 4.0, 0.55), (470.0, 5.0, 0.60), (880.0, 7.0, 0.85), (1320.0, 9.0, 1.00),
    (1840.0, 11.0, 0.90), (2550.0, 12.0, 0.70), (3350.0, 14.0, 0.50), (4600.0, 14.0, 0.30),
)

# Cab: airborne transmission loss + cab-air boom + panel mode.
CAB_AIR = chain(
    hp(22.0, 0.7),
    lp(330.0, 0.75),
    lp(650.0, 0.6),
    peak(40.0, 1.6, 4.0),
    peak(128.0, 3.0, 3.0),
)
CAB_RASP = chain(hp(450.0, 0.7), lp(2400.0, 0.7))
CAB_STRUCT = chain(hp(22.0, 0.8), lp(150.0, 0.8), peak(40.0, 1.6, 4.0))
CAB_BLOCK = chain(lp(650.0, 0.7), highshelf(1500.0, -14.0))
CAB_MECH = chain(lp(1800.0, 0.7))
CAB_INTAKE = chain(lp(700.0, 0.7))


def _bank(x: np.ndarray, modes) -> np.ndarray:
    out = np.zeros_like(x)
    for f0, q, g in modes:
        out += g * periodic_sosfilt(x, chain(bp(f0, q)))
    return out


def render_sources(op: OperatingPoint, geo: LoopGeometry, seed: int) -> Sources:
    rng = np.random.default_rng(seed)
    p = PERSONALITY
    n = geo.n_samples
    rpm = geo.rpm_exact
    ds = _deg_s(rpm)
    rpm_n = rpm / RPM_MAX
    fuel = op.fuel
    idle_ness = float(np.clip((900.0 - rpm) / 300.0, 0.0, 1.0))

    # Irregularity: larger at idle and at light load (governor hunting, injection spread).
    wobble_deg = 1.0 + 4.5 * idle_ness
    crank = Crank(geo, rng, wobble_deg)
    amp_jit = 0.03 + 0.06 * idle_ness + (0.02 if fuel == 0 else 0.0)
    time_jit_deg = 0.25 + 0.5 * idle_ness

    exh = np.zeros(n)
    comb_p = np.zeros(n)     # pressure bump (low-frequency, for drone)
    knock = np.zeros(n)      # sharp pressure-rise excitation (for block modes)
    inj = np.zeros(n)
    valves = np.zeros(n)
    intake_env = np.zeros(n)

    # --- amplitude laws (WORKING_VALUE) ---
    flow = (0.25 + 0.75 * fuel ** 0.75) * (0.4 + 0.6 * rpm_n) ** 1.3
    comb_amp = (0.15 + 0.85 * fuel) if fuel > 0 else 0.12        # motoring: compression only
    clatter = (0.55 + 0.30 * fuel) * (1.0 + 0.5 * idle_ness) if fuel > 0 else 0.0
    if op.engine_brake:
        flow = 0.10 * (0.55 + 0.45 * rpm_n)

    tau_r = max(0.00045, 7.0 * ds)
    crack = 0.18 + 0.25 * fuel
    blow_len = int(min(n, max(0.012, 6 * 42.0 * ds) * FS))
    comb_len = int(min(n, max(0.02, 6 * 30.0 * ds) * FS))
    knock_len = int(0.004 * FS)
    click_len = int(0.002 * FS)
    jake = np.zeros(n)

    for cyc in range(geo.n_cycles):
        for slot, cyl in enumerate(FIRING_ORDER):
            c = cyl - 1
            # loop sample 0 sits LOOP_ORIGIN_DEG before cylinder-1 firing TDC (quiet part of the
            # cycle, so no sharp event lands on the seam; shared by all clips for phase alignment)
            tdc = (LOOP_ORIGIN_DEG + 720.0 * cyc + 120.0 * slot + p.timing_bias_deg[c]
                   + rng.normal(0, time_jit_deg))
            a_rand = 1.0 + rng.normal(0.0, amp_jit)
            # exhaust valve opens ~130 deg after firing TDC
            t_ex = crank.sample_of(tdc + 130.0) + p.exh_delay_ms[c] * 1e-3 * FS
            tau_d = 40.0 * ds * p.width_bias[c] * (1.0 + rng.normal(0.0, 0.06))
            dsp.add_kernel_circular(exh, t_ex, k_blowdown(tau_r, tau_d, crack), blow_len,
                                    flow * p.amp_bias[c] * a_rand)
            # combustion (start of injection ~ 4 deg BTDC, premixed burn just after TDC)
            t_c = crank.sample_of(tdc + 2.0)
            if fuel > 0:
                dsp.add_kernel_circular(comb_p, t_c, k_alpha(6.0 * ds, 22.0 * ds), comb_len,
                                        comb_amp * p.amp_bias[c] * a_rand)
                kk = clatter * p.clatter_bias[c] * (1.0 + rng.normal(0, 0.15))
                dsp.add_kernel_circular(knock, t_c, k_alpha(0.00004, 0.0003), knock_len, kk)
                t_inj = crank.sample_of(tdc - 6.0)
                dsp.add_kernel_circular(inj, t_inj, k_click(6800.0, 0.00018), click_len,
                                        0.35 * (1.0 + rng.normal(0, 0.1)))
            else:
                # motoring compression/expansion: smooth, symmetric-ish bump
                dsp.add_kernel_circular(comb_p, crank.sample_of(tdc - 25.0),
                                        k_alpha(20.0 * ds, 25.0 * ds), comb_len, comb_amp)
            if op.engine_brake:
                # compression release just before TDC: very sharp, high-energy blow-down
                t_j = crank.sample_of(tdc - 4.0) + p.exh_delay_ms[c] * 1e-3 * FS
                ja = (0.35 + 0.65 * rpm_n) ** 1.2 * p.amp_bias[c] * (1.0 + rng.normal(0, 0.05))
                dsp.add_kernel_circular(jake, t_j, k_blowdown(0.00012, 11.0 * ds * p.width_bias[c], 0.6),
                                        blow_len, ja)
                dsp.add_kernel_circular(comb_p, crank.sample_of(tdc - 20.0),
                                        k_alpha(14.0 * ds, 18.0 * ds), comb_len, 0.5)
            # valve train: exhaust + intake opening/closing ticks (light)
            for off in (130.0, 370.0, 345.0, 590.0):
                dsp.add_kernel_circular(valves, crank.sample_of(tdc + off), k_click(3900.0, 0.00025),
                                        click_len, 0.12 * (1.0 + rng.normal(0, 0.25)))
            # intake stroke envelope (opens ~360 deg after firing TDC)
            dsp.add_kernel_circular(intake_env, crank.sample_of(tdc + 360.0),
                                    k_alpha(20.0 * ds, 60.0 * ds), comb_len, 1.0)

    # --- exhaust turbulence: noise breathing with the blow-down pulses ---
    env_src = jake if op.engine_brake else exh
    env = np.clip(env_src / (np.max(env_src) + 1e-9), 0.0, None)
    noise = dsp.periodic_noise(rng, n)
    if op.engine_brake:
        turb_band = periodic_sosfilt(noise, chain(hp(160.0, 0.7), lp(5200.0, 0.7), peak(1700.0, 1.2, 4.0)))
        turb = turb_band * (0.04 + env ** 2.0) * 0.55 * (0.6 + 0.4 * rpm_n)
        raw = jake * 1.0 + turb
        raw = dsp.soft_clip(raw / (np.max(np.abs(raw)) + 1e-9), 1.4) * np.max(np.abs(raw))
    else:
        turb_band = periodic_sosfilt(noise, chain(hp(120.0, 0.7), lp(2800.0, 0.7)))
        turb = turb_band * (0.10 + env ** 1.3) * (0.25 + 0.55 * fuel) * flow
        raw = exh + turb

    exhaust_out = periodic_sosfilt(raw, EXH_EXT)

    # --- block radiation: clatter + pressure-rise excitation through structural modes ---
    dp = np.diff(comb_p, append=comb_p[:1]) * (0.002 / ds) * 0.02  # rate of pressure rise (scaled)
    block = _bank(knock + dp, BLOCK_MODES)
    block = periodic_sosfilt(block, chain(lp(6000.0, 0.7)))

    # --- drone: gas-torque fluctuation transmitted through mounts ---
    drone = periodic_sosfilt(comb_p, chain(hp(22.0, 0.8), lp(160.0, 0.8)))

    # --- mechanics ---
    revs = crank.revs()
    gear_amp = 0.0045 * (0.4 + 0.6 * rpm_n) * (0.6 + 0.4 * max(fuel, 0.3 if op.engine_brake else 0.0))
    gear = gear_amp * (np.sin(2 * np.pi * 38.0 * revs) * (1.0 + 0.3 * dsp.periodic_lfo(n, geo.n_cycles * 3))
                       + 0.35 * np.sin(2 * np.pi * 76.0 * revs + 0.7))
    mech_noise = periodic_sosfilt(dsp.periodic_noise(rng, n), chain(bp(420.0, 0.8))) * 0.004 * (0.3 + rpm_n)
    mech = gear + mech_noise + periodic_sosfilt(valves, chain(hp(1500.0))) * 0.6 + \
        periodic_sosfilt(inj, chain(hp(3000.0))) * (0.5 if fuel > 0 else 0.0)

    # --- intake roar ---
    in_noise = periodic_sosfilt(dsp.periodic_noise(rng, n), chain(hp(380.0, 0.7), lp(3200.0, 0.7),
                                                                   peak(900.0, 2.0, 3.0)))
    in_env = intake_env / (np.max(intake_env) + 1e-9)
    intake = in_noise * (0.55 + 0.45 * in_env) * 0.05 * (rpm_n ** 2) * (0.3 + 0.7 * op.boost)

    return Sources(exhaust=exhaust_out, exhaust_raw=raw, block=block, drone=drone, mech=mech,
                   intake=intake, meta={"wobble_deg": wobble_deg, "amp_jit": amp_jit})


# --------------------------------------------------------------------------- perspectives
MIX_EXT = {"exhaust": 1.00, "block": 0.30, "drone": 0.0, "mech": 1.0, "intake": 1.0}


def mix_ext(s: Sources) -> np.ndarray:
    return (MIX_EXT["exhaust"] * s.exhaust + MIX_EXT["block"] * s.block
            + MIX_EXT["mech"] * s.mech + MIX_EXT["intake"] * s.intake)


def mix_cab(s: Sources) -> np.ndarray:
    air = periodic_sosfilt(s.exhaust, CAB_AIR)
    struct = periodic_sosfilt(s.drone, CAB_STRUCT)
    blk = periodic_sosfilt(s.block, CAB_BLOCK)
    mech = periodic_sosfilt(s.mech, CAB_MECH)
    intake = periodic_sosfilt(s.intake, CAB_INTAKE)
    rasp = periodic_sosfilt(s.exhaust, CAB_RASP)  # exhaust rasp leaking through the rear wall
    return 0.55 * air + 0.020 * struct + 0.08 * blk + 0.45 * mech + 0.4 * intake + 0.05 * rasp


def render_loop(rpm: float, load: float, engine_brake: bool = False, target_s: float = 4.0,
                seed: int | None = None) -> tuple[dict[str, np.ndarray], LoopGeometry]:
    geo = loop_geometry(rpm, target_s)
    if seed is None:
        seed = int(rpm * 10 + load * 1000 + (7 if engine_brake else 0))
    op = OperatingPoint(geo.rpm_exact, load, engine_brake)
    s = render_sources(op, geo, seed)
    if engine_brake:
        # engine-brake layer holds only the brake-specific components (added on top of the
        # off-load layer at runtime), so drop mechanics/intake.
        s.mech = np.zeros_like(s.mech)
        s.intake = np.zeros_like(s.intake)
    return {"ext": mix_ext(s), "cab": mix_cab(s)}, geo
