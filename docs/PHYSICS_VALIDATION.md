# Physics validation — Stage 1, tractor solo 4x2

Status: **all 21 scenarios and 32 xUnit tests are green** in the plain .NET runner (2026-11-09, base commit `e9a9268` plus this change). Nothing has been run in Unity or on a device yet. Unity was still being installed.

Parameter provenance: `docs/VEHICLE_REFERENCE_DATA.md`. Most numbers are WORKING_VALUE. The tolerances below therefore check **plausibility and numerical quality** (stability, no creep, no spikes, dt-independence, sign conventions). They do **not** check that the model matches a specific real truck.

## 1. How to run

```powershell
dotnet test tools/physics-runner                                    # 32 tests (xUnit), ~3 s
dotnet run -c Release --project tools/physics-runner/Runner         # all scenarios + CSV to artifacts/physics/<timestamp>/
dotnet run -c Release --project tools/physics-runner/Runner -- --only brake_80_0_dry
uv run tools/telemetry/plot.py artifacts/physics/<timestamp>/        # one PNG per CSV, next to it
```

Requirements: a .NET SDK 8 or newer (projects target `net8.0` with `RollForward=Major`), and `uv` for the plots.

On this machine the system-wide SDK was missing. A user-local SDK 10.0.403 was installed to `%LOCALAPPDATA%\Microsoft\dotnet` with the official `dotnet-install.ps1`. To use it, set `DOTNET_ROOT` to that folder and put it first in `PATH`.

## 2. Architecture (ADR 0004)

```
game/Assets/_Project/Vehicle/Physics/        Game.Vehicle.Physics.asmdef (noEngineReferences: true), pure C# 9
  Math/          Vec3, Quat, Mat3 (double; Unity component layout; handedness-agnostic formulas)
  Definitions/   VehicleDefinition, TireDefinition, EngineDefinition, GearboxDefinition (+schemaVersion,
                 Validate()), MassProperties (CoM + inertia tensor from mass elements), Data/*.json
  Core/          IGroundQuery, GroundHit, ChassisState, DriverInput, AppliedForce
  Components/    TireModel, Engine, AmtController, Steering, CabSuspension, WheelState
  VehicleModel   the solver: ChassisState + DriverInput + IGroundQuery -> forces at world points
tools/physics-runner/
  Sim/           compiles the sources above via <Compile Include="../../../game/.../*.cs">,
                 plus RigidBody6Dof, AnalyticGround, scenario/driver/metric/telemetry code
  Runner/        console: all scenarios -> CSV + summary.md
  Tests/         xUnit
tests/physics/scenarios/*.json   scenario = ground, initial state, driver, checks (min/max + status + source)
tools/telemetry/plot.py          CSV -> PNG
```

### Fixed step and substeps
`VehicleModel.Step(dt, chassis, input, ground)` is called once per fixed step (100 Hz).

Once per step it does:
- suspension and contact: multi-ray wheel contact, spring, tire radial compliance, damper, anti-roll bar;
- steering, brakes/ABS/ASR/hill-hold, AMT logic.

Then it runs `substeps` (default 4) inner iterations of:
- tire relaxation states and combined-slip forces;
- wheel spin;
- engine;
- clutch + brake constraints, solved with projected Gauss-Seidel using Coulomb capacity limits. A locked brake gives exactly ω = 0, so there is no creep.

During the substeps the chassis velocity is held fixed. The resulting tire forces are averaged over the substeps and handed to the rigid-body host. The model **never integrates the chassis and never applies gravity**.

### Unity adapter (to be written by the leader / gameplay; it is a thin layer)
```csharp
// Vehicle/Runtime/VehicleBody.cs (UnityEngine side) — sketch
void Awake() {
    model = new VehicleModel(vehicleDef, engineDef, gearboxDef, tires, settings);   // defs from TextAsset JSON
    rb.mass = (float)model.MassProps.Mass;
    rb.centerOfMass = ToV3(model.MassProps.CenterOfMass);
    // inertia: diagonalise MassProps.Inertia (symmetric 3x3) -> rb.inertiaTensor + rb.inertiaTensorRotation
}
void FixedUpdate() {                       // Time.fixedDeltaTime = 0.01
    var s = new ChassisState { Position = ToD(rb.position), Rotation = ToD(rb.rotation),
        CenterOfMassWorld = ToD(rb.worldCenterOfMass), LinearVelocity = ToD(rb.linearVelocity),
        AngularVelocity = ToD(rb.angularVelocity) };
    model.Step(Time.fixedDeltaTime, s, input, groundQuery);     // groundQuery: Physics.Raycast on the road mesh layer
    for (int i = 0; i < model.ForceCount; i++)
        rb.AddForceAtPosition(ToV3(model.Forces[i].Force), ToV3(model.Forces[i].Point), ForceMode.Force);
}
```
- `IGroundQuery` maps to `Physics.Raycast(origin, dir, out hit, maxDist, roadMask)`. Use `QueryTriggerInteraction.Ignore` and do not allocate. The surface friction scale comes from a `PhysicMaterial`/surface table lookup keyed by the collider.
- The vehicle frame origin is on the ground below the rear-axle centre at design ride height. The prefab's root must use the same origin, or the adapter applies a constant offset.
- Gravity stays on the Rigidbody (`useGravity = true`). PhysX integrates the body and resolves chassis–world collisions. The wheels never have colliders.
- Floating origin: an origin shift between steps is safe. The solver keeps no absolute world positions between steps. Tire deflections, suspension `SPrev` and the previous velocity used for cab acceleration are all relative quantities. `ChassisState` is in world coordinates, but it is used only within a single step.
- The solver uses `double` internally. Converting to and from Unity `float` happens only in the adapter.

## 3. Results (runner, dt = 0.01 s, 4 substeps)

Run `artifacts/physics/20261109-110958` (gitignored). CSV and PNG for every scenario are in that folder.

| docs/04 §6 | Scenario | Metric | Result | Expected / tolerance | Status of expectation | Pass |
|---|---|---|---|---|---|---|
| 1 | standstill_flat_parking (300 s) | drift / max \|v\| after 5 s | 0 m / 1e-14 m/s | ≤ 5 mm / ≤ 1 mm/s | WORKING_VALUE (no-creep threshold) | ✅ |
| 1 | standstill_12pct_uphill_parking | drift / max \|v\| | 2.2 µm / 7.3 µm/s | ≤ 5 mm / ≤ 1 mm/s | WORKING_VALUE | ✅ |
| 1 | standstill_12pct_downhill_parking | drift / max \|v\| | 4.6 µm / 10 µm/s | ≤ 5 mm / ≤ 1 mm/s | WORKING_VALUE | ✅ |
| 2 | launch_0_80_flat | rollback / stall / min rpm | 0 m / no / 600 rpm | ≤ 2 cm / no / ≥ 550 | WORKING_VALUE | ✅ |
| 2 | launch_6pct_uphill (full throttle, HSA) | rollback / stall | 1.5 mm / no | ≤ 5 cm / no | WORKING_VALUE | ✅ |
| 2 | launch_6pct_uphill_light_throttle (40 %) | rollback / 0–15 km/h | 1.5 mm / 2.7 s | ≤ 5 cm / 2–25 s | WORKING_VALUE | ✅ |
| 3 | launch_0_80_flat | 0–60 / 0–80 km/h | 10.0 s / 14.2 s | 7–20 s / 12–32 s | WORKING_VALUE (power-to-weight plausibility; no sourced solo-tractor data) | ✅ |
| 3 | repeatability, 3 runs (headings 0°/37°/113°) | max deviation 0–60 / 0–80 | 0.00 % / 0.00 % | ≤ 3 % | docs/04 + task brief | ✅ |
| 4 | top_speed_flat (100 s full throttle) | max / settled speed | 89.35 / 89.35 km/h | ≤ 90.5 / 87–90 | SOURCED (S3: 90 km/h limiter) | ✅ |
| 5 | brake_80_0_dry (ABS) | stop distance / MFDD | 33.3 m / 7.69 m/s² | 32–55 m / 5.0–8.0 | WORKING_VALUE; MFDD per R13 definition. The lower bound 5.0 is the R13 N3 figure, UNVERIFIED. | ✅ |
| 5 | brake_80_0_dry | lateral deviation / yaw rate | 3e-7 m / 0 °/s | ≤ 0.5 m / ≤ 2 °/s | WORKING_VALUE | ✅ |
| 5 | brake_80_0_wet (ABS, μ≈0.5) | stop distance / MFDD | 53.0 m / 4.69 m/s² | 45–85 m / 3.0–5.5 | WORKING_VALUE | ✅ |
| 7 | circle_r25_10kmh | radius error / a_y / steer÷Ackermann | 0.02 m / 0.308 / 1.009 | ≤ 0.5 / 0.278–0.340 / 0.9–1.6 | DERIVED (v²/R, atan(L/R)) | ✅ |
| 7 | circle_r25_20kmh | same | 0.09 m / 1.229 / 1.036 | ≤ 0.5 / 1.111–1.358 / 0.9–1.6 | DERIVED | ✅ |
| 7 | circle_r50_20kmh | same | 0.04 m / 0.617 / 1.037 | ≤ 0.5 / 0.556–0.679 / 0.9–1.6 | DERIVED | ✅ |
| 7 | circle_r50_35kmh | same; body roll | 0.24 m / 1.881 / 1.113; 0.99° | ≤ 0.5 / 1.701–2.079 / 0.9–1.6; ≤ 3° | DERIVED | ✅ |
| 7 | understeer gradient (test) | steer÷Ackermann at 10 → 20 km/h, R25 | 1.009 → 1.036 | increasing | qualitative | ✅ |
| 11 | curb_8cm_both (8 km/h) | max Δv per step / teleport / max Fz÷static | 0.062 m/s / 1e-14 m / 1.87 | ≤ 0.35 / ≤ 1e-6 / ≤ 4 | WORKING_VALUE | ✅ |
| 11 | curb_15cm_both | same | 0.096 / 2e-14 / 2.88 | ≤ 0.35 / ≤ 1e-6 / ≤ 4 | WORKING_VALUE | ✅ |
| 11 | curb_15cm_left (one side) | same; max roll | 0.049 / 1e-14 / 2.76; 5.8° | …; ≤ 8° | DERIVED (geometric 4.5° plus overshoot) | ✅ |
| 12 | dt 50/100/120 Hz | 0–80 / stop dist. dry / a_y R25 | 1.07 % / 0.64 % / 0.02 % max deviation | ≤ 5 % | WORKING_VALUE | ✅ |
| 12 | substeps 2/4/8 | stop distance dry | 0.34 % | ≤ 5 % | WORKING_VALUE | ✅ |
| 15 | steer_sign_forward_right / left | yaw rate | +10.9 / −10.9 °/s | > +1 / < −1 | DERIVED (Unity frame: +steer = right = +yaw about +Y) | ✅ |
| 15 | steer_sign_reverse_right | yaw rate | −3.85 °/s | < −1 | DERIVED | ✅ |
| — | zero allocation (test) | GC bytes over 2000 steps (solver + integrator) | 0 | 0 | CLAUDE.md | ✅ |
| — | cost | mean solver + integrator time per 10 ms step (desktop, Release) | ~2–17 µs | — | measured on desktop, **not** on a phone | info |

Repeatability is exactly 0 % because the runner is deterministic. Earlier iterations showed about 0.6 % spread from heading-dependent rounding, after which shift timing lands on a different step. The test still guards the 3 % budget. In Unity, PhysX is not deterministic across devices (docs/04 §1), so the same 3 % check must be repeated on the phone.

## 4. Plot review (PNGs looked at, not just numbers)

Reviewed: launch_0_80_flat, launch_6pct_uphill, brake_80_0_dry, standstill_12pct_downhill_parking, curb_15cm_left (twice: before and after the fixes below).

Findings that led to changes during this run:
1. **Curb 15 cm.** The first version had a single-step Fz spike of 117 kN (5× static) on the front-left wheel. The cause was a rigid tire on the bump stop. Fix: tire radial compliance in series with the spring, solved by Newton iteration. The spike is now 2.8×, with a smooth roll to −5° and a clean recovery.
2. **Teleport metric.** It compared the vehicle-origin displacement with the CoM velocity, which is wrong under rotation. It now compares CoM position with CoM velocity, and the residual is 1e-14 m.
3. **Launch.** Without traction control the rear wheels spun to slip 0.9 and the engine hit the 2100 rpm governor (empty tractor, rear axle about 2.7 t). Added ASR (engine intervention only) and a faster clutch close. Slip now peaks at about 0.1–0.2. The pedal input to the AMT is now the effective value after limiter and ASR, so the top gear 12 is reached and cruise is 1225 rpm at 89 km/h. Before this, the AMT stayed in 11th at 1600 rpm because the driver pedal was at 100 %.
4. **Braking.** The engine was dragged to 0 rpm (stall/restart) by wheel lock and by the clutch staying closed through downshifts. Now the clutch opens when ABS is active and at idle without throttle, so no stall. Low-speed tire damping τ went from 0.01 to 0.03 s, which reduced rocking after the stop. A small residual tire wind-up stays after the stop with all wheels braked (±2 kN front/rear, summing to 0). This is physically plausible.
5. **Cab pitch.** It hit its ±4° clamp under 0.3 g. The gain was reparametrised as h/r_g². Now about 1° at 3 m/s² and 2.7° at 0.8 g braking.
6. **Neutral steer.** With load-proportional cornering stiffness the result was exactly Ackermann at all speeds. Degressive stiffness (K ∝ Fz^0.7) now gives understeer that grows with speed.

Remaining visual notes (not failures):
- During a full-throttle launch in gears 4–5 the engine still briefly reaches about 2000 rpm, because the shift cooldown and skip logic lag a very light vehicle. AMT tuning is planned for Stage 2.
- The rear (lightly loaded) wheels briefly lock at brake onset before ABS reacts (slip −1 for about 0.1 s). There is no load-proportional brake distribution (EBS) yet.

## 5. Known gaps / not modelled (Stage 1)

- Unsprung masses are lumped into the chassis. There are no wheel-hop modes. The tire vertical spring has no mass and no damping.
- Brakes: first-order pressure lag only. There is no air system, tanks, compressor, EBS load distribution, retarder or engine brake. All of that is Stage 2 (docs/04 §2.8).
- AMT: no manual mode, no creep function, no grade-based shift strategy beyond the launch gear. The clutch has no thermal model.
- Engine: no BSFC/fuel, no exhaust brake.
- Tire: single effective radius; surface table only in the runner; no camber or turn-slip; aligning torque is an estimate for steering feedback only.
- Contact: rays are in the wheel plane only. Ruts and lateral curb edges under a wide dual pair are not resolved. The ruts and speed-bump scenarios from §6.11 are not written yet.
- Not covered yet: items 6, 8, 9, 10, 13, 14 (they need a trailer, a retarder, floating origin or a 30-min soak), and the 40 t variants of 2, 3 and 5.
- No Unity PlayMode or device run yet. The Samsung A CPU cost and the substep count benchmark are pending (ADR 0004).
