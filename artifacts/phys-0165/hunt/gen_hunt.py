# ADR 0165 rollover hunt (same grid as ADR 0158): combination x throttle x steer x speed, 30 s each.
import json, sys, pathlib
root = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
base = json.loads((root / "tests/physics/scenarios/fuzz_shrink_speed_runaway_fulllock.json").read_text(encoding="utf-8"))
keep = {"nan_detected", "max_pos_jump_m", "max_tire_friction_ratio", "articulation_limit_excess_deg", "min_air_all_bar",
        "max_speed_kmh", "min_com_height_m", "max_free_flight_energy_gain_j"}
checks = [c for c in base["checks"] if c["metric"] in keep]
# whole-run limits only (no 'to'/'from' windows that are specific to the repro timing)
checks += [c for c in base["checks"] if c["metric"] in ("max_dv_step_ms", "max_fifth_wheel_error_mm", "max_body_penetration_m") and "to" not in c and "from" not in c]
checks += [{"metric": "body_contact_s", "status": "WORKING_VALUE", "source": "recorded only: > 0 = the run ended on the chassis colliders (rollover)", "min": 0}]
n = 0
for comb in ("empty", "cargo24", "laden40"):
    for thr in (0.2, 0.4, 0.6):
        for steer in (-1, 1):
            for v in (20, 30, 40, 50):
                sc = dict(base)
                sc["id"] = f"hunt_{comb}_t{int(thr*10)}_s{'L' if steer < 0 else 'R'}_{v}"
                sc["description"] = "ADR 0165 rollover hunt (grid of ADR 0158)"
                sc["combination"] = comb
                sc["initial"] = {"speedKmh": v}
                sc["driver"] = {"type": "timeline", "keys": [{"t": 0, "throttle": thr, "brake": 0, "steer": steer, "selector": "D"}]}
                sc["checks"] = checks
                (out / (sc["id"] + ".json")).write_text(json.dumps(sc, indent=1), encoding="utf-8")
                n += 1
print(n, "scenarios")
