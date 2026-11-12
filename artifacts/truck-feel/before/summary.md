# Physics validation run 2026-11-12 15:05  (commit 52029731)

| scenario | metric | value | min | max | status | source |
|---|---|---|---|---|---|---|
| launch_flat_comb_part60@empty | rollback_m | 2.418E-05 |  | 0.02 | PASS | WORKING_VALUE: no rollback on flat |
| launch_flat_comb_part60@empty | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_flat_comb_part60@empty | min_rpm [1..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near idle or above |
| launch_flat_comb_part60@empty | time_to_kmh(50) | 13.92 | 8 | 30 | PASS | DERIVED: part load: plausibility around the Proctor/Grimes SAE 950136 traffic averages (bobtail 0.138 g, box 0.106 g over the first 50 ft) |
| launch_flat_comb_part60@empty | max_shift_retard_torque_nm [1..end s] | 0 |  | 1 | PASS | WORKING_VALUE: ADR 0004 addendum 2026-11-10: no vehicle braking during an up-shift |
| launch_flat_comb_part60@empty | max_shift_eye_pitch_swing_deg(1.5) [1..30 s] | 4.495 |  | 3 | **FAIL** | WORKING_VALUE: ADR 0134 regression guard (WORKING_VALUE): per-shift eye nod at 60 % pedal |
| launch_flat_comb_part60@empty | max_clutch_temp_c | 28.36 |  | 250 | PASS | WORKING_VALUE: clutch below the warning temperature on a flat start |
| launch_flat_comb_part60@empty | max_dv_step_ms | 0.02847 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_flat_comb_part60@empty | max_fifth_wheel_error_mm | 0.006973 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| launch_flat_comb_part60@laden40 | rollback_m | 0.0001558 |  | 0.02 | PASS | WORKING_VALUE: no rollback on flat |
| launch_flat_comb_part60@laden40 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_flat_comb_part60@laden40 | min_rpm [1..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near idle or above |
| launch_flat_comb_part60@laden40 | time_to_kmh(50) | 32.91 | 15 | 45 | PASS | DERIVED: part load 40 t: ~3.5 ft/s2 max from rest for 27-36 t trucks (Washburn freight curriculum 4.1, engineering estimate) -> >= 13 s to 50 km/h |
| launch_flat_comb_part60@laden40 | max_shift_retard_torque_nm [1..end s] | 0 |  | 1 | PASS | WORKING_VALUE: ADR 0004 addendum 2026-11-10: no vehicle braking during an up-shift |
| launch_flat_comb_part60@laden40 | max_shift_eye_pitch_swing_deg(1.5) [1..30 s] | 3.226 |  | 3 | **FAIL** | WORKING_VALUE: ADR 0134 regression guard (WORKING_VALUE): per-shift eye nod at 60 % pedal |
| launch_flat_comb_part60@laden40 | max_clutch_temp_c | 35.36 |  | 250 | PASS | WORKING_VALUE: clutch below the warning temperature on a flat start |
| launch_flat_comb_part60@laden40 | max_dv_step_ms | 0.01574 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_flat_comb_part60@laden40 | max_fifth_wheel_error_mm | 0.004631 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
