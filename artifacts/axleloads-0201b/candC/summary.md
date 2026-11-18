# Physics validation run 2026-11-15 10:33  (commit 8962caf66)

| scenario | metric | value | min | max | status | source |
|---|---|---|---|---|---|---|
| air_leak_park_circuit@laden40 | trailer_emergency | 1 | 1 |  | PASS | WORKING_VALUE: red-line loss applies the trailer brakes (emergency relay valve) |
| air_leak_park_circuit@laden40 | min_speed_kmh [40..end s] | 0.0001277 |  | 0.5 | PASS | WORKING_VALUE: spring brakes + trailer emergency brake stop the combination |
| air_leak_park_circuit@laden40 | low_air_warning | 1 | 1 |  | PASS | WORKING_VALUE: warning |
| air_leak_rear_circuit@laden40 | low_air_warning | 1 | 1 |  | PASS | WORKING_VALUE: low-pressure warning must come on |
| air_leak_rear_circuit@laden40 | min_air_service_bar | 0 |  | 1 | PASS | WORKING_VALUE: rear circuit empties |
| air_leak_rear_circuit@laden40 | stop_distance_m | 32.51 |  | 52.4 | PASS | SOURCED: UN R13 Annex 4 2.4.1: residual braking N3 laden from 40 km/h: s <= 0.15 v + (100/30) v^2/115 = 52.4 m (test from 60 km/h is harder; ADR 0201 errata, was 2 v^2/130 at 60 km/h = M2/M3) |
| air_leak_rear_circuit@laden40 | max_lateral_deviation_m | 4.969E-07 |  | 1 | PASS | WORKING_VALUE: stable straight-line stop on the remaining circuits |
| brake_80_0_dry | stop_distance_m | 34.25 | 32 | 55 | PASS | WORKING_VALUE: v^2/(2 a) with WORKING mu plus 0.3-0.5 s pneumatic build-up; no sourced solo-tractor data |
| brake_80_0_dry | mfdd_ms2 | 7.718 | 5 | 8 | PASS | WORKING_VALUE: MFDD (UN R13 Annex 4 definition); lower bound 5.0 m/s^2 = believed UN R13 N3 type-0 minimum (UNVERIFIED), upper bound ~ mu*g |
| brake_80_0_dry | max_lateral_deviation_m | 1.706E-06 |  | 0.5 | PASS | WORKING_VALUE: straight-line stability under ABS braking |
| brake_80_0_dry | max_yaw_rate_dps | 0 |  | 2 | PASS | WORKING_VALUE: no spin / yaw instability under ABS braking |
| brake_80_0_dry | rear_lock_time_s | 0 |  | 0.03 | PASS | WORKING_VALUE: Stage 2 fix of the Stage 1 note: no ~0.1 s drive-axle lock at brake onset (EBS load sensing + wheel-deceleration ABS) |
| brake_80_0_dry_abs_comb@empty | max_dv_step_ms | 0.07644 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| brake_80_0_dry_abs_comb@empty | max_fifth_wheel_error_mm | 0.01463 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| brake_80_0_dry_abs_comb@empty | stop_distance_m | 39.16 | 35 | 61.2 | PASS | SOURCED: upper bound = 0.15 v + v^2/130 at 80 km/h = 61.2 m: UN R13 Annex 4 type-0 N3 (table confirmed via GRRF-56-3, unece.org TRANS-WP29-GRRF-56-inf03e; cells did not extract from the MLIT PDF S5); lower bound ~ v^2/(2 x 0.8 g) + build-up |
| brake_80_0_dry_abs_comb@empty | mfdd_ms2 | 7.432 | 5 | 8 | PASS | SOURCED: MFDD (R13 Annex 4 definition); 5.0 m/s^2 = N3 type-0 minimum dm (same GRRF-56-3 table); <= mu g |
| brake_80_0_dry_abs_comb@empty | max_lateral_deviation_m | 5.875E-06 |  | 0.5 | PASS | WORKING_VALUE: straight-line stability under ABS |
| brake_80_0_dry_abs_comb@empty | max_articulation_deg | 0 |  | 2 | PASS | WORKING_VALUE: no trailer swing under ABS braking on a straight |
| brake_80_0_dry_abs_comb@empty | rear_lock_time_s | 0 |  | 0.03 | PASS | WORKING_VALUE: Stage 2 fix: no tractor drive-axle lock at brake onset (EBS load sensing + decel-threshold ABS) |
| brake_80_0_dry_abs_comb@empty | trailer_lock_time_s | 0 |  | 0.05 | PASS | WORKING_VALUE: trailer ABS 2S/2M prevents lock |
| brake_80_0_dry_abs_comb@laden40 | max_dv_step_ms | 0.07441 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| brake_80_0_dry_abs_comb@laden40 | max_fifth_wheel_error_mm | 0.01661 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| brake_80_0_dry_abs_comb@laden40 | stop_distance_m | 41.35 | 35 | 61.2 | PASS | SOURCED: upper bound = 0.15 v + v^2/130 at 80 km/h = 61.2 m: UN R13 Annex 4 type-0 N3 (table confirmed via GRRF-56-3, unece.org TRANS-WP29-GRRF-56-inf03e; cells did not extract from the MLIT PDF S5); lower bound ~ v^2/(2 x 0.8 g) + build-up |
| brake_80_0_dry_abs_comb@laden40 | mfdd_ms2 | 6.877 | 5 | 8 | PASS | SOURCED: MFDD (R13 Annex 4 definition); 5.0 m/s^2 = N3 type-0 minimum dm (same GRRF-56-3 table); <= mu g |
| brake_80_0_dry_abs_comb@laden40 | max_lateral_deviation_m | 9.256E-06 |  | 0.5 | PASS | WORKING_VALUE: straight-line stability under ABS |
| brake_80_0_dry_abs_comb@laden40 | max_articulation_deg | 0 |  | 2 | PASS | WORKING_VALUE: no trailer swing under ABS braking on a straight |
| brake_80_0_dry_abs_comb@laden40 | rear_lock_time_s | 0 |  | 0.03 | PASS | WORKING_VALUE: Stage 2 fix: no tractor drive-axle lock at brake onset (EBS load sensing + decel-threshold ABS) |
| brake_80_0_dry_abs_comb@laden40 | trailer_lock_time_s | 0 |  | 0.05 | PASS | WORKING_VALUE: trailer ABS 2S/2M prevents lock |
| brake_80_0_dry_noabs_comb@solo | max_dv_step_ms | 0.07953 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| brake_80_0_dry_noabs_comb@solo | rear_lock_time_s | 3.1 | 0.3 |  | PASS | WORKING_VALUE: without ABS the wheels lock (expected behaviour, not a failure) |
| brake_80_0_dry_noabs_comb@solo | stop_distance_m | 44.14 | 30 | 150 | PASS | WORKING_VALUE: locked-wheel sliding friction bounds |
| brake_80_0_dry_noabs_comb@solo | stop_distance_m | 44.14 | 33 | 150 | PASS | WORKING_VALUE: no-ABS: locked or near-locked wheels |
| brake_80_0_dry_noabs_comb@empty | max_dv_step_ms | 0.0754 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| brake_80_0_dry_noabs_comb@empty | stop_distance_m | 43.93 | 30 | 150 | PASS | WORKING_VALUE: locked-wheel sliding friction bounds |
| brake_80_0_dry_noabs_comb@empty | stop_distance_m | 43.93 | 33 | 150 | PASS | WORKING_VALUE: no-ABS: locked or near-locked wheels |
| brake_80_0_dry_noabs_comb@laden40 | max_dv_step_ms | 0.07451 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| brake_80_0_dry_noabs_comb@laden40 | stop_distance_m | 49.19 | 30 | 150 | PASS | WORKING_VALUE: locked-wheel sliding friction bounds |
| brake_80_0_dry_noabs_comb@laden40 | stop_distance_m | 49.19 | 33 | 150 | PASS | WORKING_VALUE: no-ABS: locked or near-locked wheels |
| brake_80_0_wet | stop_distance_m | 50.81 | 45 | 85 | PASS | WORKING_VALUE: v^2/(2 a) with WORKING mu plus 0.3-0.5 s pneumatic build-up; no sourced solo-tractor data |
| brake_80_0_wet | mfdd_ms2 | 4.912 | 3 | 5.5 | PASS | WORKING_VALUE: MFDD band from wet peak mu ~0.5 (WORKING_VALUE) |
| brake_80_0_wet | max_lateral_deviation_m | 1.321E-06 |  | 0.5 | PASS | WORKING_VALUE: straight-line stability under ABS braking |
| brake_80_0_wet | max_yaw_rate_dps | 0 |  | 2 | PASS | WORKING_VALUE: no spin / yaw instability under ABS braking |
| brake_80_0_wet_abs_comb@empty | max_dv_step_ms | 0.05067 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| brake_80_0_wet_abs_comb@empty | max_fifth_wheel_error_mm | 0.0094 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| brake_80_0_wet_abs_comb@empty | stop_distance_m | 55.19 | 45 | 95 | PASS | WORKING_VALUE: mu_wet ~0.5 (WORKING): v^2/(2 x 0.45 g) + build-up |
| brake_80_0_wet_abs_comb@empty | mfdd_ms2 | 4.798 | 3 | 5.5 | PASS | WORKING_VALUE: <= mu_wet g |
| brake_80_0_wet_abs_comb@empty | max_lateral_deviation_m | 4.641E-06 |  | 0.5 | PASS | WORKING_VALUE: straight-line stability under ABS |
| brake_80_0_wet_abs_comb@empty | max_articulation_deg | 0 |  | 2 | PASS | WORKING_VALUE: no trailer swing under ABS braking on a straight |
| brake_80_0_wet_abs_comb@empty | rear_lock_time_s | 0 |  | 0.03 | PASS | WORKING_VALUE: Stage 2 fix: no tractor drive-axle lock at brake onset (EBS load sensing + decel-threshold ABS) |
| brake_80_0_wet_abs_comb@empty | trailer_lock_time_s | 0 |  | 0.05 | PASS | WORKING_VALUE: trailer ABS 2S/2M prevents lock |
| brake_80_0_wet_abs_comb@laden40 | max_dv_step_ms | 0.05455 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| brake_80_0_wet_abs_comb@laden40 | max_fifth_wheel_error_mm | 0.01203 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| brake_80_0_wet_abs_comb@laden40 | stop_distance_m | 56.8 | 45 | 95 | PASS | WORKING_VALUE: mu_wet ~0.5 (WORKING): v^2/(2 x 0.45 g) + build-up |
| brake_80_0_wet_abs_comb@laden40 | mfdd_ms2 | 4.683 | 3 | 5.5 | PASS | WORKING_VALUE: <= mu_wet g |
| brake_80_0_wet_abs_comb@laden40 | max_lateral_deviation_m | 7.498E-06 |  | 0.5 | PASS | WORKING_VALUE: straight-line stability under ABS |
| brake_80_0_wet_abs_comb@laden40 | max_articulation_deg | 2.175E-05 |  | 2 | PASS | WORKING_VALUE: no trailer swing under ABS braking on a straight |
| brake_80_0_wet_abs_comb@laden40 | rear_lock_time_s | 0 |  | 0.03 | PASS | WORKING_VALUE: Stage 2 fix: no tractor drive-axle lock at brake onset (EBS load sensing + decel-threshold ABS) |
| brake_80_0_wet_abs_comb@laden40 | trailer_lock_time_s | 0 |  | 0.05 | PASS | WORKING_VALUE: trailer ABS 2S/2M prevents lock |
| brake_80_0_wet_noabs_comb@solo | max_dv_step_ms | 0.04888 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| brake_80_0_wet_noabs_comb@solo | rear_lock_time_s | 5.99 | 0.3 |  | PASS | WORKING_VALUE: without ABS the wheels lock (expected behaviour, not a failure) |
| brake_80_0_wet_noabs_comb@solo | stop_distance_m | 75.58 | 30 | 150 | PASS | WORKING_VALUE: locked-wheel sliding friction bounds |
| brake_80_0_wet_noabs_comb@empty | max_dv_step_ms | 0.04962 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| brake_80_0_wet_noabs_comb@empty | stop_distance_m | 78.32 | 30 | 150 | PASS | WORKING_VALUE: locked-wheel sliding friction bounds |
| brake_80_0_wet_noabs_comb@laden40 | max_dv_step_ms | 0.05205 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| brake_80_0_wet_noabs_comb@laden40 | stop_distance_m | 81.99 | 30 | 150 | PASS | WORKING_VALUE: locked-wheel sliding friction bounds |
| brake_response_static@solo | brake_response_s | 0.25 |  | 0.6 | PASS | SOURCED: UN R13 Annex 4 4.1.1: braking force on the least favourable axle within 0.6 s (criterion here: 75 % of the final chamber pressure; Annex 6 method not verified) |
| brake_response_static@solo | brake_response_s(1) | 0.31 |  | 0.6 | PASS | SOURCED: UN R13 Annex 4 4.1.1 |
| brake_response_static@solo | brake_response_s | 0.25 | 0.15 |  | PASS | WORKING_VALUE: pneumatic build-up is not instantaneous |
| brake_response_static@empty | brake_response_s | 0.25 |  | 0.6 | PASS | SOURCED: UN R13 Annex 4 4.1.1: braking force on the least favourable axle within 0.6 s (criterion here: 75 % of the final chamber pressure; Annex 6 method not verified) |
| brake_response_static@empty | brake_response_s(1) | 0.31 |  | 0.6 | PASS | SOURCED: UN R13 Annex 4 4.1.1 |
| brake_response_static@empty | brake_response_s | 0.25 | 0.15 |  | PASS | WORKING_VALUE: pneumatic build-up is not instantaneous |
| brake_response_static@empty | brake_response_s(2) | 0.54 |  | 0.6 | PASS | SOURCED: UN R13 Annex 4 4.1.1 (trailer axle: longest lines, cascaded lag) |
| brake_response_static@laden40 | brake_response_s | 0.25 |  | 0.6 | PASS | SOURCED: UN R13 Annex 4 4.1.1: braking force on the least favourable axle within 0.6 s (criterion here: 75 % of the final chamber pressure; Annex 6 method not verified) |
| brake_response_static@laden40 | brake_response_s(1) | 0.31 |  | 0.6 | PASS | SOURCED: UN R13 Annex 4 4.1.1 |
| brake_response_static@laden40 | brake_response_s | 0.25 | 0.15 |  | PASS | WORKING_VALUE: pneumatic build-up is not instantaneous |
| brake_response_static@laden40 | brake_response_s(2) | 0.53 |  | 0.6 | PASS | SOURCED: UN R13 Annex 4 4.1.1 (trailer axle) |
| brake_response_static@laden40 | brake_response_s(2) | 0.53 | 0.3 |  | PASS | WORKING_VALUE: trailer builds up later than the tractor (longer lines) |
| circle_r25_10kmh | radius_error_m [20..end s] | 0.02316 |  | 0.5 | PASS | WORKING_VALUE: path follower + vehicle hold the circle |
| circle_r25_10kmh | lat_accel_ms2 [20..end s] | 0.3082 | 0.278 | 0.34 | PASS | DERIVED: v^2/R = 0.309 m/s^2 +/-10% |
| circle_r25_10kmh | steer_vs_ackermann(3.7) [20..end s] | 1.012 | 0.9 | 1.6 | PASS | DERIVED: mean steer angle / atan(L/R), L=3.70 m: ~1 (kinematic) at low speed, >1 = understeer |
| circle_r25_10kmh | max_abs_roll_deg [20..end s] | 0.1731 |  | 3 | PASS | WORKING_VALUE: body roll sanity below 0.2 g |
| circle_r25_10kmh | mean_speed_kmh [20..end s] | 9.999 | 8.5 | 11.5 | PASS | WORKING_VALUE: speed controller holds the target |
| circle_r25_20kmh | radius_error_m [20..end s] | 0.09363 |  | 0.5 | PASS | WORKING_VALUE: path follower + vehicle hold the circle |
| circle_r25_20kmh | lat_accel_ms2 [20..end s] | 1.229 | 1.111 | 1.358 | PASS | DERIVED: v^2/R = 1.235 m/s^2 +/-10% |
| circle_r25_20kmh | steer_vs_ackermann(3.7) [20..end s] | 1.044 | 0.9 | 1.6 | PASS | DERIVED: mean steer angle / atan(L/R), L=3.70 m: ~1 (kinematic) at low speed, >1 = understeer |
| circle_r25_20kmh | max_abs_roll_deg [20..end s] | 0.6896 |  | 3 | PASS | WORKING_VALUE: body roll sanity below 0.2 g |
| circle_r25_20kmh | mean_speed_kmh [20..end s] | 20 | 18.5 | 21.5 | PASS | WORKING_VALUE: speed controller holds the target |
| circle_r50_10kmh_comb@empty | radius_error_m [30..end s] | 0.01903 |  | 0.6 | PASS | WORKING_VALUE: path following |
| circle_r50_10kmh_comb@empty | lat_accel_ms2 [30..end s] | 0.1543 | 0.1389 | 0.1698 | PASS | DERIVED: v^2/R |
| circle_r50_10kmh_comb@empty | trailer_offtracking_m [30..end s] | 0.6085 | 0.4 | 0.8 | PASS | DERIVED: steady low-speed offtracking: sqrt(R^2+e^2) vs sqrt(R^2+e^2-L^2) with e = 0.68 m, L = 7.7 m -> 0.59 m |
| circle_r50_10kmh_comb@empty | max_dv_step_ms | 0.0255 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| circle_r50_10kmh_comb@empty | max_fifth_wheel_error_mm | 0.00608 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| circle_r50_10kmh_comb@laden40 | radius_error_m [30..end s] | 0.02631 |  | 0.6 | PASS | WORKING_VALUE: path following |
| circle_r50_10kmh_comb@laden40 | lat_accel_ms2 [30..end s] | 0.1542 | 0.1389 | 0.1698 | PASS | DERIVED: v^2/R |
| circle_r50_10kmh_comb@laden40 | trailer_offtracking_m [30..end s] | 0.6034 | 0.4 | 0.8 | PASS | DERIVED: steady low-speed offtracking: sqrt(R^2+e^2) vs sqrt(R^2+e^2-L^2) with e = 0.68 m, L = 7.7 m -> 0.59 m |
| circle_r50_10kmh_comb@laden40 | max_dv_step_ms | 0.01435 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| circle_r50_10kmh_comb@laden40 | max_fifth_wheel_error_mm | 0.006732 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| circle_r50_20kmh | radius_error_m [20..end s] | 0.0456 |  | 0.5 | PASS | WORKING_VALUE: path follower + vehicle hold the circle |
| circle_r50_20kmh | lat_accel_ms2 [20..end s] | 0.6166 | 0.556 | 0.679 | PASS | DERIVED: v^2/R = 0.617 m/s^2 +/-10% |
| circle_r50_20kmh | steer_vs_ackermann(3.7) [20..end s] | 1.046 | 0.9 | 1.6 | PASS | DERIVED: mean steer angle / atan(L/R), L=3.70 m: ~1 (kinematic) at low speed, >1 = understeer |
| circle_r50_20kmh | max_abs_roll_deg [20..end s] | 0.3461 |  | 3 | PASS | WORKING_VALUE: body roll sanity below 0.2 g |
| circle_r50_20kmh | mean_speed_kmh [20..end s] | 20 | 18.5 | 21.5 | PASS | WORKING_VALUE: speed controller holds the target |
| circle_r50_35kmh | radius_error_m [20..end s] | 0.2476 |  | 0.5 | PASS | WORKING_VALUE: path follower + vehicle hold the circle |
| circle_r50_35kmh | lat_accel_ms2 [20..end s] | 1.88 | 1.701 | 2.079 | PASS | DERIVED: v^2/R = 1.890 m/s^2 +/-10% |
| circle_r50_35kmh | steer_vs_ackermann(3.7) [20..end s] | 1.14 | 0.9 | 1.6 | PASS | DERIVED: mean steer angle / atan(L/R), L=3.70 m: ~1 (kinematic) at low speed, >1 = understeer |
| circle_r50_35kmh | max_abs_roll_deg [20..end s] | 1.053 |  | 3 | PASS | WORKING_VALUE: body roll sanity below 0.2 g |
| circle_r50_35kmh | mean_speed_kmh [20..end s] | 35 | 33.5 | 36.5 | PASS | WORKING_VALUE: speed controller holds the target |
| circle_r50_35kmh_comb@empty | radius_error_m [30..end s] | 0.2498 |  | 0.6 | PASS | WORKING_VALUE: path following |
| circle_r50_35kmh_comb@empty | lat_accel_ms2 [30..end s] | 1.881 | 1.701 | 2.079 | PASS | DERIVED: v^2/R |
| circle_r50_35kmh_comb@empty | trailer_offtracking_m [30..end s] | 0.4824 | -0.5 | 0.55 | PASS | WORKING_VALUE: offtracking shrinks / reverses with speed (tire slip angles) |
| circle_r50_35kmh_comb@empty | max_trailer_roll_deg [30..end s] | 0.7233 |  | 4 | PASS | WORKING_VALUE: moderate roll at 0.19 g |
| circle_r50_35kmh_comb@empty | max_dv_step_ms | 0.02668 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| circle_r50_35kmh_comb@empty | max_fifth_wheel_error_mm | 0.08673 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| circle_r50_35kmh_comb@laden40 | radius_error_m [30..end s] | 0.2849 |  | 0.6 | PASS | WORKING_VALUE: path following |
| circle_r50_35kmh_comb@laden40 | lat_accel_ms2 [30..end s] | 1.879 | 1.701 | 2.079 | PASS | DERIVED: v^2/R |
| circle_r50_35kmh_comb@laden40 | trailer_offtracking_m [30..end s] | 0.4124 | -0.5 | 0.55 | PASS | WORKING_VALUE: offtracking shrinks / reverses with speed (tire slip angles) |
| circle_r50_35kmh_comb@laden40 | max_trailer_roll_deg [30..end s] | 2.64 |  | 4 | PASS | WORKING_VALUE: moderate roll at 0.19 g |
| circle_r50_35kmh_comb@laden40 | max_dv_step_ms | 0.0222 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| circle_r50_35kmh_comb@laden40 | max_fifth_wheel_error_mm | 0.07801 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| couple_miss_25cm@empty | coupling_events | 0 | 0 | 0 | PASS | WORKING_VALUE: kingpin wider than the throat mouth (+/- 0.18 m) misses the jaw |
| couple_miss_25cm@empty | coupled_final | 0 | 0 | 0 | PASS | WORKING_VALUE: still uncoupled |
| couple_miss_25cm@laden40 | coupling_events | 0 | 0 | 0 | PASS | WORKING_VALUE: kingpin wider than the throat mouth (+/- 0.18 m) misses the jaw |
| couple_miss_25cm@laden40 | coupled_final | 0 | 0 | 0 | PASS | WORKING_VALUE: still uncoupled |
| couple_offset_left_18cm@empty | coupling_events | 1 | 1 | 1 | PASS | WORKING_VALUE: throat ramps guide the kingpin to the jaw: locks once |
| couple_offset_left_18cm@empty | max_kingpin_long_kn | 36.44 |  | 150 | PASS | WORKING_VALUE: coupling bump stays moderate (compliant engagement), as couple_uncouple |
| couple_offset_left_18cm@empty | kingpin_load_vs_static [40..end s] | 1.019 | 0.97 | 1.03 | PASS | DERIVED: legs up, brakes locked: static nose load |
| couple_offset_left_18cm@empty | max_fifth_wheel_error_mm [20..end s] | 4.787E-07 |  | 5 | PASS | WORKING_VALUE: after the engagement phase the kingpin point is rigid again |
| couple_offset_left_18cm@laden40 | coupling_events | 1 | 1 | 1 | PASS | WORKING_VALUE: throat ramps guide the kingpin to the jaw: locks once |
| couple_offset_left_18cm@laden40 | max_kingpin_long_kn | 90.97 |  | 150 | PASS | WORKING_VALUE: coupling bump stays moderate (compliant engagement), as couple_uncouple |
| couple_offset_left_18cm@laden40 | kingpin_load_vs_static [40..end s] | 1.022 | 0.97 | 1.03 | PASS | DERIVED: legs up, brakes locked: static nose load |
| couple_offset_left_18cm@laden40 | max_fifth_wheel_error_mm [20..end s] | 1.008E-05 |  | 5 | PASS | WORKING_VALUE: after the engagement phase the kingpin point is rigid again |
| couple_offset_right_15cm@empty | coupling_events | 1 | 1 | 1 | PASS | WORKING_VALUE: throat ramps guide the kingpin to the jaw: locks once |
| couple_offset_right_15cm@empty | max_kingpin_long_kn | 36.44 |  | 150 | PASS | WORKING_VALUE: coupling bump stays moderate (compliant engagement), as couple_uncouple |
| couple_offset_right_15cm@empty | kingpin_load_vs_static [40..end s] | 1.02 | 0.97 | 1.03 | PASS | DERIVED: legs up, brakes locked: static nose load |
| couple_offset_right_15cm@empty | max_fifth_wheel_error_mm [20..end s] | 4.874E-07 |  | 5 | PASS | WORKING_VALUE: after the engagement phase the kingpin point is rigid again |
| couple_offset_right_15cm@laden40 | coupling_events | 1 | 1 | 1 | PASS | WORKING_VALUE: throat ramps guide the kingpin to the jaw: locks once |
| couple_offset_right_15cm@laden40 | max_kingpin_long_kn | 99.48 |  | 150 | PASS | WORKING_VALUE: coupling bump stays moderate (compliant engagement), as couple_uncouple |
| couple_offset_right_15cm@laden40 | kingpin_load_vs_static [40..end s] | 1.021 | 0.97 | 1.03 | PASS | DERIVED: legs up, brakes locked: static nose load |
| couple_offset_right_15cm@laden40 | max_fifth_wheel_error_mm [20..end s] | 4.687E-06 |  | 5 | PASS | WORKING_VALUE: after the engagement phase the kingpin point is rigid again |
| couple_standstill_locked@empty | coupling_events | 1 | 1 | 1 | PASS | WORKING_VALUE: jaw locks once |
| couple_standstill_locked@empty | kingpin_load_vs_static [50..end s] | 1.006 | 0.97 | 1.03 | PASS | DERIVED: legs up, brakes locked, standing: kingpin carries the static nose load (statics) |
| couple_standstill_locked@empty | max_speed_after_ms [60..end s] | 0.0001152 |  | 0.005 | PASS | WORKING_VALUE: no creep after the legs are up |
| couple_standstill_locked@empty | max_dv_step_ms | 0.07616 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion |
| couple_standstill_locked@laden40 | coupling_events | 1 | 1 | 1 | PASS | WORKING_VALUE: jaw locks once |
| couple_standstill_locked@laden40 | kingpin_load_vs_static [50..end s] | 1.014 | 0.97 | 1.03 | PASS | DERIVED: legs up, brakes locked, standing: kingpin carries the static nose load (statics) |
| couple_standstill_locked@laden40 | max_speed_after_ms [60..end s] | 0.0005382 |  | 0.005 | PASS | WORKING_VALUE: no creep after the legs are up |
| couple_standstill_locked@laden40 | max_dv_step_ms | 0.1283 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion |
| couple_uncouple@empty | coupling_events | 1 | 1 | 1 | PASS | WORKING_VALUE: jaw locks once |
| couple_uncouple@empty | kingpin_load_vs_static [20..24 s] | 0.9823 | 0.9 | 1.1 | PASS | DERIVED: kingpin load after coupling and raising the legs = static nose load |
| couple_uncouple@empty | uncoupling_events | 1 | 1 | 1 | PASS | WORKING_VALUE: released once |
| couple_uncouple@empty | tractor_trailer_distance_m | 81.48 | 8 |  | PASS | WORKING_VALUE: tractor drove away |
| couple_uncouple@empty | trailer_drift_m [50..end s] | 0.0008785 |  | 0.03 | PASS | WORKING_VALUE: uncoupled trailer held by its emergency/spring brakes on the legs |
| couple_uncouple@empty | max_dv_step_ms | 0.07616 |  | 0.35 | PASS | WORKING_VALUE: coupling impact spread by the compliant jaw engagement (0.4 s, 4 Hz); no solver explosion |
| couple_uncouple@empty | max_kingpin_long_kn [2..8 s] | 32.69 |  | 150 | PASS | WORKING_VALUE: coupling bump at idle-creep approach stays moderate (compliant engagement) |
| couple_uncouple@empty | wheel_lift [40..end s] | 0 |  | 0 | PASS | WORKING_VALUE: uncoupling with the legs taking the nose load: the tractor does not jump |
| couple_uncouple@laden40 | coupling_events | 1 | 1 | 1 | PASS | WORKING_VALUE: jaw locks once |
| couple_uncouple@laden40 | kingpin_load_vs_static [20..24 s] | 0.9735 | 0.9 | 1.1 | PASS | DERIVED: kingpin load after coupling and raising the legs = static nose load |
| couple_uncouple@laden40 | uncoupling_events | 1 | 1 | 1 | PASS | WORKING_VALUE: released once |
| couple_uncouple@laden40 | tractor_trailer_distance_m | 79.56 | 8 |  | PASS | WORKING_VALUE: tractor drove away |
| couple_uncouple@laden40 | trailer_drift_m [50..end s] | 0.003263 |  | 0.03 | PASS | WORKING_VALUE: uncoupled trailer held by its emergency/spring brakes on the legs |
| couple_uncouple@laden40 | max_dv_step_ms | 0.1283 |  | 0.35 | PASS | WORKING_VALUE: coupling impact spread by the compliant jaw engagement (0.4 s, 4 Hz); no solver explosion |
| couple_uncouple@laden40 | max_kingpin_long_kn [2..8 s] | 43.39 |  | 150 | PASS | WORKING_VALUE: coupling bump at idle-creep approach stays moderate (compliant engagement) |
| couple_uncouple@laden40 | wheel_lift [40..end s] | 0 |  | 0 | PASS | WORKING_VALUE: uncoupling with the legs taking the nose load: the tractor does not jump |
| curb_15cm_both | max_dv_step_ms | 0.1006 |  | 0.35 | PASS | WORKING_VALUE: docs/04 s6.11 continuous contact / no teleport; 0.35 m/s change per 10 ms step (~3.5 g) limit |
| curb_15cm_both | max_pos_jump_m | 1.908E-14 |  | 1E-06 | PASS | WORKING_VALUE: position change fully explained by velocity (no teleport) |
| curb_15cm_both | final_z_m | 65.72 | 45 |  | PASS | WORKING_VALUE: vehicle actually crosses the obstacle |
| curb_15cm_both | max_fz_ratio | 3.191 |  | 4 | PASS | WORKING_VALUE: no extreme wheel-load spikes (bump-stop engagement allowed) |
| curb_15cm_both | max_abs_roll_deg | 0 |  | 6 | PASS | WORKING_VALUE: no roll-over tendency |
| curb_15cm_left | max_dv_step_ms | 0.05284 |  | 0.35 | PASS | WORKING_VALUE: docs/04 s6.11 continuous contact / no teleport; 0.35 m/s change per 10 ms step (~3.5 g) limit |
| curb_15cm_left | max_pos_jump_m | 1.418E-14 |  | 1E-06 | PASS | WORKING_VALUE: position change fully explained by velocity (no teleport) |
| curb_15cm_left | final_z_m | 65.71 | 45 |  | PASS | WORKING_VALUE: vehicle actually crosses the obstacle |
| curb_15cm_left | max_fz_ratio | 2.664 |  | 4 | PASS | WORKING_VALUE: no extreme wheel-load spikes (bump-stop engagement allowed) |
| curb_15cm_left | max_abs_roll_deg | 5.692 |  | 8 | PASS | DERIVED: geometric roll atan(0.15 m / ~1.9 m track) = 4.5 deg plus dynamic overshoot; >8 deg would indicate roll-over tendency |
| curb_15cm_left_comb@empty | max_dv_step_ms | 0.04944 |  | 0.35 | PASS | WORKING_VALUE: no impulse spikes |
| curb_15cm_left_comb@empty | max_pos_jump_m | 9.624E-15 |  | 1E-06 | PASS | WORKING_VALUE: no teleport |
| curb_15cm_left_comb@empty | max_fz_ratio | 3.662 |  | 4 | PASS | WORKING_VALUE: bounded wheel load peaks |
| curb_15cm_left_comb@empty | max_trailer_roll_deg | 2.805 |  | 8 | PASS | WORKING_VALUE: geometric roll (0.15 m over ~2 m track) plus overshoot |
| curb_15cm_left_comb@empty | max_fifth_wheel_error_mm | 0.0391 |  | 5 | PASS | WORKING_VALUE: constraint holds |
| curb_15cm_left_comb@laden40 | max_dv_step_ms | 0.06127 |  | 0.35 | PASS | WORKING_VALUE: no impulse spikes |
| curb_15cm_left_comb@laden40 | max_pos_jump_m | 1.044E-14 |  | 1E-06 | PASS | WORKING_VALUE: no teleport |
| curb_15cm_left_comb@laden40 | max_fz_ratio | 2.968 |  | 4 | PASS | WORKING_VALUE: bounded wheel load peaks |
| curb_15cm_left_comb@laden40 | max_trailer_roll_deg | 3.395 |  | 8 | PASS | WORKING_VALUE: geometric roll (0.15 m over ~2 m track) plus overshoot |
| curb_15cm_left_comb@laden40 | max_fifth_wheel_error_mm | 0.04042 |  | 5 | PASS | WORKING_VALUE: constraint holds |
| curb_8cm_both | max_dv_step_ms | 0.06908 |  | 0.35 | PASS | WORKING_VALUE: docs/04 s6.11 continuous contact / no teleport; 0.35 m/s change per 10 ms step (~3.5 g) limit |
| curb_8cm_both | max_pos_jump_m | 1.867E-14 |  | 1E-06 | PASS | WORKING_VALUE: position change fully explained by velocity (no teleport) |
| curb_8cm_both | final_z_m | 65.72 | 45 |  | PASS | WORKING_VALUE: vehicle actually crosses the obstacle |
| curb_8cm_both | max_fz_ratio | 1.931 |  | 4 | PASS | WORKING_VALUE: no extreme wheel-load spikes (bump-stop engagement allowed) |
| curb_8cm_both | max_abs_roll_deg | 0 |  | 6 | PASS | WORKING_VALUE: no roll-over tendency |
| curb_strike_14cm_50kmh_comb@empty | max_dv_step_ms | 0.06903 |  | 0.35 | PASS | WORKING_VALUE: no impulse spikes (phone single-step jolt was 0.6-0.7 m/s; sim baseline <= 0.1) |
| curb_strike_14cm_50kmh_comb@empty | max_pos_jump_m | 3.852E-14 |  | 1E-06 | PASS | WORKING_VALUE: no teleport |
| curb_strike_14cm_50kmh_comb@empty | max_fz_ratio | 4.176 |  | 4.2 | PASS | WORKING_VALUE: bounded wheel load peaks (sim 2026-11-09: 3.90 empty / 3.53 laden; phone saw 6.8) |
| curb_strike_14cm_50kmh_comb@empty | max_trailer_roll_deg | 2.579 |  | 8 | PASS | WORKING_VALUE: geometric roll plus overshoot |
| curb_strike_14cm_50kmh_comb@empty | max_fifth_wheel_error_mm | 0.05808 |  | 5 | PASS | WORKING_VALUE: constraint holds |
| curb_strike_14cm_50kmh_comb@empty | wheel_off_ground_time_s | 0.7 |  | 0.75 | PASS | WORKING_VALUE: regression guard on measured value 2026-11-09 (union over 10 wheel ends; dominated by the drop off the kerb end, see PHYSICS_VALIDATION) |
| curb_strike_14cm_50kmh_comb@empty | max_wheel_airtime_s(1) | 0.19 |  | 0.15 | **FAIL** | WORKING_VALUE: axle flight: longest single-wheel unload; tractor target < 0.15 s (lead brief 2026-11-09) |
| curb_strike_14cm_50kmh_comb@empty | max_wheel_airtime_s | 0.21 |  | 0.25 | PASS | WORKING_VALUE: regression guard on measured value 2026-11-09 (empty tridem: axle 1 hangs at full droop while axles 2-3 are still on the kerb; frame torsion not modelled) |
| curb_strike_14cm_50kmh_comb@laden40 | max_dv_step_ms | 0.08204 |  | 0.35 | PASS | WORKING_VALUE: no impulse spikes (phone single-step jolt was 0.6-0.7 m/s; sim baseline <= 0.1) |
| curb_strike_14cm_50kmh_comb@laden40 | max_pos_jump_m | 2.656E-14 |  | 1E-06 | PASS | WORKING_VALUE: no teleport |
| curb_strike_14cm_50kmh_comb@laden40 | max_fz_ratio | 3.328 |  | 4.2 | PASS | WORKING_VALUE: bounded wheel load peaks (sim 2026-11-09: 3.90 empty / 3.53 laden; phone saw 6.8) |
| curb_strike_14cm_50kmh_comb@laden40 | max_trailer_roll_deg | 2.238 |  | 8 | PASS | WORKING_VALUE: geometric roll plus overshoot |
| curb_strike_14cm_50kmh_comb@laden40 | max_fifth_wheel_error_mm | 0.1008 |  | 5 | PASS | WORKING_VALUE: constraint holds |
| curb_strike_14cm_50kmh_comb@laden40 | wheel_off_ground_time_s | 0.21 |  | 0.28 | PASS | WORKING_VALUE: regression guard on measured value 2026-11-09 (union over 10 wheel ends; dominated by the drop off the kerb end, see PHYSICS_VALIDATION) |
| curb_strike_14cm_50kmh_comb@laden40 | max_wheel_airtime_s(1) | 0.09 |  | 0.12 | PASS | WORKING_VALUE: axle flight: longest single-wheel unload; tractor target < 0.15 s (lead brief 2026-11-09) |
| curb_strike_14cm_50kmh_comb@laden40 | max_wheel_airtime_s | 0.09 |  | 0.12 | PASS | WORKING_VALUE: axle flight: longest single-wheel unload; target < 0.15 s (lead brief 2026-11-09) |
| curb_strike_5cm_50kmh_comb@empty | max_dv_step_ms | 0.03951 |  | 0.35 | PASS | WORKING_VALUE: no impulse spikes (phone single-step jolt was 0.6-0.7 m/s; sim baseline <= 0.1) |
| curb_strike_5cm_50kmh_comb@empty | max_pos_jump_m | 2.112E-14 |  | 1E-06 | PASS | WORKING_VALUE: no teleport |
| curb_strike_5cm_50kmh_comb@empty | max_fz_ratio | 1.771 |  | 2.2 | PASS | WORKING_VALUE: bounded wheel load peaks (sim 2026-11-09: 1.79 empty / 1.67 laden; phone saw 6.8) |
| curb_strike_5cm_50kmh_comb@empty | max_trailer_roll_deg | 0.7743 |  | 8 | PASS | WORKING_VALUE: geometric roll plus overshoot |
| curb_strike_5cm_50kmh_comb@empty | max_fifth_wheel_error_mm | 0.003246 |  | 5 | PASS | WORKING_VALUE: constraint holds |
| curb_strike_5cm_50kmh_comb@empty | wheel_off_ground_time_s | 0.05 |  | 0.08 | PASS | WORKING_VALUE: regression guard on measured value 2026-11-09 (union over 10 wheel ends; dominated by the drop off the kerb end, see PHYSICS_VALIDATION) |
| curb_strike_5cm_50kmh_comb@empty | max_wheel_airtime_s(1) | 0 |  | 0.03 | PASS | WORKING_VALUE: axle flight: longest single-wheel unload; tractor target < 0.15 s (lead brief 2026-11-09) |
| curb_strike_5cm_50kmh_comb@empty | max_wheel_airtime_s | 0.02 |  | 0.05 | PASS | WORKING_VALUE: axle flight: longest single-wheel unload; target < 0.15 s (lead brief 2026-11-09) |
| curb_strike_5cm_50kmh_comb@laden40 | max_dv_step_ms | 0.03772 |  | 0.35 | PASS | WORKING_VALUE: no impulse spikes (phone single-step jolt was 0.6-0.7 m/s; sim baseline <= 0.1) |
| curb_strike_5cm_50kmh_comb@laden40 | max_pos_jump_m | 4.252E-14 |  | 1E-06 | PASS | WORKING_VALUE: no teleport |
| curb_strike_5cm_50kmh_comb@laden40 | max_fz_ratio | 1.665 |  | 2.2 | PASS | WORKING_VALUE: bounded wheel load peaks (sim 2026-11-09: 1.79 empty / 1.67 laden; phone saw 6.8) |
| curb_strike_5cm_50kmh_comb@laden40 | max_trailer_roll_deg | 0.7196 |  | 8 | PASS | WORKING_VALUE: geometric roll plus overshoot |
| curb_strike_5cm_50kmh_comb@laden40 | max_fifth_wheel_error_mm | 0.005525 |  | 5 | PASS | WORKING_VALUE: constraint holds |
| curb_strike_5cm_50kmh_comb@laden40 | wheel_off_ground_time_s | 0 |  | 0.03 | PASS | WORKING_VALUE: regression guard on measured value 2026-11-09 (union over 10 wheel ends; dominated by the drop off the kerb end, see PHYSICS_VALIDATION) |
| curb_strike_5cm_50kmh_comb@laden40 | max_wheel_airtime_s(1) | 0 |  | 0.03 | PASS | WORKING_VALUE: axle flight: longest single-wheel unload; tractor target < 0.15 s (lead brief 2026-11-09) |
| curb_strike_5cm_50kmh_comb@laden40 | max_wheel_airtime_s | 0 |  | 0.03 | PASS | WORKING_VALUE: axle flight: longest single-wheel unload; target < 0.15 s (lead brief 2026-11-09) |
| downhill_7pct_brake_cruise_60@laden40 | mean_speed_kmh [60..end s] | 60 | 59 | 61.5 | PASS | WORKING_VALUE: speed stabilised at the set speed |
| downhill_7pct_brake_cruise_60@laden40 | speed_range_kmh [60..end s] | 5.807E-10 |  | 2 | PASS | WORKING_VALUE: no hunting / limit cycle of the downhill speed control |
| downhill_7pct_brake_cruise_60@laden40 | max_retarder_torque_nm | 2855 | 1000 | 4000 | PASS | SOURCED: S2: secondary retarder up to 4000 Nm / 600 kW (class reference) |
| downhill_7pct_brake_cruise_60@laden40 | max_service_demand | 0 |  | 0 | PASS | WORKING_VALUE: service brake not needed |
| downhill_7pct_brake_cruise_60@laden40 | max_dv_step_ms | 0.006844 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| downhill_7pct_brake_cruise_60@laden40 | max_fifth_wheel_error_mm | 0.0001002 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| downhill_7pct_full_lever@laden40 | speed_range_kmh [80..end s] | 0.000891 |  | 3 | PASS | WORKING_VALUE: speed stabilises (endurance brakes stronger than gravity at 70 km/h) |
| downhill_7pct_full_lever@laden40 | max_speed_kmh | 70.6 |  | 71 | PASS | WORKING_VALUE: no runaway |
| downhill_7pct_full_lever@laden40 | max_engine_brake_torque_nm | 1155 | 500 |  | PASS | WORKING_VALUE: engine brake active (S1 class: 375 kW at 2300 rpm) |
| downhill_7pct_full_lever@laden40 | max_dv_step_ms | 0.01284 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| downhill_7pct_full_lever@laden40 | max_fifth_wheel_error_mm | 0.001827 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| downhill_7pct_service_pumping@laden40 | min_air_service_bar | 5.24 |  | 9 | PASS | WORKING_VALUE: pumping the pedal consumes more air (~50 NL per application, 10 chambers) than the compressor delivers (~450 NL/min at rated speed): the classic long-descent pressure loss |
| downhill_7pct_service_pumping@laden40 | min_air_service_bar | 5.24 | 3 |  | PASS | WORKING_VALUE: the service brake keeps working (pressure does not collapse within 4 min) |
| downhill_7pct_service_pumping@laden40 | low_air_warning | 1 | 1 |  | PASS | WORKING_VALUE: warning lamp comes on: real consequence of pumping on a long descent |
| downhill_7pct_service_pumping@laden40 | max_speed_kmh | 45.88 |  | 50 | PASS | WORKING_VALUE: speed controlled |
| downhill_7pct_service_pumping@laden40 | max_dv_step_ms | 0.03963 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| downhill_7pct_service_pumping@laden40 | max_fifth_wheel_error_mm | 0.01069 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| downhill_7pct_typeIIA@laden40 | mean_speed_kmh [60..end s] | 30 | 25 | 35 | PASS | SOURCED: UN R13 Annex 4 1.8.2: laden, 30 km/h average on 7% for 6 km without service/secondary/parking brakes (+/-5 km/h) |
| downhill_7pct_typeIIA@laden40 | max_service_demand | 0 |  | 0 | PASS | SOURCED: UN R13 Annex 4 1.8.2: service brake not used |
| downhill_7pct_typeIIA@laden40 | max_rpm | 1930 |  | 2400 | PASS | WORKING_VALUE: engine overrun limit while engine braking (WORKING_VALUE 2400 rpm) |
| downhill_7pct_typeIIA@laden40 | max_speed_kmh [30..end s] | 31.66 |  | 40 | PASS | WORKING_VALUE: no runaway |
| downhill_7pct_typeIIA@laden40 | max_dv_step_ms | 0.03615 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| downhill_7pct_typeIIA@laden40 | max_fifth_wheel_error_mm | 0.0007976 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| downhill_8pct_retarder_comb@laden40 | mean_speed_kmh [60..end s] | 40 | 35 | 45 | PASS | WORKING_VALUE: docs/04 s6.6 (zjazd 6-8% ze stabilizacja predkosci); docs nie podaja liczby dla 40 km/h na 8% (UNVERIFIED): target +/-5 km/h |
| downhill_8pct_retarder_comb@laden40 | speed_range_kmh [60..end s] | 1.983E-07 |  | 2 | PASS | WORKING_VALUE: stable descent (jak downhill_7pct_brake_cruise_60: <= 2 km/h) |
| downhill_8pct_retarder_comb@laden40 | max_service_demand | 0 |  | 0 | PASS | WORKING_VALUE: bez przegrzania hamulcow: hamulec roboczy nieuzywany na zjezdzie. Model termiczny hamulcow NIE istnieje (docs/PHYSICS_VALIDATION.md §7), wiec to proxy; analog R13 1.8.2 (SOURCED) dla 7%/30 km/h w downhill_7pct_typeIIA |
| downhill_8pct_retarder_comb@laden40 | max_retarder_torque_nm | 2192 |  | 4000 | PASS | SOURCED: S2 secondary retarder limit 4000 Nm (jak downhill_7pct_brake_cruise_60) |
| downhill_8pct_retarder_comb@laden40 | max_rpm | 2026 |  | 2400 | PASS | WORKING_VALUE: engine overrun limit while engine braking (WORKING_VALUE 2400 rpm) |
| downhill_8pct_retarder_comb@laden40 | max_dv_step_ms | 0.03601 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| downhill_8pct_retarder_comb@laden40 | max_fifth_wheel_error_mm | 0.0002423 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| free_fall_drop_comb | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN |
| free_fall_drop_comb | free_flight_s | 1.05 | 0.3 |  | PASS | DERIVED: the drop really is a flight: free fall of ~0.9 m (wheels hang below the static pose) lasts ~sqrt(2*0.9/9.81) = 0.43 s; require >= 0.3 s |
| free_fall_drop_comb | max_free_flight_energy_gain_j | 0 |  | 1 | PASS | WORKING_VALUE: no energy source in free flight: E = KE + PE must not grow between samples |
| free_fall_drop_comb | max_free_flight_accel_error_ms2 | 0.007663 |  | 0.05 | PASS | DERIVED: |a_com - g| <= aero drag 0.5*rho*CdA*v^2/M: rho 1.2, CdA <= 7.5 m^2 (tractor 6.0 + trailer 1.5, VehicleDefinition/TrailerDefinition), v <= 9 m/s, M >= 30 t -> 0.0122 m/s^2; limit 0.05 |
| free_fall_drop_comb | max_body_penetration_m | 0.01325 |  | 0.05 | PASS | WORKING_VALUE: ADR 0165: at the 1 m-drop landing (4.4 m/s, nose pitched 8 deg down, bump stops) the tractor Bumper bottom corner reaches the road and its plastic cover crushes; the ADR 0158 rigid contact touched too (2 speculative corners at t 1.46 s) but reported 0 by construction. Limit 0.05 m = same bumper-strike crush bound as kerb_step_27cm_42kmh_comb. Measured 0.025 m |
| free_fall_drop_comb | min_com_height_m | 0.7477 | 0.5 |  | PASS | WORKING_VALUE: no fall-through: the tractor CoM (1.05 m static) may dip on the bump stops at the 1 m-drop landing (measured 0.737 m) but stays well above the road |
| free_fall_drop_comb | max_fifth_wheel_error_mm | 1.365 |  | 15 | PASS | WORKING_VALUE: coupling holds through a 1 m-drop landing (4.4 m/s impact; measured 7.5 mm, driving limit is 5 mm), no blow-up |
| fuzz_concrete_solo | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: M34 fuzz invariant: no NaN/Inf in any body state (docs/04 s6.14) |
| fuzz_concrete_solo | max_pos_jump_m | 5.684E-17 |  | 0.0001 | PASS | WORKING_VALUE: M34 fuzz invariant: no teleportation; |dx_com - v*dt| residual must stay at numerical-noise level (k=1: any real motion is v*dt; threshold 1e-4 m = 0.1 mm slack) |
| fuzz_concrete_solo | max_dv_step_ms | 5.334E-16 |  | 0.35 | PASS | WORKING_VALUE: M34 fuzz invariant: per-step velocity change of either body <= 0.35 m/s (same ceiling as kerb scenarios; solver impulse spikes would exceed it) |
| fuzz_concrete_solo | max_tire_friction_ratio | 5.737E-16 |  | 1.001 | PASS | WORKING_VALUE: M34 fuzz invariant: sqrt(Fx^2+Fy^2) <= mu*Fz on every loaded wheel; combined-slip model bounds it by construction, margin 0.001 for float rounding |
| fuzz_concrete_solo | min_air_all_bar | 0 | 0 |  | PASS | WORKING_VALUE: M34 fuzz invariant: no negative air pressure in any reservoir/line (physical impossibility) |
| fuzz_flat_dry_laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: M34 fuzz invariant: no NaN/Inf in any body state (docs/04 s6.14) |
| fuzz_flat_dry_laden40 | max_pos_jump_m | 4.962E-16 |  | 0.0001 | PASS | WORKING_VALUE: M34 fuzz invariant: no teleportation; |dx_com - v*dt| residual must stay at numerical-noise level (k=1: any real motion is v*dt; threshold 1e-4 m = 0.1 mm slack) |
| fuzz_flat_dry_laden40 | max_dv_step_ms | 0.0003513 |  | 0.35 | PASS | WORKING_VALUE: M34 fuzz invariant: per-step velocity change of either body <= 0.35 m/s (same ceiling as kerb scenarios; solver impulse spikes would exceed it) |
| fuzz_flat_dry_laden40 | max_tire_friction_ratio | 0.006959 |  | 1.001 | PASS | WORKING_VALUE: M34 fuzz invariant: sqrt(Fx^2+Fy^2) <= mu*Fz on every loaded wheel; combined-slip model bounds it by construction, margin 0.001 for float rounding |
| fuzz_flat_dry_laden40 | articulation_limit_excess_deg | 0 |  | 3.5 | PASS | WORKING_VALUE: D59 (owner, 2026-11-13) / ADR 0158 F1, ADR 0165: articulation may exceed the fifth-wheel soft yaw stop (yawLimitDeg = 90, yawStopFrequencyHz 3, tractor_4x2_generic.vehicle.json) by <= 3.5 deg; a stiffer stop (>= 4.5 Hz) breaks the 0.35 m/s jerk limit (ADR 0158 table). Measured max 3.33 deg (M34 hunt) |
| fuzz_flat_dry_laden40 | max_fifth_wheel_error_mm | 9.129E-07 |  | 5 | PASS | WORKING_VALUE: M34 fuzz invariant: kingpin/saddle constraint position error <= 5 mm (same as soak) |
| fuzz_flat_dry_laden40 | min_air_all_bar | 8.5 | 0 |  | PASS | WORKING_VALUE: M34 fuzz invariant: no negative air pressure in any reservoir/line (physical impossibility) |
| fuzz_flat_wet_laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: M34 fuzz invariant: no NaN/Inf in any body state (docs/04 s6.14) |
| fuzz_flat_wet_laden40 | max_pos_jump_m | 4.942E-16 |  | 0.0001 | PASS | WORKING_VALUE: M34 fuzz invariant: no teleportation; |dx_com - v*dt| residual must stay at numerical-noise level (k=1: any real motion is v*dt; threshold 1e-4 m = 0.1 mm slack) |
| fuzz_flat_wet_laden40 | max_dv_step_ms | 0.0003513 |  | 0.35 | PASS | WORKING_VALUE: M34 fuzz invariant: per-step velocity change of either body <= 0.35 m/s (same ceiling as kerb scenarios; solver impulse spikes would exceed it) |
| fuzz_flat_wet_laden40 | max_tire_friction_ratio | 0.01133 |  | 1.001 | PASS | WORKING_VALUE: M34 fuzz invariant: sqrt(Fx^2+Fy^2) <= mu*Fz on every loaded wheel; combined-slip model bounds it by construction, margin 0.001 for float rounding |
| fuzz_flat_wet_laden40 | articulation_limit_excess_deg | 0 |  | 3.5 | PASS | WORKING_VALUE: D59 (owner, 2026-11-13) / ADR 0158 F1, ADR 0165: articulation may exceed the fifth-wheel soft yaw stop (yawLimitDeg = 90, yawStopFrequencyHz 3, tractor_4x2_generic.vehicle.json) by <= 3.5 deg; a stiffer stop (>= 4.5 Hz) breaks the 0.35 m/s jerk limit (ADR 0158 table). Measured max 3.33 deg (M34 hunt) |
| fuzz_flat_wet_laden40 | max_fifth_wheel_error_mm | 9.125E-07 |  | 5 | PASS | WORKING_VALUE: M34 fuzz invariant: kingpin/saddle constraint position error <= 5 mm (same as soak) |
| fuzz_flat_wet_laden40 | min_air_all_bar | 7.951 | 0 |  | PASS | WORKING_VALUE: M34 fuzz invariant: no negative air pressure in any reservoir/line (physical impossibility) |
| fuzz_grade8_dry_laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: M34 fuzz invariant: no NaN/Inf in any body state (docs/04 s6.14) |
| fuzz_grade8_dry_laden40 | max_pos_jump_m | 2.687E-15 |  | 0.0001 | PASS | WORKING_VALUE: M34 fuzz invariant: no teleportation; |dx_com - v*dt| residual must stay at numerical-noise level (k=1: any real motion is v*dt; threshold 1e-4 m = 0.1 mm slack) |
| fuzz_grade8_dry_laden40 | max_dv_step_ms | 0.08251 |  | 0.35 | PASS | WORKING_VALUE: M34 fuzz invariant: per-step velocity change of either body <= 0.35 m/s (same ceiling as kerb scenarios; solver impulse spikes would exceed it) |
| fuzz_grade8_dry_laden40 | max_tire_friction_ratio | 1 |  | 1.001 | PASS | WORKING_VALUE: M34 fuzz invariant: sqrt(Fx^2+Fy^2) <= mu*Fz on every loaded wheel; combined-slip model bounds it by construction, margin 0.001 for float rounding |
| fuzz_grade8_dry_laden40 | articulation_limit_excess_deg | 1.643 |  | 3.5 | PASS | WORKING_VALUE: D59 (owner, 2026-11-13) / ADR 0158 F1, ADR 0165: articulation may exceed the fifth-wheel soft yaw stop (yawLimitDeg = 90, yawStopFrequencyHz 3, tractor_4x2_generic.vehicle.json) by <= 3.5 deg; a stiffer stop (>= 4.5 Hz) breaks the 0.35 m/s jerk limit (ADR 0158 table). Measured max 3.33 deg (M34 hunt) |
| fuzz_grade8_dry_laden40 | max_fifth_wheel_error_mm | 0.09072 |  | 5 | PASS | WORKING_VALUE: M34 fuzz invariant: kingpin/saddle constraint position error <= 5 mm (same as soak) |
| fuzz_grade8_dry_laden40 | min_air_all_bar | 8.5 | 0 |  | PASS | WORKING_VALUE: M34 fuzz invariant: no negative air pressure in any reservoir/line (physical impossibility) |
| fuzz_gradedown8_wet_empty | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: M34 fuzz invariant: no NaN/Inf in any body state (docs/04 s6.14) |
| fuzz_gradedown8_wet_empty | max_pos_jump_m | 4.553E-16 |  | 0.0001 | PASS | WORKING_VALUE: M34 fuzz invariant: no teleportation; |dx_com - v*dt| residual must stay at numerical-noise level (k=1: any real motion is v*dt; threshold 1e-4 m = 0.1 mm slack) |
| fuzz_gradedown8_wet_empty | max_dv_step_ms | 0.01421 |  | 0.35 | PASS | WORKING_VALUE: M34 fuzz invariant: per-step velocity change of either body <= 0.35 m/s (same ceiling as kerb scenarios; solver impulse spikes would exceed it) |
| fuzz_gradedown8_wet_empty | max_tire_friction_ratio | 0.9343 |  | 1.001 | PASS | WORKING_VALUE: M34 fuzz invariant: sqrt(Fx^2+Fy^2) <= mu*Fz on every loaded wheel; combined-slip model bounds it by construction, margin 0.001 for float rounding |
| fuzz_gradedown8_wet_empty | articulation_limit_excess_deg | 0 |  | 3.5 | PASS | WORKING_VALUE: D59 (owner, 2026-11-13) / ADR 0158 F1, ADR 0165: articulation may exceed the fifth-wheel soft yaw stop (yawLimitDeg = 90, yawStopFrequencyHz 3, tractor_4x2_generic.vehicle.json) by <= 3.5 deg; a stiffer stop (>= 4.5 Hz) breaks the 0.35 m/s jerk limit (ADR 0158 table). Measured max 3.33 deg (M34 hunt) |
| fuzz_gradedown8_wet_empty | max_fifth_wheel_error_mm | 0.0004539 |  | 5 | PASS | WORKING_VALUE: M34 fuzz invariant: kingpin/saddle constraint position error <= 5 mm (same as soak) |
| fuzz_gradedown8_wet_empty | min_air_all_bar | 8.367 | 0 |  | PASS | WORKING_VALUE: M34 fuzz invariant: no negative air pressure in any reservoir/line (physical impossibility) |
| fuzz_gravel_cargo24 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: M34 fuzz invariant: no NaN/Inf in any body state (docs/04 s6.14) |
| fuzz_gravel_cargo24 | max_pos_jump_m | 4.92E-16 |  | 0.0001 | PASS | WORKING_VALUE: M34 fuzz invariant: no teleportation; |dx_com - v*dt| residual must stay at numerical-noise level (k=1: any real motion is v*dt; threshold 1e-4 m = 0.1 mm slack) |
| fuzz_gravel_cargo24 | max_dv_step_ms | 0.0003209 |  | 0.35 | PASS | WORKING_VALUE: M34 fuzz invariant: per-step velocity change of either body <= 0.35 m/s (same ceiling as kerb scenarios; solver impulse spikes would exceed it) |
| fuzz_gravel_cargo24 | max_tire_friction_ratio | 0.009054 |  | 1.001 | PASS | WORKING_VALUE: M34 fuzz invariant: sqrt(Fx^2+Fy^2) <= mu*Fz on every loaded wheel; combined-slip model bounds it by construction, margin 0.001 for float rounding |
| fuzz_gravel_cargo24 | articulation_limit_excess_deg | 0 |  | 3.5 | PASS | WORKING_VALUE: D59 (owner, 2026-11-13) / ADR 0158 F1, ADR 0165: articulation may exceed the fifth-wheel soft yaw stop (yawLimitDeg = 90, yawStopFrequencyHz 3, tractor_4x2_generic.vehicle.json) by <= 3.5 deg; a stiffer stop (>= 4.5 Hz) breaks the 0.35 m/s jerk limit (ADR 0158 table). Measured max 3.33 deg (M34 hunt) |
| fuzz_gravel_cargo24 | max_fifth_wheel_error_mm | 8.148E-07 |  | 5 | PASS | WORKING_VALUE: M34 fuzz invariant: kingpin/saddle constraint position error <= 5 mm (same as soak) |
| fuzz_gravel_cargo24 | min_air_all_bar | 8.5 | 0 |  | PASS | WORKING_VALUE: M34 fuzz invariant: no negative air pressure in any reservoir/line (physical impossibility) |
| fuzz_kerb8cm_dry_laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: M34 fuzz invariant: no NaN/Inf in any body state (docs/04 s6.14) |
| fuzz_kerb8cm_dry_laden40 | max_pos_jump_m | 4.942E-16 |  | 0.0001 | PASS | WORKING_VALUE: M34 fuzz invariant: no teleportation; |dx_com - v*dt| residual must stay at numerical-noise level (k=1: any real motion is v*dt; threshold 1e-4 m = 0.1 mm slack) |
| fuzz_kerb8cm_dry_laden40 | max_dv_step_ms | 0.0003513 |  | 0.35 | PASS | WORKING_VALUE: M34 fuzz invariant: per-step velocity change of either body <= 0.35 m/s (same ceiling as kerb scenarios; solver impulse spikes would exceed it) |
| fuzz_kerb8cm_dry_laden40 | max_tire_friction_ratio | 0.006947 |  | 1.001 | PASS | WORKING_VALUE: M34 fuzz invariant: sqrt(Fx^2+Fy^2) <= mu*Fz on every loaded wheel; combined-slip model bounds it by construction, margin 0.001 for float rounding |
| fuzz_kerb8cm_dry_laden40 | articulation_limit_excess_deg | 0 |  | 3.5 | PASS | WORKING_VALUE: D59 (owner, 2026-11-13) / ADR 0158 F1, ADR 0165: articulation may exceed the fifth-wheel soft yaw stop (yawLimitDeg = 90, yawStopFrequencyHz 3, tractor_4x2_generic.vehicle.json) by <= 3.5 deg; a stiffer stop (>= 4.5 Hz) breaks the 0.35 m/s jerk limit (ADR 0158 table). Measured max 3.33 deg (M34 hunt) |
| fuzz_kerb8cm_dry_laden40 | max_fifth_wheel_error_mm | 9.127E-07 |  | 5 | PASS | WORKING_VALUE: M34 fuzz invariant: kingpin/saddle constraint position error <= 5 mm (same as soak) |
| fuzz_kerb8cm_dry_laden40 | min_air_all_bar | 8.5 | 0 |  | PASS | WORKING_VALUE: M34 fuzz invariant: no negative air pressure in any reservoir/line (physical impossibility) |
| fuzz_mud_gradedown5_laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: M34 fuzz invariant: no NaN/Inf in any body state (docs/04 s6.14) |
| fuzz_mud_gradedown5_laden40 | max_pos_jump_m | 7.293E-15 |  | 0.0001 | PASS | WORKING_VALUE: M34 fuzz invariant: no teleportation; |dx_com - v*dt| residual must stay at numerical-noise level (k=1: any real motion is v*dt; threshold 1e-4 m = 0.1 mm slack) |
| fuzz_mud_gradedown5_laden40 | max_dv_step_ms | 0.01847 |  | 0.35 | PASS | WORKING_VALUE: M34 fuzz invariant: per-step velocity change of either body <= 0.35 m/s (same ceiling as kerb scenarios; solver impulse spikes would exceed it) |
| fuzz_mud_gradedown5_laden40 | max_tire_friction_ratio | 1 |  | 1.001 | PASS | WORKING_VALUE: M34 fuzz invariant: sqrt(Fx^2+Fy^2) <= mu*Fz on every loaded wheel; combined-slip model bounds it by construction, margin 0.001 for float rounding |
| fuzz_mud_gradedown5_laden40 | articulation_limit_excess_deg | 0 |  | 3.5 | PASS | WORKING_VALUE: D59 (owner, 2026-11-13) / ADR 0158 F1, ADR 0165: articulation may exceed the fifth-wheel soft yaw stop (yawLimitDeg = 90, yawStopFrequencyHz 3, tractor_4x2_generic.vehicle.json) by <= 3.5 deg; a stiffer stop (>= 4.5 Hz) breaks the 0.35 m/s jerk limit (ADR 0158 table). Measured max 3.33 deg (M34 hunt) |
| fuzz_mud_gradedown5_laden40 | max_fifth_wheel_error_mm | 0.01039 |  | 5 | PASS | WORKING_VALUE: M34 fuzz invariant: kingpin/saddle constraint position error <= 5 mm (same as soak) |
| fuzz_mud_gradedown5_laden40 | min_air_all_bar | 8.5 | 0 |  | PASS | WORKING_VALUE: M34 fuzz invariant: no negative air pressure in any reservoir/line (physical impossibility) |
| fuzz_shrink_articulation_stop_fulllock | articulation_limit_excess_deg | 1.803 |  | 3.5 | PASS | WORKING_VALUE: D59 (owner, 2026-11-13) / ADR 0158 F1, ADR 0165: articulation may exceed the fifth-wheel soft yaw stop (yawLimitDeg = 90, yawStopFrequencyHz 3, tractor_4x2_generic.vehicle.json) by <= 3.5 deg; a stiffer stop (>= 4.5 Hz) breaks the 0.35 m/s jerk limit (ADR 0158 table). Measured max 3.33 deg (M34 hunt) |
| fuzz_shrink_articulation_stop_fulllock | max_articulation_deg | 91.8 | 0 |  | PASS | WORKING_VALUE: observed value |
| fuzz_shrink_articulation_stop_fulllock | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN |
| fuzz_shrink_articulation_stop_fulllock | max_dv_step_ms | 0.1806 |  | 0.35 | PASS | WORKING_VALUE: no impulse spikes |
| fuzz_shrink_speed_runaway_fulllock | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN |
| fuzz_shrink_speed_runaway_fulllock | max_pos_jump_m | 6.118E-15 |  | 0.0001 | PASS | WORKING_VALUE: no teleport |dx_com - v*dt| <= 1e-4 m |
| fuzz_shrink_speed_runaway_fulllock | max_dv_step_ms [0..3.5 s] | 0.1085 |  | 0.35 | PASS | WORKING_VALUE: driving phase before the rollover: per-step velocity change <= 0.35 m/s (kerb-scenario ceiling) |
| fuzz_shrink_speed_runaway_fulllock | max_dv_step_ms | 0.6167 |  | 4.2 | PASS | DERIVED: whole run incl. the side impact: <= sqrt(2 g dh) = 4.18 m/s, dh = 0.89 m = trailer CoM drop from its tip-over apex (2.164 m) to lying on its side (1.275 m = half width), ADR 0158; measured 2.04 m/s |
| fuzz_shrink_speed_runaway_fulllock | max_tire_friction_ratio | 1 |  | 1.001 | PASS | WORKING_VALUE: sqrt(Fx^2+Fy^2) <= mu*Fz, margin 0.001 |
| fuzz_shrink_speed_runaway_fulllock | articulation_limit_excess_deg | 0 |  | 3.5 | PASS | WORKING_VALUE: D59 (owner, 2026-11-13) / ADR 0158 F1, ADR 0165: articulation may exceed the fifth-wheel soft yaw stop (yawLimitDeg = 90, yawStopFrequencyHz 3, tractor_4x2_generic.vehicle.json) by <= 3.5 deg; a stiffer stop (>= 4.5 Hz) breaks the 0.35 m/s jerk limit (ADR 0158 table). Measured max 3.33 deg (M34 hunt) |
| fuzz_shrink_speed_runaway_fulllock | max_fifth_wheel_error_mm [0..3.5 s] | 0.7632 |  | 5 | PASS | WORKING_VALUE: driving phase: kingpin constraint error <= 5 mm |
| fuzz_shrink_speed_runaway_fulllock | max_fifth_wheel_error_mm | 5.805 |  | 50 | PASS | WORKING_VALUE: whole run: coupling holds through the side impact (measured 24.5 mm peak at landing, 9 mm lying: colliders and the soft kingpin joint are slightly over-constrained), no blow-up; ADR 0158 |
| fuzz_shrink_speed_runaway_fulllock | min_air_all_bar | 8.5 | 0 |  | PASS | WORKING_VALUE: no negative air pressure |
| fuzz_shrink_speed_runaway_fulllock | max_speed_kmh | 30.24 |  | 90.5 | PASS | WORKING_VALUE: EU limiter 90 km/h (docs/04 s5), same margin as top_speed_flat_comb (+0.5); before ADR 0158: 275.4 km/h |
| fuzz_shrink_speed_runaway_fulllock | min_com_height_m | 1.059 | 0.9 |  | PASS | WORKING_VALUE: no fall-through: both CoMs stay above the road (static tractor CoM 1.05 m, lying on its side >= 1.25 m); before ADR 0158: -3070 m |
| fuzz_shrink_speed_runaway_fulllock | max_body_penetration_m | 0.09393 |  | 0.1 | PASS | DERIVED: ADR 0165 compliant contact (4 Hz, zeta 1 per corner effective mass): side-impact peak crush <= v/(e*omega) + n*g/omega^2 = 4.18/(e*25.1) + 2*9.81/25.1^2 = 0.061 + 0.031 = 0.092 m (v = DERIVED impact bound of this scenario, n = 2 g corner load of the lying trailer); limit 0.10 m. A real curtain-sider roof rail / cab corner crushes decimetres in a rollover (UNVERIFIED). Measured 0.090 m (trailer Body corner, t 4.12 s); ADR 0158 rigid contact: 0.0004 m |
| fuzz_shrink_speed_runaway_fulllock | max_body_penetration_m [10..end s] | 0.02857 |  | 0.035 | PASS | WORKING_VALUE: ADR 0165: lying at rest the static sink n*g/omega^2 = 2*9.81/25.1^2 = 0.031 m; limit 0.035 m (no visible sinking of the lying trailer on a phone screen). Measured 0.030 m |
| fuzz_shrink_speed_runaway_fulllock | body_contact_s | 25.99 | 1 |  | PASS | WORKING_VALUE: the rollover ends on the chassis colliders (scenario meaning), ADR 0158 |
| fuzz_shrink_speed_runaway_fulllock | max_free_flight_energy_gain_j | 0 |  | 1 | PASS | WORKING_VALUE: no energy source in free flight: E = KE + PE must not grow between samples, ADR 0158 |
| fuzz_shrink_speed_runaway_fulllock | max_energy_j | 2.055E+06 |  | 2.133E+06 | PASS | WORKING_VALUE: throttle 0.378 only replaces losses while upright; nothing may raise E above its t=0 value (2.031 MJ) + 5 % (measured max 2.055 MJ at t~0.5 s, +1.2 %) |
| fuzz_shrink_speed_runaway_fulllock | max_speed_after_ms [8..end s] | 1.914E-07 |  | 0.05 | PASS | WORKING_VALUE: the overturned combination slides to a stop (body friction 0.6 = Unity default PhysicsMaterial) and stays at rest |
| fuzz_touch_dry_laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: M34 fuzz invariant: no NaN/Inf in any body state (docs/04 s6.14) |
| fuzz_touch_dry_laden40 | max_pos_jump_m | 1.796E-15 |  | 0.0001 | PASS | WORKING_VALUE: M34 fuzz invariant: no teleportation; |dx_com - v*dt| residual must stay at numerical-noise level (k=1: any real motion is v*dt; threshold 1e-4 m = 0.1 mm slack) |
| fuzz_touch_dry_laden40 | max_dv_step_ms | 0.004172 |  | 0.35 | PASS | WORKING_VALUE: M34 fuzz invariant: per-step velocity change of either body <= 0.35 m/s (same ceiling as kerb scenarios; solver impulse spikes would exceed it) |
| fuzz_touch_dry_laden40 | max_tire_friction_ratio | 1 |  | 1.001 | PASS | WORKING_VALUE: M34 fuzz invariant: sqrt(Fx^2+Fy^2) <= mu*Fz on every loaded wheel; combined-slip model bounds it by construction, margin 0.001 for float rounding |
| fuzz_touch_dry_laden40 | articulation_limit_excess_deg | 0 |  | 3.5 | PASS | WORKING_VALUE: D59 (owner, 2026-11-13) / ADR 0158 F1, ADR 0165: articulation may exceed the fifth-wheel soft yaw stop (yawLimitDeg = 90, yawStopFrequencyHz 3, tractor_4x2_generic.vehicle.json) by <= 3.5 deg; a stiffer stop (>= 4.5 Hz) breaks the 0.35 m/s jerk limit (ADR 0158 table). Measured max 3.33 deg (M34 hunt) |
| fuzz_touch_dry_laden40 | max_fifth_wheel_error_mm | 0.04502 |  | 5 | PASS | WORKING_VALUE: M34 fuzz invariant: kingpin/saddle constraint position error <= 5 mm (same as soak) |
| fuzz_touch_dry_laden40 | min_air_all_bar | 8.5 | 0 |  | PASS | WORKING_VALUE: M34 fuzz invariant: no negative air pressure in any reservoir/line (physical impossibility) |
| fuzz_touch_wet_empty | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: M34 fuzz invariant: no NaN/Inf in any body state (docs/04 s6.14) |
| fuzz_touch_wet_empty | max_pos_jump_m | 2.656E-15 |  | 0.0001 | PASS | WORKING_VALUE: M34 fuzz invariant: no teleportation; |dx_com - v*dt| residual must stay at numerical-noise level (k=1: any real motion is v*dt; threshold 1e-4 m = 0.1 mm slack) |
| fuzz_touch_wet_empty | max_dv_step_ms | 0.07499 |  | 0.35 | PASS | WORKING_VALUE: M34 fuzz invariant: per-step velocity change of either body <= 0.35 m/s (same ceiling as kerb scenarios; solver impulse spikes would exceed it) |
| fuzz_touch_wet_empty | max_tire_friction_ratio | 1 |  | 1.001 | PASS | WORKING_VALUE: M34 fuzz invariant: sqrt(Fx^2+Fy^2) <= mu*Fz on every loaded wheel; combined-slip model bounds it by construction, margin 0.001 for float rounding |
| fuzz_touch_wet_empty | articulation_limit_excess_deg | 0.7074 |  | 3.5 | PASS | WORKING_VALUE: D59 (owner, 2026-11-13) / ADR 0158 F1, ADR 0165: articulation may exceed the fifth-wheel soft yaw stop (yawLimitDeg = 90, yawStopFrequencyHz 3, tractor_4x2_generic.vehicle.json) by <= 3.5 deg; a stiffer stop (>= 4.5 Hz) breaks the 0.35 m/s jerk limit (ADR 0158 table). Measured max 3.33 deg (M34 hunt) |
| fuzz_touch_wet_empty | max_fifth_wheel_error_mm | 0.5822 |  | 5 | PASS | WORKING_VALUE: M34 fuzz invariant: kingpin/saddle constraint position error <= 5 mm (same as soak) |
| fuzz_touch_wet_empty | min_air_all_bar | 8.5 | 0 |  | PASS | WORKING_VALUE: M34 fuzz invariant: no negative air pressure in any reservoir/line (physical impossibility) |
| grade_5pct_steady@laden40 | mean_speed_kmh [150..end s] | 49.77 | 44 | 60 | PASS | DERIVED: v = eta P / (m g (sin a + f_r) + aero): 0.92 x 368 kW / (40 t x 9.81 x 0.0554 + ~0.7 kN) = 15 m/s (54 km/h); gear steps cost a few km/h |
| grade_5pct_steady@laden40 | speed_range_kmh [150..end s] | 0.05342 |  | 6 | PASS | WORKING_VALUE: no gear hunting on the climb (mass/grade-aware AMT) |
| grade_5pct_steady@laden40 | min_rpm [150..end s] | 1464 | 1000 |  | PASS | WORKING_VALUE: engine kept in the torque plateau (S1: 980-1270 rpm max torque) |
| grade_5pct_steady@laden40 | max_dv_step_ms | 0.006851 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| grade_5pct_steady@laden40 | max_fifth_wheel_error_mm | 0.0007608 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| grade_6pct_steady_comb@laden40 | mean_speed_kmh [150..end s] | 42.63 | 38 | 54 | PASS | DERIVED: v = eta P / (m g (sin a + f_r) + aero): 0.92 x 368 kW / (40 t x 9.81 x (0.0599+0.008) + ~0.7 kN) = 338.6 kW / 27.34 kN = 12.4 m/s = 44.6 km/h; pasmo jak w grade_5pct_steady (ok. +/-18%) |
| grade_6pct_steady_comb@laden40 | speed_range_kmh [150..end s] | 6.126E-05 |  | 6 | PASS | WORKING_VALUE: no gear hunting on the climb (limit jak w grade_5pct_steady) |
| grade_6pct_steady_comb@laden40 | downshift_count [150..end s] | 0 |  | 0 | PASS | WORKING_VALUE: docs/04 s6.4 'ustalona predkosc na podjezdzie' — zero redukcji w ustalonym oknie (jak launch_6pct_uphill_comb, ADR 0024) |
| grade_6pct_steady_comb@laden40 | min_rpm [150..end s] | 1640 | 1000 |  | PASS | WORKING_VALUE: engine kept in the torque plateau (S1: 980-1270 rpm max torque) |
| grade_6pct_steady_comb@laden40 | max_dv_step_ms | 0.008194 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| grade_6pct_steady_comb@laden40 | max_fifth_wheel_error_mm | 0.00129 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| jackknife_wet_curve_abs_100@empty | max_articulation_deg | 4.586 |  | 10 | PASS | WORKING_VALUE: ABS keeps the combination stable (and cuts the retarder) |
| jackknife_wet_curve_abs_100@empty | rear_lock_time_s | 0 |  | 0.1 | PASS | WORKING_VALUE: ABS prevents lock |
| jackknife_wet_curve_abs_100@empty | max_dv_step_ms | 0.05054 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| jackknife_wet_curve_abs_100@laden40 | max_articulation_deg | 5.139 |  | 10 | PASS | WORKING_VALUE: ABS keeps the combination stable (and cuts the retarder) |
| jackknife_wet_curve_abs_100@laden40 | rear_lock_time_s | 0 |  | 0.1 | PASS | WORKING_VALUE: ABS prevents lock |
| jackknife_wet_curve_abs_100@laden40 | max_dv_step_ms | 0.04929 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| jackknife_wet_curve_abs_50@empty | max_articulation_deg | 7.786 |  | 10 | PASS | WORKING_VALUE: ABS keeps the combination stable (and cuts the retarder) |
| jackknife_wet_curve_abs_50@empty | rear_lock_time_s | 0 |  | 0.1 | PASS | WORKING_VALUE: ABS prevents lock |
| jackknife_wet_curve_abs_50@empty | max_dv_step_ms | 0.03995 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| jackknife_wet_curve_abs_50@laden40 | max_articulation_deg | 5.139 |  | 10 | PASS | WORKING_VALUE: ABS keeps the combination stable (and cuts the retarder) |
| jackknife_wet_curve_abs_50@laden40 | rear_lock_time_s | 0 |  | 0.1 | PASS | WORKING_VALUE: ABS prevents lock |
| jackknife_wet_curve_abs_50@laden40 | max_dv_step_ms | 0.03865 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| jackknife_wet_curve_noabs@empty | max_articulation_deg | 87.52 | 30 |  | PASS | WORKING_VALUE: jackknife must be possible: lightly loaded drive axle locks first without load sensing, empty trailer pushes (classic driver/defect case) |
| jackknife_wet_curve_noabs@empty | rear_lock_time_s | 2.52 | 0.5 |  | PASS | WORKING_VALUE: drive axle locks without ABS |
| jackknife_wet_curve_noabs@empty | max_dv_step_ms | 0.04628 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| jackknife_wet_curve_noabs@laden40 | rear_lock_time_s | 4.51 | 0.5 |  | PASS | WORKING_VALUE: drive axle locks without ABS |
| jackknife_wet_curve_noabs@laden40 | max_dv_step_ms | 0.04106 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| jackknife_wet_curve_retarder_noabs@empty | max_articulation_deg | 92.36 | 30 |  | PASS | WORKING_VALUE: retarder on a slippery road without ABS cut-off: drive axle lock -> jackknife (why retarders are cut by ABS) |
| jackknife_wet_curve_retarder_noabs@empty | rear_lock_time_s | 1.85 | 0.2 |  | PASS | WORKING_VALUE: drive axle locks |
| jackknife_wet_curve_retarder_noabs@empty | max_dv_step_ms | 0.2267 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| jackknife_wet_curve_retarder_noabs@laden40 | rear_lock_time_s | 0.84 | 0.2 |  | PASS | WORKING_VALUE: drive axle locks |
| jackknife_wet_curve_retarder_noabs@laden40 | max_dv_step_ms | 0.2446 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| kerb_step_27cm_42kmh_comb@laden40 | max_dv_step_ms | 0.321 |  | 0.35 | PASS | WORKING_VALUE: no impulse spikes (same limit as the 14 cm kerb strike) |
| kerb_step_27cm_42kmh_comb@laden40 | max_pos_jump_m | 1.055E-14 |  | 1E-06 | PASS | WORKING_VALUE: no teleport |
| kerb_step_27cm_42kmh_comb@laden40 | max_fz_ratio | 6.061 | 5.2 | 7.5 | PASS | WORKING_VALUE: regression guard on measured 6.50 (phone 6.8x); a 27 cm step is above the tyre envelope a vertical-ray contact can climb smoothly |
| kerb_step_27cm_42kmh_comb@laden40 | max_wheel_airtime_s(1) | 0.39 |  | 0.5 | PASS | WORKING_VALUE: regression guard on measured 0.42 s (phone: both front wheels unloaded ~0.4 s) |
| kerb_step_27cm_42kmh_comb@laden40 | max_fifth_wheel_error_mm | 2.51 |  | 5 | PASS | WORKING_VALUE: constraint holds |
| kerb_step_27cm_42kmh_comb@laden40 | max_body_penetration_m | 0.03688 |  | 0.05 | PASS | WORKING_VALUE: ADR 0165: bumper strike on the 27 cm kerb crushes the bumper cover <= 5 cm (4 Hz contact, impact ~3.5 m/s limited by the jerk ceiling); measured 0.038 m (tractor Bumper corner, t 2.88 s) |
| lane_change_60@empty | max_articulation_deg | 1.334 |  | 6 | PASS | WORKING_VALUE: trailer follows without large swing at ~0.15-0.2 g |
| lane_change_60@empty | rearward_amplification | 0.9585 | 0.8 | 1.6 | PASS | WORKING_VALUE: as above |
| lane_change_60@empty | articulation_settle_deg [26..end s] | 0.0004366 |  | 0.5 | PASS | WORKING_VALUE: trailer swing damped after the manoeuvre |
| lane_change_60@empty | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift in a normal lane change |
| lane_change_60@empty | max_lat_accel_ms2 | 0.8731 |  | 2.5 | PASS | WORKING_VALUE: manoeuvre stays at the intended moderate level |
| lane_change_60@empty | max_yaw_rate_dps | 3.056 |  | 10 | PASS | WORKING_VALUE: no spin |
| lane_change_60@empty | max_dv_step_ms | 0.008578 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| lane_change_60@empty | max_fifth_wheel_error_mm | 0.005121 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| lane_change_60@laden40 | max_articulation_deg | 1.311 |  | 6 | PASS | WORKING_VALUE: trailer follows without large swing at ~0.15-0.2 g |
| lane_change_60@laden40 | rearward_amplification | 0.9665 | 0.8 | 1.6 | PASS | WORKING_VALUE: rearward amplification of tractor-semitrailers is about 1.0-1.3 in the literature (UNVERIFIED); WORKING band 0.8-1.6 |
| lane_change_60@laden40 | articulation_settle_deg [26..end s] | 0.0003936 |  | 0.5 | PASS | WORKING_VALUE: trailer swing damped after the manoeuvre |
| lane_change_60@laden40 | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift in a normal lane change |
| lane_change_60@laden40 | max_lat_accel_ms2 | 0.8726 |  | 2.5 | PASS | WORKING_VALUE: manoeuvre stays at the intended moderate level |
| lane_change_60@laden40 | max_yaw_rate_dps | 3.075 |  | 10 | PASS | WORKING_VALUE: no spin |
| lane_change_60@laden40 | max_dv_step_ms | 0.008423 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| lane_change_60@laden40 | max_fifth_wheel_error_mm | 0.004909 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| lane_change_80@solo | max_articulation_deg | 0 |  | 6 | PASS | WORKING_VALUE: trailer follows without large swing at ~0.15-0.2 g |
| lane_change_80@solo | articulation_settle_deg [26..end s] | 0 |  | 0.5 | PASS | WORKING_VALUE: trailer swing damped after the manoeuvre |
| lane_change_80@solo | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift in a normal lane change |
| lane_change_80@solo | max_lat_accel_ms2 | 0.9226 |  | 2.5 | PASS | WORKING_VALUE: manoeuvre stays at the intended moderate level |
| lane_change_80@solo | max_yaw_rate_dps | 2.431 |  | 10 | PASS | WORKING_VALUE: no spin |
| lane_change_80@solo | max_dv_step_ms | 0.009147 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| lane_change_80@solo | max_fifth_wheel_error_mm | 0 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| lane_change_80@empty | max_articulation_deg | 0.8519 |  | 6 | PASS | WORKING_VALUE: trailer follows without large swing at ~0.15-0.2 g |
| lane_change_80@empty | rearward_amplification | 0.9906 | 0.8 | 1.6 | PASS | WORKING_VALUE: as above |
| lane_change_80@empty | articulation_settle_deg [26..end s] | 0.0002176 |  | 0.5 | PASS | WORKING_VALUE: trailer swing damped after the manoeuvre |
| lane_change_80@empty | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift in a normal lane change |
| lane_change_80@empty | max_lat_accel_ms2 | 0.9382 |  | 2.5 | PASS | WORKING_VALUE: manoeuvre stays at the intended moderate level |
| lane_change_80@empty | max_yaw_rate_dps | 2.476 |  | 10 | PASS | WORKING_VALUE: no spin |
| lane_change_80@empty | max_dv_step_ms | 0.009159 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| lane_change_80@empty | max_fifth_wheel_error_mm | 0.003565 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| lane_change_80@laden40 | max_articulation_deg | 0.8255 |  | 6 | PASS | WORKING_VALUE: trailer follows without large swing at ~0.15-0.2 g |
| lane_change_80@laden40 | rearward_amplification | 0.9963 | 0.8 | 1.6 | PASS | WORKING_VALUE: rearward amplification of tractor-semitrailers is about 1.0-1.3 in the literature (UNVERIFIED); WORKING band 0.8-1.6 |
| lane_change_80@laden40 | articulation_settle_deg [26..end s] | 0.0003673 |  | 0.5 | PASS | WORKING_VALUE: trailer swing damped after the manoeuvre |
| lane_change_80@laden40 | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift in a normal lane change |
| lane_change_80@laden40 | max_lat_accel_ms2 | 0.9704 |  | 2.5 | PASS | WORKING_VALUE: manoeuvre stays at the intended moderate level |
| lane_change_80@laden40 | max_yaw_rate_dps | 2.559 |  | 10 | PASS | WORKING_VALUE: no spin |
| lane_change_80@laden40 | max_dv_step_ms | 0.009469 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| lane_change_80@laden40 | max_fifth_wheel_error_mm | 0.003593 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| launch_0_80_flat | rollback_m | 0 |  | 0.02 | PASS | WORKING_VALUE: no rollback on flat |
| launch_0_80_flat | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_0_80_flat | min_rpm [1..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near/above idle 600 rpm |
| launch_0_80_flat | time_to_kmh(60) | 10.33 | 7 | 20 | PASS | WORKING_VALUE: plausibility band from power-to-weight (368 kW / 7.5 t); no sourced solo-tractor acceleration data |
| launch_0_80_flat | time_to_kmh(80) | 14.69 | 12 | 32 | PASS | WORKING_VALUE: plausibility band from power-to-weight (368 kW / 7.5 t); no sourced solo-tractor acceleration data |
| launch_0_80_flat | max_dv_step_ms | 0.03451 |  | 0.1 | PASS | WORKING_VALUE: no jolts > 10 m/s^2 within one 10 ms step (shifts, clutch lock-up) |
| launch_0_80_flat | max_rpm_in_gear(6) [1..end s] | 1596 |  | 1900 | PASS | WORKING_VALUE: Stage 2 fix of the Stage 1 note: no ~2000 rpm overshoot in gears 4-5 (upshift prediction, short same-direction hold-off) |
| launch_12pct_uphill_comb@laden40 | rollback_m | 0.005335 |  | 0.05 | PASS | WORKING_VALUE: no rollback |
| launch_12pct_uphill_comb@laden40 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: no stall |
| launch_12pct_uphill_comb@laden40 | time_to_kmh(15) | 10.07 | 5 | 15 | PASS | WORKING_VALUE: plausibility; 8.7 s measured with ADR 0024 strategy (WORKING_VALUE) |
| launch_12pct_uphill_comb@laden40 | shift_count | 4 |  | 6 | PASS | WORKING_VALUE: no gear hunting: 1-2-3-4-5 then hold (17 shifts / 7 down-shifts 4-5-4 before ADR 0024) |
| launch_12pct_uphill_comb@laden40 | downshift_count [2..end s] | 0 |  | 0 | PASS | WORKING_VALUE: full throttle and still accelerating or on the governor: no down-shift (ADR 0024) |
| launch_12pct_uphill_comb@laden40 | min_speed_kmh [20..end s] | 19.48 | 18 |  | PASS | WORKING_VALUE: power-limited climb: 0.92 x 368 kW / (40 t x 9.81 x 0.125) = 6.9 m/s (25 km/h) upper bound; 18 km/h floor = 13.2 km/h with hunting before ADR 0024 |
| launch_12pct_uphill_comb@laden40 | max_dv_step_ms | 0.02551 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_12pct_uphill_comb@laden40 | max_fifth_wheel_error_mm | 0.01764 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| launch_6pct_uphill | rollback_m | 0.001666 |  | 0.05 | PASS | WORKING_VALUE: docs/04 s6.2 'bez cofania sie'; 5 cm allowance for tire/suspension compliance |
| launch_6pct_uphill | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_6pct_uphill | min_rpm [2..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near idle or above |
| launch_6pct_uphill | time_to_kmh(30) | 6.969 | 4 | 25 | PASS | WORKING_VALUE: plausibility band from power-to-weight (368 kW / 7.5 t); no sourced solo-tractor acceleration data |
| launch_6pct_uphill_cargo24_comb@cargo24 | rollback_m | 0.002404 |  | 0.05 | PASS | WORKING_VALUE: docs/04 s6.2 'bez cofania sie'; 5 cm for tire/suspension/kingpin compliance (jak launch_6pct_uphill_comb) |
| launch_6pct_uphill_cargo24_comb@cargo24 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_6pct_uphill_cargo24_comb@cargo24 | min_rpm [2..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near idle or above |
| launch_6pct_uphill_cargo24_comb@cargo24 | time_to_kmh(15) | 4.831 | 3 | 35 | PASS | WORKING_VALUE: plausibility band of launch_6pct_uphill_comb@laden40 (3-35 s); 24 t cargo ~ 38 t GCW, close to 40 t. UNVERIFIED (docs nie podaja liczby dla 24 t) |
| launch_6pct_uphill_cargo24_comb@cargo24 | max_clutch_temp_c | 36.71 |  | 250 | PASS | WORKING_VALUE: hill start must not overheat the clutch (thermal model WORKING_VALUE) |
| launch_6pct_uphill_cargo24_comb@cargo24 | shift_count | 5 |  | 14 | PASS | WORKING_VALUE: no gear hunting on the climb (limit jak w launch_6pct_uphill_comb) |
| launch_6pct_uphill_cargo24_comb@cargo24 | downshift_count [2..25 s] | 0 |  | 0 | PASS | WORKING_VALUE: full throttle and still accelerating: no down-shift (jak launch_6pct_uphill_comb, ADR 0024) |
| launch_6pct_uphill_cargo24_comb@cargo24 | min_speed_kmh [20..end s] | 29.73 | 10 |  | PASS | WORKING_VALUE: keeps climbing after the start (no stall-out from hunting) |
| launch_6pct_uphill_cargo24_comb@cargo24 | max_dv_step_ms | 0.02021 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_6pct_uphill_cargo24_comb@cargo24 | max_fifth_wheel_error_mm | 0.01212 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| launch_6pct_uphill_comb@empty | rollback_m | 0.002215 |  | 0.05 | PASS | WORKING_VALUE: docs/04 s6.2 'bez cofania sie'; 5 cm for tire/suspension/kingpin compliance |
| launch_6pct_uphill_comb@empty | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_6pct_uphill_comb@empty | min_rpm [2..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near idle or above |
| launch_6pct_uphill_comb@empty | time_to_kmh(15) | 3.106 | 1.5 | 20 | PASS | WORKING_VALUE: plausibility (14.5 t, traction-limited ~3 m/s^2 minus grade) |
| launch_6pct_uphill_comb@empty | max_clutch_temp_c | 29.16 |  | 250 | PASS | WORKING_VALUE: hill start must not overheat the clutch (thermal model WORKING_VALUE) |
| launch_6pct_uphill_comb@empty | shift_count | 7 |  | 14 | PASS | WORKING_VALUE: no gear hunting on the climb (Stage 2 fix: up-shift lands above the grade down-shift line) |
| launch_6pct_uphill_comb@empty | downshift_count [2..25 s] | 0 |  | 0 | PASS | WORKING_VALUE: full throttle and still accelerating: no down-shift (predictive down-shift hold, ADR 0024) |
| launch_6pct_uphill_comb@empty | min_speed_kmh [20..end s] | 54.58 | 10 |  | PASS | WORKING_VALUE: keeps climbing after the start (no stall-out from hunting) |
| launch_6pct_uphill_comb@empty | max_dv_step_ms | 0.0212 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_6pct_uphill_comb@empty | max_fifth_wheel_error_mm | 0.00844 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| launch_6pct_uphill_comb@laden40 | rollback_m | 0.002389 |  | 0.05 | PASS | WORKING_VALUE: docs/04 s6.2 'bez cofania sie'; 5 cm for tire/suspension/kingpin compliance |
| launch_6pct_uphill_comb@laden40 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_6pct_uphill_comb@laden40 | min_rpm [2..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near idle or above |
| launch_6pct_uphill_comb@laden40 | time_to_kmh(15) | 4.942 | 3 | 35 | PASS | WORKING_VALUE: 40 t on 6%: traction-limited (~0.8 x 11 t on the drive axle = 90 kN) minus 25 kN grade -> ~1.6 m/s^2 -> 2.6 s + clutch engagement; plausibility |
| launch_6pct_uphill_comb@laden40 | max_clutch_temp_c | 37.28 |  | 250 | PASS | WORKING_VALUE: hill start must not overheat the clutch (thermal model WORKING_VALUE) |
| launch_6pct_uphill_comb@laden40 | time_to_kmh(15) | 4.942 | 4.39 | 5.29 | PASS | WORKING_VALUE: regression guard = PlayMode CombinationLabTests.HillStart_6pct_40t (runner 4.84 s +-0.45 s after ADR 0134 smooth shift ramps; was 4.5 s); 6.2 s after ADR 0019 was a 3-2-3 shift, ADR 0024 |
| launch_6pct_uphill_comb@laden40 | shift_count | 5 |  | 14 | PASS | WORKING_VALUE: no gear hunting on the climb (Stage 2 fix: up-shift lands above the grade down-shift line) |
| launch_6pct_uphill_comb@laden40 | downshift_count [2..25 s] | 0 |  | 0 | PASS | WORKING_VALUE: full throttle and still accelerating: no down-shift (predictive down-shift hold, ADR 0024) |
| launch_6pct_uphill_comb@laden40 | min_speed_kmh [20..end s] | 28.68 | 10 |  | PASS | WORKING_VALUE: keeps climbing after the start (no stall-out from hunting) |
| launch_6pct_uphill_comb@laden40 | max_dv_step_ms | 0.01993 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_6pct_uphill_comb@laden40 | max_fifth_wheel_error_mm | 0.01151 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| launch_6pct_uphill_light_comb@laden40 | rollback_m | 0.002389 |  | 0.05 | PASS | WORKING_VALUE: no rollback |
| launch_6pct_uphill_light_comb@laden40 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: no stall |
| launch_6pct_uphill_light_comb@laden40 | time_to_kmh(10) | 20.11 | 3 | 45 | PASS | WORKING_VALUE: plausibility |
| launch_6pct_uphill_light_comb@laden40 | max_dv_step_ms | 0.01009 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_6pct_uphill_light_comb@laden40 | max_fifth_wheel_error_mm | 0.001915 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| launch_6pct_uphill_light_throttle | rollback_m | 0.001666 |  | 0.05 | PASS | WORKING_VALUE: docs/04 s6.2 'bez cofania sie' |
| launch_6pct_uphill_light_throttle | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_6pct_uphill_light_throttle | time_to_kmh(15) | 2.543 | 2 | 25 | PASS | WORKING_VALUE: plausibility band from power-to-weight (368 kW / 7.5 t); no sourced solo-tractor acceleration data |
| launch_flat_comb@empty | rollback_m | 2.255E-05 |  | 0.02 | PASS | WORKING_VALUE: no rollback on flat |
| launch_flat_comb@empty | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_flat_comb@empty | min_rpm [1..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near idle or above |
| launch_flat_comb@empty | time_to_kmh(60) | 13.82 | 12 | 35 | PASS | DERIVED: power-to-weight: 0.5 m v^2 / (0.75 x 368 kW) + 6-8 shifts x ~0.6 s interruption; 14.5 t |
| launch_flat_comb@empty | time_to_kmh(80) | 21.25 | 20 | 55 | PASS | DERIVED: as above incl. aero; 14.5 t |
| launch_flat_comb@empty | max_speed_kmh | 89.38 |  | 90.5 | PASS | SOURCED: S3: 90 km/h limiter |
| launch_flat_comb@empty | max_rpm_in_gear(6) [1..end s] | 1635 |  | 1900 | PASS | WORKING_VALUE: Stage 2 fix: no over-rev to the 1900-2100 rpm governor in the low gears |
| launch_flat_comb@empty | max_shift_retard_torque_nm [1..end s] | 0 |  | 1 | PASS | WORKING_VALUE: owner feel test 2026-11-10: no wheel brake / retarder / engine brake torque during an up-shift unless commanded (ADR 0004 addendum 2026-11-10) |
| launch_flat_comb@empty | min_accel_shift_gap_ms2 [1..end s] | -0.2076 | -0.3 |  | PASS | DERIVED: per-gap mean dv/dt with the clutch open: only rolling (cr 0.005-0.0055 x g = 0.05 m/s2) + aero (~0.05 laden / ~0.15 empty at 88 km/h) may decelerate; limit ~1.5x the worst case |
| launch_flat_comb@empty | max_shift_eye_pitch_swing_deg(1.5) [1..30 s] | 4.517 |  | 4 | **FAIL** | WORKING_VALUE: ADR 0134 owner feel test 2026-11-12 (pitch 'like a sports car'): regression guard on the per-shift eye nod; before ADR 0134 5.4 deg empty / 4.6 deg laden |
| launch_flat_comb@empty | max_clutch_temp_c | 28.14 |  | 250 | PASS | WORKING_VALUE: clutch below the warning temperature on a flat start |
| launch_flat_comb@empty | max_dv_step_ms | 0.02636 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_flat_comb@empty | max_fifth_wheel_error_mm | 0.009363 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| launch_flat_comb@laden40 | rollback_m | 0.0001335 |  | 0.02 | PASS | WORKING_VALUE: no rollback on flat |
| launch_flat_comb@laden40 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_flat_comb@laden40 | min_rpm [1..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near idle or above |
| launch_flat_comb@laden40 | time_to_kmh(60) | 28.04 | 25 | 60 | PASS | DERIVED: 0.5 x 40 t x 16.7^2 / (0.7 x 368 kW) = 22 s + shifts + rolling; plausibility band, no sourced test data |
| launch_flat_comb@laden40 | time_to_kmh(80) | 47.58 | 40 | 95 | PASS | DERIVED: as above, 22.2 m/s: 38 s + shifts + rolling + aero |
| launch_flat_comb@laden40 | max_speed_kmh | 89.17 |  | 90.5 | PASS | SOURCED: S3: 90 km/h limiter |
| launch_flat_comb@laden40 | max_rpm_in_gear(6) [1..end s] | 1681 |  | 1900 | PASS | WORKING_VALUE: Stage 2 fix: no over-rev to the 1900-2100 rpm governor in the low gears |
| launch_flat_comb@laden40 | max_shift_retard_torque_nm [1..end s] | 0 |  | 1 | PASS | WORKING_VALUE: owner feel test 2026-11-10: no wheel brake / retarder / engine brake torque during an up-shift unless commanded (ADR 0004 addendum 2026-11-10) |
| launch_flat_comb@laden40 | min_accel_shift_gap_ms2 [1..end s] | -0.1242 | -0.3 |  | PASS | DERIVED: per-gap mean dv/dt with the clutch open: only rolling (cr 0.005-0.0055 x g = 0.05 m/s2) + aero (~0.05 laden / ~0.15 empty at 88 km/h) may decelerate; limit ~1.5x the worst case |
| launch_flat_comb@laden40 | max_shift_eye_pitch_swing_deg(1.5) [1..30 s] | 3.187 |  | 4 | PASS | WORKING_VALUE: ADR 0134 owner feel test 2026-11-12 (pitch 'like a sports car'): regression guard on the per-shift eye nod; before ADR 0134 5.4 deg empty / 4.6 deg laden |
| launch_flat_comb@laden40 | max_clutch_temp_c | 38.14 |  | 250 | PASS | WORKING_VALUE: clutch below the warning temperature on a flat start |
| launch_flat_comb@laden40 | max_dv_step_ms | 0.02108 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_flat_comb@laden40 | max_fifth_wheel_error_mm | 0.00915 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| launch_flat_comb_part60@empty | rollback_m | 2.255E-05 |  | 0.02 | PASS | WORKING_VALUE: no rollback on flat |
| launch_flat_comb_part60@empty | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_flat_comb_part60@empty | min_rpm [1..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near idle or above |
| launch_flat_comb_part60@empty | time_to_kmh(50) | 15.08 | 8 | 30 | PASS | DERIVED: part load: plausibility around the Proctor/Grimes SAE 950136 traffic averages (bobtail 0.138 g, box 0.106 g over the first 50 ft) |
| launch_flat_comb_part60@empty | max_shift_retard_torque_nm [1..end s] | 0 |  | 1 | PASS | WORKING_VALUE: ADR 0004 addendum 2026-11-10: no vehicle braking during an up-shift |
| launch_flat_comb_part60@empty | max_shift_eye_pitch_swing_deg(1.5) [1..30 s] | 3.655 |  | 3.8 | PASS | WORKING_VALUE: ADR 0134 regression guard (WORKING_VALUE): per-shift eye nod at 60 % pedal; before ADR 0134 4.5 deg empty / 3.2 deg laden |
| launch_flat_comb_part60@empty | max_clutch_temp_c | 28.39 |  | 250 | PASS | WORKING_VALUE: clutch below the warning temperature on a flat start |
| launch_flat_comb_part60@empty | max_dv_step_ms | 0.02494 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_flat_comb_part60@empty | max_fifth_wheel_error_mm | 0.007019 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| launch_flat_comb_part60@laden40 | rollback_m | 0.0001335 |  | 0.02 | PASS | WORKING_VALUE: no rollback on flat |
| launch_flat_comb_part60@laden40 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_flat_comb_part60@laden40 | min_rpm [1..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near idle or above |
| launch_flat_comb_part60@laden40 | time_to_kmh(50) | 34.13 | 15 | 45 | PASS | DERIVED: part load 40 t: ~3.5 ft/s2 max from rest for 27-36 t trucks (Washburn freight curriculum 4.1, engineering estimate) -> >= 13 s to 50 km/h |
| launch_flat_comb_part60@laden40 | max_shift_retard_torque_nm [1..end s] | 0 |  | 1 | PASS | WORKING_VALUE: ADR 0004 addendum 2026-11-10: no vehicle braking during an up-shift |
| launch_flat_comb_part60@laden40 | max_shift_eye_pitch_swing_deg(1.5) [1..30 s] | 2.246 |  | 3.8 | PASS | WORKING_VALUE: ADR 0134 regression guard (WORKING_VALUE): per-shift eye nod at 60 % pedal; before ADR 0134 4.5 deg empty / 3.2 deg laden |
| launch_flat_comb_part60@laden40 | max_clutch_temp_c | 35.69 |  | 250 | PASS | WORKING_VALUE: clutch below the warning temperature on a flat start |
| launch_flat_comb_part60@laden40 | max_dv_step_ms | 0.01261 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_flat_comb_part60@laden40 | max_fifth_wheel_error_mm | 0.004352 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| limiter_downhill_2pct_comb@laden40 | max_speed_kmh | 94.34 |  | 96 | PASS | WORKING_VALUE: overrun protection: limiter 90 km/h (S3) + 4 km/h offset, overshoot below 2 km/h |
| limiter_downhill_2pct_comb@laden40 | min_speed_kmh [60..end s] | 93.78 | 88 |  | PASS | SOURCED: S3: the limiter only cuts fuelling, it does not brake - no speed drop below the limiter band on a descent |
| limiter_downhill_2pct_comb@laden40 | max_service_demand | 0 |  | 0 | PASS | WORKING_VALUE: service brake not used by the overrun protection |
| limiter_downhill_2pct_comb@laden40 | max_dv_step_ms | 0.003621 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| limiter_downhill_2pct_comb@laden40 | max_fifth_wheel_error_mm | 0.0001518 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| limiter_downhill_5pct_comb@laden40 | max_speed_kmh | 95.3 |  | 96 | PASS | WORKING_VALUE: overrun protection: limiter 90 km/h (S3) + 4 km/h offset, overshoot below 2 km/h |
| limiter_downhill_5pct_comb@laden40 | mean_speed_kmh [60..end s] | 94 | 92.5 | 95 | PASS | WORKING_VALUE: settles at limiter + offset; the limiter itself never brakes, so the speed stays above 90 km/h on the grade |
| limiter_downhill_5pct_comb@laden40 | speed_range_kmh [60..end s] | 6.096E-10 |  | 1.5 | PASS | WORKING_VALUE: no hunting / limit cycle of the overrun control |
| limiter_downhill_5pct_comb@laden40 | max_retarder_torque_nm | 1734 | 300 | 4000 | PASS | SOURCED: S2: secondary retarder up to 4000 Nm / 600 kW (class reference) |
| limiter_downhill_5pct_comb@laden40 | max_service_demand | 0 |  | 0 | PASS | WORKING_VALUE: service brake not used by the overrun protection |
| limiter_downhill_5pct_comb@laden40 | max_dv_step_ms | 0.006458 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| limiter_downhill_5pct_comb@laden40 | max_fifth_wheel_error_mm | 8.222E-05 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| manual_mode_shifts@laden40 | max_gear | 5 | 5 | 5 | PASS | WORKING_VALUE: driver-selected gears 2 -> 5 only (no automatic upshift in manual) |
| manual_mode_shifts@laden40 | rejected_shifts | 4 | 1 |  | PASS | WORKING_VALUE: over-revving downshift refused |
| manual_mode_shifts@laden40 | max_rpm [1..end s] | 2073 |  | 2130 | PASS | WORKING_VALUE: S1: max revs 2100 rpm (governor fade) respected in manual; 30 rpm overshoot allowance |
| manual_mode_shifts@laden40 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: no stall |
| park_12pct_down_comb@empty | creep_m [5..end s] | 0.002726 |  | 0.005 | PASS | SOURCED: holds without creep in the ground plane; 12% from R13 Annex 4 para 2.3.2 (towing vehicle parking brake holds the combination on 12%) |
| park_12pct_down_comb@empty | creep_m [60..end s] | 9.917E-06 |  | 0.0005 | PASS | WORKING_VALUE: no creep at all once settled (tire / suspension compliance only in the first seconds) |
| park_12pct_down_comb@empty | drift_m [5..end s] | 0.00379 |  | 0.012 | PASS | WORKING_VALUE: incl. vertical settling of the levelled air suspension (deadband 8 mm) |
| park_12pct_down_comb@empty | max_speed_after_ms [5..end s] | 0.0004806 |  | 0.001 | PASS | WORKING_VALUE: no oscillation / creep after settling |
| park_12pct_down_comb@empty | trailer_creep_m [5..end s] | 0.004754 |  | 0.005 | PASS | WORKING_VALUE: trailer held through the kingpin |
| park_12pct_down_comb@empty | max_dv_step_ms | 0.01017 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| park_12pct_down_comb@empty | max_fifth_wheel_error_mm | 9.579E-05 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| park_12pct_down_comb@laden40 | creep_m [5..end s] | 0.001519 |  | 0.005 | PASS | SOURCED: holds without creep in the ground plane; 12% from R13 Annex 4 para 2.3.2 (towing vehicle parking brake holds the combination on 12%) |
| park_12pct_down_comb@laden40 | creep_m [60..end s] | 4.432E-05 |  | 0.0005 | PASS | WORKING_VALUE: no creep at all once settled (tire / suspension compliance only in the first seconds) |
| park_12pct_down_comb@laden40 | drift_m [5..end s] | 0.004649 |  | 0.012 | PASS | WORKING_VALUE: incl. vertical settling of the levelled air suspension (deadband 8 mm) |
| park_12pct_down_comb@laden40 | max_speed_after_ms [5..end s] | 0.0005004 |  | 0.001 | PASS | WORKING_VALUE: no oscillation / creep after settling |
| park_12pct_down_comb@laden40 | trailer_creep_m [5..end s] | 0.004715 |  | 0.005 | PASS | WORKING_VALUE: trailer held through the kingpin |
| park_12pct_down_comb@laden40 | max_dv_step_ms | 0.01021 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| park_12pct_down_comb@laden40 | max_fifth_wheel_error_mm | 0.0003008 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| park_12pct_up_comb@empty | creep_m [5..end s] | 0.001917 |  | 0.005 | PASS | SOURCED: holds without creep in the ground plane; 12% from R13 Annex 4 para 2.3.2 (towing vehicle parking brake holds the combination on 12%) |
| park_12pct_up_comb@empty | creep_m [60..end s] | 5.713E-06 |  | 0.0005 | PASS | WORKING_VALUE: no creep at all once settled (tire / suspension compliance only in the first seconds) |
| park_12pct_up_comb@empty | drift_m [5..end s] | 0.005539 |  | 0.012 | PASS | WORKING_VALUE: incl. vertical settling of the levelled air suspension (deadband 8 mm) |
| park_12pct_up_comb@empty | max_speed_after_ms [5..end s] | 0.0004209 |  | 0.001 | PASS | WORKING_VALUE: no oscillation / creep after settling |
| park_12pct_up_comb@empty | trailer_creep_m [5..end s] | 0.005053 |  | 0.005 | **FAIL** | WORKING_VALUE: trailer held through the kingpin |
| park_12pct_up_comb@empty | max_dv_step_ms | 0.01015 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| park_12pct_up_comb@empty | max_fifth_wheel_error_mm | 8.472E-05 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| park_12pct_up_comb@laden40 | creep_m [5..end s] | 0.000998 |  | 0.005 | PASS | SOURCED: holds without creep in the ground plane; 12% from R13 Annex 4 para 2.3.2 (towing vehicle parking brake holds the combination on 12%) |
| park_12pct_up_comb@laden40 | creep_m [60..end s] | 3.619E-05 |  | 0.0005 | PASS | WORKING_VALUE: no creep at all once settled (tire / suspension compliance only in the first seconds) |
| park_12pct_up_comb@laden40 | drift_m [5..end s] | 0.003374 |  | 0.012 | PASS | WORKING_VALUE: incl. vertical settling of the levelled air suspension (deadband 8 mm) |
| park_12pct_up_comb@laden40 | max_speed_after_ms [5..end s] | 0.000427 |  | 0.001 | PASS | WORKING_VALUE: no oscillation / creep after settling |
| park_12pct_up_comb@laden40 | trailer_creep_m [5..end s] | 0.003402 |  | 0.005 | PASS | WORKING_VALUE: trailer held through the kingpin |
| park_12pct_up_comb@laden40 | max_dv_step_ms | 0.01016 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| park_12pct_up_comb@laden40 | max_fifth_wheel_error_mm | 0.0002431 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| park_brake_drive_away_comb@empty | max_speed_kmh [0..11 s] | 0.0005781 |  | 0.5 | PASS | WORKING_VALUE: owner requirement 2026-11-10: with P applied the truck must not drive off (speed stays ~0 for 10 s of full throttle) |
| park_brake_drive_away_comb@empty | creep_m [0..11 s] | 1.077E-05 |  | 0.05 | PASS | WORKING_VALUE: no creep through the parking brake (tyre/driveline wind-up only) |
| park_brake_drive_away_comb@empty | park_warning [1.1..11 s] | 1 | 1 |  | PASS | WORKING_VALUE: drive-away interlock raises the parking-brake warning (cluster/HUD, chime) |
| park_brake_drive_away_comb@empty | park_warning [13..end s] | 0 |  | 0 | PASS | WORKING_VALUE: no warning once P is released |
| park_brake_drive_away_comb@empty | max_clutch_temp_c | 26.54 |  | 120 | PASS | WORKING_VALUE: interlock keeps the clutch open: no slip heating against the spring brakes |
| park_brake_drive_away_comb@empty | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall against the parking brake |
| park_brake_drive_away_comb@empty | max_dv_step_ms | 0.02662 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion against the brakes |
| park_brake_drive_away_comb@laden40 | max_speed_kmh [0..11 s] | 0.002765 |  | 0.5 | PASS | WORKING_VALUE: owner requirement 2026-11-10: with P applied the truck must not drive off (speed stays ~0 for 10 s of full throttle) |
| park_brake_drive_away_comb@laden40 | creep_m [0..11 s] | 4.865E-05 |  | 0.05 | PASS | WORKING_VALUE: no creep through the parking brake (tyre/driveline wind-up only) |
| park_brake_drive_away_comb@laden40 | park_warning [1.1..11 s] | 1 | 1 |  | PASS | WORKING_VALUE: drive-away interlock raises the parking-brake warning (cluster/HUD, chime) |
| park_brake_drive_away_comb@laden40 | park_warning [13..end s] | 0 |  | 0 | PASS | WORKING_VALUE: no warning once P is released |
| park_brake_drive_away_comb@laden40 | max_clutch_temp_c | 31.87 |  | 120 | PASS | WORKING_VALUE: interlock keeps the clutch open: no slip heating against the spring brakes |
| park_brake_drive_away_comb@laden40 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall against the parking brake |
| park_brake_drive_away_comb@laden40 | min_speed_kmh [30..end s] | 46.72 | 25 |  | PASS | WORKING_VALUE: after P release the launch is normal (launch_flat_comb laden40 reaches ~30 km/h ~15 s after the start) |
| park_brake_drive_away_comb@laden40 | max_dv_step_ms | 0.02056 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion against the brakes |
| park_brake_hold_no_interlock_comb@laden40 | max_speed_kmh | 0.04415 |  | 1 | PASS | WORKING_VALUE: owner requirement 2026-11-10: 40 t must not move against the applied parking brake even under full engine torque in the launch gear |
| park_brake_hold_no_interlock_comb@laden40 | creep_m [0..12 s] | 0.02692 |  | 0.15 | PASS | WORKING_VALUE: only tyre / driveline wind-up, no drive-through |
| park_brake_hold_no_interlock_comb@laden40 | max_dv_step_ms | 0.001468 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion against the brakes |
| park_flat_5min_comb@empty | drift_m [5..end s] | 6.344E-05 |  | 0.005 | PASS | WORKING_VALUE: no creep |
| park_flat_5min_comb@empty | max_speed_after_ms [5..end s] | 3.703E-06 |  | 0.001 | PASS | WORKING_VALUE: no oscillation |
| park_flat_5min_comb@empty | max_dv_step_ms | 2.017E-05 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| park_flat_5min_comb@empty | max_fifth_wheel_error_mm | 4.038E-08 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| park_flat_5min_comb@laden40 | drift_m [5..end s] | 0.0003721 |  | 0.005 | PASS | WORKING_VALUE: no creep |
| park_flat_5min_comb@laden40 | max_speed_after_ms [5..end s] | 2.808E-05 |  | 0.001 | PASS | WORKING_VALUE: no oscillation |
| park_flat_5min_comb@laden40 | max_dv_step_ms | 0.0003513 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| park_flat_5min_comb@laden40 | max_fifth_wheel_error_mm | 9.126E-07 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| park_low_air_drive_away_comb@laden40 | max_speed_kmh | 0.002763 |  | 0.5 | PASS | WORKING_VALUE: spring brakes applied by low air: no drive-away until the system is charged (S5 / docs/04: air loss has real consequences) |
| park_low_air_drive_away_comb@laden40 | park_warning [1.1..end s] | 1 | 1 |  | PASS | WORKING_VALUE: interlock warning also for spring brakes applied by low air |
| park_low_air_drive_away_comb@laden40 | max_clutch_temp_c | 25 |  | 60 | PASS | WORKING_VALUE: clutch stays open |
| reverse_dock_s_maneuver_comb@empty | max_articulation_deg | 91.41 | 20 | 95 | PASS | WORKING_VALUE: S-manoeuvre folds the trailer but the fifth-wheel stop bounds it: +/-90 deg soft deformable stop (3 Hz critically damped), 95 deg = stop + compliance margin; >=20 deg proves the manoeuvre actually articulated |
| reverse_dock_s_maneuver_comb@empty | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: all wheels stay loaded while reversing |
| reverse_dock_s_maneuver_comb@empty | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| reverse_dock_s_maneuver_comb@empty | min_speed_kmh | -9.659 | -15 | -2 | PASS | WORKING_VALUE: dock reversing speed bounded: SpeedFwd < 0 in reverse, so |v| <= 15 km/h means min_speed_kmh >= -15; <= -2 km/h proves it actually reversed (integration r5: with selector D the S-steer path still ends at z -7.5 m, so final_z alone passed) |
| reverse_dock_s_maneuver_comb@empty | final_z_m | -29.17 |  | -3 | PASS | WORKING_VALUE: vehicle actually reversed (heading 0: forward = +z, so z must decrease by >= 3 m in 30 s) |
| reverse_dock_s_maneuver_comb@empty | max_dv_step_ms | 0.1159 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| reverse_dock_s_maneuver_comb@empty | max_fifth_wheel_error_mm | 0.1761 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| reverse_dock_s_maneuver_comb@laden40 | max_articulation_deg | 91.86 | 20 | 95 | PASS | WORKING_VALUE: S-manoeuvre folds the trailer but the fifth-wheel stop bounds it: +/-90 deg soft deformable stop (3 Hz critically damped), 95 deg = stop + compliance margin; >=20 deg proves the manoeuvre actually articulated |
| reverse_dock_s_maneuver_comb@laden40 | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: all wheels stay loaded while reversing |
| reverse_dock_s_maneuver_comb@laden40 | stalled | 1 |  | 0 | **FAIL** | WORKING_VALUE: engine must not stall |
| reverse_dock_s_maneuver_comb@laden40 | min_speed_kmh | -9.677 | -15 | -2 | PASS | WORKING_VALUE: dock reversing speed bounded: SpeedFwd < 0 in reverse, so |v| <= 15 km/h means min_speed_kmh >= -15; <= -2 km/h proves it actually reversed (integration r5: with selector D the S-steer path still ends at z -7.5 m, so final_z alone passed) |
| reverse_dock_s_maneuver_comb@laden40 | final_z_m | -23.29 |  | -3 | PASS | WORKING_VALUE: vehicle actually reversed (heading 0: forward = +z, so z must decrease by >= 3 m in 30 s) |
| reverse_dock_s_maneuver_comb@laden40 | max_dv_step_ms | 0.1574 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| reverse_dock_s_maneuver_comb@laden40 | max_fifth_wheel_error_mm | 0.1421 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| reverse_grade6pct_comb@empty | min_speed_kmh | -4.727 | -12 |  | PASS | WORKING_VALUE: ramp reversing speed bounded: SpeedFwd < 0 in reverse, |v| <= 12 km/h means min_speed_kmh >= -12 |
| reverse_grade6pct_comb@empty | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| reverse_grade6pct_comb@empty | min_rpm | 599.5 | 550 |  | PASS | WORKING_VALUE: engine stays above idle (idle 600 rpm; bound 550 guards lugging/stall) |
| reverse_grade6pct_comb@empty | drift_m | 44.41 | 8 |  | PASS | WORKING_VALUE: makes progress up the ramp: >= 8 m displacement in 40 s at 4 km/h target (4 km/h x 40 s = 44 m theoretical, minus ramp-up) |
| reverse_grade6pct_comb@empty | final_z_m | -44.33 |  | -5 | PASS | WORKING_VALUE: heading 0, grade rises towards +z: reversing up the ramp means z decreases by >= 5 m |
| reverse_grade6pct_comb@empty | max_articulation_deg | 0 |  | 20 | PASS | WORKING_VALUE: trailer stays aligned in straight reverse: articulation << mechanical stop +/-90 deg |
| reverse_grade6pct_comb@empty | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift on the ramp |
| reverse_grade6pct_comb@empty | max_dv_step_ms | 0.02042 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| reverse_grade6pct_comb@empty | max_fifth_wheel_error_mm | 0.006167 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| reverse_grade6pct_comb@laden40 | min_speed_kmh | -5.927 | -12 |  | PASS | WORKING_VALUE: ramp reversing speed bounded: SpeedFwd < 0 in reverse, |v| <= 12 km/h means min_speed_kmh >= -12 |
| reverse_grade6pct_comb@laden40 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| reverse_grade6pct_comb@laden40 | min_rpm | 599.5 | 550 |  | PASS | WORKING_VALUE: engine stays above idle (idle 600 rpm; bound 550 guards lugging/stall) |
| reverse_grade6pct_comb@laden40 | drift_m | 61.17 | 8 |  | PASS | WORKING_VALUE: makes progress up the ramp: >= 8 m displacement in 40 s at 4 km/h target (4 km/h x 40 s = 44 m theoretical, minus ramp-up) |
| reverse_grade6pct_comb@laden40 | final_z_m | -61.06 |  | -5 | PASS | WORKING_VALUE: heading 0, grade rises towards +z: reversing up the ramp means z decreases by >= 5 m |
| reverse_grade6pct_comb@laden40 | max_articulation_deg | 0 |  | 20 | PASS | WORKING_VALUE: trailer stays aligned in straight reverse: articulation << mechanical stop +/-90 deg |
| reverse_grade6pct_comb@laden40 | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift on the ramp |
| reverse_grade6pct_comb@laden40 | max_dv_step_ms | 0.01647 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| reverse_grade6pct_comb@laden40 | max_fifth_wheel_error_mm | 0.002615 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| rollover_r50_cog_high@laden40 | lat_accel_at_first_lift | 0.3362 | 0.25 | 0.55 | PASS | WORKING_VALUE: static rollover threshold of laden tractor-semitrailers ~0.3-0.45 g in the literature (UMTRI / Winkler; not opened, UNVERIFIED) |
| rollover_r50_cog_high@laden40 | max_fifth_wheel_error_mm | 0.1204 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| rollover_r50_cog_low@laden40 | lat_accel_at_first_lift | 0.4563 | 0.25 | 0.55 | PASS | WORKING_VALUE: static rollover threshold of laden tractor-semitrailers ~0.3-0.45 g in the literature (UMTRI / Winkler; not opened, UNVERIFIED) |
| rollover_r50_cog_low@laden40 | max_fifth_wheel_error_mm | 0.1592 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| slalom_70_comb@empty | max_articulation_deg | 1.53 |  | 6 | PASS | WORKING_VALUE: trailer follows the slalom without large swing; limit jak w lane_change_80 (6 deg). UNVERIFIED dla tej geometrii |
| slalom_70_comb@empty | rearward_amplification | 0.9693 | 0.8 | 1.6 | PASS | WORKING_VALUE: as above |
| slalom_70_comb@empty | articulation_settle_deg [26..end s] | 0.0001614 |  | 0.5 | PASS | WORKING_VALUE: trailer swing damped after the manoeuvre (jak lane_change_80) |
| slalom_70_comb@empty | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift in a slalom at 70 km/h |
| slalom_70_comb@empty | max_lat_accel_ms2 | 1.325 |  | 3.5 | PASS | WORKING_VALUE: manoeuvre stays at the intended moderate level; a_y peak ~ A pi^2 v^2 / (2 L^2) = 3.5*pi^2*(70/3.6)^2/(2*50^2) ~ 2.6 m/s^2, limit UNVERIFIED 3.5 |
| slalom_70_comb@empty | max_yaw_rate_dps | 3.989 |  | 10 | PASS | WORKING_VALUE: no spin |
| slalom_70_comb@empty | max_dv_step_ms | 0.01284 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| slalom_70_comb@empty | max_fifth_wheel_error_mm | 0.008843 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| slalom_70_comb@laden40 | max_articulation_deg | 1.612 |  | 6 | PASS | WORKING_VALUE: trailer follows the slalom without large swing; limit jak w lane_change_80 (6 deg). UNVERIFIED dla tej geometrii |
| slalom_70_comb@laden40 | rearward_amplification | 0.9902 | 0.8 | 1.6 | PASS | WORKING_VALUE: rearward amplification of tractor-semitrailers is about 1.0-1.3 in the literature (UNVERIFIED); WORKING band 0.8-1.6 (jak lane_change_80) |
| slalom_70_comb@laden40 | articulation_settle_deg [26..end s] | 0.0002437 |  | 0.5 | PASS | WORKING_VALUE: trailer swing damped after the manoeuvre (jak lane_change_80) |
| slalom_70_comb@laden40 | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift in a slalom at 70 km/h |
| slalom_70_comb@laden40 | max_lat_accel_ms2 | 1.431 |  | 3.5 | PASS | WORKING_VALUE: manoeuvre stays at the intended moderate level; a_y peak ~ A pi^2 v^2 / (2 L^2) = 3.5*pi^2*(70/3.6)^2/(2*50^2) ~ 2.6 m/s^2, limit UNVERIFIED 3.5 |
| slalom_70_comb@laden40 | max_yaw_rate_dps | 4.309 |  | 10 | PASS | WORKING_VALUE: no spin |
| slalom_70_comb@laden40 | max_dv_step_ms | 0.01392 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| slalom_70_comb@laden40 | max_fifth_wheel_error_mm | 0.01005 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| soak_30min_cycle@laden40 | max_fifth_wheel_error_mm | 0.01879 |  | 5 | PASS | WORKING_VALUE: no constraint drift over 30 min |
| soak_30min_cycle@laden40 | max_dv_step_ms | 0.1822 |  | 0.35 | PASS | WORKING_VALUE: no spikes |
| soak_30min_cycle@laden40 | mean_speed_kmh [30..50 s] | 73.02 | 60 | 82 | PASS | WORKING_VALUE: first cycle cruise |
| soak_30min_cycle@laden40 | mean_speed_kmh [1740..1760 s] | 72.46 | 60 | 82 | PASS | WORKING_VALUE: last cycle cruise (compare with first: no drift) |
| soak_30min_cycle@laden40 | max_speed_after_ms [85..89.9 s] | 0.0001335 |  | 0.002 | PASS | WORKING_VALUE: standstill in the first cycle |
| soak_30min_cycle@laden40 | max_speed_after_ms [1795..1799.9 s] | 0.0001492 |  | 0.002 | PASS | WORKING_VALUE: standstill in the last cycle: no energy growth |
| soak_30min_cycle@laden40 | min_air_service_bar | 11.34 | 8 |  | PASS | WORKING_VALUE: air supply sustains the duty cycle |
| soak_30min_cycle@laden40 | max_articulation_deg | 2.215 |  | 12 | PASS | WORKING_VALUE: lane changes stay tame |
| soak_30min_cycle@laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: M34 soak invariant: no NaN/Inf in 30 min (docs/04 s6.14) |
| soak_30min_cycle@laden40 | max_tire_friction_ratio | 0.916 |  | 1.001 | PASS | WORKING_VALUE: M34 soak invariant: sqrt(Fx^2+Fy^2) <= mu*Fz on every loaded wheel, margin 0.001 for float rounding |
| soak_30min_cycle@laden40 | articulation_limit_excess_deg | 0 |  | 0 | PASS | WORKING_VALUE: M34 soak invariant: articulation inside the 90 deg yaw stop (tractor_4x2_generic.vehicle.json:305) |
| soak_30min_cycle@laden40 | min_air_all_bar | 8.03 | 0 |  | PASS | WORKING_VALUE: M34 soak invariant: no negative pressure in any reservoir/line |
| soak_30min_cycle@laden40 | max_pos_jump_m | 0.003642 |  | 0.01 | PASS | WORKING_VALUE: M34 no-teleport: residual |dx_com - v*SampleDt|; sampleEvery=5 (SampleDt=0.05 s), uniformly braking body gives 0.5*a*SampleDt^2 = 0.5*8*0.05^2 = 0.01 m; measured 0.0037 |
| soak_30min_cycle@laden40 | energy_drift_j [1787..1799.9 s] | 3.981 |  | 5 | PASS | WORKING_VALUE: M34 soak: E=KE+PE drift over the last standstill window; parked baseline 727 kJ, measured 0.34-1.33 J (< 2e-6 relative); threshold 5 J = 7e-6 relative |
| soak_30min_cycle@laden40 | cab_spectrum_peak_amp_dps [1740..1800 s] | 0.1412 |  | 1 | PASS | WORKING_VALUE: M34 soak: dominant-frequency amplitude of the cab pitch-rate spectrum over the last 60 s; measured 0.147 deg/s at 1.17 Hz; threshold 1 deg/s bounds oscillation growth |
| soak_30min_parked@laden40 | drift_m [5..end s] | 0.0003719 |  | 0.005 | PASS | WORKING_VALUE: no creep |
| soak_30min_parked@laden40 | max_speed_after_ms [5..end s] | 2.762E-05 |  | 0.001 | PASS | WORKING_VALUE: no energy drift / oscillation |
| soak_30min_parked@laden40 | max_kinetic_energy_j [5..end s] | 1.301E-05 |  | 0.001 | PASS | WORKING_VALUE: no energy growth |
| soak_30min_parked@laden40 | min_air_service_bar [5..end s] | 12.5 | 10.5 |  | PASS | WORKING_VALUE: governor keeps the reservoirs in the cut-in/cut-out band |
| soak_30min_parked@laden40 | max_dv_step_ms | 0.001271 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| soak_30min_parked@laden40 | max_fifth_wheel_error_mm | 8.664E-07 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| soak_30min_parked@laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: M34 soak invariant: no NaN/Inf in 30 min (docs/04 s6.14) |
| soak_30min_parked@laden40 | max_tire_friction_ratio | 0.007023 |  | 1.001 | PASS | WORKING_VALUE: M34 soak invariant: sqrt(Fx^2+Fy^2) <= mu*Fz on every loaded wheel, margin 0.001 for float rounding |
| soak_30min_parked@laden40 | articulation_limit_excess_deg | 0 |  | 0 | PASS | WORKING_VALUE: M34 soak invariant: articulation inside the 90 deg yaw stop (tractor_4x2_generic.vehicle.json:305) |
| soak_30min_parked@laden40 | min_air_all_bar | 8.362 | 0 |  | PASS | WORKING_VALUE: M34 soak invariant: no negative pressure in any reservoir/line |
| soak_30min_parked@laden40 | energy_drift_j [5..end s] | 0.1076 |  | 5 | PASS | WORKING_VALUE: M34 soak: E=KE+PE drift over the whole parked soak; measured 0.57 J of 727 kJ (7.8e-7 relative); threshold 5 J |
| soak_30min_parked@laden40 | max_pos_jump_m [5..end s] | 6.475E-08 |  | 0.001 | PASS | WORKING_VALUE: M34 no-teleport at standstill; measured 2.1e-5 m (suspension settling); threshold 1e-3 m |
| soak_30min_parked@laden40 | cab_spectrum_peak_amp_dps [1740..1800 s] | 2.653E-14 |  | 0.01 | PASS | WORKING_VALUE: M34 soak: cab pitch-rate spectrum amplitude at standstill; measured 3.7e-14 deg/s (no oscillation); threshold 0.01 deg/s |
| speed_bump_comb@solo | max_dv_step_ms | 0.06927 |  | 0.35 | PASS | WORKING_VALUE: no impulse spikes |
| speed_bump_comb@solo | max_pos_jump_m | 9.166E-15 |  | 1E-06 | PASS | WORKING_VALUE: no teleport |
| speed_bump_comb@solo | max_fz_ratio | 1.826 |  | 4 | PASS | WORKING_VALUE: bounded wheel load peaks |
| speed_bump_comb@solo | max_cab_heave_mm | 35.82 |  | 50 | PASS | WORKING_VALUE: cab mounts stay inside their travel (soft stops) |
| speed_bump_comb@empty | max_dv_step_ms | 0.07009 |  | 0.35 | PASS | WORKING_VALUE: no impulse spikes |
| speed_bump_comb@empty | max_pos_jump_m | 1.06E-14 |  | 1E-06 | PASS | WORKING_VALUE: no teleport |
| speed_bump_comb@empty | max_fz_ratio | 1.756 |  | 4 | PASS | WORKING_VALUE: bounded wheel load peaks |
| speed_bump_comb@empty | max_cab_heave_mm | 34.32 |  | 50 | PASS | WORKING_VALUE: cab mounts stay inside their travel (soft stops) |
| speed_bump_comb@laden40 | max_dv_step_ms | 0.07326 |  | 0.35 | PASS | WORKING_VALUE: no impulse spikes |
| speed_bump_comb@laden40 | max_pos_jump_m | 1.032E-14 |  | 1E-06 | PASS | WORKING_VALUE: no teleport |
| speed_bump_comb@laden40 | max_fz_ratio | 1.753 |  | 4 | PASS | WORKING_VALUE: bounded wheel load peaks |
| speed_bump_comb@laden40 | max_cab_heave_mm | 41.69 |  | 50 | PASS | WORKING_VALUE: cab mounts stay inside their travel (soft stops) |
| standstill_12pct_downhill_parking | creep_m [5..end s] | 1.113E-05 |  | 0.005 | PASS | WORKING_VALUE: no creep in the ground plane (Stage 2: replaces the 3D drift, which now includes the levelled air suspension settling) |
| standstill_12pct_downhill_parking | creep_m [60..end s] | 4.882E-09 |  | 0.0005 | PASS | WORKING_VALUE: no creep at all once settled |
| standstill_12pct_downhill_parking | drift_m [5..end s] | 0.006934 |  | 0.012 | PASS | WORKING_VALUE: 3D displacement incl. vertical settling of the levelled rear air suspension (deadband 8 mm) |
| standstill_12pct_downhill_parking | max_speed_after_ms [5..end s] | 0.0003589 |  | 0.001 | PASS | WORKING_VALUE: no oscillation: |v| < 1 mm/s after settling |
| standstill_12pct_downhill_parking | max_abs_roll_deg [5..end s] | 2.577E-15 |  | 0.5 | PASS | WORKING_VALUE: sanity: vehicle stays level laterally |
| standstill_12pct_uphill_parking | creep_m [5..end s] | 1.079E-05 |  | 0.005 | PASS | WORKING_VALUE: no creep in the ground plane (Stage 2: replaces the 3D drift, which now includes the levelled air suspension settling) |
| standstill_12pct_uphill_parking | creep_m [60..end s] | 3.622E-09 |  | 0.0005 | PASS | WORKING_VALUE: no creep at all once settled |
| standstill_12pct_uphill_parking | drift_m [5..end s] | 0.004796 |  | 0.012 | PASS | WORKING_VALUE: 3D displacement incl. vertical settling of the levelled rear air suspension (deadband 8 mm) |
| standstill_12pct_uphill_parking | max_speed_after_ms [5..end s] | 0.0002806 |  | 0.001 | PASS | WORKING_VALUE: no oscillation: |v| < 1 mm/s after settling |
| standstill_12pct_uphill_parking | max_abs_roll_deg [5..end s] | 0 |  | 0.5 | PASS | WORKING_VALUE: sanity: vehicle stays level laterally |
| standstill_flat_parking | creep_m [5..end s] | 0 |  | 0.005 | PASS | WORKING_VALUE: no creep in the ground plane (Stage 2: replaces the 3D drift, which now includes the levelled air suspension settling) |
| standstill_flat_parking | creep_m [60..end s] | 0 |  | 0.0005 | PASS | WORKING_VALUE: no creep at all once settled |
| standstill_flat_parking | drift_m [5..end s] | 0 |  | 0.012 | PASS | WORKING_VALUE: 3D displacement incl. vertical settling of the levelled rear air suspension (deadband 8 mm) |
| standstill_flat_parking | max_speed_after_ms [5..end s] | 1.124E-14 |  | 0.001 | PASS | WORKING_VALUE: no oscillation: |v| < 1 mm/s after settling |
| standstill_flat_parking | max_abs_roll_deg [5..end s] | 0 |  | 0.5 | PASS | WORKING_VALUE: sanity: vehicle stays level laterally |
| steer_sign_forward_left | yaw_rate_mean_dps [3..end s] | -10.83 |  | -1 | PASS | DERIVED: docs/04 s6.15 steering command sign -> yaw sign (Unity frame: +steer = right = +yaw about +Y) |
| steer_sign_forward_left | lateral_displacement_m | -19.08 |  | -0.5 | PASS | DERIVED: moves towards -X (left) |
| steer_sign_forward_right | yaw_rate_mean_dps [3..end s] | 10.83 | 1 |  | PASS | DERIVED: docs/04 s6.15 steering command sign -> yaw sign (Unity frame: +steer = right = +yaw about +Y) |
| steer_sign_forward_right | lateral_displacement_m | 19.08 | 0.5 |  | PASS | DERIVED: moves towards +X (right) |
| steer_sign_reverse_right | yaw_rate_mean_dps [6..end s] | -3.875 |  | -1 | PASS | DERIVED: docs/04 s6.15 steering command sign -> yaw sign (Unity frame: +steer = right = +yaw about +Y); reversing: yaw = v/L tan(delta) with v<0 |
| steer_sign_reverse_right | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| steer_sign_reverse_right_comb@empty | yaw_rate_mean_dps [4..end s] | -3.984 |  | -0.3 | PASS | DERIVED: reversing with right steer: tractor yaws negative (same sign as solo) |
| steer_sign_reverse_right_comb@empty | max_dv_step_ms | 0.01522 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| steer_sign_reverse_right_comb@laden40 | yaw_rate_mean_dps [4..end s] | -3.162 |  | -0.3 | PASS | DERIVED: reversing with right steer: tractor yaws negative (same sign as solo) |
| steer_sign_reverse_right_comb@laden40 | max_dv_step_ms | 0.007772 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| steer_sign_right_comb@empty | yaw_rate_mean_dps [4..end s] | 21.08 | 1 |  | PASS | DERIVED: Unity frame: +steer = right = +yaw about +Y (same as solo) |
| steer_sign_right_comb@empty | max_dv_step_ms | 0.03068 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| steer_sign_right_comb@laden40 | yaw_rate_mean_dps [4..end s] | 17.16 | 1 |  | PASS | DERIVED: Unity frame: +steer = right = +yaw about +Y (same as solo) |
| steer_sign_right_comb@laden40 | max_dv_step_ms | 0.02309 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| straight_0_80_0@solo | rollback_m | 0 |  | 0.02 | PASS | WORKING_VALUE: no rollback on flat |
| straight_0_80_0@solo | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| straight_0_80_0@solo | time_to_kmh(60) | 10.33 | 7 | 20 | PASS | WORKING_VALUE: same band as launch_0_80_flat (power-to-weight 368 kW / 7.5 t) |
| straight_0_80_0@solo | time_to_kmh(80) | 14.69 | 12 | 32 | PASS | WORKING_VALUE: same band as launch_0_80_flat |
| straight_0_80_0@solo | max_speed_kmh | 80.58 |  | 83 | PASS | WORKING_VALUE: hold controller: overshoot after the full-throttle phase <= 3 km/h |
| straight_0_80_0@solo | stop_distance_m | 36.04 | 32 | 55 | PASS | SOURCED: same band as brake_80_0_dry (solo, dry, ABS) |
| straight_0_80_0@solo | mfdd_ms2 | 7.491 | 5 | 8 | PASS | SOURCED: R13 Annex 4 MFDD, N3 type-0 minimum 5.0 m/s^2; <= mu g |
| straight_0_80_0@solo | max_lateral_deviation_m | 5.748E-08 |  | 0.5 | PASS | WORKING_VALUE: straight-line stability under ABS braking (brake_80_0_* limit) |
| straight_0_80_0@solo | rear_lock_time_s | 0 |  | 0.03 | PASS | WORKING_VALUE: no drive-axle lock at brake onset (brake_80_0_* limit) |
| straight_0_80_0@solo | max_dv_step_ms | 0.08019 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes |
| straight_0_80_0@solo | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN |
| straight_0_80_0@empty | rollback_m | 2.255E-05 |  | 0.02 | PASS | WORKING_VALUE: no rollback on flat |
| straight_0_80_0@empty | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| straight_0_80_0@empty | time_to_kmh(60) | 13.82 | 12 | 35 | PASS | DERIVED: same band as launch_flat_comb@empty |
| straight_0_80_0@empty | time_to_kmh(80) | 21.25 | 20 | 55 | PASS | DERIVED: same band as launch_flat_comb@empty |
| straight_0_80_0@empty | max_speed_kmh | 80.4 |  | 83 | PASS | WORKING_VALUE: hold controller: overshoot after the full-throttle phase <= 3 km/h |
| straight_0_80_0@empty | stop_distance_m | 40.11 | 35 | 61.2 | PASS | SOURCED: same band as brake_80_0_dry_abs_comb: R13 Annex 4 type-0 N3 0.15 v + v^2/130 at 80 km/h |
| straight_0_80_0@empty | mfdd_ms2 | 7.364 | 5 | 8 | PASS | SOURCED: R13 Annex 4 MFDD, N3 type-0 minimum 5.0 m/s^2; <= mu g |
| straight_0_80_0@empty | max_lateral_deviation_m | 3.821E-07 |  | 0.5 | PASS | WORKING_VALUE: straight-line stability under ABS braking (brake_80_0_* limit) |
| straight_0_80_0@empty | rear_lock_time_s | 0 |  | 0.03 | PASS | WORKING_VALUE: no drive-axle lock at brake onset (brake_80_0_* limit) |
| straight_0_80_0@empty | max_dv_step_ms | 0.07621 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes |
| straight_0_80_0@empty | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN |
| straight_0_80_0@empty | trailer_lock_time_s | 0 |  | 0.05 | PASS | WORKING_VALUE: trailer ABS 2S/2M prevents lock |
| straight_0_80_0@empty | max_fifth_wheel_error_mm | 0.01517 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift |
| straight_0_80_0@empty | max_articulation_deg | 0 |  | 2 | PASS | WORKING_VALUE: no trailer swing on a straight incl. ABS stop |
| straight_0_80_0@laden40 | rollback_m | 0.0001335 |  | 0.02 | PASS | WORKING_VALUE: no rollback on flat |
| straight_0_80_0@laden40 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| straight_0_80_0@laden40 | time_to_kmh(60) | 28.04 | 25 | 60 | PASS | DERIVED: same band as launch_flat_comb@laden40 |
| straight_0_80_0@laden40 | time_to_kmh(80) | 47.58 | 40 | 95 | PASS | DERIVED: same band as launch_flat_comb@laden40 |
| straight_0_80_0@laden40 | max_speed_kmh | 80.02 |  | 83 | PASS | WORKING_VALUE: hold controller: overshoot after the full-throttle phase <= 3 km/h |
| straight_0_80_0@laden40 | stop_distance_m | 41.06 | 35 | 61.2 | PASS | SOURCED: same band as brake_80_0_dry_abs_comb |
| straight_0_80_0@laden40 | mfdd_ms2 | 6.913 | 5 | 8 | PASS | SOURCED: R13 Annex 4 MFDD, N3 type-0 minimum 5.0 m/s^2; <= mu g |
| straight_0_80_0@laden40 | max_lateral_deviation_m | 9.108E-07 |  | 0.5 | PASS | WORKING_VALUE: straight-line stability under ABS braking (brake_80_0_* limit) |
| straight_0_80_0@laden40 | rear_lock_time_s | 0 |  | 0.03 | PASS | WORKING_VALUE: no drive-axle lock at brake onset (brake_80_0_* limit) |
| straight_0_80_0@laden40 | max_dv_step_ms | 0.07504 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes |
| straight_0_80_0@laden40 | nan_detected | 0 |  | 0 | PASS | WORKING_VALUE: no NaN |
| straight_0_80_0@laden40 | trailer_lock_time_s | 0 |  | 0.05 | PASS | WORKING_VALUE: trailer ABS 2S/2M prevents lock |
| straight_0_80_0@laden40 | max_fifth_wheel_error_mm | 0.01796 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift |
| straight_0_80_0@laden40 | max_articulation_deg | 4.162E-07 |  | 2 | PASS | WORKING_VALUE: no trailer swing on a straight incl. ABS stop |
| straight_after_steer_pulse@solo | max_articulation_deg [10..14 s] | 0 |  | 0.05 | PASS | WORKING_VALUE: ADR 0151: released wheel -> trailer realigns; ideal-stick plate friction held 0.41 deg (40 t) for 20 s |
| straight_after_steer_pulse@solo | max_yaw_rate_dps [10..14 s] | 1.112E-05 |  | 0.05 | PASS | WORKING_VALUE: ADR 0151: straight wheels -> no steady turn (was 0.43 deg/s at 40 t) |
| straight_after_steer_pulse@solo | max_articulation_deg | 0 |  | 5 | PASS | WORKING_VALUE: the flick itself stays a mild manoeuvre |
| straight_after_steer_pulse@solo | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift |
| straight_after_steer_pulse@solo | max_dv_step_ms | 0.01371 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes |
| straight_after_steer_pulse@solo | max_fifth_wheel_error_mm | 0 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift |
| straight_after_steer_pulse@empty | max_articulation_deg [10..14 s] | 0.0004551 |  | 0.05 | PASS | WORKING_VALUE: ADR 0151: released wheel -> trailer realigns; ideal-stick plate friction held 0.41 deg (40 t) for 20 s |
| straight_after_steer_pulse@empty | max_yaw_rate_dps [10..14 s] | 8.345E-05 |  | 0.05 | PASS | WORKING_VALUE: ADR 0151: straight wheels -> no steady turn (was 0.43 deg/s at 40 t) |
| straight_after_steer_pulse@empty | max_articulation_deg | 2.303 |  | 5 | PASS | WORKING_VALUE: the flick itself stays a mild manoeuvre |
| straight_after_steer_pulse@empty | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift |
| straight_after_steer_pulse@empty | max_dv_step_ms | 0.01338 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes |
| straight_after_steer_pulse@empty | max_fifth_wheel_error_mm | 0.007944 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift |
| straight_after_steer_pulse@laden40 | max_articulation_deg [10..14 s] | 0.002605 |  | 0.05 | PASS | WORKING_VALUE: ADR 0151: released wheel -> trailer realigns; ideal-stick plate friction held 0.41 deg (40 t) for 20 s |
| straight_after_steer_pulse@laden40 | max_yaw_rate_dps [10..14 s] | 0.001014 |  | 0.05 | PASS | WORKING_VALUE: ADR 0151: straight wheels -> no steady turn (was 0.43 deg/s at 40 t) |
| straight_after_steer_pulse@laden40 | max_articulation_deg | 2.436 |  | 5 | PASS | WORKING_VALUE: the flick itself stays a mild manoeuvre |
| straight_after_steer_pulse@laden40 | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift |
| straight_after_steer_pulse@laden40 | max_dv_step_ms | 0.01244 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes |
| straight_after_steer_pulse@laden40 | max_fifth_wheel_error_mm | 0.008915 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift |
| top_speed_flat | max_speed_kmh | 89.34 |  | 90.5 | PASS | SOURCED: Council Directive 92/6/EEC as amended by 2002/85/EC: N3 speed limitation device set to 90 km/h (+0.5 km/h numeric allowance WORKING_VALUE) |
| top_speed_flat | mean_speed_kmh [80..end s] | 89.34 | 88 | 90 | PASS | WORKING_VALUE: settles just under the limiter set speed; 3 km/h band |
| top_speed_flat_comb@empty | max_speed_kmh | 89.38 |  | 90.5 | PASS | SOURCED: S3: 90 km/h speed limiter (N3) |
| top_speed_flat_comb@empty | mean_speed_kmh [90..end s] | 89.38 | 88 | 90 | PASS | SOURCED: settles at the limiter: 89 +/- 1 km/h (set speed 90 km/h, 2 km/h fuelling fade band) |
| top_speed_flat_comb@empty | final_gear | 12 | 12 | 12 | PASS | WORKING_VALUE: top gear at cruise |
| top_speed_flat_comb@empty | max_dv_step_ms | 0.007993 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| top_speed_flat_comb@empty | max_fifth_wheel_error_mm | 0.0004311 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| top_speed_flat_comb@laden40 | max_speed_kmh | 89.17 |  | 90.5 | PASS | SOURCED: S3: 90 km/h speed limiter (N3) |
| top_speed_flat_comb@laden40 | mean_speed_kmh [90..end s] | 89.17 | 88 | 90 | PASS | SOURCED: settles at the limiter: 89 +/- 1 km/h (set speed 90 km/h, 2 km/h fuelling fade band) |
| top_speed_flat_comb@laden40 | final_gear | 12 | 12 | 12 | PASS | WORKING_VALUE: top gear at cruise |
| top_speed_flat_comb@laden40 | max_dv_step_ms | 0.00278 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| top_speed_flat_comb@laden40 | max_fifth_wheel_error_mm | 0.0001231 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |

## Multi-run checks
- repeatability 0-60 km/h [s]: [10.326, 10.326, 10.326] mean 10.326, max dev 0.00%
- repeatability 0-80 km/h [s]: [14.694, 14.694, 14.694] mean 14.694, max dev 0.00%
- launch_0_80_flat:time_to_kmh(80) @dt 50Hz/60Hz/100Hz/120Hz: [14.441, 14.413, 14.694, 14.738] mean 14.571, max dev 1.14%
- brake_80_0_dry:stop_distance_m(0) @dt 50Hz/60Hz/100Hz/120Hz: [34.128, 34.379, 34.253, 34.343] mean 34.276, max dev 0.43%
- circle_r25_20kmh:lat_accel_ms2(0) @dt 50Hz/60Hz/100Hz/120Hz: [1.218, 1.218, 1.218, 1.218] mean 1.218, max dev 0.02%
- brake_80_0_dry_abs_comb@laden40:stop_distance_m(0) @dt 50Hz/60Hz/100Hz/120Hz: [40.907, 41.166, 41.350, 41.370] mean 41.198, max dev 0.71%
- lane_change_80@laden40:max_articulation_deg(0) @dt 50Hz/60Hz/100Hz/120Hz: [0.822, 0.823, 0.825, 0.826] mean 0.824, max dev 0.28%
- launch_flat_comb@laden40:time_to_kmh(60) @dt 50Hz/60Hz/100Hz/120Hz: [28.395, 28.283, 28.043, 28.162] mean 28.221, max dev 0.63%
- brake_80_0_dry:stop_distance_m(0) @substeps 2/4/8: [34.243, 34.253, 34.699] mean 34.398, max dev 0.88%
- brake_80_0_dry_abs_comb@laden40:stop_distance_m(0) @substeps 2/4/8: [41.093, 41.350, 41.128] mean 41.190, max dev 0.39%
- cost: full 40 t combination (10 wheel ends x 15 rays, 4 substeps, fifth wheel 8 it.), desktop Release: mean 13.7 us/step, p50 12.5, p99 26.7, max 1032.3 us
