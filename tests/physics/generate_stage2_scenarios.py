"""Generates the Stage 2 validation scenarios (combination, air brakes, endurance brakes, AMT).

Usage (from the repo root):  uv run python tests/physics/generate_stage2_scenarios.py tests/physics/scenarios

The JSON files in tests/physics/scenarios are the authority that the runner and the tests read. This script
is how the Stage 2 files were produced (keeps the solo / empty / 40 t variants and the check sources
consistent). If you hand-edit a generated JSON, port the change here or the next regeneration loses it.
Stage 1 solo scenarios are hand-written and not touched by this script. So are the R5/R6 coupling scenarios
(couple_standstill_locked, couple_offset_*, couple_miss_25cm).
"""
import json, os, sys

OUT = sys.argv[1]
W = "WORKING_VALUE"; D = "DERIVED"; S = "SOURCED"
R13 = "UN R13 Annex 4"


def chk(metric, mn=None, mx=None, status=W, source="", arg=0, frm=0, to=0, variant=""):
    c = {"metric": metric, "status": status, "source": source}
    if mn is not None: c["min"] = mn
    if mx is not None: c["max"] = mx
    if arg: c["arg"] = arg
    if frm: c["from"] = frm
    if to: c["to"] = to
    if variant: c["variant"] = variant
    return c


def key(t, throttle=0, brake=0, steer=0, park=False, sel="D", lever=0, manual=False, up=False, down=False):
    k = {"t": t, "throttle": throttle, "brake": brake, "steer": steer, "parkingBrake": park, "selector": sel}
    if lever: k["retarderLever"] = lever
    if manual: k["manual"] = True
    if up: k["shiftUp"] = True
    if down: k["shiftDown"] = True
    return k


def sc(id, desc, spec, duration, driver, checks, variants=None, ground=None, initial=None, **kw):
    d = {"schemaVersion": 1, "id": id, "description": desc, "spec": spec}
    if variants: d["variants"] = variants
    d["ground"] = ground or {"gradePercent": 0, "surface": "dry_asphalt"}
    d["initial"] = initial or {}
    d.update(kw)
    d["duration"] = duration
    d["driver"] = driver
    d["checks"] = checks
    with open(os.path.join(OUT, id + ".json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


COMB = ["empty", "laden40"]
ALL3 = ["solo", "empty", "laden40"]
stable = [chk("max_dv_step_ms", mx=0.35, source="no solver explosion / impulse spikes (per-step velocity change of either body)"),
          chk("max_fifth_wheel_error_mm", mx=5, source="kingpin constraint drift (custom fifth-wheel constraint)")]

# ---------------- 1. parking ----------------
for grade, name in [(12, "down"), (-12, "up")]:
    # Vehicle faces +Z; ground rises towards +Z for positive grade -> facing uphill. "down" = facing downhill.
    g = -grade if name == "down" else -grade
    sc(f"park_12pct_{name}_comb",
       f"Combination parked on 12% (facing {name}hill), tractor spring brakes only (R13 Annex 4 2.3.2), engine idling, 300 s",
       "docs/04 s6.1", 300,
       {"type": "timeline", "keys": [key(0, park=True, sel="N")]},
       [chk("creep_m", mx=0.005, frm=5, source="holds without creep in the ground plane; 12% from R13 Annex 4 para 2.3.2 (towing vehicle parking brake holds the combination on 12%)", status=S),
        chk("creep_m", mx=0.0005, frm=60, source="no creep at all once settled (tire / suspension compliance only in the first seconds)"),
        chk("drift_m", mx=0.012, frm=5, source="incl. vertical settling of the levelled air suspension (deadband 8 mm)"),
        chk("max_speed_after_ms", mx=0.001, frm=5, source="no oscillation / creep after settling"),
        chk("trailer_creep_m", mx=0.005, frm=5, source="trailer held through the kingpin")] + stable,
       variants=COMB, ground={"gradePercent": g, "surface": "dry_asphalt"}, initial={"parkingBrake": True})

sc("park_flat_5min_comb", "Combination parked on flat ground, 300 s, idling", "docs/04 s6.1", 300,
   {"type": "timeline", "keys": [key(0, park=True, sel="N")]},
   [chk("drift_m", mx=0.005, frm=5, source="no creep"), chk("max_speed_after_ms", mx=0.001, frm=5, source="no oscillation")] + stable,
   variants=COMB, initial={"parkingBrake": True})

# ---------------- 2./3. launch ----------------
sc("launch_flat_comb", "Standstill on flat, release brake, full throttle, AMT auto, to the limiter", "docs/04 s6.2, s6.3", 120,
   {"type": "timeline", "keys": [key(0, brake=1), key(1.0, throttle=1)]},
   [chk("rollback_m", mx=0.02, source="no rollback on flat"),
    chk("stalled", mx=0, source="engine must not stall"),
    chk("min_rpm", mn=550, frm=1, source="engine stays near idle or above"),
    chk("time_to_kmh", arg=60, mn=12, mx=35, variant="empty", status=D,
        source="power-to-weight: 0.5 m v^2 / (0.75 x 368 kW) + 6-8 shifts x ~0.6 s interruption; 14.5 t"),
    chk("time_to_kmh", arg=80, mn=20, mx=55, variant="empty", status=D, source="as above incl. aero; 14.5 t"),
    chk("time_to_kmh", arg=60, mn=25, mx=60, variant="laden40", status=D,
        source="0.5 x 40 t x 16.7^2 / (0.7 x 368 kW) = 22 s + shifts + rolling; plausibility band, no sourced test data"),
    chk("time_to_kmh", arg=80, mn=40, mx=95, variant="laden40", status=D, source="as above, 22.2 m/s: 38 s + shifts + rolling + aero"),
    chk("max_speed_kmh", mx=90.5, status=S, source="S3: 90 km/h limiter"),
    chk("max_rpm_in_gear", arg=6, mx=1900, frm=1, source="Stage 2 fix: no over-rev to the 1900-2100 rpm governor in the low gears"),
    chk("max_shift_retard_torque_nm", mx=1, frm=1,
        source="owner feel test 2026-11-10: no wheel brake / retarder / engine brake torque during an up-shift unless commanded (ADR 0004 addendum 2026-11-10)"),
    chk("min_accel_shift_gap_ms2", mn=-0.3, frm=1, status=D,
        source="per-gap mean dv/dt with the clutch open: only rolling (cr 0.005-0.0055 x g = 0.05 m/s2) + aero (~0.05 laden / ~0.15 empty at 88 km/h) may decelerate; limit ~1.5x the worst case"),
    chk("max_clutch_temp_c", mx=250, source="clutch below the warning temperature on a flat start")] + stable,
   variants=COMB)

sc("launch_6pct_uphill_comb", "Standstill facing uphill on 6% held by the service brake, release, full throttle (hill start aid)",
   "docs/04 s6.2", 60,
   {"type": "timeline", "keys": [key(0, brake=1), key(2.0, throttle=1)]},
   [chk("rollback_m", mx=0.05, source="docs/04 s6.2 'bez cofania sie'; 5 cm for tire/suspension/kingpin compliance"),
    chk("stalled", mx=0, source="engine must not stall"),
    chk("min_rpm", mn=550, frm=2, source="engine stays near idle or above"),
    chk("time_to_kmh", arg=15, mn=1.5, mx=20, variant="empty", source="plausibility (14.5 t, traction-limited ~3 m/s^2 minus grade)"),
    chk("time_to_kmh", arg=15, mn=3, mx=35, variant="laden40",
        source="40 t on 6%: traction-limited (~0.8 x 11 t on the drive axle = 90 kN) minus 25 kN grade -> ~1.6 m/s^2 -> 2.6 s + clutch engagement; plausibility"),
    chk("max_clutch_temp_c", mx=250, source="hill start must not overheat the clutch (thermal model WORKING_VALUE)"),
    chk("time_to_kmh", arg=15, mn=4.05, mx=4.95, variant="laden40",
        source="regression guard = PlayMode CombinationLabTests.HillStart_6pct_40t (runner 4.5 s +-10 %); 6.2 s after ADR 0019 was a 3-2-3 shift, ADR 0024"),
    chk("shift_count", mx=14, source="no gear hunting on the climb (Stage 2 fix: up-shift lands above the grade down-shift line)"),
    chk("downshift_count", mx=0, frm=2, to=25,
        source="full throttle and still accelerating: no down-shift (predictive down-shift hold, ADR 0024)"),
    chk("min_speed_kmh", mn=10, frm=20, source="keeps climbing after the start (no stall-out from hunting)")] + stable,
   variants=COMB, ground={"gradePercent": 6, "surface": "dry_asphalt"})

sc("launch_12pct_uphill_comb", "40 t hill start on 12% (steep ramp), full throttle: climbs without gear hunting",
   "docs/04 s6.2", 45,
   {"type": "timeline", "keys": [key(0, brake=1), key(2.0, throttle=1)]},
   [chk("rollback_m", mx=0.05, source="no rollback"), chk("stalled", mx=0, source="no stall"),
    chk("time_to_kmh", arg=15, mn=5, mx=15, source="plausibility; 8.7 s measured with ADR 0024 strategy (WORKING_VALUE)"),
    chk("shift_count", mx=6, source="no gear hunting: 1-2-3-4-5 then hold (17 shifts / 7 down-shifts 4-5-4 before ADR 0024)"),
    chk("downshift_count", mx=0, frm=2, source="full throttle and still accelerating or on the governor: no down-shift (ADR 0024)"),
    chk("min_speed_kmh", mn=18, frm=20, source="power-limited climb: 0.92 x 368 kW / (40 t x 9.81 x 0.125) = 6.9 m/s (25 km/h) upper bound; "
        "18 km/h floor = 13.2 km/h with hunting before ADR 0024")] + stable,
   variants=["laden40"], ground={"gradePercent": 12, "surface": "dry_asphalt"})

sc("launch_6pct_uphill_light_comb", "6% hill start with 35 % throttle (gentle driver)", "docs/04 s6.2", 60,
   {"type": "timeline", "keys": [key(0, brake=1), key(2.0, throttle=0.35)]},
   [chk("rollback_m", mx=0.05, source="no rollback"), chk("stalled", mx=0, source="no stall"),
    chk("time_to_kmh", arg=10, mn=3, mx=45, source="plausibility")] + stable,
   variants=["laden40"], ground={"gradePercent": 6, "surface": "dry_asphalt"})

# ---------------- 4. top speed and 5% grade ----------------
sc("top_speed_flat_comb", "Full throttle on flat from 60 km/h, 120 s", "docs/04 s6.4", 120,
   {"type": "timeline", "keys": [key(0, throttle=1)]},
   [chk("max_speed_kmh", mx=90.5, status=S, source="S3: 90 km/h speed limiter (N3)"),
    chk("mean_speed_kmh", mn=87, mx=90, frm=90, status=S, source="settles at the limiter"),
    chk("final_gear", mn=12, mx=12, source="top gear at cruise")] + stable,
   variants=COMB, initial={"speedKmh": 60})

sc("grade_5pct_steady", "40 t on a 5% climb, full throttle from 60 km/h, steady speed after 150 s", "docs/04 s6.4", 200,
   {"type": "timeline", "keys": [key(0, throttle=1)]},
   [chk("mean_speed_kmh", mn=44, mx=60, frm=150, status=D,
        source="v = eta P / (m g (sin a + f_r) + aero): 0.92 x 368 kW / (40 t x 9.81 x 0.0554 + ~0.7 kN) = 15 m/s (54 km/h); gear steps cost a few km/h"),
    chk("speed_range_kmh", mx=6, frm=150, source="no gear hunting on the climb (mass/grade-aware AMT)"),
    chk("min_rpm", mn=1000, frm=150, source="engine kept in the torque plateau (S1: 980-1270 rpm max torque)")] + stable,
   variants=["laden40"], ground={"gradePercent": 5, "surface": "dry_asphalt"}, initial={"speedKmh": 60})

# ---------------- 5. braking 80 -> 0 ----------------
for surf, mu in [("dry", "dry_asphalt"), ("wet", "wet_asphalt")]:
    for abs_on in [True, False]:
        sid = f"brake_80_0_{surf}_{'abs' if abs_on else 'noabs'}_comb"
        variants = COMB if abs_on else ALL3
        ch = list(stable) if abs_on else [stable[0]]
        if abs_on:
            if surf == "dry":
                ch += [chk("stop_distance_m", mn=35, mx=61.2, status=W,
                           source="upper bound = 0.15 v + v^2/130 at 80 km/h (believed R13 N3 type-0 formula, UNVERIFIED; the type-0 table did not extract); lower bound ~ v^2/(2 x 0.8 g) + build-up"),
                       chk("mfdd_ms2", mn=5.0, mx=8.0, source="MFDD (R13 Annex 4 definition); 5.0 = believed N3 type-0 minimum (UNVERIFIED); <= mu g"),
                       ]
            else:
                ch += [chk("stop_distance_m", mn=45, mx=95, source="mu_wet ~0.5 (WORKING): v^2/(2 x 0.45 g) + build-up"),
                       chk("mfdd_ms2", mn=3.0, mx=5.5, source="<= mu_wet g")]
            ch += [chk("max_lateral_deviation_m", mx=0.5, source="straight-line stability under ABS"),
                   chk("max_articulation_deg", mx=2.0, source="no trailer swing under ABS braking on a straight"),
                   chk("rear_lock_time_s", mx=0.03, source="Stage 2 fix: no tractor drive-axle lock at brake onset (EBS load sensing + decel-threshold ABS)"),
                   chk("trailer_lock_time_s", mx=0.05, source="trailer ABS 2S/2M prevents lock")]
        else:
            ch += [chk("rear_lock_time_s", mn=0.3, source="without ABS the wheels lock (expected behaviour, not a failure)", variant="solo"),
                   chk("stop_distance_m", mn=30, mx=150, source="locked-wheel sliding friction bounds")]
            if surf == "dry":
                ch += [chk("stop_distance_m", mn=33, mx=150, source="no-ABS: locked or near-locked wheels")]
        sc(sid, f"80->0 km/h full service brake, {surf} asphalt, ABS {'on' if abs_on else 'off'}", "docs/04 s6.5", 20,
           {"type": "timeline", "keys": [key(0), key(0.5, brake=1)]}, ch, variants=variants,
           ground={"gradePercent": 0, "surface": mu}, initial={"speedKmh": 80, "gear": 11},
           overrides={"absEnabled": abs_on})

sc("brake_response_static", "Stationary vehicle, full service brake application (response time as in R13, vehicle at rest)", "docs/04 s6.5 / s2.8", 3,
   {"type": "timeline", "keys": [key(0, sel="N"), key(0.5, brake=1, sel="N")]},
   [chk("brake_response_s", arg=0, mx=0.6, status=S, source=f"{R13} 4.1.1: braking force on the least favourable axle within 0.6 s (criterion here: 75 % of the final chamber pressure; Annex 6 method not verified)"),
    chk("brake_response_s", arg=1, mx=0.6, status=S, source=f"{R13} 4.1.1"),
    chk("brake_response_s", arg=0, mn=0.15, source="pneumatic build-up is not instantaneous"),
    chk("brake_response_s", arg=2, mx=0.6, status=S, source=f"{R13} 4.1.1 (trailer axle: longest lines, cascaded lag)", variant="empty"),
    chk("brake_response_s", arg=2, mx=0.6, status=S, source=f"{R13} 4.1.1 (trailer axle)", variant="laden40"),
    chk("brake_response_s", arg=2, mn=0.3, source="trailer builds up later than the tractor (longer lines)", variant="laden40"),
    ], variants=ALL3)
for v in COMB:
    pass

# ---------------- 6. downhill ----------------
sc("downhill_7pct_typeIIA", "R13 type-IIA-like: 40 t, 7% down, 30 km/h held with endurance brakes only (brake cruise), 6 km",
   "docs/04 s6.6", 720,
   {"type": "speedhold", "targetKmh": 30, "enduranceOnly": True},
   [chk("mean_speed_kmh", mn=25, mx=35, frm=60, status=S,
        source=f"{R13} 1.8.2: laden, 30 km/h average on 7% for 6 km without service/secondary/parking brakes (+/-5 km/h)"),
    chk("max_service_demand", mx=0, status=S, source=f"{R13} 1.8.2: service brake not used"),
    chk("max_rpm", mx=2400, source="engine overrun limit while engine braking (WORKING_VALUE 2400 rpm)"),
    chk("max_speed_kmh", mx=40, frm=30, source="no runaway")] + stable,
   variants=["laden40"], ground={"gradePercent": -7, "surface": "dry_asphalt"}, initial={"speedKmh": 30},
   sampleEvery=5)

sc("downhill_7pct_brake_cruise_60", "40 t, 7% down, brake cruise at 60 km/h with engine brake + retarder stages", "docs/04 s6.6", 180,
   {"type": "speedhold", "targetKmh": 60, "enduranceOnly": True},
   [chk("mean_speed_kmh", mn=59, mx=61.5, frm=60, source="speed stabilised at the set speed"),
    chk("speed_range_kmh", mx=2, frm=60, source="no hunting / limit cycle of the downhill speed control"),
    chk("max_retarder_torque_nm", mn=1000, mx=4000, status=S, source="S2: Intarder up to 4000 Nm / 600 kW (class reference)"),
    chk("max_service_demand", mx=0, source="service brake not needed")] + stable,
   variants=["laden40"], ground={"gradePercent": -7, "surface": "dry_asphalt"}, initial={"speedKmh": 60})

sc("downhill_7pct_full_lever", "40 t, 7% down from 70 km/h, endurance lever at maximum, no pedal: speed settles", "docs/04 s6.6", 120,
   {"type": "timeline", "keys": [key(0, lever=5)]},
   [chk("speed_range_kmh", mx=3, frm=80, source="speed stabilises (endurance brakes stronger than gravity at 70 km/h)"),
    chk("max_speed_kmh", mx=71, source="no runaway"),
    chk("max_engine_brake_torque_nm", mn=500, source="engine brake active (VEB+ class; S1 375 kW at 2300 rpm)")] + stable,
   variants=["laden40"], ground={"gradePercent": -7, "surface": "dry_asphalt"}, initial={"speedKmh": 70})

sc("downhill_7pct_service_pumping", "40 t, 7% down at 40 km/h with service brake only (endurance brakes off), driver pumps the pedal",
   "docs/04 s6.6", 240,
   {"type": "speedhold", "targetKmh": 40, "pumpPeriod": 4},
   [chk("min_air_service_bar", mx=9.0, source="pumping the pedal consumes more air (~50 NL per application, 10 chambers) than the compressor delivers (~450 NL/min at rated speed): the classic long-descent pressure loss"),
    chk("min_air_service_bar", mn=3.0, source="the service brake keeps working (pressure does not collapse within 4 min)"),
    chk("low_air_warning", mn=1, source="warning lamp comes on: real consequence of pumping on a long descent"),
    chk("max_speed_kmh", mx=50, source="speed controlled")] + stable,
   variants=["laden40"], ground={"gradePercent": -7, "surface": "dry_asphalt"}, initial={"speedKmh": 40},
   overrides={"enduranceBrakes": False})

sc("air_leak_rear_circuit", "60 km/h, circuit 2 (rear) bursts at t=3 s, then emergency stop at t=15 s", "docs/04 s6.6 / s2.8", 40,
   {"type": "timeline", "keys": [key(0, throttle=0.4), key(15, brake=1)]},
   [chk("low_air_warning", mn=1, source="low-pressure warning must come on"),
    chk("min_air_service_bar", mx=1.0, source="rear circuit empties"),
    chk("stop_distance_m", mx=64.4, status=S, source=f"{R13} 2.2: secondary braking N: s <= 0.15 v + 2 v^2/130 at 60 km/h"),
    chk("max_lateral_deviation_m", mx=1.0, source="stable straight-line stop on the remaining circuits")],
   variants=["laden40"], initial={"speedKmh": 60}, events=[{"t": 3, "type": "leak", "circuit": 2, "lpm": 3000}])

sc("air_leak_park_circuit", "60 km/h, circuit 3 (spring brakes + trailer supply) bursts at t=3 s, no pedal", "docs/04 s2.8", 60,
   {"type": "timeline", "keys": [key(0, throttle=0.4), key(3)]},
   [chk("trailer_emergency", mn=1, source="red-line loss applies the trailer brakes (emergency relay valve)"),
    chk("min_speed_kmh", mx=0.5, frm=40, source="spring brakes + trailer emergency brake stop the combination"),
    chk("low_air_warning", mn=1, source="warning")],
   variants=["laden40"], initial={"speedKmh": 60}, events=[{"t": 3, "type": "leak", "circuit": 3, "lpm": 3000}])

# ---------------- 7. circle / rollover ----------------
for kmh in [10, 35]:
    sc(f"circle_r50_{kmh}kmh_comb", f"Combination on R = 50 m at {kmh} km/h", "docs/04 s6.7", 60,
       {"type": "circle", "targetKmh": kmh, "radius": 50, "direction": 1},
       [chk("radius_error_m", mx=0.6, frm=30, source="path following"),
        chk("lat_accel_ms2", mn=(kmh / 3.6) ** 2 / 50 * 0.9, mx=(kmh / 3.6) ** 2 / 50 * 1.1, frm=30, status=D, source="v^2/R")] +
       ([chk("trailer_offtracking_m", mn=0.4, mx=0.8, frm=30, status=D,
             source="steady low-speed offtracking: sqrt(R^2+e^2) vs sqrt(R^2+e^2-L^2) with e = 0.68 m, L = 7.7 m -> 0.59 m")] if kmh == 10 else
        [chk("trailer_offtracking_m", mn=-0.5, mx=0.55, frm=30, source="offtracking shrinks / reverses with speed (tire slip angles)"),
         chk("max_trailer_roll_deg", mx=4, frm=30, source="moderate roll at 0.19 g")]) + stable,
       variants=COMB)

for name, h in [("low", 1.9), ("high", 2.6)]:
    sc(f"rollover_r50_cog_{name}", f"40 t on R = 50 m, speed ramp until the first wheel lifts, cargo CoG {h} m", "docs/04 s6.7", 140,
       {"type": "circle", "targetKmh": 30, "radius": 50, "direction": 1, "rampKmhPerS": 0.5, "rampStart": 15},
       [chk("lat_accel_at_first_lift", mn=0.25, mx=0.55, status=W,
            source="static rollover threshold of laden tractor-semitrailers ~0.3-0.45 g in the literature (UMTRI / Winkler; not opened, UNVERIFIED)")] + [stable[1]],
       variants=["laden40"], cargo={"massKg": 0, "cogHeight": h}, endCondition="wheel_lift")

# ---------------- 8. lane change ----------------
for kmh, L in [(60, 50), (80, 70)]:
    ay = 1.75 * (3.14159 / L) ** 2 * (kmh / 3.6) ** 2
    sc(f"lane_change_{kmh}", f"Double lane change 3.5 m over {L} m at {kmh} km/h (path peak a_y {ay / 9.81:.2f} g, ISO 14791-like lateral level)", "docs/04 s6.8", 30,
       {"type": "lanechange", "targetKmh": kmh, "startDistance": 40, "length": L, "offset": 3.5, "doubleChange": True, "holdLength": 30},
       [chk("max_articulation_deg", mx=6, source="trailer follows without large swing at ~0.15-0.2 g"),
        chk("rearward_amplification", mn=0.8, mx=1.6, source="rearward amplification of tractor-semitrailers is about 1.0-1.3 in the literature (UNVERIFIED); WORKING band 0.8-1.6", variant="laden40"),
        chk("rearward_amplification", mn=0.8, mx=1.6, source="as above", variant="empty"),
        chk("articulation_settle_deg", mx=0.5, frm=26, source="trailer swing damped after the manoeuvre"),
        chk("wheel_lift", mx=0, source="no wheel lift in a normal lane change"),
        chk("max_lat_accel_ms2", mx=2.5, source="manoeuvre stays at the intended moderate level"),
        chk("max_yaw_rate_dps", mx=10, source="no spin")] + stable,
       variants=ALL3 if kmh == 80 else COMB, initial={"speedKmh": kmh})

# ---------------- 9. jackknife ----------------
sc("jackknife_wet_curve_noabs",
   "Wet R = 120 m curve at 60 km/h, EBS fault (no ABS, no load sensing: pneumatic back-up), driver brakes with half pedal at t = 6 s holding the steering",
   "docs/04 s6.9", 14,
   {"type": "circle", "targetKmh": 60, "radius": 120, "direction": 1, "brakeAt": 6, "brakeLevel": 0.5, "holdSteerOnBrake": True},
   [chk("max_articulation_deg", mn=30, source="jackknife must be possible: lightly loaded drive axle locks first without load sensing, empty trailer pushes (classic driver/defect case)", variant="empty"),
    chk("rear_lock_time_s", mn=0.5, source="drive axle locks without ABS"), stable[0]],
   variants=COMB, ground={"gradePercent": 0, "surface": "wet_asphalt"}, initial={"speedKmh": 60},
   overrides={"absEnabled": False, "loadSensing": False})

sc("jackknife_wet_curve_retarder_noabs",
   "Wet R = 120 m curve at 60 km/h, ABS failed, driver pulls the endurance lever to full and touches the pedal at t = 6 s (retarder locks the drive axle)",
   "docs/04 s6.9", 14,
   {"type": "circle", "targetKmh": 60, "radius": 120, "direction": 1, "brakeAt": 6, "brakeLevel": 0.2, "holdSteerOnBrake": True, "retarderLever": 5},
   [chk("max_articulation_deg", mn=30, source="retarder on a slippery road without ABS cut-off: drive axle lock -> jackknife (why retarders are cut by ABS)", variant="empty"),
    chk("rear_lock_time_s", mn=0.2, source="drive axle locks"), stable[0]],
   variants=COMB, ground={"gradePercent": 0, "surface": "wet_asphalt"}, initial={"speedKmh": 60},
   overrides={"absEnabled": False})

for lvl in [0.5, 1.0]:
    sc(f"jackknife_wet_curve_abs_{int(lvl * 100)}",
       f"Same curve, ABS and load sensing working, pedal {lvl:.0%} at t = 6 s with the steering held",
       "docs/04 s6.9", 14,
       {"type": "circle", "targetKmh": 60, "radius": 120, "direction": 1, "brakeAt": 6, "brakeLevel": lvl, "holdSteerOnBrake": True, "retarderLever": 5},
       [chk("max_articulation_deg", mx=10, source="ABS keeps the combination stable (and cuts the retarder)"),
        chk("rear_lock_time_s", mx=0.1, source="ABS prevents lock"), stable[0]],
       variants=COMB, ground={"gradePercent": 0, "surface": "wet_asphalt"}, initial={"speedKmh": 60})

# ---------------- 11. curbs / bump ----------------
sc("curb_15cm_left_comb", "Left wheels of the whole combination over a 15 cm curb at 8 km/h", "docs/04 s6.11", 18,
   {"type": "speedhold", "targetKmh": 8},
   [chk("max_dv_step_ms", mx=0.35, source="no impulse spikes"),
    chk("max_pos_jump_m", mx=1e-6, source="no teleport"),
    chk("max_fz_ratio", mx=4, source="bounded wheel load peaks"),
    chk("max_trailer_roll_deg", mx=8, source="geometric roll (0.15 m over ~2 m track) plus overshoot"),
    chk("max_fifth_wheel_error_mm", mx=5, source="constraint holds")],
   variants=COMB, initial={"speedKmh": 8},
   ground={"gradePercent": 0, "surface": "dry_asphalt", "boxes": [{"minX": -3, "maxX": -0.5, "minZ": 6, "maxZ": 9, "height": 0.15}]})

# ---- Kerb block geometry, derived from art-source/truck/dims.json (single source of truth, ADR 0014/0019) ----
# The block must cover the contact patches of ALL left wheels (tractor front, tractor dual rear, trailer tridem) and must
# not touch a right wheel, otherwise the scenario silently tests a different event. If dims.json changes so that this
# stops holding, generation FAILS with the numbers instead of widening the block or the checks.
DIMS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "art-source", "truck", "dims.json"), encoding="utf-8"))["values"]


def dv(k):
    return DIMS[k]["value"]


def left_wheel_x_extent():
    """(min_x, max_x) of every left tyre contact patch (vehicle centreline x = 0, left = -x), from dims.json."""
    ext = []
    hs = dv("tyre_section_width_m") / 2
    ts = dv("trailer_tyre_section_width_m") / 2
    ext.append((-dv("front_track_m") / 2 - hs, -dv("front_track_m") / 2 + hs))
    for sgn in (-1, 1):  # dual rear: two tyres at +-dual_spacing/2 around the track centre
        c = -dv("rear_track_m") / 2 + sgn * dv("dual_spacing_m") / 2
        ext.append((c - hs, c + hs))
    ext.append((-dv("trailer_track_m") / 2 - ts, -dv("trailer_track_m") / 2 + ts))
    return min(e[0] for e in ext), max(e[1] for e in ext)


def kerb_box(h, z0, z1):
    lo, hi = left_wheel_x_extent()
    box = {"minX": -3, "maxX": -0.5, "minZ": z0, "maxZ": z1, "height": h}
    errs = []
    if box["minX"] > lo: errs.append(f"block minX {box['minX']} does not cover the outermost left tyre edge {lo:.4f} m")
    if box["maxX"] < hi: errs.append(f"block maxX {box['maxX']} does not cover the innermost left tyre edge {hi:.4f} m")
    if box["maxX"] > 0: errs.append(f"block maxX {box['maxX']} reaches the centreline, right wheels would be hit")
    if dv("artic_length_m") > dv("max_artic_length_m"):
        errs.append(f"combination {dv('artic_length_m')} m exceeds the legal {dv('max_artic_length_m')} m")
    if abs(dv("artic_length_m") - 16.47) > 1e-6:
        errs.append(f"dims.json artic_length_m = {dv('artic_length_m')} (expected 16.47, ADR 0019); re-derive the scenario geometry")
    if z1 - z0 < dv("tyre_diameter_m"):
        errs.append("block shorter than a tyre diameter: wheels never fully climb it")
    if errs:
        sys.exit("generate_stage2_scenarios: kerb geometry check FAILED (not loosening anything):\n  " + "\n  ".join(errs))
    return box


def airtime(mx, variant, arg=0, src=""):
    return chk("max_wheel_airtime_s", mx=mx, arg=arg, variant=variant, source=src)


# Kerb strike at 50 km/h. Thresholds are regression guards on the 2026-11-09 baseline of the core (WORKING_VALUE, not
# requirements) and are STRICT: do not raise them to make a run pass. A failing run is a physics finding, report it
# (test_scenario_strictness.py fails if these are loosened). The 14 cm hop is a known weakness (phone saw ~0.4 s axle lift).
KERB = {  # h_cm: (height, fz_ceiling, fz_src, off_empty, off_laden, tractor_axle_empty, all_empty, tractor_axle_laden, all_laden)
    5: (0.05, 2.2, "sim 2026-11-09: 1.79 empty / 1.67 laden", 0.08, 0.03, 0.03, 0.05, 0.03, 0.03),
    14: (0.14, 4.2, "sim 2026-11-09: 3.90 empty / 3.53 laden", 0.75, 0.28, 0.15, 0.25, 0.12, 0.12),
}
OFFSRC = "regression guard on measured value 2026-11-09 (union over 10 wheel ends; dominated by the drop off the kerb end, see PHYSICS_VALIDATION)"
AXSRC = "axle flight: longest single-wheel unload; tractor target < 0.15 s (lead brief 2026-11-09)"
ALLSRC = "axle flight: longest single-wheel unload; target < 0.15 s (lead brief 2026-11-09)"
TRIDEM = "regression guard on measured value 2026-11-09 (empty tridem: axle 1 hangs at full droop while axles 2-3 are still on the kerb; frame torsion not modelled)"
for h_cm, (ft, fzmax, fzsrc, off_e, off_l, ax_e, all_e, ax_l, all_l) in KERB.items():
    base = [chk("max_dv_step_ms", mx=0.35, source="no impulse spikes (phone single-step jolt was 0.6-0.7 m/s; sim baseline <= 0.1)"),
            chk("max_pos_jump_m", mx=1e-6, source="no teleport"),
            chk("max_fz_ratio", mx=fzmax, source=f"bounded wheel load peaks ({fzsrc}; phone saw 6.8)"),
            chk("max_trailer_roll_deg", mx=8, source="geometric roll plus overshoot"),
            chk("max_fifth_wheel_error_mm", mx=5, source="constraint holds"),
            chk("wheel_off_ground_time_s", mx=off_e, variant="empty", source=OFFSRC),
            chk("wheel_off_ground_time_s", mx=off_l, variant="laden40", source=OFFSRC),
            airtime(ax_e, "empty", 1, AXSRC),
            airtime(all_e, "empty", 0, TRIDEM if h_cm == 14 else ALLSRC),
            airtime(ax_l, "laden40", 1, AXSRC),
            airtime(all_l, "laden40", 0, ALLSRC)]
    sc(f"curb_strike_{h_cm}cm_50kmh_comb",
       f"Left wheels of the whole combination hit a {h_cm} cm kerb face at 50 km/h",
       "docs/04 s6.11", 10,
       {"type": "speedhold", "targetKmh": 50}, base,
       variants=["empty", "laden40"], initial={"speedKmh": 50},
       ground={"gradePercent": 0, "surface": "dry_asphalt", "boxes": [kerb_box(ft, 30, 33)]})

# Phone event reconstruction (DEVICE-RUN-2026-11-09 r3, s = 598 m): the per-step suspension + tyre travel on the phone
# shows a ~27 cm effective step at 42 km/h with 40 t, not a 14 cm kerb (PHYSICS_VALIDATION s3a). Regression guards.
sc("kerb_step_27cm_42kmh_comb",
   "Phone event reconstruction (DEVICE-RUN-2026-11-09 r3, s = 598 m): 40 t at 42 km/h, left wheels hit a 27 cm effective step (kerb on a higher carriageway edge)",
   "docs/04 s6.11; docs/PHYSICS_VALIDATION.md s3a", 6,
   {"type": "speedhold", "targetKmh": 42},
   [chk("max_dv_step_ms", mx=0.35, source="no impulse spikes (same limit as the 14 cm kerb strike)"),
    chk("max_pos_jump_m", mx=1e-6, source="no teleport"),
    chk("max_fz_ratio", mn=5.2, mx=7.5, source="regression guard on measured 6.50 (phone 6.8x); a 27 cm step is above the tyre envelope a vertical-ray contact can climb smoothly"),
    chk("max_wheel_airtime_s", mx=0.5, arg=1, source="regression guard on measured 0.42 s (phone: both front wheels unloaded ~0.4 s)"),
    chk("max_fifth_wheel_error_mm", mx=5, source="constraint holds")],
   variants=["laden40"], initial={"speedKmh": 42},
   ground={"gradePercent": 0, "surface": "dry_asphalt", "boxes": [kerb_box(0.27, 30, 33)]})

sc("speed_bump_comb","Speed bump 7 cm x 0.5 m across the lane at 15 km/h", "docs/04 s6.11", 12,
   {"type": "speedhold", "targetKmh": 15},
   [chk("max_dv_step_ms", mx=0.35, source="no impulse spikes"),
    chk("max_pos_jump_m", mx=1e-6, source="no teleport"),
    chk("max_fz_ratio", mx=4, source="bounded wheel load peaks"),
    chk("max_cab_heave_mm", mx=50, source="cab mounts stay inside their travel (soft stops)")],
   variants=ALL3, initial={"speedKmh": 15},
   ground={"gradePercent": 0, "surface": "dry_asphalt", "boxes": [{"minX": -5, "maxX": 5, "minZ": 10, "maxZ": 10.5, "height": 0.07}]})

# ---------------- 14. soak ----------------
sc("soak_30min_cycle", "30 min simulated: 20 x (accelerate to 80, double lane change, brake to stop, stand)", "docs/04 s6.14", 1800,
   {"type": "soak", "targetKmh": 80, "cyclePeriod": 90},
   [chk("max_fifth_wheel_error_mm", mx=5, source="no constraint drift over 30 min"),
    chk("max_dv_step_ms", mx=0.35, source="no spikes"),
    chk("mean_speed_kmh", mn=60, mx=82, frm=30, to=50, source="first cycle cruise"),
    chk("mean_speed_kmh", mn=60, mx=82, frm=1740, to=1760, source="last cycle cruise (compare with first: no drift)"),
    chk("max_speed_after_ms", mx=0.002, frm=85, to=89.9, source="standstill in the first cycle"),
    chk("max_speed_after_ms", mx=0.002, frm=1795, to=1799.9, source="standstill in the last cycle: no energy growth"),
    chk("min_air_service_bar", mn=8, source="air supply sustains the duty cycle"),
    chk("max_articulation_deg", mx=12, source="lane changes stay tame")],
   variants=["laden40"], sampleEvery=5)

sc("soak_30min_parked", "30 min simulated parked with the engine idling", "docs/04 s6.14", 1800,
   {"type": "timeline", "keys": [key(0, park=True, sel="N")]},
   [chk("drift_m", mx=0.005, frm=5, source="no creep"), chk("max_speed_after_ms", mx=0.001, frm=5, source="no energy drift / oscillation"),
    chk("max_kinetic_energy_j", mx=1e-3, frm=5, source="no energy growth"),
    chk("min_air_service_bar", mn=10.5, frm=5, source="governor keeps the reservoirs in the cut-in/cut-out band")] + stable,
   variants=["laden40"], initial={"parkingBrake": True}, sampleEvery=5)

# ---------------- 15. steering sign ----------------
for sel, st, exp in [("D", 0.3, "right"), ("R", 0.15, "reverse_right")]:
    if sel == "D":
        ch = [chk("yaw_rate_mean_dps", mn=1, frm=4, status=D, source="Unity frame: +steer = right = +yaw about +Y (same as solo)")]
        keys = [key(0, throttle=0.3, steer=st)]
        init = {"speedKmh": 15}
    else:
        ch = [chk("yaw_rate_mean_dps", mx=-0.3, frm=4, status=D, source="reversing with right steer: tractor yaws negative (same sign as solo)")]
        keys = [key(0, brake=1, sel="R"), key(1, throttle=0.25, steer=st, sel="R")]
        init = {}
    sc(f"steer_sign_{exp}_comb", f"Steering sign with trailer ({exp})", "docs/04 s6.15", 8,
       {"type": "timeline", "keys": keys}, ch + [stable[0]], variants=COMB, initial=init)

# ---------------- coupling ----------------
sc("couple_uncouple", "Trailer on landing gear; tractor reverses under it, couples, raises legs, drives 15 m, parks, lowers legs, uncouples, drives away",
   "docs/04 s2.9", 75,
   {"type": "timeline", "keys": [key(0, brake=1, sel="R"), key(1, throttle=0.05, sel="R"), key(6, brake=1, sel="R"),
                                 key(7, brake=1), key(17, throttle=0.25), key(25, brake=0.6), key(30, park=True, sel="N"),
                                 key(50, brake=1), key(52, throttle=0.25), key(65, brake=0.5)]},
   [chk("coupling_events", mn=1, mx=1, source="jaw locks once"),
    chk("kingpin_load_vs_static", mn=0.9, mx=1.1, frm=20, to=24, status=D, source="kingpin load after coupling and raising the legs = static nose load"),
    chk("uncoupling_events", mn=1, mx=1, source="released once"),
    chk("tractor_trailer_distance_m", mn=8, source="tractor drove away"),
    chk("trailer_drift_m", mx=0.03, frm=50, source="uncoupled trailer held by its emergency/spring brakes on the legs"),
    chk("max_dv_step_ms", mx=0.35, source="coupling impact spread by the compliant jaw engagement (0.4 s, 4 Hz); no solver explosion"),
    chk("max_kingpin_long_kn", mx=150, frm=2, to=8, source="coupling bump at idle-creep approach stays moderate (compliant engagement)"),
    chk("wheel_lift", mx=0, frm=40, source="uncoupling with the legs taking the nose load: the tractor does not jump")],
   variants=COMB, overrides={"coupled": False, "trailerGap": 2.0},
   events=[{"t": 0.5, "type": "couple_arm"}, {"t": 8, "type": "landing_gear_up"},
           {"t": 31, "type": "landing_gear_down"}, {"t": 48, "type": "uncouple"}])

# ---------------- AMT manual ----------------
sc("manual_mode_shifts", "Manual mode: start in 2nd, shift up by hand, try an over-revving downshift at speed (must be rejected)",
   "docs/04 s2.7", 40,
   {"type": "timeline", "keys": [key(0, brake=1, manual=True), key(0.5, brake=1, manual=True, up=True), key(1.0, throttle=1, manual=True),
                                 key(6, throttle=1, manual=True, up=True), key(6.2, throttle=1, manual=True),
                                 key(11, throttle=1, manual=True, up=True), key(11.2, throttle=1, manual=True),
                                 key(16, throttle=1, manual=True, up=True), key(16.2, throttle=1, manual=True),
                                 key(22, throttle=1, manual=True, down=True), key(22.2, throttle=1, manual=True),
                                 key(23, manual=True, down=True), key(23.2, manual=True), key(23.4, manual=True, down=True), key(23.6, manual=True),
                                 key(23.8, manual=True, down=True), key(24, manual=True)]},
   [chk("max_gear", mn=5, mx=5, source="driver-selected gears 2 -> 5 only (no automatic upshift in manual)"),
    chk("rejected_shifts", mn=1, source="over-revving downshift refused"),
    chk("max_rpm", mx=2130, frm=1, source="S1: max revs 2100 rpm (governor fade) respected in manual; 30 rpm overshoot allowance"),
    chk("stalled", mx=0, source="no stall")],
   variants=["laden40"])
print("ok")
