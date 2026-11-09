using System;
using System.Collections;
using Game.Controls;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using UnityEngine.TestTools.Constraints;
using Is = UnityEngine.TestTools.Constraints.Is;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    /// <summary>
    /// Stage 1 PlayMode validation of the Unity adapter (PhysX rigid body + pure C# solver). Physics runs in
    /// Script simulation mode (Tick + Physics.Simulate at exactly 0.01 s) so tests are fast and independent of
    /// frame rate. Geometry is built per test (flat box, 12 % slab, 15 cm platform), not taken from the scene.
    /// Reference values: docs/PHYSICS_VALIDATION.md (runner, after the Stage 2 merge).
    /// </summary>
    public class VehicleLabTests
    {
        const float Dt = 0.01f;
        /// <summary>Test world lives 500 m below any scene content left by other tests (wheel rays point down).</summary>
        static readonly Vector3 O = new Vector3(0f, -500f, 0f);
        SimulationMode m_PrevMode;
        GameObject m_World;
        VehicleBody m_Body;

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

        void FlatGround() => Box("Flat", new Vector3(0, -0.5f, 0), new Vector3(600, 1, 600), Quaternion.identity);

        VehicleBody Spawn(Vector3 pos, Quaternion rot, bool parked)
        {
            Physics.SyncTransforms();
            m_Body = GrayboxTractorBuilder.Build(VehicleDataAsset.LoadDefault(), null, null);
            m_Body.ResetPose(O + pos, rot);
            m_Body.Model.InitParking(parked);
            m_Body.Input = new DriverInput { Selector = GearSelector.Drive, ParkingBrake = parked };
            return m_Body;
        }

        void Step(int n, Action perStep = null)
        {
            var vis = m_Body.GetComponent<VehicleVisuals>();
            for (int i = 0; i < n; i++)
            {
                perStep?.Invoke();
                m_Body.Tick(Dt);
                Physics.Simulate(Dt);
                vis.Capture(Dt);
            }
        }

        double ForwardKmh => m_Body.Model.SpeedForward * 3.6;

        /// <summary>Simple speed holder for tests (P on throttle/brake).</summary>
        void Cruise(float kmh, float steer)
        {
            var inp = m_Body.Input;
            double e = kmh - ForwardKmh;
            inp.Throttle = Mathf.Clamp01((float)e * 0.15f);
            inp.Brake = e < -3 ? Mathf.Clamp01((float)-e * 0.05f) : 0f;
            inp.Steer = steer;
            inp.ParkingBrake = false;
            inp.Selector = GearSelector.Drive;
            m_Body.Input = inp;
        }

        // ------------------------------------------------------------------ tests

        [Test]
        public void MassProperties_FromDefinition_NotFromColliders()
        {
            FlatGround();
            Spawn(Vector3.zero, Quaternion.identity, true);
            var rb = m_Body.Body;
            var mp = m_Body.Model.MassProps;
            Assert.AreEqual(mp.Mass, rb.mass, 1e-2, "mass");
            Assert.That((rb.centerOfMass - mp.CenterOfMass.ToUnity()).magnitude, Is.LessThan(1e-4f), "centre of mass");
            Assert.IsFalse(rb.automaticInertiaTensor);
            var I = rb.inertiaTensor;
            double trace = mp.Inertia.m00 + mp.Inertia.m11 + mp.Inertia.m22;
            Assert.AreEqual(trace, I.x + I.y + I.z, trace * 1e-4, "inertia trace preserved");
        }

        [Test]
        public void SteeringSign_AllInputModes_AgreeWithWheelAngleAndYaw()
        {
            // "Turn right" through every input mode.
            float keyboard = KeyboardDriverInput.StepSteer(0f, +1, 0.3f, 1.2f, 2.0f);
            var touch = new TouchSteeringWheel();
            touch.PointerDown(new Vector2(0, 150));            // finger at 12 o'clock
            touch.PointerDrag(new Vector2(150 * Mathf.Sin(0.5f), 150 * Mathf.Cos(0.5f)));  // moved clockwise
            var it = new DriverIntent();
            for (int i = 0; i < 20; i++) touch.Sample(0.016f, default, ref it);
            float touchSteer = it.Steer;
            float gyroRaw = GyroMath.TiltAngleDeg(new Vector3(Mathf.Sin(0.3f), -Mathf.Cos(0.3f), 0)); // right edge down
            float gyro = GyroMath.SteerFromTilt(GyroMath.Relative(gyroRaw, GyroMath.TiltAngleDeg(new Vector3(0, -1, 0))), 35f, 1f);
            var ap = new AutopilotDriverInput { CircleCenter = new Vector3(30, 0, 0), Radius = 30, Clockwise = true };
            var apIntent = new DriverIntent();
            ap.Sample(0.02f, new VehicleFeedback { Position = Vector3.zero, Forward = Vector3.forward, ForwardSpeed = 5f }, ref apIntent);

            var modes = new (string name, float steer)[] { ("keyboard", keyboard), ("touch", touchSteer), ("gyro", gyro), ("autopilot", apIntent.Steer) };
            foreach (var m in modes) Assert.Greater(m.steer, 0.05f, $"{m.name}: right input must give a positive steer command");

            FlatGround();
            foreach (var m in modes)
            {
                if (m_Body != null) Object.DestroyImmediate(m_Body.gameObject);
                Spawn(Vector3.zero, Quaternion.identity, false);
                Step(300, () => Cruise(15f, 0f));
                Step(200, () => Cruise(15f, Mathf.Clamp(m.steer, 0.2f, 1f)));
                var front = m_Body.Model.Wheels[0];
                Assert.Greater(front.SteerAngle, 0.0, $"{m.name}: road-wheel angle sign");
                Assert.Greater(m_Body.Model.YawRate, 0.02, $"{m.name}: yaw rate (right turn = +yaw about +Y)");
            }
        }

        [TestCase(0f, TestName = "Standstill_12pct_Uphill_ParkingBrake_60s_NoDrift")]
        [TestCase(180f, TestName = "Standstill_12pct_Downhill_ParkingBrake_60s_NoDrift")]
        public void Standstill_12pct_ParkingBrake(float yaw)
        {
            // Slab rising toward +Z at 12 %.
            var slope = Quaternion.Euler(-Mathf.Atan(0.12f) * Mathf.Rad2Deg, 0, 0);
            Box("Slope12", slope * new Vector3(0, -0.5f, 0), new Vector3(200, 1, 200), slope);
            var rot = slope * Quaternion.Euler(0, yaw, 0);
            Spawn(Vector3.zero, rot, true);
            Step(300); // 3 s settle
            Vector3 p0 = m_Body.Body.worldCenterOfMass;
            float maxSpeed = 0f;
            for (int k = 0; k < 6; k++)
            {
                Step(1000); // 10 s
                var w = m_Body.Model.Wheels;
                string ws = "";
                foreach (var q in w) ws += $" {q.Name}: om={q.Omega:E2} ux={q.Ux * 1000:F3}mm fx={q.Fx:F0} fz={q.Fz:F0} brakeT={q.BrakeTorque:F0} springP={q.SpringChamberPressure:F2};";
                Debug.Log($"[TEST] 12% yaw {yaw} t={(k + 1) * 10}s drift {(m_Body.Body.worldCenterOfMass - p0).magnitude * 1000f:F3} mm v={m_Body.Body.linearVelocity.magnitude * 1000f:F4} mm/s park={m_Body.Model.ParkingBrakeState:F2}{ws}");
            }
            for (int i = 0; i < 100; i++) { Step(1); maxSpeed = Mathf.Max(maxSpeed, m_Body.Body.linearVelocity.magnitude); }
            float drift = (m_Body.Body.worldCenterOfMass - p0).magnitude;
            Debug.Log($"[TEST] 12% yaw {yaw}: drift {drift * 1000f:F3} mm over 61 s, max |v| at end {maxSpeed * 1000f:F3} mm/s");
            Assert.Less(drift, 0.01f, "drift over 60 s must be < 1 cm");
            Assert.Less(maxSpeed, 0.005f, "no oscillation / creep at the end");
        }

        [Test]
        public void ZeroToSixty_Flat_WithinTenPercentOfRunner()
        {
            const double runner = 9.678; // docs/PHYSICS_VALIDATION.md §3, launch_0_80_flat (solo tractor)
            FlatGround();
            Spawn(Vector3.zero, Quaternion.identity, false);
            var inp = m_Body.Input;
            inp.Brake = 1; inp.Throttle = 0; inp.ParkingBrake = false; inp.Selector = GearSelector.Drive;
            m_Body.Input = inp;
            Step(100); // 1 s on the service brake, like the runner scenario
            inp.Brake = 0; inp.Throttle = 1;
            m_Body.Input = inp;
            double tStart = m_Body.SimTime, t60 = double.NaN;
            for (int i = 0; i < 4000 && double.IsNaN(t60); i++)
            {
                Step(1);
                if (Math.Abs(ForwardKmh) >= 60) t60 = m_Body.SimTime - tStart + Dt; // runner counts from the step before throttle
            }
            Debug.Log($"[TEST] 0-60 km/h Unity {t60:F3} s vs runner {runner:F3} s ({(t60 / runner - 1) * 100:F1} %)");
            Assert.IsFalse(double.IsNaN(t60), "never reached 60 km/h");
            Assert.AreEqual(runner, t60, runner * 0.10, "0-60 within ±10 % of the runner");
        }

        [Test]
        public void Curb15cm_BothWheels_NoTeleport()
        {
            FlatGround();
            // 15 cm platform with a vertical edge, 20 m ahead.
            Box("Curb15", new Vector3(0, 0.075f, 30f), new Vector3(10f, 0.15f, 20f), Quaternion.identity, SurfaceKind.Concrete);
            Spawn(Vector3.zero, Quaternion.identity, false);
            Step(600, () => Cruise(8f, 0f)); // accelerate to 8 km/h
            var rb = m_Body.Body;
            Vector3 prevV = rb.linearVelocity, prevC = rb.worldCenterOfMass;
            float maxDv = 0f, maxJump = 0f;
            float maxFzRatio = 0f;
            for (int i = 0; i < 800; i++)
            {
                Step(1, () => Cruise(8f, 0f));
                Vector3 v = rb.linearVelocity, c = rb.worldCenterOfMass;
                maxDv = Mathf.Max(maxDv, (v - prevV).magnitude);
                maxJump = Mathf.Max(maxJump, ((c - prevC) - v * Dt).magnitude); // position change not explained by velocity
                foreach (var w in m_Body.Model.Wheels) maxFzRatio = Mathf.Max(maxFzRatio, (float)(w.Fz / Math.Max(1, w.StaticLoad)));
                prevV = v; prevC = c;
            }
            Debug.Log($"[TEST] curb 15 cm: max |dv| per step {maxDv:F3} m/s, max unexplained displacement {maxJump * 1000f:F3} mm, max Fz/static {maxFzRatio:F2}, z {rb.position.z - O.z:F1} m, y {rb.position.y - O.y:F3} m");
            Assert.Greater(rb.position.z - O.z, 26f, "truck must have climbed onto the platform");
            Assert.Greater(rb.position.y - O.y, 0.10f, "rear axle origin on the platform");
            Assert.Less(maxDv, 0.35f, "max |Δv| per 10 ms step (runner limit 0.35 m/s)");
            Assert.Less(maxJump, 0.002f, "no teleport (PhysX depenetration / position snap)");
            Assert.Less(maxFzRatio, 4f, "Fz peak ≤ 4× static");
        }

        /// <summary>
        /// Zero GC per fixed step, measured with the Unity Test Framework constraint
        /// Is.Not.AllocatingGCMemory() (counts GC.Alloc profiler samples on the calling thread while the delegate
        /// runs). Mono in the editor reports 0 from GC.GetAllocatedBytesForCurrentThread, and the per-frame GC counter
        /// is dominated by the test runner's own allocations, so neither is usable. A control delegate that does
        /// allocate must be detected, proving the constraint is live in this run.
        /// </summary>
        [Test]
        public void FixedStep_ZeroGcAllocation()
        {
            FlatGround();
            Spawn(Vector3.zero, Quaternion.identity, false);
            Step(300, () => Cruise(30f, 0.2f)); // warm up: caches, JIT, surface lookup
            var vis = m_Body.GetComponent<VehicleVisuals>();
            var body = m_Body;
            var inp = body.Input;
            inp.Throttle = 0.6f; inp.Steer = 0.3f; inp.ParkingBrake = false;
            body.Input = inp;

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
                }
            };
            Assert.That(steps, Is.Not.AllocatingGCMemory(), "2000 fixed steps (solver + adapter + PhysX + visuals capture) must not allocate");
            Debug.Log($"[TEST] GC: 2000 fixed steps allocated nothing (control allocation detected); mean step {body.AverageStepMicros:F1} µs, speed {body.SpeedKmh:F1} km/h");
        }
    }
}
