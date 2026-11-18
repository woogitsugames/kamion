# Physics validation run 2026-11-16 08:16  (commit 1027ae772)

| scenario | metric | value | min | max | status | source |
|---|---|---|---|---|---|---|
| jackknife_fast_fold_impact_comb@empty | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN (solver explosion) |
| jackknife_fast_fold_impact_comb@empty | max_pos_jump_m | 1.327E-15 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v dt| <= 1e-4 m |
| jackknife_fast_fold_impact_comb@empty | max_dv_step_ms | 0.1681 |  | 0.35 | PASS | WORKING_VALUE: per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58) |
| jackknife_fast_fold_impact_comb@empty | max_fifth_wheel_error_mm | 1.289 |  | 5 | PASS | WORKING_VALUE: kingpin stays in the jaw through the contact (driving limit 5 mm) |
| jackknife_fast_fold_impact_comb@empty | coupling_contact_s | 7.12 | 1 |  | PASS | WORKING_VALUE: the trailer reaches the cab |
| jackknife_fast_fold_impact_comb@empty | max_articulation_rate_dps | 54.28 | 30 |  | PASS | WORKING_VALUE: a real swing impact: relative yaw rate before the contact >= 30 deg/s |
| jackknife_fast_fold_impact_comb@empty | articulation_limit_excess_deg | 1.564 |  | 2.5 | PASS | WORKING_VALUE: articulation beyond the geometric contact angle (first contact of the level combination at 117.12 deg (trailer side wall, half width 1.275 m, on the cab rear corner x 1.245 m, 2.07 m ahead of the kingpin; CouplingContact.FirstContactArticulationDeg, analytic in JackknifeContactTests)) |
| jackknife_fast_fold_impact_comb@empty | max_coupling_penetration_m | 0.05284 |  | 0.07 | PASS | WORKING_VALUE: peak crush at the swing impact (measured 0.050-0.053 m) <= 7 cm |
| jackknife_fast_fold_impact_comb@empty | coupling_contact_restitution | 0.02894 |  | 0.1 | PASS | WORKING_VALUE: no rebound off the cab |
| jackknife_fast_fold_impact_comb@empty | max_body_rate_dps | 33.93 |  | 60 | PASS | WORKING_VALUE: no spin-up after the impact |
| jackknife_fast_fold_impact_comb@laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN (solver explosion) |
| jackknife_fast_fold_impact_comb@laden40 | max_pos_jump_m | 1.329E-15 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v dt| <= 1e-4 m |
| jackknife_fast_fold_impact_comb@laden40 | max_dv_step_ms | 0.2253 |  | 0.35 | PASS | WORKING_VALUE: per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58) |
| jackknife_fast_fold_impact_comb@laden40 | max_fifth_wheel_error_mm | 0.6025 |  | 5 | PASS | WORKING_VALUE: kingpin stays in the jaw through the contact (driving limit 5 mm) |
| jackknife_fast_fold_impact_comb@laden40 | coupling_contact_s | 7.28 | 1 |  | PASS | WORKING_VALUE: the trailer reaches the cab |
| jackknife_fast_fold_impact_comb@laden40 | max_articulation_rate_dps | 53.26 | 30 |  | PASS | WORKING_VALUE: a real swing impact: relative yaw rate before the contact >= 30 deg/s |
| jackknife_fast_fold_impact_comb@laden40 | articulation_limit_excess_deg | 1.67 |  | 2.5 | PASS | WORKING_VALUE: articulation beyond the geometric contact angle (first contact of the level combination at 117.12 deg (trailer side wall, half width 1.275 m, on the cab rear corner x 1.245 m, 2.07 m ahead of the kingpin; CouplingContact.FirstContactArticulationDeg, analytic in JackknifeContactTests)) |
| jackknife_fast_fold_impact_comb@laden40 | max_coupling_penetration_m | 0.05023 |  | 0.07 | PASS | WORKING_VALUE: peak crush at the swing impact (measured 0.050-0.053 m) <= 7 cm |
| jackknife_fast_fold_impact_comb@laden40 | coupling_contact_restitution | 0.0281 |  | 0.1 | PASS | WORKING_VALUE: no rebound off the cab |
| jackknife_fast_fold_impact_comb@laden40 | max_body_rate_dps | 35.06 |  | 60 | PASS | WORKING_VALUE: no spin-up after the impact |
| jackknife_fold_120_reverse_comb@empty | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN (solver explosion) |
| jackknife_fold_120_reverse_comb@empty | max_pos_jump_m | 1.345E-15 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v dt| <= 1e-4 m |
| jackknife_fold_120_reverse_comb@empty | max_dv_step_ms | 0.1596 |  | 0.35 | PASS | WORKING_VALUE: per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58) |
| jackknife_fold_120_reverse_comb@empty | max_fifth_wheel_error_mm | 1.298 |  | 5 | PASS | WORKING_VALUE: kingpin stays in the jaw through the contact (driving limit 5 mm) |
| jackknife_fold_120_reverse_comb@empty | coupling_contact_s | 9.32 | 1 |  | PASS | WORKING_VALUE: the trailer reaches the cab and stays on it |
| jackknife_fold_120_reverse_comb@empty | articulation_limit_excess_deg | 1.501 |  | 2.5 | PASS | WORKING_VALUE: articulation beyond the geometric contact angle (first contact of the level combination at 117.12 deg (trailer side wall, half width 1.275 m, on the cab rear corner x 1.245 m, 2.07 m ahead of the kingpin; CouplingContact.FirstContactArticulationDeg, analytic in JackknifeContactTests)); measured 1.4-1.7 deg = crush + plate pitch / roll lean |
| jackknife_fold_120_reverse_comb@empty | max_coupling_penetration_m | 0.05071 |  | 0.07 | PASS | WORKING_VALUE: cab corner / trailer side crush while the drive axle pushes (5 Hz soft contact, measured 0.046-0.051 m) <= 7 cm |
| jackknife_fold_120_reverse_comb@empty | coupling_contact_restitution | 0.03027 |  | 0.1 | PASS | WORKING_VALUE: no rebound off the cab (crushing panels; recovery speed 0.05 m/s) |
| jackknife_fold_120_reverse_comb@empty | max_body_rate_dps | 32.65 |  | 60 | PASS | WORKING_VALUE: no spin-up: body angular rates stay at the folding rates (< 40 deg/s measured) |
| jackknife_fold_120_reverse_comb@laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN (solver explosion) |
| jackknife_fold_120_reverse_comb@laden40 | max_pos_jump_m | 1.354E-15 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v dt| <= 1e-4 m |
| jackknife_fold_120_reverse_comb@laden40 | max_dv_step_ms | 0.1965 |  | 0.35 | PASS | WORKING_VALUE: per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58) |
| jackknife_fold_120_reverse_comb@laden40 | max_fifth_wheel_error_mm | 0.6898 |  | 5 | PASS | WORKING_VALUE: kingpin stays in the jaw through the contact (driving limit 5 mm) |
| jackknife_fold_120_reverse_comb@laden40 | coupling_contact_s | 7.47 | 1 |  | PASS | WORKING_VALUE: the trailer reaches the cab and stays on it |
| jackknife_fold_120_reverse_comb@laden40 | articulation_limit_excess_deg | 1.479 |  | 2.5 | PASS | WORKING_VALUE: articulation beyond the geometric contact angle (first contact of the level combination at 117.12 deg (trailer side wall, half width 1.275 m, on the cab rear corner x 1.245 m, 2.07 m ahead of the kingpin; CouplingContact.FirstContactArticulationDeg, analytic in JackknifeContactTests)); measured 1.4-1.7 deg = crush + plate pitch / roll lean |
| jackknife_fold_120_reverse_comb@laden40 | max_coupling_penetration_m | 0.04573 |  | 0.07 | PASS | WORKING_VALUE: cab corner / trailer side crush while the drive axle pushes (5 Hz soft contact, measured 0.046-0.051 m) <= 7 cm |
| jackknife_fold_120_reverse_comb@laden40 | coupling_contact_restitution | 0.03245 |  | 0.1 | PASS | WORKING_VALUE: no rebound off the cab (crushing panels; recovery speed 0.05 m/s) |
| jackknife_fold_120_reverse_comb@laden40 | max_body_rate_dps | 27.12 |  | 60 | PASS | WORKING_VALUE: no spin-up: body angular rates stay at the folding rates (< 40 deg/s measured) |
| jackknife_tight_turn_forward_10_comb@empty | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN (solver explosion) |
| jackknife_tight_turn_forward_10_comb@empty | max_pos_jump_m | 4.67E-15 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v dt| <= 1e-4 m |
| jackknife_tight_turn_forward_10_comb@empty | max_dv_step_ms | 0.08134 |  | 0.35 | PASS | WORKING_VALUE: per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58) |
| jackknife_tight_turn_forward_10_comb@empty | max_fifth_wheel_error_mm | 0.1765 |  | 5 | PASS | WORKING_VALUE: kingpin stays in the jaw through the contact (driving limit 5 mm) |
| jackknife_tight_turn_forward_10_comb@empty | max_articulation_deg [30..40 s] | 57.28 | 55 | 61 | PASS | WORKING_VALUE: steady tight turn: 55-60 deg articulation (review P1 range) |
| jackknife_tight_turn_forward_10_comb@empty | max_speed_kmh [30..40 s] | 10 | 9.5 | 10.5 | PASS | WORKING_VALUE: steady 10 km/h before the stop |
| jackknife_tight_turn_forward_10_comb@empty | coupling_contact_s | 0 |  | 0 | PASS | WORKING_VALUE: no tractor-trailer contact (trailer front swing radius 2.029 m (art model trailer_manifest.json measured.front_swing 2.0294; coupling boxes BodyCoupling + Nose) vs cab back 2.07 m ahead of the kingpin: 4.1 cm clearance when level) |
| jackknife_tight_turn_forward_10_comb@empty | max_coupling_penetration_m | 0 |  | 0 | PASS | WORKING_VALUE: no tractor-trailer penetration |
| jackknife_tight_turn_forward_10_comb@empty | max_coupling_contact_force_kn | 0 |  | 0 | PASS | WORKING_VALUE: no contact force |
| jackknife_tight_turn_forward_10_comb@laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN (solver explosion) |
| jackknife_tight_turn_forward_10_comb@laden40 | max_pos_jump_m | 4.426E-15 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v dt| <= 1e-4 m |
| jackknife_tight_turn_forward_10_comb@laden40 | max_dv_step_ms | 0.08054 |  | 0.35 | PASS | WORKING_VALUE: per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58) |
| jackknife_tight_turn_forward_10_comb@laden40 | max_fifth_wheel_error_mm | 0.163 |  | 5 | PASS | WORKING_VALUE: kingpin stays in the jaw through the contact (driving limit 5 mm) |
| jackknife_tight_turn_forward_10_comb@laden40 | max_articulation_deg [30..40 s] | 58.45 | 55 | 61 | PASS | WORKING_VALUE: steady tight turn: 55-60 deg articulation (review P1 range) |
| jackknife_tight_turn_forward_10_comb@laden40 | max_speed_kmh [30..40 s] | 9.997 | 9.5 | 10.5 | PASS | WORKING_VALUE: steady 10 km/h before the stop |
| jackknife_tight_turn_forward_10_comb@laden40 | coupling_contact_s | 0 |  | 0 | PASS | WORKING_VALUE: no tractor-trailer contact (trailer front swing radius 2.029 m (art model trailer_manifest.json measured.front_swing 2.0294; coupling boxes BodyCoupling + Nose) vs cab back 2.07 m ahead of the kingpin: 4.1 cm clearance when level) |
| jackknife_tight_turn_forward_10_comb@laden40 | max_coupling_penetration_m | 0 |  | 0 | PASS | WORKING_VALUE: no tractor-trailer penetration |
| jackknife_tight_turn_forward_10_comb@laden40 | max_coupling_contact_force_kn | 0 |  | 0 | PASS | WORKING_VALUE: no contact force |
| jackknife_tight_turn_forward_comb@empty | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN (solver explosion) |
| jackknife_tight_turn_forward_comb@empty | max_pos_jump_m | 4.987E-15 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v dt| <= 1e-4 m |
| jackknife_tight_turn_forward_comb@empty | max_dv_step_ms | 0.07223 |  | 0.35 | PASS | WORKING_VALUE: per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58) |
| jackknife_tight_turn_forward_comb@empty | max_fifth_wheel_error_mm | 0.04498 |  | 5 | PASS | WORKING_VALUE: kingpin stays in the jaw through the contact (driving limit 5 mm) |
| jackknife_tight_turn_forward_comb@empty | max_articulation_deg [30..40 s] | 57.62 | 55 | 61 | PASS | WORKING_VALUE: steady tight turn: 55-60 deg articulation (review P1 range) |
| jackknife_tight_turn_forward_comb@empty | max_speed_kmh [30..40 s] | 5.084 | 4.5 | 5.5 | PASS | WORKING_VALUE: steady 5 km/h before the stop |
| jackknife_tight_turn_forward_comb@empty | coupling_contact_s | 0 |  | 0 | PASS | WORKING_VALUE: no tractor-trailer contact (trailer front swing radius 2.029 m (art model trailer_manifest.json measured.front_swing 2.0294; coupling boxes BodyCoupling + Nose) vs cab back 2.07 m ahead of the kingpin: 4.1 cm clearance when level) |
| jackknife_tight_turn_forward_comb@empty | max_coupling_penetration_m | 0 |  | 0 | PASS | WORKING_VALUE: no tractor-trailer penetration |
| jackknife_tight_turn_forward_comb@empty | max_coupling_contact_force_kn | 0 |  | 0 | PASS | WORKING_VALUE: no contact force |
| jackknife_tight_turn_forward_comb@laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN (solver explosion) |
| jackknife_tight_turn_forward_comb@laden40 | max_pos_jump_m | 5.05E-15 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v dt| <= 1e-4 m |
| jackknife_tight_turn_forward_comb@laden40 | max_dv_step_ms | 0.07153 |  | 0.35 | PASS | WORKING_VALUE: per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58) |
| jackknife_tight_turn_forward_comb@laden40 | max_fifth_wheel_error_mm | 0.04033 |  | 5 | PASS | WORKING_VALUE: kingpin stays in the jaw through the contact (driving limit 5 mm) |
| jackknife_tight_turn_forward_comb@laden40 | max_articulation_deg [30..40 s] | 58.12 | 55 | 61 | PASS | WORKING_VALUE: steady tight turn: 55-60 deg articulation (review P1 range) |
| jackknife_tight_turn_forward_comb@laden40 | max_speed_kmh [30..40 s] | 4.978 | 4.5 | 5.5 | PASS | WORKING_VALUE: steady 5 km/h before the stop |
| jackknife_tight_turn_forward_comb@laden40 | coupling_contact_s | 0 |  | 0 | PASS | WORKING_VALUE: no tractor-trailer contact (trailer front swing radius 2.029 m (art model trailer_manifest.json measured.front_swing 2.0294; coupling boxes BodyCoupling + Nose) vs cab back 2.07 m ahead of the kingpin: 4.1 cm clearance when level) |
| jackknife_tight_turn_forward_comb@laden40 | max_coupling_penetration_m | 0 |  | 0 | PASS | WORKING_VALUE: no tractor-trailer penetration |
| jackknife_tight_turn_forward_comb@laden40 | max_coupling_contact_force_kn | 0 |  | 0 | PASS | WORKING_VALUE: no contact force |
| probe_turn55_stop_from20kmh@empty | max_articulation_deg | 52.38 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@empty | final_articulation_deg | 51.62 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@empty | max_articulation_deg [30..40 s] | 49.16 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@empty | max_speed_kmh [30..40 s] | 20 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@empty | coupling_contact_s | 0.22 |  | 0 | **FAIL** | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@empty | max_coupling_penetration_m | 0.00466 |  | 0 | **FAIL** | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@empty | max_coupling_contact_force_kn | 54.74 |  | 0 | **FAIL** | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@empty | max_dv_step_ms | 0.08133 |  | 1 | PASS | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@laden40 | max_articulation_deg | 49.45 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@laden40 | final_articulation_deg | 49.03 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@laden40 | max_articulation_deg [30..40 s] | 48.91 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@laden40 | max_speed_kmh [30..40 s] | 20 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@laden40 | coupling_contact_s | 6.79 |  | 0 | **FAIL** | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@laden40 | max_coupling_penetration_m | 0.0002179 |  | 0 | **FAIL** | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@laden40 | max_coupling_contact_force_kn | 70.98 |  | 0 | **FAIL** | WORKING_VALUE: x |
| probe_turn55_stop_from20kmh@laden40 | max_dv_step_ms | 0.08206 |  | 1 | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@empty | max_articulation_deg | 56.69 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@empty | final_articulation_deg | 56.41 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@empty | max_articulation_deg [30..40 s] | 55.32 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@empty | max_speed_kmh [30..40 s] | 15 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@empty | coupling_contact_s | 0 |  | 0 | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@empty | max_coupling_penetration_m | 0 |  | 0 | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@empty | max_coupling_contact_force_kn | 0 |  | 0 | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@empty | max_dv_step_ms | 0.08354 |  | 1 | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@laden40 | max_articulation_deg | 56.86 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@laden40 | final_articulation_deg | 56.36 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@laden40 | max_articulation_deg [30..40 s] | 56.19 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@laden40 | max_speed_kmh [30..40 s] | 15 | 0 |  | PASS | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@laden40 | coupling_contact_s | 0.16 |  | 0 | **FAIL** | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@laden40 | max_coupling_penetration_m | 0.0008534 |  | 0 | **FAIL** | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@laden40 | max_coupling_contact_force_kn | 66.59 |  | 0 | **FAIL** | WORKING_VALUE: x |
| probe_turn57_stop_from15kmh@laden40 | max_dv_step_ms | 0.08457 |  | 1 | PASS | WORKING_VALUE: x |
