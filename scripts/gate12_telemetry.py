"""Gates 1-2 phone analysis: reads the output of scripts/gate12-phone.ps1 (<out>/<serial>/<run>/telemetry/drive-*.csv
+ metrics.json) and writes <out>/gate12-summary.json and <out>/gate12-summary.md.

Checks (limits mirror the .NET runner scenarios, tests/physics/scenarios; WORKING_VALUE unless noted):
  park_*      drift of the tractor (x, z) from t0+5 s  <= 0.01 m (gate 1: "brak dryfu na postoju"), max speed <= 0.0036 km/h
  c*_*        max |dv| per physics step <= 0.35 m/s (no teleport / solver explosion, docs/04 s6.11), no NaN,
              speed hold after reaching the target: std <= 1.5 km/h, mean within +/-1.5 km/h of the target
  c50_solo_N  repeatability of time 0->30 km/h and 0->38 km/h over the three runs: max deviation from the mean <= 3 %
              (gate 1 asks 0->80 km/h x3 +/-3 %; the lab autopilot only drives circles, so this is a PROXY - label it so)
  c50_40t     max |articulation| in steady state, fifth wheel error max <= 5 mm (runner limit)
  s080_*      autopilot straight080 (ADR 0195): time 0->60 / 0->80 km/h from the throttle step, distance to 80, hold speed,
              stop distance 80->0 from the brake onset (first rising edge of brake_in), MFDD (UN R13 Annex 4, 0.8 v0..0.1 v0),
              max deceleration (0.1 s window), max |wheel slip| and wheel-lock time during the stop, lateral deviation in
              the stop; limits = the runner scenario tests/physics/scenarios/straight_0_80_0.json (same bands per preset)
  s080_solo_N repeatability of time 0->60 / 0->80 km/h over the three runs: max deviation from the mean <= 3 % (gate 1)
Frame metrics (p50/p95/p99, PSS, temperature) are copied from metrics.json; physics cost per step from step_us.

Usage: uv run --project tools/perf python scripts/gate12_telemetry.py artifacts/gate12/<ts>
"""
import csv
import glob
import json
import math
import os
import sys

import numpy as np

DV_LIMIT = 0.35
DRIFT_LIMIT = 0.01
REPEAT_LIMIT = 0.03
SPEED_STD_LIMIT = 1.5
FW_ERR_LIMIT = 5.0


def load_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    head = rows[0]
    data = {}
    for i, h in enumerate(head):
        col = []
        for r in rows[1:]:
            try:
                col.append(float(r[i]))
            except (ValueError, IndexError):
                col.append(float('nan'))
        data[h] = np.array(col)
    return data


def pct(a, q):
    a = a[np.isfinite(a)]
    return float(np.percentile(a, q)) if a.size else None


def fit_circle(x, z):
    a = np.c_[2 * x, 2 * z, np.ones_like(x)]
    b = x * x + z * z
    (cx, cz, c), *_ = np.linalg.lstsq(a, b, rcond=None)
    r = math.sqrt(max(c + cx * cx + cz * cz, 0.0))
    return cx, cz, r


def first_time(t, cond):
    idx = np.nonzero(cond)[0]
    return float(t[idx[0]]) if idx.size else None


def analyse_run(name, d, target_kmh):
    t = d['t']
    out = {'samples': int(t.size), 'span_s': float(t[-1] - t[0]) if t.size else 0.0}
    out['nan_detected'] = int(sum(int(np.isnan(d[k]).any()) for k in ('x', 'z', 'speed_kmh') if k in d))
    if 'step_us' in d:
        s = d['step_us']
        out['step_us'] = {'p50': pct(s, 50), 'p95': pct(s, 95), 'p99': pct(s, 99), 'max': float(np.nanmax(s))}
    if all(k in d for k in ('vel_x', 'vel_y', 'vel_z')):
        v = np.c_[d['vel_x'], d['vel_y'], d['vel_z']]
        dv = np.linalg.norm(np.diff(v, axis=0), axis=1)
        out['max_dv_step_ms'] = float(np.nanmax(dv)) if dv.size else 0.0
    checks = []
    if out.get('max_dv_step_ms') is not None:
        checks.append(('max_dv_step_ms', out['max_dv_step_ms'], f'<= {DV_LIMIT}', out['max_dv_step_ms'] <= DV_LIMIT))
    checks.append(('nan_detected', out['nan_detected'], '== 0', out['nan_detected'] == 0))
    if name.startswith('park'):
        m = t >= t[0] + 5
        x, z = d['x'][m], d['z'][m]
        drift = float(np.max(np.hypot(x - x[0], z - z[0]))) if x.size else None
        vmax = float(np.nanmax(np.abs(d['speed_kmh'][m]))) if x.size else None
        out.update(drift_m=drift, max_speed_kmh=vmax, parking_state_last=float(d['parking_state'][-1]) if 'parking_state' in d else None)
        checks.append(('drift_m', drift, f'<= {DRIFT_LIMIT}', drift is not None and drift <= DRIFT_LIMIT))
        checks.append(('max_speed_kmh', vmax, '<= 0.0036', vmax is not None and vmax <= 0.0036))
    else:
        sp = d['speed_kmh']
        t_move = first_time(t, sp > 0.5)
        t30 = first_time(t, sp >= 30) if target_kmh >= 30 else None
        tt = first_time(t, sp >= 0.95 * target_kmh)
        out.update(t_move_s=t_move, t_0_30_s=(t30 - t_move) if (t30 is not None and t_move is not None) else None,
                   t_0_target95_s=(tt - t_move) if (tt is not None and t_move is not None) else None, target_kmh=target_kmh)
        if tt is not None:
            m = t >= tt + 10
            if m.sum() > 100:
                out['speed_mean_kmh'] = float(np.nanmean(sp[m]))
                out['speed_std_kmh'] = float(np.nanstd(sp[m]))
                cx, cz, r = fit_circle(d['x'][m], d['z'][m])
                rr = np.hypot(d['x'][m] - cx, d['z'][m] - cz)
                out['path_radius_m'] = {'fit': r, 'std': float(np.std(rr)), 'min': float(rr.min()), 'max': float(rr.max())}
                checks.append(('speed_std_kmh', out['speed_std_kmh'], f'<= {SPEED_STD_LIMIT}', out['speed_std_kmh'] <= SPEED_STD_LIMIT))
                checks.append(('speed_mean_kmh', out['speed_mean_kmh'], f'{target_kmh} +/- 1.5', abs(out['speed_mean_kmh'] - target_kmh) <= 1.5))
                if 'articulation_deg' in d and 'coupled' in d and np.nanmax(d['coupled']) > 0.5:
                    a = d['articulation_deg'][m]
                    out['articulation_deg'] = {'mean': float(np.nanmean(a)), 'std': float(np.nanstd(a)), 'max_abs': float(np.nanmax(np.abs(a)))}
                    fw = d['fifth_wheel_err_mm']
                    out['fifth_wheel_err_mm_max'] = float(np.nanmax(np.abs(fw)))
                    checks.append(('fifth_wheel_err_mm_max', out['fifth_wheel_err_mm_max'], f'<= {FW_ERR_LIMIT}', out['fifth_wheel_err_mm_max'] <= FW_ERR_LIMIT))
            else:
                checks.append(('steady_window', int(m.sum()), '> 100 samples', False))
        else:
            checks.append(('reached_target', 0, f'>= 0.95 x {target_kmh} km/h', False))
    out['checks'] = [{'metric': c[0], 'value': c[1], 'limit': c[2], 'pass': bool(c[3])} for c in checks]
    out['pass'] = all(c[3] for c in checks)
    return out


TARGETS = {'c50': 40.0, 'c25': 25.0}

# straight080 limits per preset: same bands as tests/physics/scenarios/straight_0_80_0.json (WORKING_VALUE / SOURCED there).
STRAIGHT_LIMITS = {
    'solo':  {'t60': (7, 20), 't80': (12, 32), 'stop': (32, 55)},
    'empty': {'t60': (12, 35), 't80': (20, 55), 'stop': (35, 61.2)},
    '40t':   {'t60': (25, 60), 't80': (40, 95), 'stop': (35, 61.2)},
    '24t':   {'t60': (12, 60), 't80': (20, 95), 'stop': (35, 61.2)},
}
MFDD_LIMITS = (5.0, 8.0)
LAT_DEV_LIMIT = 0.5
LOCK_LIMIT_S = 0.05
SPEED_OVERSHOOT_KMH = 83.0


def straight_preset(name):
    p = name.split('_')
    return p[1] if len(p) > 1 and p[1] in STRAIGHT_LIMITS else 'solo'


def analyse_straight(name, d):
    """Autopilot straight080 run (ADR 0195): same metric definitions as the .NET runner (Sim/Metrics.cs)."""
    t = d['t']
    n = t.size
    out = {'samples': int(n), 'span_s': float(t[-1] - t[0]) if n else 0.0, 'preset': straight_preset(name)}
    out['nan_detected'] = int(sum(int(np.isnan(d[k]).any()) for k in ('x', 'z', 'speed_kmh') if k in d))
    if 'step_us' in d:
        su = d['step_us']
        out['step_us'] = {'p50': pct(su, 50), 'p95': pct(su, 95), 'p99': pct(su, 99), 'max': float(np.nanmax(su))}
    if all(k in d for k in ('vel_x', 'vel_y', 'vel_z')):
        v3 = np.c_[d['vel_x'], d['vel_y'], d['vel_z']]
        dv = np.linalg.norm(np.diff(v3, axis=0), axis=1)
        out['max_dv_step_ms'] = float(np.nanmax(dv)) if dv.size else 0.0
    lim = STRAIGHT_LIMITS[out['preset']]
    checks = []
    if out.get('max_dv_step_ms') is not None:
        checks.append(('max_dv_step_ms', out['max_dv_step_ms'], f'<= {DV_LIMIT}', out['max_dv_step_ms'] <= DV_LIMIT))
    checks.append(('nan_detected', out['nan_detected'], '== 0', out['nan_detected'] == 0))
    dt = float(np.median(np.diff(t))) if n > 1 else 0.01
    v = np.abs(d['v_fwd']) if 'v_fwd' in d else d['speed_kmh'] / 3.6
    kmh = v * 3.6
    th, br = d['throttle_in'], d['brake_in']
    x, z = d['x'], d['z']
    ith = np.nonzero(th > 0.01)[0]
    if not ith.size or ith[0] == 0:
        checks.append(('launch_recorded', 0, 'throttle step inside the recording', False))
        out['checks'] = [{'metric': c[0], 'value': c[1], 'limit': c[2], 'pass': bool(c[3])} for c in checks]
        out['pass'] = False
        return out
    i0 = int(ith[0])
    t_th = float(t[i0]) - dt
    path = np.r_[0.0, np.cumsum(np.hypot(np.diff(x), np.diff(z)))]
    for key, kv in (('t_0_60_s', 60.0), ('t_0_80_s', 80.0)):
        idx = np.nonzero(kmh[i0:] >= kv)[0]
        out[key] = float(t[i0 + idx[0]] - t_th) if idx.size else None
    i80 = np.nonzero(kmh[i0:] >= 80.0)[0]
    out['s_0_80_m'] = float(path[i0 + i80[0]] - path[i0]) if i80.size else None
    out['max_speed_kmh'] = float(np.nanmax(kmh))
    # brake onset: first rising edge of the pedal after the throttle step
    rise = np.nonzero((br[1:] > 0.05) & (br[:-1] <= 0.05))[0] + 1
    rise = rise[rise > i0]
    if rise.size:
        ib = int(rise[0])
        if i80.size:
            hold = (np.arange(n) >= i0 + i80[0]) & (np.arange(n) < ib)
            if hold.sum() > 10:
                out['hold_mean_kmh'] = float(np.mean(kmh[hold])); out['hold_std_kmh'] = float(np.std(kmh[hold]))
        v0 = float(v[ib - 1])
        out['v_brake_kmh'] = v0 * 3.6
        ist = np.nonzero(v[ib:] < 0.05)[0]
        if ist.size:
            ie = ib + int(ist[0])
            out['stop_distance_m'] = float(np.hypot(x[ie] - x[ib - 1], z[ie] - z[ib - 1]))
            out['stop_time_s'] = float(t[ie] - t[ib - 1])
            seg = slice(ib, ie + 1)
            ia = np.nonzero(v[seg] <= 0.8 * v0)[0]; iz = np.nonzero(v[seg] <= 0.1 * v0)[0]
            if ia.size and iz.size and iz[0] > ia[0]:
                a, e = ib + ia[0], ib + iz[0]
                out['mfdd_ms2'] = float((v[a] ** 2 - v[e] ** 2) / (2 * (path[e] - path[a])))
            w = max(1, int(round(0.1 / dt)))
            if ie - ib > w:
                dec = (v[ib:ie + 1 - w] - v[ib + w:ie + 1]) / (w * dt)
                out['max_decel_ms2'] = float(np.max(dec))
            if 'a_long' in d:
                out['max_decel_a_long_ms2'] = float(-np.nanmin(d['a_long'][seg]))
            # lateral deviation in the stop, from the line through the onset point along the onset velocity
            hx, hz = x[ib] - x[ib - 1], z[ib] - z[ib - 1]
            hn = math.hypot(hx, hz) or 1.0
            lat = np.abs((x[seg] - x[ib - 1]) * (hz / hn) - (z[seg] - z[ib - 1]) * (hx / hn))
            out['stop_lat_dev_m'] = float(np.max(lat))
            slips = [k for k in d if k.endswith('_slip')]
            if slips:
                sl = np.c_[tuple(d[k][seg] for k in slips)]
                moving = v[seg] > 1.0
                out['max_abs_slip'] = float(np.nanmax(np.abs(sl[moving]))) if moving.any() else 0.0
                worst = int(np.nanargmax(np.nanmax(np.abs(sl[moving]), axis=0))) if moving.any() else 0
                out['max_abs_slip_wheel'] = slips[worst][:-5]
                out['wheel_lock_time_s'] = float(np.sum(np.any(sl[moving] < -0.5, axis=1)) * dt)
    # checks (runner bands)
    def band(metric, val, lo_hi):
        lo, hi = lo_hi
        checks.append((metric, val, f'{lo}..{hi}', val is not None and lo <= val <= hi))
    band('t_0_60_s', out.get('t_0_60_s'), lim['t60'])
    band('t_0_80_s', out.get('t_0_80_s'), lim['t80'])
    checks.append(('max_speed_kmh', out['max_speed_kmh'], f'<= {SPEED_OVERSHOOT_KMH}', out['max_speed_kmh'] <= SPEED_OVERSHOOT_KMH))
    band('stop_distance_m', out.get('stop_distance_m'), lim['stop'])
    band('mfdd_ms2', out.get('mfdd_ms2'), MFDD_LIMITS)
    sl = out.get('stop_lat_dev_m')
    checks.append(('stop_lat_dev_m', sl, f'<= {LAT_DEV_LIMIT}', sl is not None and sl <= LAT_DEV_LIMIT))
    lk = out.get('wheel_lock_time_s')
    checks.append(('wheel_lock_time_s', lk, f'<= {LOCK_LIMIT_S}', lk is not None and lk <= LOCK_LIMIT_S))
    if 'fifth_wheel_err_mm' in d and 'coupled' in d and np.nanmax(d['coupled']) > 0.5:
        out['fifth_wheel_err_mm_max'] = float(np.nanmax(np.abs(d['fifth_wheel_err_mm'])))
        checks.append(('fifth_wheel_err_mm_max', out['fifth_wheel_err_mm_max'], f'<= {FW_ERR_LIMIT}', out['fifth_wheel_err_mm_max'] <= FW_ERR_LIMIT))
        if 'articulation_deg' in d:
            out['max_abs_articulation_deg'] = float(np.nanmax(np.abs(d['articulation_deg'][i0:])))
            checks.append(('max_abs_articulation_deg', out['max_abs_articulation_deg'], '<= 2.0', out['max_abs_articulation_deg'] <= 2.0))
    out['checks'] = [{'metric': c[0], 'value': c[1], 'limit': c[2], 'pass': bool(c[3])} for c in checks]
    out['pass'] = all(c[3] for c in checks)
    return out


def main(root):
    runs_file = os.path.join(root, 'gate12-runs.json')
    meta = json.load(open(runs_file, encoding='utf-8-sig')) if os.path.isfile(runs_file) else {}
    summary = {'root': root, 'apk': meta.get('apk'), 'devices': {}}
    for serial_dir in sorted(glob.glob(os.path.join(root, '*', ''))):
        serial = os.path.basename(os.path.dirname(serial_dir))
        dev = {}
        for run_dir in sorted(glob.glob(os.path.join(serial_dir, '*', ''))):
            name = os.path.basename(os.path.dirname(run_dir))
            r = {}
            mp = os.path.join(run_dir, 'metrics.json')
            if os.path.isfile(mp):
                m = json.load(open(mp, encoding='utf-8-sig'))
                r['frame'] = m.get('frameTime'); r['gpuMs'] = m.get('gpuMs'); r['cpuMainMs'] = m.get('cpuMainMs')
                r['pssMb'] = m.get('pssMb'); r['batteryTempC'] = m.get('batteryTempC'); r['thermalStatus'] = m.get('thermalStatus')
                r['build'] = (m.get('gameSummary') or {}).get('build')
            csvs = sorted(glob.glob(os.path.join(run_dir, 'telemetry', '**', 'drive-*.csv'), recursive=True))
            if csvs:
                d = load_csv(csvs[-1])
                r['telemetry_csv'] = csvs[-1]
                r['physics'] = analyse_straight(name, d) if name.startswith('s080') else analyse_run(name, d, TARGETS.get(name.split('_')[0], 40.0))
            dev[name] = r
        rep = [dev[k]['physics'] for k in sorted(dev) if k.startswith('c50_solo_') and 'physics' in dev[k]]
        if len(rep) >= 2:
            res = {}
            for key in ('t_0_30_s', 't_0_target95_s'):
                vals = [p.get(key) for p in rep if p.get(key) is not None]
                if len(vals) >= 2:
                    mean = sum(vals) / len(vals)
                    dev_max = max(abs(v - mean) for v in vals) / mean if mean else None
                    res[key] = {'values': vals, 'mean': mean, 'max_dev': dev_max, 'pass': dev_max is not None and dev_max <= REPEAT_LIMIT}
            dev['_repeatability_proxy'] = res
        srep = [dev[k]['physics'] for k in sorted(dev) if k.startswith('s080_solo_') and 'physics' in dev[k]]
        if len(srep) >= 2:
            res = {}
            for key in ('t_0_60_s', 't_0_80_s'):
                vals = [p.get(key) for p in srep if p.get(key) is not None]
                if len(vals) >= 2:
                    mean = sum(vals) / len(vals)
                    dev_max = max(abs(v - mean) for v in vals) / mean if mean else None
                    res[key] = {'values': vals, 'mean': mean, 'max_dev': dev_max, 'pass': dev_max is not None and dev_max <= REPEAT_LIMIT}
            dev['_repeatability_0_80'] = res
        summary['devices'][serial] = dev
    with open(os.path.join(root, 'gate12-summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    lines = [f'# Gate 1-2 phone summary ({root})', '', f"APK: {summary['apk']}", '']
    for serial, dev in summary['devices'].items():
        lines += [f'## {serial}', '', '| run | build | FPS mean | p50/p95/p99 ms | PSS MB | temp C | step_us p50/p99 | physics | notes |', '|---|---|---|---|---|---|---|---|---|']
        for name, r in dev.items():
            if name.startswith('_'):
                continue
            fr = r.get('frame') or {}
            ph = r.get('physics') or {}
            su = ph.get('step_us') or {}
            fails = [c['metric'] for c in ph.get('checks', []) if not c['pass']]
            note = ', '.join(f"{k}={ph[k]:.4g}" for k in ('drift_m', 't_0_30_s', 't_0_target95_s', 'speed_std_kmh', 't_0_60_s', 't_0_80_s', 's_0_80_m',
                                                           'stop_distance_m', 'mfdd_ms2', 'max_decel_ms2', 'max_abs_slip', 'wheel_lock_time_s',
                                                           'stop_lat_dev_m', 'max_dv_step_ms', 'fifth_wheel_err_mm_max') if isinstance(ph.get(k), (int, float)))
            lines.append(f"| {name} | {r.get('build')} | {fr.get('meanFps')} | {fr.get('p50Ms')}/{fr.get('p95Ms')}/{fr.get('p99Ms')} | {r.get('pssMb')} | {r.get('batteryTempC')} | "
                         f"{su.get('p50')}/{su.get('p99')} | {'PASS' if ph.get('pass') else ('FAIL ' + ','.join(fails) if ph else 'no telemetry')} | {note} |")
        rp = dev.get('_repeatability_proxy')
        if rp:
            lines += ['', 'Repeatability PROXY (circle50 autopilot from rest, 3 runs; gate asks straight 0-80 x3):']
            for k, v in rp.items():
                dv = 'n/a' if v['max_dev'] is None else f"{100 * v['max_dev']:.2f} %"
                lines.append(f"- {k}: {['%.2f' % x for x in v['values']]} mean {v['mean']:.2f} s, max dev {dv} -> {'PASS' if v['pass'] else 'FAIL'} (limit 3 %)")
        rs = dev.get('_repeatability_0_80')
        if rs:
            lines += ['', 'Repeatability 0-60 / 0-80 km/h (autopilot straight080, solo, 3 runs; gate 1 limit +/-3 %):']
            for k, v in rs.items():
                dv = 'n/a' if v['max_dev'] is None else f"{100 * v['max_dev']:.2f} %"
                lines.append(f"- {k}: {['%.2f' % x for x in v['values']]} mean {v['mean']:.2f} s, max dev {dv} -> {'PASS' if v['pass'] else 'FAIL'}")
        lines.append('')
    with open(os.path.join(root, 'gate12-summary.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
