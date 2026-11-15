"""ADR 0232: synthesis model 0232 (engine layers, turbo, pneumatics) and the telemetry behind the A/B scenes.

Everything is synthesised inside the test process; the only repository files read are the vehicle
definition JSONs (physics parameters) and the committed physics telemetry CSVs.
"""

import numpy as np
import pytest

import analyze
import dsp
import engine_synth as eng
import physics_params as pp
import render_ab0232 as ab
import render_all
import runtime_sim as rs
import synth0176 as s76
import synth0232 as s32
import telemetry0232 as tel
from el_analyze import lufs
from synth_helpers import FS

LOADS = (0.0, 0.4, 1.0)


@pytest.fixture(scope="module")
def loops():
    """2 s loops of both models: rpm x load, both perspectives."""
    out = {}
    for model in eng.MODELS:
        for rpm in (600, 1000, 1300, 1800, 2100):
            for load in LOADS:
                out[model, rpm, load], _ = eng.render_loop(rpm, load, target_s=2.0, model=model)
    return out


def band_db(x: np.ndarray, lo: float, hi: float) -> float:
    p = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / FS)
    return 10 * np.log10(p[(f >= lo) & (f < hi)].sum() + 1e-30)


def order_db(x: np.ndarray, rpm_exact: float, order: float) -> float:
    spec = np.abs(np.fft.rfft(x))
    k = int(round(order * rpm_exact / 60.0 * len(x) / FS))
    return 20 * np.log10(spec[k - 1:k + 2].max() + 1e-30)


# --------------------------------------------------------------------------- determinism
def test_model_0232_is_deterministic():
    a, _ = eng.render_loop(1500, 0.4, target_s=2.0, model="0232")
    b, _ = eng.render_loop(1500, 0.4, target_s=2.0, model="0232")
    assert np.array_equal(a["ext"], b["ext"]) and np.array_equal(a["cab"], b["cab"])


@pytest.mark.parametrize("name", sorted(s32.LAYERS))
def test_sfx_0232_is_deterministic(name):
    fn, _ = s32.LAYERS[name]
    assert np.array_equal(fn(), fn())


def test_main_model_is_unchanged():
    """model="main" must stay the synthesis of origin/main (A side of the A/B): values recorded from the
    main bank, whose 198 WAV files this branch reproduces bit for bit (docs/adr/0232)."""
    ref = {
        (1500, 1.0, False): {"ext": (0.1911237737748566, 0.07869792855807403), "cab": (0.11399285538991065, 0.0834769402507405)},
        (900, 0.0, False): {"ext": (0.03260906617471406, -0.01421426766825857), "cab": (0.023694587889457545, -0.017334786280646216)},
        (1800, 0.0, True): {"ext": (0.17044783172771338, -0.022631962218636534), "cab": (0.09260186634393254, -0.0030637700709517904)},
    }
    for (rpm, load, brake), want in ref.items():
        got, _ = eng.render_loop(rpm, load, engine_brake=brake, target_s=2.0, seed=7, model="main")
        for p, (rms, sample) in want.items():
            assert dsp.rms(got[p]) == pytest.approx(rms, rel=1e-9)
            assert got[p][1234] == pytest.approx(sample, rel=1e-7, abs=1e-12)


def test_unknown_model_is_rejected():
    with pytest.raises(ValueError):
        eng.render_loop(1300, 1.0, target_s=1.0, model="nope")


# --------------------------------------------------------------------------- clipping / levels
def test_bank_gain_keeps_reference_loudness_without_clipping():
    """0232 bank: the reference cell (full load, 1300 rpm) is as loud as in the main bank, peaks stay under the ceiling."""
    cells = [("engine", 2100, "on", 1.0), ("engine", 1300, "on", 1.0), ("engine", 600, "off", 0.0), ("ebrake", 2100, None, 0.0)]
    results = [render_all._job((kind, rpm, layer, load, "0232")) for kind, rpm, layer, load in cells]
    gains, info = render_all.bank_gains(results, "0232")
    ref_main, _ = eng.render_loop(1300, 1.0, model="main")
    ref_new = next(r for r in results if r[1] == 1300)[3]
    for p in render_all.PERSPECTIVES:
        assert gains[p] > 0
        peak_db = max(dsp.db(np.max(np.abs(r[3][p])) * gains[p]) for r in results)
        assert peak_db <= render_all.BANK_PEAK_CEILING_DBFS + 1e-6, (p, peak_db)
        if info[p]["limited_by_peak_db"] == 0.0:
            want = lufs(ref_main[p] * 10 ** (render_all.MAIN_BANK_GAIN_DB[p] / 20), FS)
            assert lufs(ref_new[p] * gains[p], FS) == pytest.approx(want, abs=0.05)


@pytest.mark.parametrize("name", sorted(s32.LAYERS))
def test_sfx_0232_is_finite_and_normalised(name):
    fn, is_loop = s32.LAYERS[name]
    x = fn()
    assert np.all(np.isfinite(x))
    if not is_loop:   # one-shots: unit peak, silent edges (no click when PlayOneShot starts or ends them)
        assert np.max(np.abs(x)) == pytest.approx(1.0, abs=1e-9)
        assert abs(x[0]) < 1e-6 and abs(x[-1]) < 1e-6
        tail = dsp.rms(x[-int(0.02 * FS):])
        assert dsp.db(tail) < -50.0


def test_sfx_0232_loudness_close_to_the_layer_it_replaces():
    """render_all scales each replacement to the LUFS of the main layer; a crestier one-shot may end lower
    (peak ceiling), never by more than 3 LU."""
    import sfx_synth as sx

    def norm(x, is_loop):
        return x * (10 ** ((-6.0 if is_loop else -1.0) / 20) / np.max(np.abs(x)))

    for name, (fn, is_loop) in s32.LAYERS.items():
        main = norm(getattr(sx, name)(), is_loop)
        new = norm(fn(), is_loop)
        new = new * 10 ** ((lufs(main, FS) - lufs(new, FS)) / 20)
        peak = np.max(np.abs(new))
        ceiling = 10 ** (-1.0 / 20)
        if peak > ceiling:
            new = new * ceiling / peak
        assert -3.0 <= lufs(new, FS) - lufs(main, FS) <= 0.05, name


@pytest.mark.parametrize("model", eng.MODELS)
@pytest.mark.parametrize("persp", ["ext", "cab"])
def test_loudness_rises_with_load(loops, model, persp):
    for rpm in (600, 1000, 1300, 1800, 2100):
        levels = [lufs(loops[model, rpm, load][persp], FS) for load in LOADS]
        assert levels[0] < levels[1] < levels[2], (model, rpm, persp, levels)
        assert 6.0 < levels[2] - levels[0] < 18.0, (model, rpm, persp, levels)   # overrun -> full load span [LU]


@pytest.mark.parametrize("persp", ["ext", "cab"])
def test_full_load_loudness_rises_with_rpm(loops, persp):
    levels = [lufs(loops["0232", rpm, 1.0][persp], FS) for rpm in (600, 1000, 1300, 1800, 2100)]
    assert all(b > a for a, b in zip(levels, levels[1:])), levels


def test_part_load_and_overrun_keep_the_main_loudness(loops):
    """0232 changes the character of the layers, not the mix: every cell within 3 LU of the main bank
    (the idle cell, which gains the governor's combustion, and the reference-cell gain included)."""
    for (model, rpm, load), lp in loops.items():
        if model != "0232":
            continue
        for p in ("ext", "cab"):
            d = lufs(lp[p], FS) - lufs(loops["main", rpm, load][p], FS)
            assert abs(d) < 3.0, (rpm, load, p, d)


# --------------------------------------------------------------------------- timbre vs load, firing orders
def test_firing_order_3_dominates(loops):
    """Inline six, four-stroke: 3 firings per revolution; orders 3, 6, 9 over the half orders of the 720 deg cycle."""
    for rpm in (1000, 1300, 1800):
        for load in LOADS:
            geo = eng.loop_geometry(rpm, 2.0)
            x = loops["0232", rpm, load]["ext"]
            o3 = order_db(x, geo.rpm_exact, 3.0)
            for half in (0.5, 1.0, 1.5, 2.5, 4.5):
                assert o3 - order_db(x, geo.rpm_exact, half) > 10.0, (rpm, load, half)
            assert o3 - order_db(x, geo.rpm_exact, 6.0) < 15.0, (rpm, load)   # order 6 present


def test_load_changes_the_harmonic_tilt_in_0232_only(loops):
    """Under load the blow-down front is steeper: order 9 gains on order 3. On main the three layers only
    differed in level for these orders."""
    for rpm in (1300, 1800):
        geo = eng.loop_geometry(rpm, 2.0)

        def tilt(model, load):
            x = loops[model, rpm, load]["ext"]
            return order_db(x, geo.rpm_exact, 9.0) - order_db(x, geo.rpm_exact, 3.0)

        new = [tilt("0232", load) for load in LOADS]
        assert new[0] < new[1] < new[2], (rpm, new)
        assert new[2] - new[0] > 2.5, (rpm, new)
        old = [tilt("main", load) for load in LOADS]
        assert abs(old[2] - old[0]) < 1.5, (rpm, old)


def test_brightness_rises_with_load(loops):
    for rpm in (1300, 1800, 2100):
        b = [band_db(loops["0232", rpm, load]["ext"], 300, 1500) - band_db(loops["0232", rpm, load]["ext"], 20, 300)
             for load in LOADS]
        assert b[0] < b[1] < b[2], (rpm, b)


def test_idle_cell_carries_combustion(loops):
    """Load-0 cell at idle speed: the governor fuels (physics), so the 0232 cell has combustion clatter the
    main cell (fuel cut) lacks; above the governor span the cell is a true overrun again."""
    idle_new, idle_old = loops["0232", 600, 0.0]["ext"], loops["main", 600, 0.0]["ext"]
    gain = (band_db(idle_new, 300, 1500) - band_db(idle_new, 20, 300)) - (band_db(idle_old, 300, 1500) - band_db(idle_old, 20, 300))
    assert gain > 2.0, gain
    assert eng.idle_governor_fuel(600.0) == pytest.approx(float(pp.drag_torque(600.0) / pp.full_load_torque(600.0)))
    assert eng.idle_governor_fuel(750.0) == 0.0 and eng.idle_governor_fuel(1300.0) == 0.0


def test_engine_brake_level_follows_the_physics_torque_curve():
    rpms = np.arange(900, 2101, 100)
    levels = [eng.engine_brake_level(float(r)) for r in rpms]
    assert all(b >= a for a, b in zip(levels, levels[1:]))
    assert levels[-1] == pytest.approx(1.0)
    want = float(pp.engine_brake_extra(1500.0) / pp.engine_brake_extra(2100.0))
    assert eng.engine_brake_level(1500.0) == pytest.approx(want)
    a, _ = eng.render_loop(1000, 0.0, engine_brake=True, target_s=2.0, model="0232")
    b, _ = eng.render_loop(2000, 0.0, engine_brake=True, target_s=2.0, model="0232")
    assert lufs(b["ext"], FS) - lufs(a["ext"], FS) > 6.0


# --------------------------------------------------------------------------- phase continuity
@pytest.mark.parametrize("load", LOADS)
def test_loop_seam_is_continuous(loops, load):
    for rpm in (600, 1300, 2100):
        for p in ("ext", "cab"):
            m = analyze.seam_metrics(loops["0232", rpm, load][p])
            assert m["seam_ratio_d1"] < 1.0 and m["seam_ratio_d2"] < 1.0, (rpm, load, p, m)


def test_turbo_whistle_loop_is_periodic():
    x = s32.turbo_whistle_loop()
    m = analyze.seam_metrics(x)
    assert m["seam_ratio_d1"] < 1.0 and m["seam_ratio_d2"] < 1.0, m
    # blade-pass line at the runtime reference frequency (slow FM wander +-0.4 % included)
    spec = np.abs(np.fft.rfft(x))
    k = int(np.argmax(spec))
    assert abs(k * FS / len(x) - s32.TURBO_REF_HZ) < 0.005 * s32.TURBO_REF_HZ


def test_turbo_whistle_is_less_tonal_than_main():
    import sfx_synth as sx

    def tone_over_noise(x):
        f = np.fft.rfftfreq(len(x), 1 / FS)
        p = np.abs(np.fft.rfft(x)) ** 2
        tone = p[(f > 3150) & (f < 3250)].sum()
        noise = p[(f > 1000) & (f < 9000)].sum() - tone
        return 10 * np.log10(tone / noise)

    assert tone_over_noise(s32.turbo_whistle_loop()) < tone_over_noise(sx.turbo_whistle_loop()) - 3.0


def test_crossfade_sweep_has_no_phase_jump():
    """rpm x load sweep through the runtime mirror on 0232 loops: voices start crank-phase aligned, so the
    largest sample step of the sweep stays in the range of the loops themselves (no splice click)."""
    rpms, loads = [1000.0, 1300.0, 1600.0], [0.0, 1.0]
    clips, max_step = [], 0.0
    for load in loads:
        for rpm in rpms:
            lp, geo = eng.render_loop(rpm, load, target_s=2.0, model="0232")
            clips.append(rs.Clip(lp["ext"], geo.rpm_exact, geo.n_cycles))
            max_step = max(max_step, float(np.max(np.abs(np.diff(lp["ext"])))))
    grid = rs.LayerGrid(rpms, loads, clips, pool=6)
    frame = int(FS / rs.FRAME_HZ)
    out = []
    n_frames = 240
    for k in range(n_frames):
        u = k / (n_frames - 1)
        grid.update(1000.0 + 600.0 * u, 0.5 - 0.5 * np.cos(4 * np.pi * u), 1.0)
        out.append(grid.render(frame, FS))
    x = np.concatenate(out)
    assert np.max(np.abs(np.diff(x))) < 1.6 * max_step
    assert np.max(np.abs(x)) <= 1.3 * max(np.max(np.abs(c.data)) for c in clips)


# --------------------------------------------------------------------------- pneumatics / turbo physics
def test_discharge_times_follow_volume_and_orifice():
    def t_half(volume, d):
        bd = s76.blowdown(volume, s32.chamber_pressure_bar(), d, seconds=3.0)
        gauge = bd["p"] - s76.P_AMB
        return float(bd["t"][np.argmax(gauge < 0.5 * gauge[0])])

    assert t_half(s32.REAR_CHAMBERS_L, s32.SERVICE_EXHAUST_MM) > t_half(s32.FRONT_CHAMBERS_L, s32.SERVICE_EXHAUST_MM)
    assert t_half(s32.SPRING_CHAMBERS_L, s32.SPRING_EXHAUST_MM) > t_half(s32.REAR_CHAMBERS_L, s32.SERVICE_EXHAUST_MM)
    assert 0.2 < s32.spring_clunk_time() < 1.0


def test_liftoff_chirp_follows_the_boost_time_constant():
    """Spool-down: the whistle line of the one-shot falls like the runtime whistle pitch law driven by Engine.Boost."""
    x = s32.turbo_liftoff(seed=1)
    tau = float(pp.engine()["boostTimeConstant"])
    for t0 in (0.1, 0.3):
        n = int(0.04 * FS)
        i0 = int(t0 * FS)
        seg = x[i0:i0 + n] * np.hanning(n)
        spec = np.abs(np.fft.rfft(seg, 1 << 16))
        f = np.fft.rfftfreq(1 << 16, 1 / FS)
        want = s32.TURBO_REF_HZ * (s32.TURBO_PITCH_BASE + s32.TURBO_PITCH_RANGE * np.exp(-(t0 + 0.02) / tau))
        band = (f > want - 250) & (f < want + 250)
        assert spec[band].max() > 2.0 * np.median(spec[(f > 1500) & (f < 6000)]), (t0, want)


# --------------------------------------------------------------------------- telemetry
@pytest.mark.parametrize("scene", [s.name for s in tel.SCENES])
def test_telemetry_is_physical(scene):
    f = tel.load(scene)
    assert 15.0 <= len(f) * tel.DT <= 30.0
    assert np.all((f.load >= 0) & (f.load <= 1)) and np.all((f.boost >= 0) & (f.boost <= 1))
    assert f.rpm.min() > float(pp.engine()["stallRpm"]) and f.rpm.max() <= float(pp.engine()["maxRpm"])
    neutral = f.amt == tel.AMT_NEUTRAL
    if neutral.any():   # torque interruption: no fuel while the gearbox is in neutral
        assert f.load[neutral].max() < 0.05
    assert np.all(f.engine_brake[np.isin(f.amt, tel.SHIFT_STATES)] == 0.0)


def test_upshift_drops_the_engine_speed():
    f = tel.load("1_ruszanie_40t")
    starts = np.nonzero((f.amt[1:] == tel.AMT_TORQUE_RAMP) & (f.amt[:-1] != tel.AMT_TORQUE_RAMP))[0] + 1
    ends = np.nonzero((f.amt[:-1] == tel.AMT_ENGAGE) & ~np.isin(f.amt[1:], tel.SHIFT_STATES))[0] + 1
    assert len(starts) >= 4 and len(starts) == len(ends)
    ratios = pp.gearbox()["forwardRatios"]
    for a, b in zip(starts, ends):
        g0, g1 = int(f.gear[a - 1]), int(f.gear[b])
        assert g1 > g0
        assert f.rpm[b] / f.rpm[a] == pytest.approx(ratios[g1 - 1] / ratios[g0 - 1], rel=0.12)


def test_runtime_detectors_fire_on_the_telemetry():
    """DrivelineSfx mirror: one engage per gear change; the engine-brake flap closes once on the descent (its
    release coincides with an up-shift there, which the game's detector deliberately keeps silent)."""
    f = tel.load("1_ruszanie_40t")
    d = ab.DrivelineSfx()
    ev = [d.step(int(a), float(s), bool(c)) for a, s, c in zip(f.amt, f.ebrake_state, f.ebrake_cmd)]
    shifts = int(np.sum((f.amt[1:] == tel.AMT_ENGAGE) & (f.amt[:-1] != tel.AMT_ENGAGE)))
    assert sum(1 for e in ev if e & d.ENGAGE) == shifts
    assert sum(1 for e in ev if e & d.DISENGAGE) == shifts
    assert not any(e & (d.EB_ENGAGE | d.EB_RELEASE) for e in ev)   # upshift sync brake must not fire the flap events
    f = tel.load("3_zjazd_hamulce_dlugotrwale")
    d = ab.DrivelineSfx()
    ev = [d.step(int(a), float(s), bool(c)) for a, s, c in zip(f.amt, f.ebrake_state, f.ebrake_cmd)]
    assert sum(1 for e in ev if e & d.EB_ENGAGE) == 1


def test_standstill_scene_contains_the_governor_cut_out():
    f = tel.load("4_postoj_pneumatyka")
    cut = np.nonzero(f.compressor[:-1] & ~f.compressor[1:])[0]
    assert len(cut) == 1
    assert f.air_supply[cut[0]] == pytest.approx(float(pp.vehicle()["air"]["cutOutBar"]), abs=0.05)
    assert f.park[0] and (~f.park).any() and f.park[-1]
