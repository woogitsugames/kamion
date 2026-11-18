# Physics validation run 2026-11-15 17:56  (commit 57a496b50)

| scenario | metric | value | min | max | status | source |
|---|---|---|---|---|---|---|
| brake_80_0_dry_abs_comb@empty | max_dv_step_ms | 0.07623 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| brake_80_0_dry_abs_comb@empty | max_fifth_wheel_error_mm | 0.01444 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| brake_80_0_dry_abs_comb@empty | stop_distance_m | 39.19 | 35 | 61.2 | PASS | SOURCED: upper bound = 0.15 v + v^2/130 at 80 km/h = 61.2 m: UN R13 Annex 4 type-0 N3 (table confirmed via GRRF-56-3, unece.org TRANS-WP29-GRRF-56-inf03e; cells did not extract from the MLIT PDF S5); lower bound ~ v^2/(2 x 0.8 g) + build-up |
| brake_80_0_dry_abs_comb@empty | mfdd_ms2 | 7.422 | 5 | 8 | PASS | SOURCED: MFDD (R13 Annex 4 definition); 5.0 m/s^2 = N3 type-0 minimum dm (same GRRF-56-3 table); <= mu g |
| brake_80_0_dry_abs_comb@empty | max_lateral_deviation_m | 5.737E-06 |  | 0.5 | PASS | WORKING_VALUE: straight-line stability under ABS |
| brake_80_0_dry_abs_comb@empty | max_articulation_deg | 0 |  | 2 | PASS | WORKING_VALUE: no trailer swing under ABS braking on a straight |
| brake_80_0_dry_abs_comb@empty | rear_lock_time_s | 0 |  | 0.03 | PASS | WORKING_VALUE: Stage 2 fix: no tractor drive-axle lock at brake onset (EBS load sensing + decel-threshold ABS) |
| brake_80_0_dry_abs_comb@empty | trailer_lock_time_s | 0 |  | 0.05 | PASS | WORKING_VALUE: trailer ABS 2S/2M prevents lock |
| brake_80_0_dry_abs_comb@laden40 | max_dv_step_ms | 0.07183 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| brake_80_0_dry_abs_comb@laden40 | max_fifth_wheel_error_mm | 0.0272 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| brake_80_0_dry_abs_comb@laden40 | stop_distance_m | 41.25 | 35 | 61.2 | PASS | SOURCED: upper bound = 0.15 v + v^2/130 at 80 km/h = 61.2 m: UN R13 Annex 4 type-0 N3 (table confirmed via GRRF-56-3, unece.org TRANS-WP29-GRRF-56-inf03e; cells did not extract from the MLIT PDF S5); lower bound ~ v^2/(2 x 0.8 g) + build-up |
| brake_80_0_dry_abs_comb@laden40 | mfdd_ms2 | 6.899 | 5 | 8 | PASS | SOURCED: MFDD (R13 Annex 4 definition); 5.0 m/s^2 = N3 type-0 minimum dm (same GRRF-56-3 table); <= mu g |
| brake_80_0_dry_abs_comb@laden40 | max_lateral_deviation_m | 8.911E-06 |  | 0.5 | PASS | WORKING_VALUE: straight-line stability under ABS |
| brake_80_0_dry_abs_comb@laden40 | max_articulation_deg | 0 |  | 2 | PASS | WORKING_VALUE: no trailer swing under ABS braking on a straight |
| brake_80_0_dry_abs_comb@laden40 | rear_lock_time_s | 0 |  | 0.03 | PASS | WORKING_VALUE: Stage 2 fix: no tractor drive-axle lock at brake onset (EBS load sensing + decel-threshold ABS) |
| brake_80_0_dry_abs_comb@laden40 | trailer_lock_time_s | 0 |  | 0.05 | PASS | WORKING_VALUE: trailer ABS 2S/2M prevents lock |
| drop_05m_comb@empty | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN |
| drop_05m_comb@empty | free_flight_s | 0.27 | 0.2 |  | PASS | DERIVED: the drop is a flight: sqrt(2 * 0.4 / 9.81) = 0.29 s (wheels hang below the static pose) |
| drop_05m_comb@empty | max_free_flight_energy_gain_j | 0 |  | 1 | PASS | WORKING_VALUE: E = KE + PE does not grow in free flight |
| drop_05m_comb@empty | drop_rebound_ratio | 0.1623 |  | 0.45 | PASS | WORKING_VALUE: damped landing: <= 45 % of the drop energy comes back as the first rebound (ADR 0228 criterion; before ADR 0228: 0.68 laden40 / 0.37 empty, measured after: 0.35 / 0.14) |
| drop_05m_comb@empty | drop_relaunch_s | 0 |  | 0.1 | PASS | WORKING_VALUE: the combination does not take off again after the landing |
| drop_05m_comb@empty | max_body_penetration_m | 0 |  | 0.05 | PASS | WORKING_VALUE: chassis does not dig into the road (ADR 0165 bumper-crush bound) |
| drop_05m_comb@empty | min_com_height_m | 0.8856 | 0.5 |  | PASS | WORKING_VALUE: no fall-through |
| drop_05m_comb@empty | max_fifth_wheel_error_mm | 0.02934 |  | 15 | PASS | WORKING_VALUE: coupling holds through the landing (free_fall_drop_comb bound) |
| drop_05m_comb@laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN |
| drop_05m_comb@laden40 | free_flight_s | 0.25 | 0.2 |  | PASS | DERIVED: the drop is a flight: sqrt(2 * 0.4 / 9.81) = 0.29 s (wheels hang below the static pose) |
| drop_05m_comb@laden40 | max_free_flight_energy_gain_j | 0 |  | 1 | PASS | WORKING_VALUE: E = KE + PE does not grow in free flight |
| drop_05m_comb@laden40 | drop_rebound_ratio | 0.389 |  | 0.45 | PASS | WORKING_VALUE: damped landing: <= 45 % of the drop energy comes back as the first rebound (ADR 0228 criterion; before ADR 0228: 0.68 laden40 / 0.37 empty, measured after: 0.35 / 0.14) |
| drop_05m_comb@laden40 | drop_relaunch_s | 0 |  | 0.1 | PASS | WORKING_VALUE: the combination does not take off again after the landing |
| drop_05m_comb@laden40 | max_body_penetration_m | 0 |  | 0.05 | PASS | WORKING_VALUE: chassis does not dig into the road (ADR 0165 bumper-crush bound) |
| drop_05m_comb@laden40 | min_com_height_m | 0.8383 | 0.5 |  | PASS | WORKING_VALUE: no fall-through |
| drop_05m_comb@laden40 | max_fifth_wheel_error_mm | 0.04901 |  | 15 | PASS | WORKING_VALUE: coupling holds through the landing (free_fall_drop_comb bound) |
| free_fall_drop_comb | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN |
| free_fall_drop_comb | free_flight_s | 0.56 | 0.3 |  | PASS | DERIVED: the drop really is a flight: free fall of ~0.9 m (wheels hang below the static pose) lasts ~sqrt(2*0.9/9.81) = 0.43 s; require >= 0.3 s |
| free_fall_drop_comb | max_free_flight_energy_gain_j | 0 |  | 1 | PASS | WORKING_VALUE: no energy source in free flight: E = KE + PE must not grow between samples |
| free_fall_drop_comb | max_free_flight_accel_error_ms2 | 0.007663 |  | 0.05 | PASS | DERIVED: |a_com - g| <= aero drag 0.5*rho*CdA*v^2/M: rho 1.2, CdA <= 7.5 m^2 (tractor 6.0 + trailer 1.5, VehicleDefinition/TrailerDefinition), v <= 9 m/s, M >= 30 t -> 0.0122 m/s^2; limit 0.05 |
| free_fall_drop_comb | max_body_penetration_m | 0.002546 |  | 0.05 | PASS | WORKING_VALUE: ADR 0165: at the 1 m-drop landing (4.4 m/s, nose pitched 8 deg down, bump stops) the tractor Bumper bottom corner reaches the road and its plastic cover crushes; the ADR 0158 rigid contact touched too (2 speculative corners at t 1.46 s) but reported 0 by construction. Limit 0.05 m = same bumper-strike crush bound as kerb_step_27cm_42kmh_comb. Measured 0.025 m |
| free_fall_drop_comb | min_com_height_m | 0.7449 | 0.5 |  | PASS | WORKING_VALUE: no fall-through: the tractor CoM (1.05 m static) may dip on the bump stops at the 1 m-drop landing (measured 0.737 m) but stays well above the road |
| free_fall_drop_comb | max_fifth_wheel_error_mm | 0.6401 |  | 15 | PASS | WORKING_VALUE: coupling holds through a 1 m-drop landing (4.4 m/s impact; measured 7.5 mm, driving limit is 5 mm), no blow-up |
| fuzz_shrink_speed_runaway_fulllock | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN |
| fuzz_shrink_speed_runaway_fulllock | max_pos_jump_m | 7.157E-15 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v*dt| <= 1e-4 m |
| fuzz_shrink_speed_runaway_fulllock | max_dv_step_ms [0..3.5 s] | 0.1284 |  | 0.35 | PASS | WORKING_VALUE: driving phase before the rollover: per-step velocity change <= 0.35 m/s (kerb-scenario ceiling) |
| fuzz_shrink_speed_runaway_fulllock | max_dv_step_ms | 0.9464 |  | 4.2 | PASS | DERIVED: whole run incl. the side impact: <= sqrt(2 g dh) = 4.18 m/s, dh = 0.89 m = trailer CoM drop from its tip-over apex (2.164 m) to lying on its side (1.275 m = half width), ADR 0158; measured 2.04 m/s |
| fuzz_shrink_speed_runaway_fulllock | max_tire_friction_ratio | 1 |  | 1.001 | PASS | WORKING_VALUE: sqrt(Fx^2+Fy^2) <= mu*Fz, margin 0.001 |
| fuzz_shrink_speed_runaway_fulllock | articulation_limit_excess_deg | 0 |  | 3.5 | PASS | WORKING_VALUE: D59 (owner, 2026-11-13) / ADR 0158 F1, ADR 0165: articulation may exceed the fifth-wheel soft yaw stop (yawLimitDeg = 90, yawStopFrequencyHz 3, tractor_4x2_generic.vehicle.json) by <= 3.5 deg; a stiffer stop (>= 4.5 Hz) breaks the 0.35 m/s jerk limit (ADR 0158 table). Measured max 3.33 deg (M34 hunt) |
| fuzz_shrink_speed_runaway_fulllock | max_fifth_wheel_error_mm [0..3.5 s] | 0.7541 |  | 5 | PASS | WORKING_VALUE: driving phase: kingpin constraint error <= 5 mm |
| fuzz_shrink_speed_runaway_fulllock | max_fifth_wheel_error_mm | 14.92 |  | 50 | PASS | WORKING_VALUE: whole run: coupling holds through the side impact (measured 24.5 mm peak at landing, 9 mm lying: colliders and the soft kingpin joint are slightly over-constrained), no blow-up; ADR 0158 |
| fuzz_shrink_speed_runaway_fulllock | min_air_all_bar | 8.5 | 0 |  | PASS | WORKING_VALUE: no negative air pressure |
| fuzz_shrink_speed_runaway_fulllock | max_speed_kmh | 30.24 |  | 90.5 | PASS | WORKING_VALUE: EU limiter 90 km/h (docs/04 s5), same margin as top_speed_flat_comb (+0.5); before ADR 0158: 275.4 km/h |
| fuzz_shrink_speed_runaway_fulllock | min_com_height_m | 1.06 | 0.9 |  | PASS | WORKING_VALUE: no fall-through: both CoMs stay above the road (static tractor CoM 1.05 m, lying on its side >= 1.25 m); before ADR 0158: -3070 m |
| fuzz_shrink_speed_runaway_fulllock | max_body_penetration_m | 0.08542 |  | 0.1 | PASS | DERIVED: ADR 0165 compliant contact (4 Hz, zeta 1 per corner effective mass): side-impact peak crush <= v/(e*omega) + n*g/omega^2 = 4.18/(e*25.1) + 2*9.81/25.1^2 = 0.061 + 0.031 = 0.092 m (v = DERIVED impact bound of this scenario, n = 2 g corner load of the lying trailer); limit 0.10 m. A real curtain-sider roof rail / cab corner crushes decimetres in a rollover (UNVERIFIED). Measured 0.090 m (trailer Body corner, t 4.12 s); ADR 0158 rigid contact: 0.0004 m |
| fuzz_shrink_speed_runaway_fulllock | max_body_penetration_m [10..end s] | 0.02859 |  | 0.035 | PASS | WORKING_VALUE: ADR 0165: lying at rest the static sink n*g/omega^2 = 2*9.81/25.1^2 = 0.031 m; limit 0.035 m (no visible sinking of the lying trailer on a phone screen). Measured 0.030 m |
| fuzz_shrink_speed_runaway_fulllock | body_contact_s | 25.91 | 1 |  | PASS | WORKING_VALUE: the rollover ends on the chassis colliders (scenario meaning), ADR 0158 |
| fuzz_shrink_speed_runaway_fulllock | max_free_flight_energy_gain_j | 0 |  | 1 | PASS | WORKING_VALUE: no energy source in free flight: E = KE + PE must not grow between samples, ADR 0158 |
| fuzz_shrink_speed_runaway_fulllock | max_energy_j | 2.055E+06 |  | 2.133E+06 | PASS | WORKING_VALUE: throttle 0.378 only replaces losses while upright; nothing may raise E above its t=0 value (2.031 MJ) + 5 % (measured max 2.055 MJ at t~0.5 s, +1.2 %) |
| fuzz_shrink_speed_runaway_fulllock | max_speed_after_ms [8..end s] | 1.38E-07 |  | 0.05 | PASS | WORKING_VALUE: the overturned combination slides to a stop (body friction 0.6 = Unity default PhysicsMaterial) and stays at rest |
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
| jackknife_fold_90_reverse_comb | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN (solver explosion) |
| jackknife_fold_90_reverse_comb | max_pos_jump_m | 6.665E-16 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v dt| <= 1e-4 m |
| jackknife_fold_90_reverse_comb | max_dv_step_ms | 0.06427 |  | 0.35 | PASS | WORKING_VALUE: per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58) |
| jackknife_fold_90_reverse_comb | max_fifth_wheel_error_mm | 0.1324 |  | 5 | PASS | WORKING_VALUE: kingpin stays in the jaw through the contact (driving limit 5 mm) |
| jackknife_fold_90_reverse_comb | max_articulation_deg | 108.6 | 95 | 112 | PASS | WORKING_VALUE: folds past the old 90 deg angular stop plus its 3.5 deg F1 tolerance (93.5 deg) and stays clear of the cab (first contact of the level combination at 117.12 deg (trailer side wall, half width 1.275 m, on the cab rear corner x 1.245 m, 2.07 m ahead of the kingpin; CouplingContact.FirstContactArticulationDeg, analytic in JackknifeContactTests)) |
| jackknife_fold_90_reverse_comb | coupling_contact_s | 0 |  | 0 | PASS | WORKING_VALUE: no tractor-trailer contact below the geometric contact angle |
| jackknife_fold_90_reverse_comb | max_coupling_penetration_m | 0 |  | 0 | PASS | WORKING_VALUE: no tractor-trailer penetration |
| jackknife_fold_90_reverse_empty | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN (solver explosion) |
| jackknife_fold_90_reverse_empty | max_pos_jump_m | 6.065E-16 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v dt| <= 1e-4 m |
| jackknife_fold_90_reverse_empty | max_dv_step_ms | 0.06093 |  | 0.35 | PASS | WORKING_VALUE: per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58) |
| jackknife_fold_90_reverse_empty | max_fifth_wheel_error_mm | 0.1978 |  | 5 | PASS | WORKING_VALUE: kingpin stays in the jaw through the contact (driving limit 5 mm) |
| jackknife_fold_90_reverse_empty | max_articulation_deg | 105.4 | 95 | 112 | PASS | WORKING_VALUE: folds past the old 90 deg angular stop plus its 3.5 deg F1 tolerance (93.5 deg) and stays clear of the cab (first contact of the level combination at 117.12 deg (trailer side wall, half width 1.275 m, on the cab rear corner x 1.245 m, 2.07 m ahead of the kingpin; CouplingContact.FirstContactArticulationDeg, analytic in JackknifeContactTests)) |
| jackknife_fold_90_reverse_empty | coupling_contact_s | 0 |  | 0 | PASS | WORKING_VALUE: no tractor-trailer contact below the geometric contact angle |
| jackknife_fold_90_reverse_empty | max_coupling_penetration_m | 0 |  | 0 | PASS | WORKING_VALUE: no tractor-trailer penetration |
| jackknife_reverse_countersteer_comb@empty | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN (solver explosion) |
| jackknife_reverse_countersteer_comb@empty | max_pos_jump_m | 4.14E-14 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v dt| <= 1e-4 m |
| jackknife_reverse_countersteer_comb@empty | max_dv_step_ms | 0.1624 |  | 0.35 | PASS | WORKING_VALUE: per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58) |
| jackknife_reverse_countersteer_comb@empty | max_fifth_wheel_error_mm | 1.522 |  | 5 | PASS | WORKING_VALUE: kingpin stays in the jaw through the contact (driving limit 5 mm) |
| jackknife_reverse_countersteer_comb@empty | max_articulation_deg | 118.5 | 60 |  | PASS | WORKING_VALUE: the counter-steer comes after the fold is deep |
| jackknife_reverse_countersteer_comb@empty | articulation_limit_excess_deg | 1.385 |  | 2.5 | PASS | WORKING_VALUE: articulation beyond the geometric contact angle (first contact of the level combination at 117.12 deg (trailer side wall, half width 1.275 m, on the cab rear corner x 1.245 m, 2.07 m ahead of the kingpin; CouplingContact.FirstContactArticulationDeg, analytic in JackknifeContactTests)) |
| jackknife_reverse_countersteer_comb@empty | max_coupling_penetration_m | 0.04627 |  | 0.07 | PASS | WORKING_VALUE: body contact crush <= 7 cm |
| jackknife_reverse_countersteer_comb@empty | final_articulation_deg | 1.401E-08 |  | 15 | PASS | WORKING_VALUE: pulling forward unfolds the combination (no sticking at the cab) |
| jackknife_reverse_countersteer_comb@empty | max_body_rate_dps | 34.85 |  | 60 | PASS | WORKING_VALUE: no spin-up |
| jackknife_reverse_countersteer_comb@laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN (solver explosion) |
| jackknife_reverse_countersteer_comb@laden40 | max_pos_jump_m | 2.124E-14 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v dt| <= 1e-4 m |
| jackknife_reverse_countersteer_comb@laden40 | max_dv_step_ms | 0.07116 |  | 0.35 | PASS | WORKING_VALUE: per-step velocity change <= 0.35 m/s (kerb jerk ceiling, ADR 0165 / D58) |
| jackknife_reverse_countersteer_comb@laden40 | max_fifth_wheel_error_mm | 0.2306 |  | 5 | PASS | WORKING_VALUE: kingpin stays in the jaw through the contact (driving limit 5 mm) |
| jackknife_reverse_countersteer_comb@laden40 | max_articulation_deg | 111.6 | 60 |  | PASS | WORKING_VALUE: the counter-steer comes after the fold is deep |
| jackknife_reverse_countersteer_comb@laden40 | articulation_limit_excess_deg | 0 |  | 2.5 | PASS | WORKING_VALUE: articulation beyond the geometric contact angle (first contact of the level combination at 117.12 deg (trailer side wall, half width 1.275 m, on the cab rear corner x 1.245 m, 2.07 m ahead of the kingpin; CouplingContact.FirstContactArticulationDeg, analytic in JackknifeContactTests)) |
| jackknife_reverse_countersteer_comb@laden40 | max_coupling_penetration_m | 0.00126 |  | 0.07 | PASS | WORKING_VALUE: body contact crush <= 7 cm |
| jackknife_reverse_countersteer_comb@laden40 | final_articulation_deg | 0.0004844 |  | 15 | PASS | WORKING_VALUE: pulling forward unfolds the combination (no sticking at the cab) |
| jackknife_reverse_countersteer_comb@laden40 | max_body_rate_dps | 33.05 |  | 60 | PASS | WORKING_VALUE: no spin-up |
| jackknife_wet_curve_noabs@empty | max_articulation_deg | 87.45 | 30 |  | PASS | WORKING_VALUE: jackknife must be possible: lightly loaded drive axle locks first without load sensing, empty trailer pushes (classic driver/defect case) |
| jackknife_wet_curve_noabs@empty | rear_lock_time_s | 2.53 | 0.5 |  | PASS | WORKING_VALUE: drive axle locks without ABS |
| jackknife_wet_curve_noabs@empty | max_dv_step_ms | 0.04639 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| jackknife_wet_curve_noabs@laden40 | rear_lock_time_s | 4.52 | 0.5 |  | PASS | WORKING_VALUE: drive axle locks without ABS |
| jackknife_wet_curve_noabs@laden40 | max_dv_step_ms | 0.0413 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| jackknife_wet_curve_retarder_noabs@empty | max_articulation_deg | 119.3 | 30 |  | PASS | WORKING_VALUE: retarder on a slippery road without ABS cut-off: drive axle lock -> jackknife (why retarders are cut by ABS) |
| jackknife_wet_curve_retarder_noabs@empty | rear_lock_time_s | 2.75 | 0.2 |  | PASS | WORKING_VALUE: drive axle locks |
| jackknife_wet_curve_retarder_noabs@empty | max_dv_step_ms | 0.2952 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| jackknife_wet_curve_retarder_noabs@laden40 | rear_lock_time_s | 0.87 | 0.2 |  | PASS | WORKING_VALUE: drive axle locks |
| jackknife_wet_curve_retarder_noabs@laden40 | max_dv_step_ms | 0.2404 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| reverse_dock_s_maneuver_comb@empty | max_articulation_deg | 118.1 | 20 |  | PASS | WORKING_VALUE: >=20 deg proves the manoeuvre actually articulated (the 0.55 lock folds it into the cab, ADR 0228) |
| reverse_dock_s_maneuver_comb@empty | articulation_limit_excess_deg | 0.9737 |  | 1.5 | PASS | WORKING_VALUE: ADR 0228: the fold is stopped by the tractor-trailer body contact (trailer side wall on the cab rear corner, 117.12 deg level); measured ~1 deg incl. crush and plate-pitch lean (was: angular 90 deg stop, max 95) |
| reverse_dock_s_maneuver_comb@empty | max_coupling_penetration_m | 0.03317 |  | 0.05 | PASS | WORKING_VALUE: ADR 0228: cab / trailer crush while the drive axle pushes the trailer into the cab <= 5 cm |
| reverse_dock_s_maneuver_comb@empty | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: all wheels stay loaded while reversing |
| reverse_dock_s_maneuver_comb@empty | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| reverse_dock_s_maneuver_comb@empty | min_speed_kmh | -9.659 | -15 | -2 | PASS | WORKING_VALUE: dock reversing speed bounded: SpeedFwd < 0 in reverse, so |v| <= 15 km/h means min_speed_kmh >= -15; <= -2 km/h proves it actually reversed (integration r5: with selector D the S-steer path still ends at z -7.5 m, so final_z alone passed) |
| reverse_dock_s_maneuver_comb@empty | final_z_m | -34.05 |  | -3 | PASS | WORKING_VALUE: vehicle actually reversed (heading 0: forward = +z, so z must decrease by >= 3 m in 30 s) |
| reverse_dock_s_maneuver_comb@empty | max_dv_step_ms | 0.1051 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| reverse_dock_s_maneuver_comb@empty | max_fifth_wheel_error_mm | 1.376 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| reverse_dock_s_maneuver_comb@laden40 | max_articulation_deg | 118.2 | 20 |  | PASS | WORKING_VALUE: >=20 deg proves the manoeuvre actually articulated (the 0.55 lock folds it into the cab, ADR 0228) |
| reverse_dock_s_maneuver_comb@laden40 | articulation_limit_excess_deg | 1.043 |  | 1.5 | PASS | WORKING_VALUE: ADR 0228: the fold is stopped by the tractor-trailer body contact (trailer side wall on the cab rear corner, 117.12 deg level); measured ~1 deg incl. crush and plate-pitch lean (was: angular 90 deg stop, max 95) |
| reverse_dock_s_maneuver_comb@laden40 | max_coupling_penetration_m | 0.03417 |  | 0.05 | PASS | WORKING_VALUE: ADR 0228: cab / trailer crush while the drive axle pushes the trailer into the cab <= 5 cm |
| reverse_dock_s_maneuver_comb@laden40 | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: all wheels stay loaded while reversing |
| reverse_dock_s_maneuver_comb@laden40 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| reverse_dock_s_maneuver_comb@laden40 | min_speed_kmh | -9.677 | -15 | -2 | PASS | WORKING_VALUE: dock reversing speed bounded: SpeedFwd < 0 in reverse, so |v| <= 15 km/h means min_speed_kmh >= -15; <= -2 km/h proves it actually reversed (integration r5: with selector D the S-steer path still ends at z -7.5 m, so final_z alone passed) |
| reverse_dock_s_maneuver_comb@laden40 | final_z_m | -33.62 |  | -3 | PASS | WORKING_VALUE: vehicle actually reversed (heading 0: forward = +z, so z must decrease by >= 3 m in 30 s) |
| reverse_dock_s_maneuver_comb@laden40 | max_dv_step_ms | 0.1421 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| reverse_dock_s_maneuver_comb@laden40 | max_fifth_wheel_error_mm | 0.8424 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
