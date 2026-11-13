using System;
using System.Linq;
using Game.Vehicle.Physics;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>
    /// ADR 0158 (F2): chassis-to-ground colliders of the runner and the free-flight energy / ballistics metrics.
    /// </summary>
    public class BodyContactTests
    {
        readonly ITestOutputHelper _out;
        public BodyContactTests(ITestOutputHelper output) { _out = output; }

        static Scenario Load(string id) =>
            Scenario.Load(System.IO.Path.Combine(RepoPaths.ScenariosDir, id + ".json"));

        /// <summary>
        /// Mutation test: the F2 repro without the chassis colliders (= the runner before ADR 0158) must fail the
        /// fall-through and speed checks; with them every check passes.
        /// </summary>
        [Fact]
        public void F2_Repro_FailsWithoutChassisContact_PassesWithIt()
        {
            var sc = Load("fuzz_shrink_speed_runaway_fulllock");
            var off = ScenarioRunner.Run(sc, new RunOptions { DisableBodyContact = true });
            foreach (var c in off.Checks) _out.WriteLine("without contact: " + c);
            // max_speed_kmh (forward-axis projection of the free-fall velocity) is not a reliable detector: it depends on
            // the chaotic tumble orientation (275 km/h with the explicit gyroscopic update, 85 km/h with the implicit one).
            string[] mustFail = { "min_com_height_m", "body_contact_s", "max_speed_after_ms" };
            foreach (var m in mustFail)
                Assert.Contains(off.Checks, c => c.Spec.metric == m && !c.Passed);
            // Energy is NOT injected even without the colliders: the run is a free fall, E = KE + PE never grows.
            Assert.True(off.Metric("free_flight_s") > 20, "expected a long free fall without colliders");
            Assert.True(off.Metric("max_free_flight_energy_gain_j") <= 1.0);

            var on = ScenarioRunner.Run(sc);
            foreach (var c in on.Checks) _out.WriteLine("with contact: " + c);
            Assert.True(on.Passed, string.Join("\n", on.Checks.Where(c => !c.Passed)));
        }

        [Fact]
        public void Metric_FreeFlight_DetectsEnergyInjectionAndNonBallisticAcceleration()
        {
            const double dt = 0.01;
            var g = new Vec3(0, -9.81, 0);
            // Ballistic: v_y = -g t, E constant -> gain 0, accel error 0.
            var ok = new RunResult { Dt = dt, SampleDt = dt, ArticulationLimitDeg = 90 };
            for (int i = 0; i < 50; i++)
                ok.Samples.Add(new Sample { T = i * dt, SystemVel = g * (i * dt), KineticEnergy = 1000 + i, PotentialEnergy = 5000 - i });
            Assert.Equal(0.49, ok.Metric("free_flight_s"), 6);
            Assert.Equal(0.0, ok.Metric("max_free_flight_energy_gain_j"), 6);
            Assert.True(ok.Metric("max_free_flight_accel_error_ms2") < 1e-9);

            // Injected: +1 m/s^2 forward and +10 J per step.
            var bad = new RunResult { Dt = dt, SampleDt = dt, ArticulationLimitDeg = 90 };
            for (int i = 0; i < 50; i++)
                bad.Samples.Add(new Sample { T = i * dt, SystemVel = g * (i * dt) + new Vec3(0, 0, 1.0 * i * dt), KineticEnergy = 1000 + 11 * i, PotentialEnergy = 5000 - i });
            Assert.Equal(10.0, bad.Metric("max_free_flight_energy_gain_j"), 6);
            Assert.Equal(1.0, bad.Metric("max_free_flight_accel_error_ms2"), 6);

            // Any wheel or collider contact excludes the pair from free flight.
            var touching = new RunResult { Dt = dt, SampleDt = dt, ArticulationLimitDeg = 90 };
            for (int i = 0; i < 10; i++)
                touching.Samples.Add(new Sample { T = i * dt, WheelsTouching = i % 2, BodyContacts = (i + 1) % 2, KineticEnergy = 100 * i });
            Assert.Equal(0.0, touching.Metric("free_flight_s"), 9);
            Assert.Equal(0.0, touching.Metric("max_free_flight_energy_gain_j"), 9);
        }

        /// <summary>A lone tractor body dropped on its side comes to rest on its colliders, with E = KE + PE + contact spring energy never growing (zeta 1, no restitution).</summary>
        [Fact]
        public void Body_DroppedOnSide_ComesToRest_WithoutEnergyGain()
        {
            var defs = ScenarioRunner.Defs;
            var tractor = defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            var body = new RigidBody6Dof(tractor.MassProps)
            {
                Rotation = Quat.AngleAxis(Math.PI / 2, Vec3.Forward),
                Position = new Vec3(0, 2.0, 0),
                Velocity = new Vec3(3, 0, 5),
            };
            var contact = new BodyGroundContact(BodyGroundContact.TractorColliders(tractor.Def));
            var ground = new AnalyticGround(0, SurfaceProps.FromName("dry_asphalt"));
            double E() => body.KineticEnergy + body.Mass * 9.81 * body.CenterOfMassWorld.y;
            double e0 = E(), ePrev = double.NaN, ePrevNoSpring = e0, maxGain = 0, maxGainNoSpring = 0;
            int maxGainStep = -1;
            for (int i = 0; i < 500; i++)
            {
                contact.Solve(body, Vec3.Zero, Vec3.Zero, 0.01, ground);
                double eNoSpring = E(), e = eNoSpring + contact.SpringEnergy;
                if (i > 0)
                {
                    if (e - ePrev > maxGain) { maxGain = e - ePrev; maxGainStep = i; }
                    maxGainNoSpring = Math.Max(maxGainNoSpring, eNoSpring - ePrevNoSpring);
                }
                if (Environment.GetEnvironmentVariable("BODYE") == "1")
                    _out.WriteLine($"{i} KE {body.KineticEnergy:F1} PE {body.Mass * 9.81 * body.CenterOfMassWorld.y:F1} spring {contact.SpringEnergy:F1} E {e:F1} n {contact.ContactCount} pen {contact.MaxPenetration * 1000:F2}");
                ePrev = e; ePrevNoSpring = eNoSpring;
                body.Integrate(0.01, contact.Force, contact.Torque);
            }
            _out.WriteLine($"E0 {e0:F0} J, end {ePrev:F0} J, max step gain incl. contact spring {maxGain:F3} J (step {maxGainStep}), without spring {maxGainNoSpring:F3} J, v {body.Velocity.Magnitude:E2} m/s, w {body.AngularVelocity.Magnitude:E2} rad/s, pen {contact.MaxPenetration * 1000:F2} mm");
            // ADR 0165: the contact is a compliant spring-damper, so the conserved quantity is KE + PE + sum 0.5 k pen^2
            // (BodyGroundContact.SpringEnergy, evaluated on the same pre-step state). KE + PE alone legitimately rises
            // while a loaded corner spring unloads (measured +190 J/step at steps 147-149 while E_total fell 340 J/step,
            // artifacts/phys-0165/droptest-diag.log). With the spring term the max step gain is 0.000 J. Allowance kept
            // from ADR 0158: 0.1 % of m g * 1 cm + 1 J (numerical round-off).
            Assert.True(maxGain < body.Mass * 9.81 * 0.01 * 0.001 + 1.0, $"energy gain {maxGain} J");
            Assert.True(body.Velocity.Magnitude < 0.01, $"still moving {body.Velocity.Magnitude} m/s");
            Assert.True(contact.MaxPenetration < 0.02);
            Assert.True(contact.ActiveContacts > 0);
        }

        /// <summary>
        /// Torque-free tumble of a lone trailer body (no gravity) for 30 s at dt 10 ms: the implicit gyroscopic update never
        /// raises the kinetic energy; the old explicit update (mutation) gains > 50 % (measured +136 %).
        /// </summary>
        [Fact]
        public void TorqueFreeTumble_ImplicitGyroscopic_NeverGainsEnergy_ExplicitDoes()
        {
            var tr = ScenarioRunner.Defs.CreateTrailer("curtainsider_tridem_13_6", null, new SolverSettings());
            double Run(bool implicitGyro, out double maxStepGain)
            {
                var b = new RigidBody6Dof(tr.MassProps) { Gravity = Vec3.Zero, AngularVelocity = new Vec3(1.5, 0.3, 2.0), ImplicitGyroscopic = implicitGyro };
                double e0 = b.KineticEnergy, prev = e0, mx = e0;
                maxStepGain = 0;
                for (int i = 0; i < 3000; i++)
                {
                    b.Integrate(0.01, Vec3.Zero, Vec3.Zero);
                    maxStepGain = Math.Max(maxStepGain, b.KineticEnergy - prev);
                    prev = b.KineticEnergy; mx = Math.Max(mx, prev);
                }
                return mx / e0 - 1;
            }
            double gainImplicit = Run(true, out double stepImplicit);
            double gainExplicit = Run(false, out _);
            _out.WriteLine($"max KE gain: implicit {gainImplicit * 100:F3} % (max step {stepImplicit:E2} J), explicit {gainExplicit * 100:F1} %");
            Assert.True(stepImplicit <= 1e-6, $"implicit gyroscopic step gained {stepImplicit} J");
            Assert.True(gainExplicit > 0.5, "mutation (explicit gyroscopic) should gain energy");
        }

        [Fact]
        public void Solve_DoesNotAllocate()
        {
            var defs = ScenarioRunner.Defs;
            var tractor = defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            var body = new RigidBody6Dof(tractor.MassProps) { Rotation = Quat.AngleAxis(Math.PI / 2, Vec3.Forward), Position = new Vec3(0, 1.24, 0) };
            var contact = new BodyGroundContact(BodyGroundContact.TractorColliders(tractor.Def));
            var ground = new AnalyticGround(0, SurfaceProps.FromName("dry_asphalt"));
            for (int i = 0; i < 10; i++) { contact.Solve(body, Vec3.Zero, Vec3.Zero, 0.01, ground); body.Integrate(0.01, contact.Force, contact.Torque); }
            long before = GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 1000; i++) { contact.Solve(body, Vec3.Zero, Vec3.Zero, 0.01, ground); body.Integrate(0.01, contact.Force, contact.Torque); }
            long allocated = GC.GetAllocatedBytesForCurrentThread() - before;
            Assert.True(contact.ActiveContacts > 0);
            Assert.Equal(0, allocated);
        }
    }
}
