# Physics validation run 2026-11-12 14:56  (commit afaa87c9)

| scenario | metric | value | min | max | status | source |
|---|---|---|---|---|---|---|
| launch_flat_comb@empty | rollback_m | 2.418E-05 |  | 0.02 | PASS | WORKING_VALUE: no rollback on flat |
| launch_flat_comb@empty | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_flat_comb@empty | min_rpm [1..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near idle or above |
| launch_flat_comb@empty | time_to_kmh(60) | 13.27 | 12 | 35 | PASS | DERIVED: power-to-weight: 0.5 m v^2 / (0.75 x 368 kW) + 6-8 shifts x ~0.6 s interruption; 14.5 t |
| launch_flat_comb@empty | time_to_kmh(80) | 20.46 | 20 | 55 | PASS | DERIVED: as above incl. aero; 14.5 t |
| launch_flat_comb@empty | max_speed_kmh | 89.39 |  | 90.5 | PASS | SOURCED: S3: 90 km/h limiter |
| launch_flat_comb@empty | max_rpm_in_gear(6) [1..end s] | 1704 |  | 1900 | PASS | WORKING_VALUE: Stage 2 fix: no over-rev to the 1900-2100 rpm governor in the low gears |
| launch_flat_comb@empty | max_shift_retard_torque_nm [1..end s] | 0 |  | 1 | PASS | WORKING_VALUE: owner feel test 2026-11-10: no wheel brake / retarder / engine brake torque during an up-shift unless commanded (ADR 0004 addendum 2026-11-10) |
| launch_flat_comb@empty | min_accel_shift_gap_ms2 [1..end s] | -0.2072 | -0.3 |  | PASS | DERIVED: per-gap mean dv/dt with the clutch open: only rolling (cr 0.005-0.0055 x g = 0.05 m/s2) + aero (~0.05 laden / ~0.15 empty at 88 km/h) may decelerate; limit ~1.5x the worst case |
| launch_flat_comb@empty | max_clutch_temp_c | 28.63 |  | 250 | PASS | WORKING_VALUE: clutch below the warning temperature on a flat start |
| launch_flat_comb@empty | max_dv_step_ms | 0.02837 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_flat_comb@empty | max_fifth_wheel_error_mm | 0.01063 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
| launch_flat_comb@laden40 | rollback_m | 0.0001558 |  | 0.02 | PASS | WORKING_VALUE: no rollback on flat |
| launch_flat_comb@laden40 | stalled | 0 |  | 0 | PASS | WORKING_VALUE: engine must not stall |
| launch_flat_comb@laden40 | min_rpm [1..end s] | 600 | 550 |  | PASS | WORKING_VALUE: engine stays near idle or above |
| launch_flat_comb@laden40 | time_to_kmh(60) | 26.91 | 25 | 60 | PASS | DERIVED: 0.5 x 40 t x 16.7^2 / (0.7 x 368 kW) = 22 s + shifts + rolling; plausibility band, no sourced test data |
| launch_flat_comb@laden40 | time_to_kmh(80) | 46.18 | 40 | 95 | PASS | DERIVED: as above, 22.2 m/s: 38 s + shifts + rolling + aero |
| launch_flat_comb@laden40 | max_speed_kmh | 89.18 |  | 90.5 | PASS | SOURCED: S3: 90 km/h limiter |
| launch_flat_comb@laden40 | max_rpm_in_gear(6) [1..end s] | 1702 |  | 1900 | PASS | WORKING_VALUE: Stage 2 fix: no over-rev to the 1900-2100 rpm governor in the low gears |
| launch_flat_comb@laden40 | max_shift_retard_torque_nm [1..end s] | 0 |  | 1 | PASS | WORKING_VALUE: owner feel test 2026-11-10: no wheel brake / retarder / engine brake torque during an up-shift unless commanded (ADR 0004 addendum 2026-11-10) |
| launch_flat_comb@laden40 | min_accel_shift_gap_ms2 [1..end s] | -0.1258 | -0.3 |  | PASS | DERIVED: per-gap mean dv/dt with the clutch open: only rolling (cr 0.005-0.0055 x g = 0.05 m/s2) + aero (~0.05 laden / ~0.15 empty at 88 km/h) may decelerate; limit ~1.5x the worst case |
| launch_flat_comb@laden40 | max_clutch_temp_c | 37.74 |  | 250 | PASS | WORKING_VALUE: clutch below the warning temperature on a flat start |
| launch_flat_comb@laden40 | max_dv_step_ms | 0.02173 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes (per-step velocity change of either body) |
| launch_flat_comb@laden40 | max_fifth_wheel_error_mm | 0.01128 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift (custom fifth-wheel constraint) |
