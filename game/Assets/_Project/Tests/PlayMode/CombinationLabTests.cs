using System;
using Game.Controls;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools.Constraints;
using Is = UnityEngine.TestTools.Constraints.Is;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    /// <summary>
    /// Stage 2 PlayMode validation of the two-body adapter (tractor + semi-trailer as two PhysX Rigidbodies, the
    /// fifth wheel solved by the core's <see cref="CombinationModel"/>, no PhysX joint). Script simulation mode at
    /// exactly 0.01 s, geometry built per test 500 m below the scene. Reference values: the .NET runner
    /// (docs/PHYSICS_VALIDATION.md §3, run stage2-final).
    /// </summary>
    public class CombinationLabTests
    {
        const float Dt = 0.01f;
        static readonly Vector3 O = new Vector3(0f, -500f, 0f);
        SimulationMode m_PrevMode;
        GameObject m_World;
        VehicleBody m_Body;
        TrailerBody m_Trailer;

        [SetUp]
        public void SetUp()
        {
            m_PrevMode = Physics.simulationMode;
            Physics.simulationMode = SimulationMode.Script;
            m_World = new GameObject("TestWorld");
        }

        [TearDown]
        public void TearDown()
        {
            if (m_Body != null) Object.DestroyImmediate(m_Body.gameObject);
            if (m_Trailer != null) Object.DestroyImmediate(m_Trailer.gameObject);
            Object.DestroyImmediate(m_World);
            Physics.simulationMode = m_PrevMode;
        }

        // ------------------------------------------------------------------ helpers

        GameObject Box(string name, Vector3 center, Vector3 size, Quaternion rot, SurfaceKind kind = SurfaceKind.DryAsphalt)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(m_World.transform, false);
            go.transform.SetPositionAndRotation(O + center, rot);
            go.transform.localScale = size;
            go.AddComponent<GroundSurface>().kind = kind;
            return go;
        }

        void Flat(SurfaceKind kind = SurfaceKind.DryAsphalt, float size = 900f) =>
            Box("Flat", new Vector3(0, -0.5f, 0), new Vector3(size, 1, size), Quaternion.identity, kind);

        /// <summary>Slab rising toward +Z at the given grade; returns the slope rotation.</summary>
        Quaternion Slope(float grade, float length = 400f)
        {
            var slope = Quaternion.Euler(-Mathf.Atan(grade) * Mathf.Rad2Deg, 0, 0);
            Box("Slope", slope * new Vector3(0, -0.5f, 0), new Vector3(120, 1, length), slope);
            return slope;
        }

        /// <summary>Coupled combination at static equilibrium, tractor origin at pos (on the ground).</summary>
        void SpawnCoupled(Vector3 pos, Quaternion rot, CargoPreset cargo, bool parked)
        {
            Build();
            m_Body.ResetPose(O + pos, rot);
            m_Trailer.Initialize(m_Body.Data, cargo, m_Body.Model.MassProps.Mass);
            m_Body.ConnectTrailer(m_Trailer, true);
            CombinationPlacement.Tractor(m_Body.Model, O + pos, rot, out Vector3 vp, out Quaternion vq);
            m_Body.SetPose(vp, vq);
            CombinationPlacement.Coupled(m_Body.Model, vp, vq, m_Trailer.Model, 0f, out Vector3 tp, out Quaternion tq);
            m_Trailer.SetPose(tp, tq);
            Finish(parked);
        }

        /// <summary>Trailer parked on its legs (kingpin above kingpinGround, heading north) and the tractor aligned with
        /// its jaw <paramref name="gap"/> metres ahead of the kingpin (runner couple_uncouple: trailerGap 2.0).</summary>
        void SpawnParkedTrailer(Vector3 kingpinGround, CargoPreset cargo, float gap)
        {
            Build();
            float jaw = (float)m_Body.Model.Def.fifthWheel.position.z;
            m_Body.ResetPose(O + kingpinGround + new Vector3(0, 0, gap - jaw), Quaternion.identity);
            m_Trailer.Initialize(m_Body.Data, cargo, m_Body.Model.MassProps.Mass);
            m_Body.ConnectTrailer(m_Trailer, false);
            CombinationPlacement.Parked(m_Trailer.Model, O + kingpinGround, Quaternion.identity, out Vector3 tp, out Quaternion tq);
            m_Trailer.SetPose(tp, tq);
            Finish(false);
        }

        void Build()
        {
            Physics.SyncTransforms();
            var data = VehicleDataAsset.LoadDefault();
            var mats = GrayboxMaterials.CreateRuntime();
            m_Body = GrayboxTractorBuilder.Build(data, null, mats);
            m_Trailer = GrayboxTrailerBuilder.Build(data, null, mats);
        }

        void Finish(bool parked)
        {
            Physics.SyncTransforms();
            m_Body.Model.InitParking(parked);
            m_Body.Input = new DriverInput { Selector = GearSelector.Drive, ParkingBrake = parked };
        }

        void Step(int n, Action perStep = null)
        {
            var vis = m_Body.GetComponent<VehicleVisuals>();
            var tvis = m_Trailer.GetComponent<TrailerVisuals>();
            for (int i = 0; i < n; i++)
            {
                perStep?.Invoke();
                m_Body.Tick(Dt);
                Physics.Simulate(Dt);
                vis.Capture(Dt);
                tvis.Capture(Dt);
            }
        }

        void SetInput(float throttle, float brake, float steer, GearSelector sel, bool park = false)
        {
            var inp = m_Body.Input;
            inp.Throttle = throttle; inp.Brake = brake; inp.Steer = steer; inp.Selector = sel; inp.ParkingBrake = park;
            m_Body.Input = inp;
        }

        double ForwardKmh => m_Body.Model.SpeedForward * 3.6;
        FifthWheel Fw => m_Body.Combination.FifthWheel;
        double ArticulationDeg => Fw.Articulation * MathUtil.Rad2Deg;

        // ------------------------------------------------------------------ tests

        [Test]
        public void MassProperties_Trailer_IncludeCargo()
        {
            Flat();
            SpawnCoupled(Vector3.zero, Quaternion.identity, CargoPreset.Gross40t, true);
            var mp = m_Trailer.Model.MassProps;
            Assert.AreEqual(mp.Mass, m_Trailer.Body.mass, 1.0, "trailer Rigidbody mass = definition + cargo");
            Assert.AreEqual(40000.0, m_Body.Model.MassProps.Mass + mp.Mass, 1.0, "40 t preset = 40.0 t gross combination mass");
            Assert.IsFalse(m_Trailer.Body.automaticInertiaTensor);
            Assert.IsTrue(m_Body.Coupled);
        }

        /// <summary>Runner couple_uncouple@laden40: reverse at idle creep into the braked 40 t trailer on its legs, the jaw locks, legs up, drive off.</summary>
        [TestCase(CargoPreset.Gross40t, TestName = "Coupling_UnderLoad_40t_SmoothAndKingpinLoadStatic")]
        [TestCase(CargoPreset.Empty, TestName = "Coupling_Empty_SmoothAndKingpinLoadStatic")]
        public void Coupling(CargoPreset cargo)
        {
            Flat();
            SpawnParkedTrailer(new Vector3(0, 0, 0), cargo, 2.0f);
            var c = m_Body.Combination;
            double maxDv = 0, maxLong = 0, maxErrAfter = 0;
            Vector3 vA = m_Body.Body.linearVelocity, vB = m_Trailer.Body.linearVelocity;
            double t = 0, kpSum = 0; int kpN = 0;
            for (int i = 0; i < 2600; i++)
            {
                t = i * Dt;
                if (t < 1.0) SetInput(0, 1, 0, GearSelector.Reverse);
                else if (t < 6.0) SetInput(0.05f, 0, 0, GearSelector.Reverse);
                else if (t < 7.0) SetInput(0, 1, 0, GearSelector.Reverse);
                else if (t < 17.0) SetInput(0, 1, 0, GearSelector.Drive);
                else SetInput(0.25f, 0, 0, GearSelector.Drive);
                if (i == 50) c.CouplingArmed = true;
                if (i == 800) m_Trailer.Model.LandingGearDown = false;
                Step(1);
                Vector3 a = m_Body.Body.linearVelocity, b = m_Trailer.Body.linearVelocity;
                maxDv = Math.Max(maxDv, Math.Max((a - vA).magnitude, (b - vB).magnitude));
                vA = a; vB = b;
                if (t >= 2 && t <= 8) maxLong = Math.Max(maxLong, Math.Abs(Fw.KingpinLoadLocal.z));
                if (Fw.Coupled && Fw.SinceCoupled > 1.0) maxErrAfter = Math.Max(maxErrAfter, Fw.PositionError);
                if (t >= 20 && t <= 24) { kpSum += Fw.KingpinLoadLocal.y; kpN++; }
            }
            double kpRatio = kpSum / Math.Max(1, kpN) / c.StaticKingpinLoad;
            Debug.Log($"[TEST] coupling {cargo}: events {Fw.CouplingEvents}, kingpin load / static {kpRatio:F3}, coupling bump max |Fx| {maxLong / 1000:F1} kN, " +
                      $"max |dv| per step {maxDv:F3} m/s, max kingpin error after engagement {maxErrAfter * 1000:F3} mm, speed {ForwardKmh:F1} km/h, gear {m_Body.Model.Amt.Gear}");
            Assert.AreEqual(1, Fw.CouplingEvents, "jaw locks once");
            Assert.IsTrue(m_Body.Coupled);
            Assert.That(kpRatio, Is.InRange(0.9, 1.1), "kingpin load after raising the legs = static nose load (runner check)");
            Assert.Less(maxLong / 1000, 150.0, "coupling bump ≤ 150 kN (runner check, compliant jaw engagement)");
            Assert.Less(maxDv, 0.35, "no solver explosion: |Δv| per step < 0.35 m/s");
            Assert.Less(maxErrAfter, 0.005, "kingpin position error < 5 mm once engaged (runner ≤ 0.16 mm)");
            Assert.Greater(ForwardKmh, 3.0, "combination drives off after coupling");
        }

        [TestCase(0f, TestName = "Standstill_12pct_40t_Uphill_ParkingBrake_60s_NoDrift")]
        [TestCase(180f, TestName = "Standstill_12pct_40t_Downhill_ParkingBrake_60s_NoDrift")]
        public void Standstill_12pct_40t(float yaw)
        {
            var slope = Slope(0.12f);
            var rot = slope * Quaternion.Euler(0, yaw, 0);
            SpawnCoupled(Vector3.zero, rot, CargoPreset.Gross40t, true);
            SetInput(0, 0, 0, GearSelector.Neutral, park: true);
            Step(300); // 3 s settle
            Vector3 a0 = m_Body.Body.worldCenterOfMass, b0 = m_Trailer.Body.worldCenterOfMass;
            Step(6000);
            float maxV = 0f;
            for (int i = 0; i < 100; i++) { Step(1); maxV = Mathf.Max(maxV, m_Body.Body.linearVelocity.magnitude, m_Trailer.Body.linearVelocity.magnitude); }
            float dA = (m_Body.Body.worldCenterOfMass - a0).magnitude, dB = (m_Trailer.Body.worldCenterOfMass - b0).magnitude;
            Debug.Log($"[TEST] 12 % 40 t yaw {yaw}: drift tractor {dA * 1000:F2} mm, trailer {dB * 1000:F2} mm over 61 s, end |v| {maxV * 1000:F3} mm/s, " +
                      $"park {m_Body.Model.ParkingBrakeState:F2}, articulation {ArticulationDeg:F3}°, kingpin err {Fw.PositionError * 1000:F3} mm");
            Assert.Less(dA, 0.01f, "tractor drift < 1 cm over 60 s");
            Assert.Less(dB, 0.01f, "trailer drift < 1 cm over 60 s");
            Assert.Less(maxV, 0.005f, "no creep or oscillation at the end");
        }

        /// <summary>Runner launch_6pct_uphill_comb@laden40: 2 s on the service brake, then full throttle; hill-start aid holds.</summary>
        [Test]
        public void HillStart_6pct_40t_NoRollback()
        {
            var slope = Slope(0.06f, 500f);
            SpawnCoupled(slope * new Vector3(0, 0, -150f), slope, CargoPreset.Gross40t, false); // on the slope plane
            // Runner frame: position along the slope; rollback = most negative displacement after the brake release.
            Vector3 fwd = slope * Vector3.forward;
            SetInput(0, 1, 0, GearSelector.Drive);
            Step(200);
            Vector3 p0 = m_Body.Body.position;
            double rollback = 0, t15 = double.NaN;
            int shifts0 = m_Body.Model.Amt.ShiftCount;
            for (int i = 0; i < 3000; i++)
            {
                SetInput(1, 0, 0, GearSelector.Drive);
                Step(1);
                double s = Vector3.Dot(m_Body.Body.position - p0, fwd);
                rollback = Math.Min(rollback, s);
                if (double.IsNaN(t15) && ForwardKmh >= 15) t15 = (i + 1) * Dt;
            }
            int shifts = m_Body.Model.Amt.ShiftCount - shifts0;
            Debug.Log($"[TEST] hill start 6 % 40 t: rollback {-rollback * 1000:F1} mm, 0-15 km/h {t15:F2} s (runner 4.84 s, ADR 0134), speed after 30 s {ForwardKmh:F1} km/h, " +
                      $"gear {m_Body.Model.Amt.Gear}, shifts {shifts}, clutch {m_Body.Model.Amt.ClutchTempC:F0} °C");
            Assert.Less(-rollback, 0.05, "rollback < 5 cm (runner 2.3 mm)");
            Assert.IsFalse(double.IsNaN(t15), "reaches 15 km/h within 30 s");
            // Reference = runner launch_6pct_uphill_comb@laden40 after ADR 0134 (4.84 s; was 4.5 s). Tolerance kept at the old
            // absolute ±0.45 s (not widened).
            Assert.AreEqual(4.84, t15, 0.45, "0-15 km/h within ±0.45 s of the runner (4.84 s, ADR 0134)");
            Assert.LessOrEqual(shifts, 14, "no gear hunting (runner limit 14 shifts)");
        }

        /// <summary>Runner brake_80_0_dry_abs_comb: 80 km/h in 11th, coast 0.5 s, full service brake, ABS on.</summary>
        [TestCase(CargoPreset.Empty, 39.0, TestName = "Brake_80_0_Dry_Abs_Empty_WithinTenPercentOfRunner")]
        [TestCase(CargoPreset.Gross40t, 40.5, TestName = "Brake_80_0_Dry_Abs_40t_WithinTenPercentOfRunner")]
        public void Brake_80_0_Dry_Abs(CargoPreset cargo, double runnerMetres)
        {
            Flat();
            SpawnCoupled(new Vector3(0, 0, -300f), Quaternion.identity, cargo, false);
            m_Body.SetMoving(80f / 3.6f, 11);
            Physics.SyncTransforms();
            SetInput(0, 0, 0, GearSelector.Drive);
            Step(50);
            Vector3 p0 = m_Body.Body.position;
            double dist = double.NaN, maxArt = 0, maxLat = 0;
            bool absSeen = false;
            for (int i = 0; i < 2000; i++)
            {
                SetInput(0, 1, 0, GearSelector.Drive);
                Step(1);
                absSeen |= m_Body.Model.Air.AbsAnyActive || m_Trailer.Model.Brakes.AbsAnyActive;
                maxArt = Math.Max(maxArt, Math.Abs(ArticulationDeg));
                maxLat = Math.Max(maxLat, Math.Abs(m_Body.Body.position.x - O.x));
                if (Math.Abs(m_Body.Model.SpeedForward) < 0.05) { dist = (m_Body.Body.position - p0).magnitude; break; }
            }
            Debug.Log($"[TEST] 80-0 dry ABS {cargo}: {dist:F2} m vs runner {runnerMetres:F1} m ({(dist / runnerMetres - 1) * 100:F1} %), ABS active {absSeen}, " +
                      $"max articulation {maxArt:F2}°, lateral deviation {maxLat:F2} m");
            Assert.IsFalse(double.IsNaN(dist), "combination must stop");
            Assert.AreEqual(runnerMetres, dist, runnerMetres * 0.10, "stop distance within ±10 % of the runner");
            Assert.Less(maxArt, 3.0, "straight-line stop, no trailer swing");
        }

        /// <summary>
        /// ADR 0082 (owner recording 2026-11-10, 108-114 s: 90 -> 94 km/h at full throttle while changing lanes): the
        /// speed limiter holds the set speed in the two-body Unity adapter too, straight and through lane changes, on
        /// asphalt and with the wheels on grass (wheel spin must not carry the vehicle past the limiter).
        /// </summary>
        [TestCase(SurfaceKind.DryAsphalt, CargoPreset.Empty, TestName = "SpeedLimiter_FullThrottle_LaneChanges_Asphalt_Empty")]
        [TestCase(SurfaceKind.DryAsphalt, CargoPreset.Gross40t, TestName = "SpeedLimiter_FullThrottle_LaneChanges_Asphalt_40t")]
        [TestCase(SurfaceKind.Grass, CargoPreset.Empty, TestName = "SpeedLimiter_FullThrottle_LaneChanges_Grass_Empty")]
        public void SpeedLimiter_FullThrottle_LaneChanges(SurfaceKind surface, CargoPreset cargo)
        {
            Flat(surface, 2600f);
            SpawnCoupled(new Vector3(0, 0, -1200f), Quaternion.identity, cargo, false);
            m_Body.SetMoving(88f / 3.6f, 11);
            Physics.SyncTransforms();
            double maxStraight = 0, maxSwerve = 0, maxGround = 0, endKmh = 0;
            for (int i = 0; i < 3600; i++)
            {
                float t = i * Dt;
                // 0-14 s straight, then 4 s-period lane changes (about 2.5 m/s2 lateral at 90 km/h).
                float steer = t < 14f ? 0f : 0.02f * Mathf.Sin(2f * Mathf.PI * (t - 14f) / 4f);
                SetInput(1, 0, steer, GearSelector.Drive);
                Step(1);
                double v = ForwardKmh;
                if (t < 14f) maxStraight = Math.Max(maxStraight, v); else maxSwerve = Math.Max(maxSwerve, v);
                maxGround = Math.Max(maxGround, m_Body.Body.linearVelocity.magnitude * 3.6);
                endKmh = v;
            }
            double lim = m_Body.Model.Def.driveline.speedLimiterKmh;
            Debug.Log($"[TEST] limiter {surface} {cargo}: max straight {maxStraight:F2}, max in lane changes {maxSwerve:F2}, max ground speed {maxGround:F2}, end {endKmh:F2} km/h (set {lim:F0})");
            Assert.LessOrEqual(maxStraight, lim + 0.5, "limiter, straight");
            Assert.LessOrEqual(maxSwerve, lim + 0.5, "limiter, lane changes");
            Assert.LessOrEqual(maxGround, lim + 1.0, "ground speed of the tractor body");
        }

        /// <summary>Runner jackknife_wet_curve_noabs@empty: R120 at 60 km/h on wet asphalt, EBS fault (no ABS, no load
        /// sensing), half pedal at 6 s with the steering held: the light drive axle locks and the combination folds.</summary>
        [Test]
        public void Jackknife_Wet_NoAbs_IsPossible()
        {
            Flat(SurfaceKind.WetAsphalt);
            const float R = 120f;
            var center = new Vector3(-R, 0f, 0f);
            SpawnCoupled(Vector3.zero, Quaternion.identity, CargoPreset.Empty, false);
            var m = m_Body.Model; var tb = m_Trailer.Model.Brakes;
            m.Air.AbsEnabled = false; m.Air.LoadSensingEnabled = false;
            tb.AbsEnabled = false; tb.LoadSensingEnabled = false;
            m_Body.SetMoving(60f / 3.6f, 0);
            Physics.SyncTransforms();
            var ap = new AutopilotDriverInput { CircleCenter = O + center, Radius = R, Clockwise = false, TargetSpeedKmh = 60f, LookAhead = 18f, Enabled = true };
            var intent = new DriverIntent();
            float held = 0f;
            double maxArt = 0; bool finite = true;
            for (int i = 0; i < 1400; i++)
            {
                float t = i * Dt;
                ap.Sample(Dt, new VehicleFeedback { Position = m_Body.Body.position, Forward = m_Body.transform.forward, ForwardSpeed = (float)m.SpeedForward }, ref intent);
                if (t < 6f) { held = intent.Steer; SetInput(intent.Throttle, intent.Brake, intent.Steer, GearSelector.Drive); }
                else SetInput(0, 0.5f, held, GearSelector.Drive);
                Step(1);
                if (t >= 6f) maxArt = Math.Max(maxArt, Math.Abs(ArticulationDeg));
                finite &= !float.IsNaN(m_Body.Body.position.x) && !float.IsNaN(m_Trailer.Body.position.x);
            }
            Debug.Log($"[TEST] jackknife wet no ABS (empty): max articulation {maxArt:F1}° (runner 81.4°), steer held {held:F3}, end speed {ForwardKmh:F1} km/h");
            Assert.IsTrue(finite, "no NaN");
            Assert.GreaterOrEqual(maxArt, 30.0, "jackknife must be possible (runner check ≥ 30°)");
        }

        /// <summary>Reversing with the trailer: straight (stays straight), then steering (articulation grows smoothly),
        /// then counter-steering (it comes back); never past the soft 90° stop, no jumps, kingpin error stays small.</summary>
        [Test]
        public void Reversing_ArticulationStaysSane()
        {
            Flat();
            SpawnCoupled(Vector3.zero, Quaternion.identity, CargoPreset.Empty, false);
            double maxStraight = 0, maxArt = 0, maxStep = 0, maxErr = 0, prev = 0, peakAfterSteer = 0, endArt = 0;
            float maxSpeed = 0f;
            for (int i = 0; i < 3600; i++)
            {
                float t = i * Dt;
                float steer = t < 12f ? 0f : t < 20f ? 0.25f : -0.5f;
                double e = -5.0 - ForwardKmh; // target 5 km/h backwards
                SetInput(Mathf.Clamp01((float)-e * 0.08f), e > 1.5 ? Mathf.Clamp01((float)e * 0.1f) : 0f, steer, GearSelector.Reverse);
                Step(1);
                double a = ArticulationDeg;
                if (i > 0) maxStep = Math.Max(maxStep, Math.Abs(a - prev));
                prev = a;
                if (t < 12f) maxStraight = Math.Max(maxStraight, Math.Abs(a));
                if (t >= 12f && t < 20f) peakAfterSteer = Math.Max(peakAfterSteer, Math.Abs(a));
                maxArt = Math.Max(maxArt, Math.Abs(a));
                maxErr = Math.Max(maxErr, Fw.PositionError);
                maxSpeed = Mathf.Max(maxSpeed, m_Body.Body.linearVelocity.magnitude, m_Trailer.Body.linearVelocity.magnitude);
                endArt = a;
            }
            Debug.Log($"[TEST] reversing: straight max {maxStraight:F2}°, after steering {peakAfterSteer:F1}°, after counter-steer end {endArt:F1}°, " +
                      $"overall max {maxArt:F1}°, max change per step {maxStep:F3}°, max kingpin error {maxErr * 1000:F2} mm, max speed {maxSpeed:F2} m/s");
            Assert.Less(maxStraight, 2.0, "straight reversing stays straight");
            Assert.Greater(peakAfterSteer, 5.0, "steering while reversing folds the trailer");
            Assert.Less(Math.Abs(endArt), peakAfterSteer, "counter-steering reduces the articulation");
            Assert.Less(maxArt, 95.0, "never past the soft 90° cab-contact stop");
            Assert.Less(maxStep, 1.0, "no articulation jumps (< 1° per 10 ms step)");
            Assert.Less(maxErr, 0.005, "kingpin error < 5 mm");
            Assert.Less(maxSpeed, 3.0f, "no runaway speeds");
        }

        /// <summary>Runner downhill_7pct_typeIIA@laden40 (R13 Type-II(A)): 40 t down 7 % with brake cruise at 30 km/h —
        /// engine brake + retarder hold the speed, the service brake stays off.</summary>
        [Test]
        public void Descent_7pct_40t_BrakeCruise30_NoServiceBrake()
        {
            var slope = Slope(0.07f, 760f);
            var downhill = slope * Quaternion.Euler(0f, 180f, 0f);
            SpawnCoupled(slope * new Vector3(0, 0, 300f), downhill, CargoPreset.Gross40t, false);
            m_Body.SetMoving(30f / 3.6f, 0);
            Physics.SyncTransforms();
            double sum = 0, vMin = 1e9, vMax = 0, maxService = 0, maxRet = 0; int n = 0;
            for (int i = 0; i < 5000; i++)
            {
                var inp = m_Body.Input;
                inp.Throttle = 0; inp.Brake = 0; inp.Steer = 0; inp.Selector = GearSelector.Drive; inp.ParkingBrake = false;
                inp.BrakeCruiseKmh = 30; inp.RetarderLever = 0;
                m_Body.Input = inp;
                Step(1);
                if (i * Dt >= 15f)
                {
                    double v = ForwardKmh; sum += v; n++;
                    vMin = Math.Min(vMin, v); vMax = Math.Max(vMax, v);
                    maxService = Math.Max(maxService, m_Body.Model.BrakeDemand);
                    maxRet = Math.Max(maxRet, m_Body.Model.Retarder.Torque);
                }
            }
            double mean = sum / n;
            Debug.Log($"[TEST] descent 7 % 40 t brake cruise 30: mean {mean:F2} km/h (runner 30.0), range {vMin:F2}..{vMax:F2}, max service demand {maxService:F3}, " +
                      $"max retarder {maxRet:F0} N m, engine brake {m_Body.Model.Engine.EngineBrakeTorque:F0} N m, gear {m_Body.Model.Amt.Gear}, rpm {m_Body.Model.Engine.Rpm:F0}");
            Assert.That(mean, Is.InRange(25.0, 35.0), "mean speed 25-35 km/h (runner check)");
            Assert.Less(maxService, 0.02, "no service brake (endurance brakes only)");
        }

        [Test]
        public void Combination_FixedStep_ZeroGcAllocation()
        {
            Flat();
            SpawnCoupled(Vector3.zero, Quaternion.identity, CargoPreset.Gross40t, false);
            Step(300, () => SetInput(0.7f, 0, 0.15f, GearSelector.Drive));
            var body = m_Body;
            var vis = m_Body.GetComponent<VehicleVisuals>();
            var tvis = m_Trailer.GetComponent<TrailerVisuals>();
            SetInput(0.6f, 0, 0.25f, GearSelector.Drive);

            object sink = null;
            Assert.That(() => { sink = new byte[64]; }, Is.AllocatingGCMemory(), "control: the constraint must see a 64 B allocation");
            GC.KeepAlive(sink);

            TestDelegate steps = () =>
            {
                for (int i = 0; i < 2000; i++)
                {
                    body.Tick(Dt);
                    Physics.Simulate(Dt);
                    vis.Capture(Dt);
                    tvis.Capture(Dt);
                }
            };
            Assert.That(steps, Is.Not.AllocatingGCMemory(), "2000 combination steps (both bodies, fifth wheel, PhysX, visuals) must not allocate");
            Debug.Log($"[TEST] GC combination: 2000 steps allocated nothing; mean step {body.AverageStepMicros:F1} µs (solver + adapter, desktop editor), speed {body.SpeedKmh:F1} km/h, articulation {ArticulationDeg:F2}°");
        }
    }
}
