# ADR 0024 - AMT: no down-shift while the truck is still pulling, no governor up-shift into a gear that cannot hold speed

Status: accepted (2026-11-10). Touches `AmtController.AutoDrive` only; no gearbox data changed.

## Context
PlayMode `CombinationLabTests.HillStart_6pct_40t_NoRollback` failed on main: 0-15 km/h 6.27 s against 4.5 s ± 10 %.
The runner gives the same number (launch_6pct_uphill_comb@laden40 6.17 s; it passed only because its range was 3-35 s),
so this was not a runner/Unity timing difference. Before ADR 0019 (`35045b5~1`) the runner gave 4.54 s and 5 shifts.

Root cause (runner CSVs, shift events): the ASR-limited launch closes the clutch in 3rd at ~1100 rpm, which is below
the grade-boosted full-throttle down-shift line (1100 + 200 = 1300 rpm). When the 0.3 s same-direction hold-off expired,
the engine was at 1293.6 rpm and still rising at ~220 rpm/s (truck accelerating at 1.5 m/s²). Because 1293.6 < 1300, the
AMT shifted 3-2, then 2-3 and 3-4, costing two torque interruptions (~1.6 s). Before ADR 0019 the engine happened to be
just above 1300 at that moment. With 0.35 t less on the drive axle the launch is a few percent slower, which was
enough to cross the line. ADR 0019 only exposed the fault. The same 3-2-3 occurred at baseline on 3, 4 and 5 % (grade sweep), and on 12 %
the strategy hunted 4-5-4 indefinitely (19 shifts in 45 s). There, the over-rev guard forced 4-5 at the governor
and the down-shift fired as soon as the 1 s hold-off ran out, while the truck was still accelerating in 5th.

## Decision
1. **Down-shift hold while pulling.** At >= 30 % pedal and outside engine-brake mode, no down-shift happens while the force
   balance in the current gear (full-load torque x pedal x ratio x efficiency / r - grade - rolling - aero, the same
   function the up-shift acceptance uses) still gives >= `minAccelAfterUpshift` x pedal. This mirrors the up-shift rule
   and adds no new parameter: the AMT up-shifts only into a gear in which it can accelerate, and it does not leave a gear
   in which it is accelerating. The hold is model-based, not measured, because the rpm trend is distorted for ~0.5 s after every clutch close.
2. **Lugging guard keeps priority.** If the model is optimistic (ASR cut, wrong mass) the engine keeps falling. The guard
   (line - 150 rpm) is judged on rpm + max(0, rpm rate) x 0.545 s, which mirrors the up-shift rpm prediction. A falling
   engine downshifts at once, and a fast-rising one just after the launch clutch closes is not treated as lugging.
3. **Over-rev up-shift needs >= 0.** At the governor the next gear is still taken with little reserve, but only if the
   truck can at least hold speed in it. Otherwise the engine stays on the governor (steep climbs).
4. **rpm-rate filter initialisation.** On the first update after construction or `ForceState`, the rate starts at 0
   (it used to see a 0 -> rpm step, a spike of ~4000 rpm/s that decayed over ~0.5 s).
5. Engine-brake mode is unchanged: there a rising rpm means the truck runs away downhill and needs the lower gear.

Source for the principle: shift programs that decide on the driving-resistance balance (the truck must be able to
accelerate in the target gear, and hysteresis between the up- and down-shift conditions prevents pendulum shifting) are the
textbook AMT approach (Naunheimer, Bertsche, Ryborz, Novak, *Automotive Transmissions*, 2nd ed., Springer 2011, chapter
on shift strategies; not re-opened, UNVERIFIED). Holding a gear on the governor on steep climbs instead of shifting up
and back is how production truck AMTs are commonly described to behave (UNVERIFIED, no manufacturer data opened). All
thresholds are WORKING_VALUE, as before.

## Consequences
- launch_6pct_uphill_comb@laden40: 6.17 -> 4.59 s, 7 -> 5 shifts (3-4-5-6-7-8, as before ADR 0019), min speed after
  20 s 28.9 -> 30.5 km/h. The PlayMode reference of 4.5 s ± 10 % was correct and stays.
- Grade sweep, 40 t, full throttle (0-15 km/h / shifts): 3 % 4.93 -> 3.54 s / 7 -> 5; 4 % 5.24 -> 3.71 / 7 -> 5;
  5 % 5.53 -> 3.89 / 6 -> 4; 7-10 % unchanged; 12 % 8.71 s / 19 -> 4 shifts, steady 21.5 km/h in 5th at 1808 rpm
  instead of 13-17 km/h hunting; 14 % 22 -> 4 shifts; 16 % now reaches 15 km/h (13.3 s).
- Fewer spurious shifts at scenario start. Previously a one-step throttle spike at t = 0 with 1068 rpm in 11th
  triggered 11-10 and then 10-9/10-11. downhill_7pct_brake_cruise_60 now goes 11-9 directly, so the engine brake works
  sooner and the peak retarder torque falls 3102 -> 2384 N m (-23 %). top_speed_flat_comb holds 11th instead of 11-10-11-12.
- New runner metric `downshift_count`. New checks: launch_6pct_uphill_comb gets time_to_kmh(15) laden40 4.05-4.95 s
  (= the PlayMode tolerance) and no down-shift 2-25 s. New scenario launch_12pct_uphill_comb@laden40: <= 6 shifts, no
  down-shift, >= 18 km/h after 20 s (fails on the old strategy: 19 / 8 / 13.2).
- Goldens regenerated: launch_6pct_uphill_comb_laden40, jackknife_wet_curve_noabs_empty (first 6 s gear/rpm only; the
  jackknife event itself is bit-identical).
- Feel: on a climb the AMT now shifts up in sequence and stays in gear. When it cannot accelerate it sits on the governor (high, steady
  engine note) instead of shifting every ~4 s.
