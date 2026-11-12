# Vehicle reference data — tractor 4x2 + curtainsider semi-trailer (Stage 2)

Every number used by the physics model, with unit, source and status:

- **SOURCED**: taken from a cited public document.
- **DERIVED**: computed from SOURCED values or from geometry (the calculation is given).
- **WORKING_VALUE**: engineering estimate for this vehicle class, **not** backed by a cited source. These need to be replaced or confirmed later (measurement, literature, OEM data).

The data files are the authority. This table documents them:
`game/Assets/_Project/Vehicle/Physics/Definitions/Data/*.json` (`schemaVersion` 1).

The vehicle is a **generic fictional** modern EU 4x2 long-haul tractor with a high sleeper cab (docs/07, decision D6). It copies no specific OEM model. Where an OEM document is cited, it is used only as a **class reference**.

## Sources

| ID | Source |
|---|---|
| S1 | Volvo Trucks fact sheet D13K500, EU6SCR, version 10 (2025-06-16), https://stpi.it.volvo.com/STPIFiles/Volvo/FactSheet/D13K500_Eng_010_338550297.pdf. **The PDF was downloaded and its text read on 2026-11-09** (Stage 2). It states: max power 368 kW (500 hp) at 1530–1800 rpm; max torque 2500 Nm at 980–1270 rpm; max revs 2100 rpm; economy range 950–1400 rpm, optimum 1100–1300 rpm; exhaust brake (EPG) 200 kW at 2300 rpm; engine brake (VEB+) 375 kW at 2300 rpm; 12.8 dm³, 6 cylinders; dry weight about 1100 kg. Used as a **class reference** only. Status upgraded from "search summary" to **SOURCED (document opened)**. |
| S2 | ZF product data sheet "TraXon", https://www.zf.com/public/org/Product-data-sheet_TraXon-Torque_71520.pdf. **The PDF was downloaded and its text read on 2026-11-09.** Standard ratios for 12 TX 2610/3420 SO (and the Intarder variants 2611/3421): 12.92, 9.98, 7.69, 5.94, 4.57, 3.53, 2.83, 2.19, 1.68, 1.30, 1.00, 0.77; reverse R1–R4 12.03, 9.29, 2.64, 2.04. Max input torque 2600 / 3400 Nm. "ZF-Intarder with up to 4,000 Nm/600 kW braking torque/power". Class reference. Status upgraded to **SOURCED (document opened)**. |
| S3 | Council Directive 92/6/EEC, as amended by 2002/85/EC (speed limitation devices; N3 at 90 km/h). docs/04 §5 also lists the 90 km/h limiter as a fact to verify. Not re-opened in Stage 2. |
| S4 | ETRTO / ISO tyre size designation, used geometrically: 315/80 R22.5 means section width 315 mm, aspect ratio 80 %, rim diameter 22.5 in; 385/65 R22.5 likewise. |
| S5 | UN Regulation No. 13 (02 series), Annex 4, English/Japanese parallel text published by MLIT Japan, https://www.mlit.go.jp/jidosha/un/UN_R013_02.pdf, **downloaded and read 2026-11-09** (35 pages, Annexes 1–4). Verified in the text: MFDD definition; Type-IIA (para 1.8.2: laden, energy equivalent to 30 km/h on a 7 % down-gradient over 6 km, service/secondary/parking brakes not engaged; engine-brake-only tolerance ±5 km/h); secondary braking for category N: s ≤ 0.15 v + 2 v²/130 (para 2.2, dm 2.2 m/s²); parking brake holds the laden vehicle on 18 % (para 2.3.1) and the towing vehicle's parking brake holds the combination on 12 % (para 2.3.2); response time: braking force on the least favourably placed axle within 0.6 s (para 4.1.1; for compressed-air systems deemed met by Annex 6, which is **not** in this document). Still **UNVERIFIED**: the numeric N3 type-0 limits (the table cells did not extract; the believed values s ≤ 0.15 v + v²/130 and dm ≥ 5.0 m/s² stay UNVERIFIED). |
| S6 | Load index table (ISO 4209 / ETRTO): load index 160 = 4500 kg per single tire. Used only as a plausibility bound for 385/65 R22.5 trailer tires; not re-opened, treat as UNVERIFIED. (Load index 156 = 4000 kg is used in S7 the same way, same status.) |
| S7 | Bridgestone M-STEER 001 datasheet, https://www.bigtyres.co.uk/media/landingpages/documents/bridgestone_m-steer-001_datasheet.pdf, **downloaded and its text read on 2026-11-09**. Rows used: 315/80 R22.5 156/150 K: overall diameter 1092 mm, static loaded radius 507 mm; 385/65 R22.5 160 K: overall diameter 1086 mm, static loaded radius 502 mm. The sheet does not state the load and pressure at which the static loaded radius was measured. The usual data-book convention is the maximum single load at its pressure, but that convention is UNVERIFIED here. Used for a secant radial stiffness (class reference, one manufacturer). |
| S8 | Hendrickson "HT Series trailer air suspensions" brochure L632, https://www.hendrickson-intl.com/getattachment/36dba227-370f-48b6-8fe3-de02635fec76/L632.pdf, **downloaded and its text read on 2026-11-09**. Used statement: HT250T is "excellent for high travel suspension applications (up to 5.9 in.)", that is 150 mm total travel for a high-travel trailer air suspension. Class reference (US product) for the order of trailer axle travel only. |

Literature quoted in check rationales but **not opened** (UNVERIFIED): static rollover threshold of laden tractor-semitrailers about 0.3–0.45 g (UMTRI / Winkler); rearward amplification of tractor-semitrailers about 1.0–1.3; EU weights and dimensions (Directive 96/53/EC: 13.6 m semitrailer, 2.55 m width, kingpin-to-rear 12.0 m, front swing radius 2.04 m, drive axle 11.5 t, tridem 24 t, 40 t GCW).

## Mass and geometry (`tractor_4x2_generic.vehicle.json`)

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Curb mass (sum of mass elements) | 7500 | kg | WORKING_VALUE | Task brief (~7.5 t), typical for this class. There is no cited OEM document. |
| Mass breakdown (frame 900, engine+gearbox 1500, cab 1300, front axle+wheels 800, rear axle+duals 1300, fuel 600, misc 600, fifth wheel 200, cooling/bumper 300) | — | kg | WORKING_VALUE | Engineering split that adds up to 7500 kg |
| Centre of mass (vehicle frame) | x 0, y 1.09, z 2.37 | m | DERIVED | Mass-weighted mean of the elements (`MassProperties.Compute`) |
| Static axle loads | front 4806, rear 2694 | kg | DERIVED | Lever rule from the CoM and the axle positions |
| Inertia tensor | computed | kg m² | DERIVED | Box elements plus the parallel-axis theorem. It is **not** taken from a collider. |
| Wheelbase | 3.70 | m | WORKING_VALUE | Typical 4x2 long-haul tractor; no cited OEM document |
| Front track (wheel centres) | 2.04 | m | WORKING_VALUE | |
| Rear track (dual-pair centres) | 1.82 | m | WORKING_VALUE | |
| Aero CdA (solo tractor) | 7.4 | m² | WORKING_VALUE | Cd ≈ 0.8 × A ≈ 9.3 m² (2.55 m width × ~3.65 m effective height) |
| Air density | 1.2 | kg/m³ | DERIVED | ISA sea level at ~20 °C |

## Tire 315/80 R22.5 (`tire_315_80_r22_5.tire.json`)

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Nominal unloaded diameter | 1.0755 | m | DERIVED | S4: 22.5 × 25.4 + 2 × 0.80 × 315 mm |
| Effective radius (geometry + kinematics) | 0.51 | m | WORKING_VALUE | Between the static loaded and unloaded radius (0.538 m unloaded). It is a single value for both uses (simplification). |
| Width | 0.315 | m | SOURCED | S4 |
| Wheel inertia per tire (tire + rim + hub + rotor) | 20 | kg m² | WORKING_VALUE | ≈ 70 kg tire at r ≈ 0.45 m plus rim and rotor |
| Radial stiffness per tire | 1.0e6 | N/m | DERIVED (S7, S6 status) | Secant: free radius 546 mm − static loaded radius 507 mm = 39 mm at 4000 kg (LI 156) → 39.2 kN / 0.039 m = 1.01e6 N/m. The secant at rated load. The tangent at the lighter steer-axle load and the radial damping were not measured (no damping in the model; the tire is a spring in series with the suspension). Checked 2026-11-09 for the kerb-strike task; value unchanged. |
| Peak μ, dry asphalt, at nominal load | 0.80 | – | WORKING_VALUE | Truck tires are usually quoted at 0.7–0.9 on dry asphalt; no cited source |
| μ load sensitivity | −0.08 per unit (Fz/Fz0 − 1) | – | WORKING_VALUE | |
| Nominal load Fz0 | 30 | kN | WORKING_VALUE | About the steer-axle load per tire |
| Longitudinal slip stiffness / Fz at Fz0 | 12 | 1/– | WORKING_VALUE | |
| Cornering stiffness / Fz at Fz0 | 7 | 1/rad | WORKING_VALUE | |
| Load exponents (K ∝ Fz^p), long. / lat. | 0.85 / 0.7 | – | WORKING_VALUE | Degressive stiffness. This is the source of understeer (see PHYSICS_VALIDATION). |
| MF shape Cx, Ex / Cy, Ey | 1.65, 0 / 1.35, −0.5 | – | WORKING_VALUE | Typical Pacejka-like shapes |
| Relaxation length x / y | 0.30 / 0.50 | m | WORKING_VALUE | |
| Low-speed damping time constant | 0.030 | s | WORKING_VALUE | Chosen for stability and damping at standstill (tuned) |
| Low-speed damping fade-out speed | 3.0 | m/s | WORKING_VALUE | |
| Rolling resistance coefficient | 0.0055 | – | WORKING_VALUE | Plausible for C3 long-haul tires. The EU tyre-label class limits (Reg. (EU) 2020/740) were not verified. |
| Pneumatic trail at zero slip | 0.06 | m | WORKING_VALUE | Used for the steering-feedback estimate only |

Wet asphalt friction scale: **0.625**, so peak μ ≈ 0.5. Status: WORKING_VALUE (`AnalyticGround.SurfaceProps`, runner only. In Unity it will come from the surface table).

## Suspension

| Parameter | Front (parabolic leaf) | Rear (air, 4 bellows, levelled) | Unit | Status | Derivation |
|---|---|---|---|---|---|
| Wheel rate per side (at reference load) | 213 000 | 91 000 | N/m | DERIVED from WORKING | k = m_corner (2π f)² with f = 1.5 Hz (front) and 1.3 Hz (rear). Both f values are WORKING_VALUE. |
| Reference load (static position at mid travel) | solo static | solo static | – | DERIVED | Front steel spring: a heavier load sags (e.g. +1.5 t front axle at 40 t = +3.9 cm, still clear of the bump stop). |
| Air spring rate scaling | – | k × (bellows force / reference load) | – | WORKING_VALUE | Air spring stiffness ∝ bellows pressure, so the natural frequency stays ~1.3 Hz at any load |
| Height levelling: time constant / deadband | – | 8 s / 8 mm | – | WORKING_VALUE | One levelling valve per axle (symmetric, does not fight roll). The bellows force is also the EBS load signal. |
| Cubic progression | 2.0e6 | 1.5e6 | N/m³ | WORKING_VALUE | |
| Travel (bump to droop) | 0.18 | 0.20 | m | WORKING_VALUE | Trailer axles also 0.20 m. That is more than the 150 mm that S8 quotes for a *high-travel* trailer air suspension, so the droop is not too short (kerb-strike analysis in PHYSICS_VALIDATION §3a). |
| Bump-stop clearance / quadratic rate | 0.025 / 4e7 | 0.025 / 4e7 | m, N/m² | WORKING_VALUE | |
| Damper bump / rebound | 9000 / 18000 | 5000 / 10000 | N s/m | DERIVED from WORKING | ζ ≈ 0.3 of sqrt(k m) solo; rebound is twice bump |
| Damper knee / high-speed slope factor | 0.3 / 0.4 | 0.3 / 0.4 | m/s, – | WORKING_VALUE | |
| Anti-roll stiffness (axle) | 200 000 | 300 000 | N m/rad | WORKING_VALUE | |

### Cab suspension (`cab`, camera only)

3-DOF cab (heave, pitch, roll) on mounts at (0, 1.15, 3.925) m (pitch/roll pivot = cab body bottom plane = dims.json cab_mount_height_m / cab_mount_z_m, ADR 0014; was 1.5 m; no effect on the validated cab metrics because the core only uses the point for sampling the chassis motion), excited by the chassis specific force at the mount point and by the chassis angular acceleration. Pitch 1.5 Hz, roll 1.6 Hz, heave 1.8 Hz, ζ 0.5 (ADR 0134, was 0.35: per-shift cab nod overshoot; WORKING_VALUE), gain h/r_g² 0.55 rad/s² per m/s². Soft progressive stops from 80 % of ±4° / ±4° / ±50 mm (no hard clamp). Status: WORKING_VALUE. Measured: about 3° cab pitch in an ABS stop (3.1–3.4° after ADR 0134), 43–46 mm heave over a 7 cm speed bump at 15 km/h.

## Engine (`diesel_r6_13l_368kw.engine.json`)

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Configuration | 13 l inline-6 diesel | – | WORKING_VALUE | Class per docs/04 §2.6 and the task brief (S1 class: 12.8 dm³ R6) |
| Peak torque plateau | 2500 Nm @ 980–1270 rpm | N m | SOURCED (class reference) | S1 (opened) |
| Rated power | 368 kW @ 1530–1800 rpm | kW | SOURCED (class reference) | S1 |
| Torque at 1530 / 1800 rpm | 2297 / 1952 | N m | DERIVED | T = P / ω from 368 kW |
| Max engine speed | 2100 | rpm | SOURCED (class reference) | S1 |
| Torque at 500 / 600 / 800 / 950 / 1400 / 1900 / 2100 rpm | 900 / 1200 / 1900 / 2450 / 2420 / 1800 / 1500 | N m | WORKING_VALUE | Shape interpolation; the governor fades torque between 1900 and 2100 rpm |
| Motoring drag 0 / 600 / 1000 / 1500 / 2000 / 2400 rpm | 60 / 90 / 130 / 190 / 260 / 320 | N m | WORKING_VALUE | |
| Rotating inertia | 3.5 | kg m² | WORKING_VALUE | |
| Idle / stall | 600 / 350 | rpm | WORKING_VALUE | |
| Turbo lag (NA fraction / boost τ) | 0.45 / 0.35 s | – | WORKING_VALUE | |
| Economy band (for gearing check) | 950–1400 (optimum 1100–1300) | rpm | SOURCED (class reference) | S1 |
| Engine brake (VEB+ class) total retarding torque at 2300 rpm | 1557 | N m | DERIVED from SOURCED | S1: 375 kW at 2300 rpm → 375 000 / 240.9 rad/s. Test `EnduranceBrakes_MatchClassReference` checks 375 kW. |
| Engine brake torque at 800 / 1000 / 1200 / 1500 / 1800 / 2100 / 2400 rpm | 300 / 650 / 900 / 1150 / 1350 / 1500 / 1557 | N m | WORKING_VALUE | Shape only; total including motoring drag. The EPG-only figure (S1: 200 kW at 2300 rpm) is not modelled separately. |
| Engine brake actuation τ | 0.25 | s | WORKING_VALUE | |
| Overrun limit while engine braking | 2400 | rpm | WORKING_VALUE | The AMT up-shifts at 2250 rpm in engine-brake mode |

## Gearbox and driveline (`amt12_od_traxon_class.gearbox.json`)

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Forward ratios 1–12 | 12.92, 9.98, 7.69, 5.94, 4.57, 3.53, 2.83, 2.19, 1.68, 1.30, 1.00, 0.77 | – | SOURCED | S2 (opened): TraXon standard ratio set |
| Reverse ratio | 12.03 | – | SOURCED | S2 (R1; R2–R4 9.29 / 2.64 / 2.04 not used) |
| Gearbox efficiency | 0.97 | – | WORKING_VALUE | |
| Final drive ratio | 3.40 | – | DERIVED | Chosen so that 12th gear runs at ~1160 rpm at 85 km/h and ~1225 rpm at 90 km/h, inside the S1 optimum band 1100–1300 rpm. Calculation: 23.6 m/s / 0.51 m × 0.77 × 3.40 = 121 rad/s. |
| Final drive efficiency | 0.97 | – | WORKING_VALUE | |
| Clutch capacity | 4000 | N m | WORKING_VALUE | About 1.6 × peak engine torque |
| Clutch thermal: heat capacity / cooling τ / warning | 25 000 J/K / 300 s / 250 °C | – | WORKING_VALUE | Energy from slip power; measured 37 °C peak for a 40 t start on 6 % |
| Shift phases (torque fade-out / neutral / sync / clutch close / torque fade-in) | 0.20 / 0.15 / 0.20 (+ ≤ 0.30 until synchronised) / 0.15 / 0.35 | s | WORKING_VALUE | ADR 0134 (was 0.12 / 0.15 / 0.20 / 0.15 with the torque tied to the clutch, ~0.6 s). Fade-out and fade-in are smoothstep curves (no jerk step); full drive torque is back ~0.9 s after the shift starts, the clutch-open gap is unchanged |
| Up-shift synchronisation | engine brake (VEB+) applied while the clutch is open and the engine is > 20 rpm above the new gear's speed; clutch closes within 40 rpm (or after 0.30 s extra); engine brake released before the clutch closes | – | WORKING_VALUE | ADR 0134. Engine drag alone (~190 N m, 3.5 kg m²) slows the engine only ~520 rpm/s, so the clutch used to close 200–300 rpm above synchronous speed and dump the engine inertia into the driveline as a jolt. Using the engine/exhaust brake to speed up up-shift synchronisation is described for production AMTs (UNVERIFIED, no manufacturer document opened) |
| Light-load skip shift | two-gear up-shift at > 50 % pedal when the engine lands ≥ max(950 rpm, lugging guard = down-shift line − 150) and the truck still accelerates ≥ 1.5 m/s² × pedal in the target gear | rpm, m/s² | WORKING_VALUE | ADR 0134. 950 rpm: S1 fact-sheet curve still gives 2450 of 2500 N m (plateau from 980 rpm). Skip-shifting when lightly loaded is a documented behaviour of production truck AMTs (Volvo I-Shift press test drive, truckinginfo.com, "Test drive: Volvo's I-Shift, a smooth operator"; class reference, not this gearbox). Empty combination on flat at full pedal: 4-6-8-9 instead of 4-5-6-7-8-9 |
| Up-shift rpm (light → full throttle) | 1250 → 1750 | rpm | WORKING_VALUE | Triggered on the rpm predicted at the end of the torque ramp (rpm rate × 0.27 s) |
| Down-shift rpm (light → full) | 850 → 1100 (+200 on climbs > 2.5 % at > 50 % pedal) | rpm | WORKING_VALUE | Grade bonus keeps the engine in the torque plateau |
| Min rpm after up-shift (light → full) | max(950 → 1250, down-shift line + 100) | rpm | WORKING_VALUE | Includes the speed lost during the interruption ((resistance / mass) × 0.545 s); prevents hunting |
| Up-shift acceptance (≥ 30 % pedal) | acceleration in the new gear ≥ 0.10 × pedal | m/s² | WORKING_VALUE | Mass/grade/aero-aware (tractive force vs resistance). At the governor (over-rev guard) the next gear needs ≥ 0, otherwise the engine stays on the governor (ADR 0024) |
| Down-shift hold (≥ 30 % pedal, not engine-brake mode) | acceleration in the current gear ≥ 0.10 × pedal (same force balance as the up-shift acceptance) | m/s² | WORKING_VALUE | Mirror of the up-shift acceptance, no new parameter; lugging guard (line − 150 rpm) judged on rpm + max(0, rpm rate) × 0.545 s still forces the down-shift (ADR 0024) |
| Max skip / up→down hold-off / same-direction hold-off | 2 gears / 1.0 s / 0.3 s | – | WORKING_VALUE | Over-rev guard (> governor − 50 rpm) bypasses both |
| Launch rpm (light → full) + load bonus / max launch gear | 800 → 1100 + 250 × required-force fraction / 4 | rpm, – | WORKING_VALUE | The launch gear is chosen from mass and grade with a 2.5× force margin |
| Creep (pedal < 0.15) | 500 | N m | WORKING_VALUE | Clutch torque at idle for manoeuvring / coupling |
| Engine-brake mode down / up-shift | 1500 / 2250 | rpm | WORKING_VALUE | Keeps VEB+ in its effective band |
| Manual mode: min rpm after a requested shift / protection down-shift | 750 / 650 | rpm | WORKING_VALUE | Over-revving down-shifts are refused |
| Speed limiter | 90 | km/h | SOURCED | S3 |
| Limiter band (fuelling fade) | 2 | km/h | WORKING_VALUE | |
| Overrun protection offset above the limiter (engine brake + retarder, PI as the brake cruise; 0 = off) | 4 | km/h | WORKING_VALUE | ADR 0082; that series trucks do this on their own is UNVERIFIED. Settles at 94 km/h on a 2–5 % descent at 40 t |
| Differential | open | – | WORKING_VALUE | No diff lock yet |

## Air brake system (tractor `air`, `brakes`, per-axle fields)

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Compressor delivery | 450 NL/min at 2000 rpm, ∝ engine speed, −3 % per bar back-pressure | – | WORKING_VALUE | Charging from empty at 1200 rpm: spring brakes released after 163 s, cut-out after 378 s (test) |
| Governor cut-out / cut-in | 12.5 / 11.0 | bar | WORKING_VALUE | APU-class |
| Reservoirs supply / circuit 1 front / circuit 2 rear / circuit 3 spring brakes + trailer | 30 / 20 / 30 / 20 | L | WORKING_VALUE | |
| Protection valve opening | 7.0 | bar | WORKING_VALUE | A burst circuit drains the supply only down to this |
| Trailer supply (red) limit / control (yellow) max | 8.5 / 7.5 | bar | WORKING_VALUE | |
| Low-pressure warning | 5.5 | bar | WORKING_VALUE | R13 warning threshold not verified |
| Spring brake: release starts / complete | 3.0 / 5.5 | bar | WORKING_VALUE | Air loss in circuit 3 applies the spring brakes progressively |
| Max chamber pressure / pad threshold | 8.5 / 0.4 | bar | WORKING_VALUE | |
| Chamber volume front / rear / trailer | 0.8 / 1.0 / 1.0 | L | WORKING_VALUE | Air consumption per application |
| Build-up τ front / rear | 0.18 / 0.22 | s | WORKING_VALUE | Measured 75 % times 0.25 / 0.31 s (vehicle at rest) ≤ 0.6 s (S5 4.1.1) |
| Build-up trailer (two cascaded lags) | 0.15 + 0.20 | s | WORKING_VALUE | Measured 0.53–0.54 s ≤ 0.6 s (S5 4.1.1) |
| Release τ front / rear / trailer | 0.25 / 0.28 / 0.30 | s | WORKING_VALUE | |
| Service brake torque per wheel end front / rear / trailer | 20 000 / 24 000 / 18 000 | N m | WORKING_VALUE | Laden rear needs ≥ 22 kN m to reach μ = 0.8 (DERIVED: 55 kN × 0.8 × 0.51 m) |
| Spring brake torque per wheel end, tractor rear | 16 000 | N m | DERIVED + WORKING margin | S5 2.3.2: the tractor alone must hold 40 t on 12 %: 40 t × 9.81 × 0.119 × 0.51 m / 2 = 11.9 kN m; ×1.35 margin |
| Spring brake torque per wheel end, trailer axles 1–2 | 12 000 | N m | WORKING_VALUE | |
| Trailer control (yellow) line with the parking lever in park | 7.5 | bar | WORKING_VALUE | European hand control valve with trailer control brakes the trailer in park (UNVERIFIED, data sheet not opened); ADR 0004 addendum 2026-11-10 |
| AMT drive-away interlock: parking brake counts as applied above / launch allowed below | spring state 0.05 / 1.0 m/s | – | WORKING_VALUE | Design rule, production behaviour UNVERIFIED; ADR 0004 addendum 2026-11-10 |
| EBS load sensing (laden axle load / minimum factor) | rear 112.8 kN / 0.25; trailer axles 78.5 kN / 0.2; front none | – | WORKING_VALUE | Signal = levelled bellows force |
| ABS: release slip / re-apply slip | 0.16 / 0.06 (+0.6 m/s slip-speed floor) | – | WORKING_VALUE | |
| ABS: wheel decel (hold) / re-accel (end dump) | 12 / 4 | m/s² | WORKING_VALUE | |
| ABS: dump τ / slow re-apply factor / cut-out speed | 0.045 s / ×3 / 1.5 m/s | – | WORKING_VALUE | Loop runs every wheel substep (2.5 ms) |
| ABS layout | tractor 4S/4M; trailer 2 modulators (per side), all wheels sensed, select-low | – | WORKING_VALUE | |
| Trailer reservoir / emergency apply / release | 80 L / 3.5 / 4.5 bar | – | WORKING_VALUE | Red-line loss → trailer service brakes from the reservoir |
| Trailer relay gain | 1.13 | – | WORKING_VALUE | 7.5 bar control → 8.5 bar chamber |
| Background consumption | 8 | NL/min | WORKING_VALUE | Air suspension, actuators |
| Brake blending | first 15 % of pedal travel = endurance brakes only | – | WORKING_VALUE | |
| Hill start aid max hold / ASR slip threshold | 2.0 s / 0.15 | – | WORKING_VALUE | |

## Retarder (`retarder`, Intarder class)

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Maximum braking torque / power at the gearbox output | 4000 / 600 | N m / kW | SOURCED (class reference) | S2 (opened): "up to 4,000 Nm/600 kW" |
| Full torque above propshaft speed | 900 rpm (≈ 50 km/h); ∝ n² below | rpm | WORKING_VALUE | Hydrodynamic characteristic |
| Lever | 0 off, 1 engine brake, 2–5 engine brake + retarder 25/50/75/100 % | – | WORKING_VALUE | |
| Fill / drain τ | 0.4 / 0.3 | s | WORKING_VALUE | |
| Brake cruise (downhill speed control) | PI on speed error, 0.35 + 0.08 /s per km/h | – | WORKING_VALUE | Holds 60.0 km/h on 7 % with 40 t (test) |
| Cut-off | throttle, ABS on the drive axle, < 1 m/s, reverse (retarder) | – | WORKING_VALUE | Without ABS the retarder can lock the drive axle on wet (jackknife scenario) |

## Steering

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Max road-wheel angle (virtual centre) | 40 | deg | WORKING_VALUE | |
| Max steer rate (road wheel) | 30 | deg/s | WORKING_VALUE | |
| Ackermann factor | 1.0 | – | WORKING_VALUE | Full Ackermann, with the rear axle as the reference line |
| Steering ratio (handwheel / road wheel) | 20 | – | WORKING_VALUE | |

## Fifth wheel and coupling (`fifthWheel`)

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Jaw position (tractor frame) | (0, 1.15, 0.68) | m | WORKING_VALUE | 0.68 m ahead of the drive axle (was 0.55 until ADR 0019: 1.45 + 3.70 − 0.55 + 12.00 = 16.60 m exceeded the 16.50 m limit of 96/53/EC Annex I 1.1; now 16.47 m); 1.15 m height = dims.json fifth_wheel_height_m (brief class range 1.10-1.15 m; ISO 1726 not opened, UNVERIFIED). Was 1.20 until ADR 0014 |
| Pitch (fore/aft plate) limit | ±12 | deg | WORKING_VALUE | Soft stop, 10 Hz |
| Roll coupling stiffness / damping / hard limit | 1.0e7 N m/rad / 2.0e5 N m s/rad / ±4° | – | WORKING_VALUE | Implicit soft constraint (unconditionally stable) |
| Articulation stop (cab/frame contact) | ±90 | deg | WORKING_VALUE | Soft stop 3 Hz, critically damped (deformable contact) |
| Plate friction | μ 0.08 × kingpin load × 0.35 m | – | WORKING_VALUE | Greased plate |
| Capture window | 0.05 m horizontal, 0.12 m vertical, < 1.5 m/s | – | WORKING_VALUE | |
| Jaw engagement | 0.4 s compliant phase, 4 Hz critically damped | – | WORKING_VALUE | Spreads the coupling bump (measured ≤ 62 kN, dv ≤ 0.14 m/s per step) |
| Baumgarte factor / speed cap / iterations | 0.2 / 0.5 m/s / 8 | – | Solver setting | Max kingpin separation in all scenarios 0.16 mm |

## Semi-trailer (`curtainsider_tridem_13_6.trailer.json`)

Frame: origin on the ground below the kingpin, axles at negative z.

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Body length / width | 13.6 / 2.55 | m | SOURCED via docs/04 §5 | EU legal maximum (Directive 96/53/EC, UNVERIFIED) |
| Kingpin height | 1.15 | m | WORKING_VALUE | Matches the fifth wheel; one source art-source/truck/dims.json (ADR 0014) |
| Kingpin to front wall | 1.6 | m | DERIVED | Front swing radius √(1.6² + 1.275²) = 2.04 m (96/53/EC limit, UNVERIFIED; box bound, the model's rounded corner measures 2.029 m) |
| Cargo bay (front wall inner face z / length / width / height) | 1.572 / 13.512 / 2.50 / 2.58 | m | WORKING_VALUE | Synced to the model (dims.json trailer_cargo_*, ADR 0019): clear height under the top rail 2.58 m (≈ 2.66 m under the roof bows); floor 1.30 + 2.58 = 3.88 m leaves 12 cm below the 4.00 m roof top. Was 1.55 / 13.5 / 2.48 / 2.70 (floor + height = 4.00 m, no roof) |
| Body mass element | centre y 2.65, size y 2.70 | m | WORKING_VALUE | Spans floor top 1.30 → roof top 4.00 (was centre 2.60) |
| Empty mass (sum of elements) | 7000 | kg | WORKING_VALUE | Frame 2200, floor 1100, body/curtains/roof 1300, tridem + wheels + brakes 2250, landing gear 150 |
| Empty CoG / static kingpin load | z −5.89 m / 1645 kg | – | DERIVED | Lever rule over the tridem centre |
| Tridem axle positions | −6.39 / −7.70 / −9.01 (1.31 m spacing) | m | WORKING_VALUE | |
| Track (wide-base single wheel centres) | 2.04 | m | WORKING_VALUE | |
| Air suspension rate per side / reference | 79 000 N/m at empty static load (1.5 Hz) | – | DERIVED from WORKING | Interconnected bellows (one levelling group: equal axle loads) |
| Dampers bump / rebound, anti-roll per axle | 9000 / 18000 N s/m, 400 000 N m/rad | – | WORKING_VALUE | |
| Landing gear legs | z −2.2 m, ±0.95 m, 4e6 N/m, 6e4 N s/m, μ 0.6; lowered foot −0.07 m (lifts the nose off the plate), raised +0.45 m, crank 0.05 m/s | – | WORKING_VALUE | |
| Trailer drag area share | 1.5 | m² | WORKING_VALUE | Combination CdA 4.3 + 1.5 = 5.8 m² (Cd ≈ 0.58 × A ≈ 10 m²) |

### Tire 385/65 R22.5 (`tire_385_65_r22_5.tire.json`)

Same model and shape factors as 315/80 R22.5 (all WORKING_VALUE) except: effective radius 0.515 m (unloaded 0.536 m by S4 geometry), width 0.385 m (S4), wheel inertia 22 kg m², radial stiffness 1.1e6 N/m (DERIVED, S7: 543 − 502 = 41 mm at 4500 kg (LI 160, S6) → 1.08e6 N/m secant), nominal load 35 kN (S6 bound 44 kN per tire), rolling resistance 0.0050.

### Load cases (runner presets; cargo is not part of the trailer data)

| Preset | Cargo | GCW | Axle loads front / drive / tridem | Kingpin |
|---|---|---|---|---|
| solo | – | 7.5 t | 4.81 / 2.69 / – t (fifth-wheel mass moved with the jaw: ±0.01 t) | – |
| empty | 0 | 14.5 t | 5.10 / 4.00 / 5.40 t (DERIVED, jaw 0.68 m) | 1.60 t |
| laden40 | 25.5 t, uniform over the bay, CoG 2.3 m (floor 1.30 + 1.0) | **40.0 t** | 6.62 / 10.76 / 22.62 t (jaw 0.68 m; was 6.27 / 11.11 with 0.55 m) | 9.88 t |
| cargo24 | 24 t | 38.5 t | – | – |

The 40 t validation set uses GCW = 40.0 t exactly (the legal maximum, worst case). Limits (Directive 96/53/EC Annex I section 3, numbering and values quoted from the owner's reference list, text UNVERIFIED): drive axle 11.5 t, non-driving single axle 10 t, tridem 24 t. The laden40 loads 6.62 / 10.76 / 22.62 t are all within them (drive axle margin 0.74 t; 0.39 t before ADR 0019). Cargo CoG height and position are scenario parameters (rollover scenarios use 1.9 m and 2.6 m).

## Solver settings (not vehicle data)

| Parameter | Value | Status |
|---|---|---|
| Fixed step | 0.01 s (100 Hz) | ADR 0004 |
| Wheel/driveline substeps | 4 (2.5 ms); ABS and chamber pressures also run per substep | WORKING_VALUE. Benchmark on the Samsung A is still pending (ADR 0004). |
| Contact rays per wheel / arc | 15 rays over ±63° | WORKING_VALUE |
| Constraint iterations (clutch + brakes) | 4 | WORKING_VALUE |
| Fifth-wheel iterations | 8 | WORKING_VALUE |
| Low-speed tire deflection cap | 1.2 × deflection at peak force below 3 m/s | WORKING_VALUE (removes the stored-slide rebound after a locked stop) |
