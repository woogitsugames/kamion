"""ADR 0228 (B-077, gate 2): jackknife / tractor-trailer body contact and heavy-landing scenarios.

Writes tests/physics/scenarios/jackknife_*.json and drop_05m_comb.json (or into the folder given as argv[1]).
Run: python tests/physics/generate_jackknife_scenarios.py [out_dir]
Limits: ADR 0228 "Kryteria". Measured values in the check sources are from the runner at the ADR commit.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tests/physics/scenarios"
W, D = "WORKING_VALUE", "DERIVED"
ADR = "ADR 0228"


def chk(metric, mn=None, mx=None, status=W, source="", arg=0, frm=0, to=0, variant=""):
    c = {"metric": metric, "status": status, "source": source}
    if arg:
        c["arg"] = arg
    if frm:
        c["from"] = frm
    if to:
        c["to"] = to
    if variant:
        c["variant"] = variant
    if mn is not None:
        c["min"] = mn
    if mx is not None:
        c["max"] = mx
    return c


def key(t, throttle=0.0, brake=0.0, steer=0.0, sel="R"):
    return {"t": t, "throttle": throttle, "brake": brake, "steer": steer, "parkingBrake": False, "selector": sel}


def sc(id, desc, duration, keys, checks, articulation=30.0, variants=("empty", "laden40"), initial=None, extra=None, combination=None):
    d = {
        "schemaVersion": 1,
        "id": id,
        "description": desc,
        "spec": f"docs/04 s6.9/s6.10, {ADR} (B-077, gate 2)",
        **({"combination": combination} if combination else {"variants": list(variants)}),
        "ground": {"gradePercent": 0, "surface": "dry_asphalt"},
        "initial": initial or {},
        "overrides": {"articulationDeg": articulation},
        "duration": duration,
        "dt": 0.01,
        "substeps": 4,
        "driver": {"type": "timeline", "keys": keys},
        "checks": checks,
    }
    if extra:
        d.update(extra)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{id}.json").write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# Common robustness checks of every contact scenario.
def robust(dv=0.35):
    return [
        chk("nan_detected", mx=0, source="no NaN (solver explosion)"),
        chk("max_pos_jump_m", mx=1e-4, source="no teleport |dx_com - v dt| <= 1e-4 m"),
        chk("max_dv_step_ms", mx=dv, source="per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58)"),
        chk("max_fifth_wheel_error_mm", mx=5, source="kingpin stays in the jaw through the contact (driving limit 5 mm)"),
    ]


GEO = ("first contact of the level combination at 117.12 deg (trailer side wall, half width 1.275 m, on the cab rear "
       "corner x 1.245 m, 2.07 m ahead of the kingpin; CouplingContact.FirstContactArticulationDeg, analytic in "
       "JackknifeContactTests)")

# 1. Fold to ~90-110 deg in reverse and stop: no artificial 90 deg stop any more, and no contact below the geometric angle.
#    The empty combination folds faster (lighter trailer), so it brakes earlier: one file per load.
for sid, comb, brake_t in (("jackknife_fold_90_reverse_comb", "laden40", 5.15), ("jackknife_fold_90_reverse_empty", "empty", 4.05)):
    sc(sid,
       f"ADR 0228 ({comb}): reversing with full lock from 30 deg articulation folds the combination past 90 deg, then the "
       "driver brakes. Before ADR 0228 an angular stop held the articulation at 90 deg (F1 tolerance 3.5 deg); now the limit "
       "is the body contact at 117.1 deg, so the fold passes 90 deg freely and nothing touches.",
       10, [key(0, brake=1), key(1, throttle=0.3, steer=1), key(brake_t, brake=1, steer=1)],
       robust() + [
           chk("max_articulation_deg", mn=95, mx=112, source=f"folds past the old 90 deg angular stop plus its 3.5 deg F1 tolerance (93.5 deg) and stays clear of the cab ({GEO})"),
           chk("coupling_contact_s", mx=0, source="no tractor-trailer contact below the geometric contact angle"),
           chk("max_coupling_penetration_m", mx=0, source="no tractor-trailer penetration"),
       ], combination=comb)

# 2. Keep folding into the cab ("120 deg" command) and push for 3 s, then brake.
sc("jackknife_fold_120_reverse_comb",
   "ADR 0228: reversing with full lock from 30 deg and keeping the throttle on after the trailer side wall meets the "
   "cab rear corner (the driver asks for ~120 deg): the body contact stops the fold near 117 deg, the drive axle pushes "
   "the trailer into the cab for ~3 s, then the driver brakes.",
   14, [key(0, brake=1), key(1, throttle=0.3, steer=1), key(9, brake=1, steer=1)],
   robust() + [
       chk("coupling_contact_s", mn=1, source="the trailer reaches the cab and stays on it"),
       chk("articulation_limit_excess_deg", mx=2.5, source=f"articulation beyond the geometric contact angle ({GEO}); measured 1.4-1.7 deg = crush + plate pitch / roll lean"),
       chk("max_coupling_penetration_m", mx=0.07, source="cab corner / trailer side crush while the drive axle pushes (5 Hz soft contact, measured 0.046-0.051 m) <= 7 cm"),
       chk("coupling_contact_restitution", mx=0.1, source="no rebound off the cab (crushing panels; recovery speed 0.05 m/s)"),
       chk("max_body_rate_dps", mx=60, source="no spin-up: body angular rates stay at the folding rates (< 40 deg/s measured)"),
   ])

# 3. Fast fold: full throttle in reverse, the trailer swings into the cab at the highest yaw rate reachable in reverse.
sc("jackknife_fast_fold_impact_comb",
   "ADR 0228: full throttle in reverse with full lock from 30 deg (reverse gear, ~12 km/h): the trailer swings into "
   "the cab at the largest relative yaw rate the tractor can produce in reverse, then the driver brakes.",
   12, [key(0, brake=1), key(1, throttle=1.0, steer=1), key(7, brake=1, steer=1)],
   robust() + [
       chk("coupling_contact_s", mn=1, source="the trailer reaches the cab"),
       chk("max_articulation_rate_dps", mn=30, source="a real swing impact: relative yaw rate before the contact >= 30 deg/s"),
       chk("articulation_limit_excess_deg", mx=2.5, source=f"articulation beyond the geometric contact angle ({GEO})"),
       chk("max_coupling_penetration_m", mx=0.07, source="peak crush at the swing impact (measured 0.050-0.053 m) <= 7 cm"),
       chk("coupling_contact_restitution", mx=0.1, source="no rebound off the cab"),
       chk("max_body_rate_dps", mx=60, source="no spin-up after the impact"),
   ])

# 4. Reversing with counter-steer, then pulling forward to straighten.
sc("jackknife_reverse_countersteer_comb",
   "ADR 0228: reversing with full lock folds the combination; at ~60 deg the driver counter-steers while still reversing "
   "(too late: the empty trailer still folds into the cab, the laden one stops at ~110 deg), stops, then pulls forward "
   "with the lock towards the trailer side for 3.5 s and straight on, which straightens the combination.",
   40, [key(0, brake=1), key(1, throttle=0.3, steer=1), key(4.5, throttle=0.3, steer=-1), key(9, brake=1, steer=-1),
        key(10, brake=1, steer=1, sel="D"), key(11, throttle=0.3, steer=1, sel="D"), key(14.5, throttle=0.3, steer=0, sel="D"),
        key(36, brake=0.5, steer=0, sel="D")],
   robust() + [
       chk("max_articulation_deg", mn=60, source="the counter-steer comes after the fold is deep"),
       chk("articulation_limit_excess_deg", mx=2.5, source=f"articulation beyond the geometric contact angle ({GEO})"),
       chk("max_coupling_penetration_m", mx=0.07, source="body contact crush <= 7 cm"),
       chk("final_articulation_deg", mx=15, source="pulling forward unfolds the combination (no sticking at the cab)"),
       chk("max_body_rate_dps", mx=60, source="no spin-up"),
   ])

# 6. Review P1 (REVIEW-2026-11-15-s22-code-113): a tight forward turn (55-60 deg articulation, the ordinary yard manoeuvre)
#    must not touch the cab, also when the driver stops hard and the trailer pitches on the plate. With the flat-fronted
#    graybox box (corner 2.063 m, 7 mm to the cab) a stop from a tight turn gave false contact (trailer "braked" by the cab);
#    the coupling geometry now follows the art model's rounded front (swing 2.029 m, BodyCoupling + Nose boxes).
NOSE = ("trailer front swing radius 2.029 m (art model trailer_manifest.json measured.front_swing 2.0294; coupling boxes "
        "BodyCoupling + Nose) vs cab back 2.07 m ahead of the kingpin: 4.1 cm clearance when level")
for sid, kmh, steer in (("jackknife_tight_turn_forward_comb", 5, 0.57), ("jackknife_tight_turn_forward_10_comb", 10, -0.57)):
    sc(sid,
       f"ADR 0228, review P1: forward at {kmh} km/h with a steady {abs(steer):.2f} lock ({'left' if steer > 0 else 'right'}) until the "
       "articulation settles at ~57-60 deg, then a full service-brake stop with the lock held (trailer pitches on the plate, "
       "tractor rocks back after the stop). Nothing may touch: no false cab contact braking the trailer in a yard turn.",
       50, [], robust() + [
           chk("max_articulation_deg", mn=55, mx=61, frm=30, to=40, source="steady tight turn: 55-60 deg articulation (review P1 range)"),
           chk("max_speed_kmh", mn=kmh - 0.5, mx=kmh + 0.5, frm=30, to=40, source=f"steady {kmh} km/h before the stop"),
           chk("coupling_contact_s", mx=0, source=f"no tractor-trailer contact ({NOSE})"),
           chk("max_coupling_penetration_m", mx=0, source="no tractor-trailer penetration"),
           chk("max_coupling_contact_force_kn", mx=0, source="no contact force"),
       ], articulation=0,
       extra={"driver": {"type": "speedhold", "targetKmh": kmh, "steer": steer, "selector": "D", "brakeAt": 40, "brakeLevel": 1}})

# 7. ADR 0228 "Otwarte 1" residual (review P2-113-1, H11 probes artifacts/jackknife-0228/h11/probe_scenarios): a hard stop
#    from 15-20 km/h in a 48-56 deg turn, laden, ends with the trailer front brushing the cab after the stop. The peak force
#    comes in the first contact step at ~0 mm penetration (the speculative contact stops the closing speed of ~1 km/h within
#    1-3 steps); the 0.6 mm penetration is a later step. Measured on alt-113-s24 (PR #113 + D79 7.63 m, 2026-11-18):
#    laden40 20 km/h: 1.10 s, 75.9 kN, 0.155 mm; 15 km/h: 0.09 s, 90.5 kN, 0.610 mm; empty: no contact. Bounds = regression
#    guards (review proposal 100 kN / 1.5 s), not a requirement; the residual is a dimension / feel decision (Otwarte 1).
for sid, kmh, steer in (("jackknife_turn_stop_brush_20_comb", 20, 0.55), ("jackknife_turn_stop_brush_15_comb", 15, 0.57)):
    sc(sid,
       f"ADR 0228 Otwarte 1 (review P2-113-1): forward at {kmh} km/h with a steady {steer:.2f} lock until the articulation "
       "settles (~48-56 deg), then a full service-brake stop with the lock held. The laden trailer may brush the cab after "
       "the stop (known residual); the brush must stay short, shallow and below 100 kN.",
       50, [], robust() + [
           chk("coupling_contact_s", mx=1.5, source="residual brush after the stop: measured 1.10 s (20 km/h) / 0.09 s (15 km/h) laden, 0 empty (review P2-113-1 bound 1.5 s)"),
           chk("max_coupling_contact_force_kn", mx=100, source="first-step stop of a ~1 km/h closing speed: measured 75.9 kN (20 km/h) / 90.5 kN (15 km/h) laden, 0 empty (review P2-113-1 bound 100 kN)"),
           chk("max_coupling_penetration_m", mx=0.001, source="sub-millimetre brush: measured 0.155 mm / 0.610 mm laden"),
       ], articulation=0,
       extra={"driver": {"type": "speedhold", "targetKmh": kmh, "steer": steer, "selector": "D", "brakeAt": 40, "brakeLevel": 1}})

# 5. Heavy landing: 0.5 m drop at standstill.
sc("drop_05m_comb",
   "ADR 0228 (B-077, ADR 0158 Open 4): the coupled combination lifted 0.5 m above its equilibrium pose and released at "
   "standstill. Before ADR 0228 the laden combination gave back 68 % of the drop energy and took off again (elastic bump stops, lossless tyres). "
   "Checks the share of the drop energy returned as the first rebound and the time spent airborne again.",
   6, [key(0, sel="D")],
   [
       chk("nan_detected", mx=0, source="no NaN"),
       chk("free_flight_s", mn=0.2, status=D, source="the drop is a flight: sqrt(2 * 0.4 / 9.81) = 0.29 s (wheels hang below the static pose)"),
       chk("max_free_flight_energy_gain_j", mx=1, source="E = KE + PE does not grow in free flight"),
       chk("drop_rebound_ratio", mx=0.45, source="damped landing: <= 45 % of the drop energy comes back as the first rebound (ADR 0228 criterion; before ADR 0228: 0.68 laden40 / 0.37 empty, measured after: 0.35 / 0.14)"),
       chk("drop_relaunch_s", mx=0.1, source="the combination does not take off again after the landing"),
       chk("max_body_penetration_m", mx=0.05, source="chassis does not dig into the road (ADR 0165 bumper-crush bound)"),
       chk("min_com_height_m", mn=0.5, source="no fall-through"),
       chk("max_fifth_wheel_error_mm", mx=15, source="coupling holds through the landing (free_fall_drop_comb bound)"),
   ], articulation=0, initial={"dropHeight": 0.5})
print("written", OUT)
