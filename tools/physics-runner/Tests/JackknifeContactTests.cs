using System;
using System.Linq;
using Game.Vehicle.Physics;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>
    /// ADR 0228 (B-077): tractor-trailer body contact (jackknife limit as a physical contact), one geometry source for the
    /// chassis-ground colliders and the coupling contact, heavy-landing damping.
    /// </summary>
    public class JackknifeContactTests
    {
        readonly ITestOutputHelper _out;
        public JackknifeContactTests(ITestOutputHelper output) { _out = output; }

        static VehicleDefinition Tractor => ScenarioRunner.Defs.Vehicles["tractor_4x2_generic"];
        static TrailerDefinition Trailer => ScenarioRunner.Defs.Trailers["curtainsider_tridem_13_6"];

        static void AssertBoxesEqual(ColliderBox[] expected, ColliderBox[] actual)
        {
            Assert.Equal(expected.Length, actual.Length);
            for (int i = 0; i < expected.Length; i++)
            {
                Assert.Equal(expected[i].Name, actual[i].Name);
                Assert.True((expected[i].Center - actual[i].Center).Magnitude < 1e-6, $"{expected[i].Name} centre {expected[i].Center} vs {actual[i].Center}");
                Assert.True((expected[i].Size - actual[i].Size).Magnitude < 1e-6, $"{expected[i].Name} size {expected[i].Size} vs {actual[i].Size}");
            }
        }

        /// <summary>One geometry source: the definition's ground boxes equal the ADR 0158 mirror of the graybox builders.</summary>
        [Fact]
        public void BodyBoxes_GroundSet_EqualsGrayboxColliderMirror()
        {
            AssertBoxesEqual(BodyGroundContact.DerivedTractorColliders(Tractor), BodyGroundContact.TractorColliders(Tractor));
            AssertBoxesEqual(BodyGroundContact.DerivedTrailerColliders(Trailer), BodyGroundContact.TrailerColliders(Trailer));
        }

        /// <summary>The level coupled combination first touches at the articulation the box geometry gives (trailer side wall on the cab's rear corner).</summary>
        [Fact]
        public void FirstContactAngle_FromGeometry()
        {
            double deg = CouplingContact.FirstContactArticulationDeg(Tractor, Trailer);
            _out.WriteLine($"first tractor-trailer contact at {deg:F2} deg");
            // Analytic: trailer side wall (half width 1.275 m) reaches the cab rear corner (x 1.245, 2.07 m ahead of the
            // kingpin): 1.245 cos(phi) + 2.07 sin(phi) = 1.275 -> phi = 180 - 31.02 - 31.86 = 117.1 deg.
            double a = Math.Atan2(1.245, 2.07) * MathUtil.Rad2Deg;
            double expected = 180 - a - Math.Asin(1.275 / Math.Sqrt(1.245 * 1.245 + 2.07 * 2.07)) * MathUtil.Rad2Deg;
            _out.WriteLine($"analytic {expected:F2} deg");
            Assert.InRange(deg, expected - 0.05, expected + 0.05);
        }

        static void LevelPose(double yawDeg, out ChassisState a, out ChassisState b)
        {
            a = new ChassisState { Rotation = Quat.Identity };
            Quat qb = Quat.AngleAxis(yawDeg * MathUtil.Deg2Rad, Vec3.Up);
            b = new ChassisState { Rotation = qb, Position = Tractor.fifthWheel.position - qb * new Vec3(0, Trailer.kingpinHeight, 0) };
        }

        /// <summary>Detection: clear just below the contact angle, a side contact on the cab rear corner just above it (both directions).</summary>
        [Theory]
        [InlineData(1)]
        [InlineData(-1)]
        public void Detect_SideWallOnCabCorner(int side)
        {
            var c = new CouplingContact { Margin = 0 };
            c.SetGeometry(Tractor.bodyBoxes, Trailer.bodyBoxes);
            Assert.True(c.HasGeometry);
            Assert.Equal(4, c.TractorBoxCount); // Frame, Cab, Mudguard_L/R (Bumper is ground-only)
            Assert.Equal(3, c.TrailerBoxCount);
            LevelPose(side * 116.0, out var a, out var b);
            c.Detect(a, b);
            for (int k = 0; k < c.Count; k++) Assert.True(c.Separation[k] >= 0, $"116 deg: unexpected penetration {c.Separation[k]:F4}");
            LevelPose(side * 118.0, out a, out b);
            c.Detect(a, b);
            int deep = -1;
            for (int k = 0; k < c.Count; k++) if (c.Separation[k] < 0 && (deep < 0 || c.Separation[k] < c.Separation[deep])) deep = k;
            Assert.True(deep >= 0, "118 deg: no contact");
            Vec3 p = c.Point[deep], n = c.Normal[deep];
            _out.WriteLine($"side {side}: point {p} normal {n} sep {c.Separation[deep]:F4}");
            Assert.Equal(1, c.TractorBox[deep]); // Cab
            Assert.Equal(0, c.TrailerBox[deep]); // Body
            Assert.InRange(Math.Abs(p.x), 1.20, 1.25);          // cab rear corner, x = 2.49 / 2
            Assert.InRange(p.z, 2.74, 2.80);                     // cab rear face z = 3.70 - 0.95
            // The trailer is pushed along its own lateral axis (away from the cab).
            Vec3 lateral = b.Rotation * Vec3.Right;
            Assert.True(Math.Abs(Math.Abs(Vec3.Dot(n, lateral)) - 1) < 1e-6, $"normal {n} not along the trailer lateral axis {lateral}");
            Assert.InRange(-c.Separation[deep], 0.02, 0.06);    // d/dphi (n.c) = 2.05 m/rad -> 0.9 deg ~ 0.032 m
        }

        /// <summary>
        /// Coupled combination in free space (no gravity, no ground), trailer yawing into the cab at 1 rad/s relative:
        /// the contact stops it near the geometric angle, does not rebound and never adds kinetic energy. Control: an elastic
        /// contact (unlimited recovery speed, no damping) gives the energy back as a rebound.
        /// </summary>
        [Fact]
        public void YawImpact_InFreeSpace_StopsAtCab_NoRebound_NoEnergyGain()
        {
            var plastic = YawImpact(null, out double gain, out double maxArt, out double rateAfter, out double maxPen);
            _out.WriteLine($"no-rebound contact: max KE gain/step {gain:F3} J, max articulation {maxArt:F2} deg, rate after {rateAfter:F3} rad/s, penetration {maxPen:F4} m");
            var elastic = YawImpact(1e6, out double gainE, out double maxArtE, out double rateAfterE, out double maxPenE);
            _out.WriteLine($"elastic control: max KE gain/step {gainE:F1} J, max articulation {maxArtE:F2} deg, rate after {rateAfterE:F3} rad/s");
            double limit = CouplingContact.FirstContactArticulationDeg(Tractor, Trailer);
            Assert.True(plastic, "trailer must reach the cab");
            Assert.InRange(maxArt, limit, limit + 2.5);
            Assert.True(maxPen < 0.07, $"penetration {maxPen:F4} m");
            Assert.True(gain <= 1.0, $"contact added {gain:F3} J in a step");
            Assert.True(Math.Abs(rateAfter) <= 0.05, $"rebound {rateAfter:F3} rad/s (approach 1 rad/s)");
            Assert.True(elastic);
            Assert.True(rateAfterE > 0.3, $"control: the elastic contact should rebound (rate after {rateAfterE:F3} rad/s)");
        }

        /// <summary>Returns true when the trailer touched the cab; rateAfter = relative yaw rate away from the cab at the end (rad/s, + = rebound).</summary>
        bool YawImpact(double? recoverySpeed, out double maxGain, out double maxArtDeg, out double rateAfter, out double maxPen)
        {
            var defs = DefinitionSet.LoadDirectory(RepoPaths.DefinitionsDir);
            if (recoverySpeed.HasValue)
            {
                defs.Vehicles["tractor_4x2_generic"].fifthWheel.contactRecoverySpeed = recoverySpeed.Value;
                defs.Vehicles["tractor_4x2_generic"].fifthWheel.contactDampingRatio = 0;
            }
            var sc = Suites.Find("jackknife_fold_120_reverse_comb@laden40");
            sc.overrides.articulationDeg = 110;
            var s = ScenarioRunner.Setup(sc, new RunOptions { DisableBodyContact = true }, defs);
            var lift = new Vec3(0, 100, 0);
            s.Body.Position += lift; s.TrailerBody.Position += lift;
            s.Body.Gravity = Vec3.Zero; s.TrailerBody.Gravity = Vec3.Zero; s.Combo.Gravity = Vec3.Zero;
            s.Body.Velocity = Vec3.Zero; s.Body.AngularVelocity = Vec3.Zero;
            var fw = s.Combo.FifthWheel;
            s.Combo.Step(sc.dt, s.Body.State, s.TrailerBody.State, default(DriverInput), s.Ground); // articulation sign
            double sgn = Math.Sign(fw.Articulation);
            Vec3 up = s.Body.Rotation * Vec3.Up;
            Vec3 w = up * (-sgn * 1.0); // d(art)/dt = (wA - wB) . upB: grows in magnitude
            Vec3 kp = s.TrailerBody.State.LocalToWorld(s.Trailer.KingpinLocal);
            s.TrailerBody.AngularVelocity = w;
            s.TrailerBody.Velocity = Vec3.Cross(w, s.TrailerBody.CenterOfMassWorld - kp);
            double dt = sc.dt, prev = s.Body.KineticEnergy + s.TrailerBody.KineticEnergy, prevArt = 0;
            maxGain = 0; maxArtDeg = 0; maxPen = 0; rateAfter = 0;
            bool touched = false;
            for (int i = 0; i < 300; i++)
            {
                s.Combo.Step(dt, s.Body.State, s.TrailerBody.State, default(DriverInput), s.Ground);
                ScenarioRunner.StepBodies(s, dt);
                double e = s.Body.KineticEnergy + s.TrailerBody.KineticEnergy;
                maxGain = Math.Max(maxGain, e - prev);
                prev = e;
                if (fw.ContactPoints > 0) touched = true;
                maxPen = Math.Max(maxPen, fw.ContactPenetration);
                double art = Math.Abs(fw.Articulation);
                maxArtDeg = Math.Max(maxArtDeg, art * MathUtil.Rad2Deg);
                if (i > 0) rateAfter = -(art - prevArt) / dt;
                prevArt = art;
            }
            return touched;
        }

        /// <summary>
        /// No allocation per step with the tractor-trailer contact active (fold pushed into the cab): the contact rows use
        /// fixed buffers (ADR 0157 zero-GC rule for the driving loop; this is the shared game core).
        /// </summary>
        [Fact]
        public void CombinationStep_WithBodyContact_DoesNotAllocate()
        {
            var sc = Suites.Find("jackknife_fold_120_reverse_comb@laden40");
            var s = ScenarioRunner.Setup(sc, new RunOptions());
            var drv = ScenarioRunner.CreateDriver(sc, s, out _);
            double dt = sc.dt, t = 0;
            var fw = s.Combo.FifthWheel;
            // Warm up into the contact (JIT, first-call allocations).
            for (int i = 0; i < 700; i++) { var inp = drv.Update(t, dt, s); s.Combo.Step(dt, s.Body.State, s.TrailerBody.State, inp, s.Ground); ScenarioRunner.StepBodies(s, dt); t += dt; }
            Assert.True(fw.ContactPoints > 0, "expected the trailer on the cab after 7 s");
            var input = new DriverInput { Throttle = 0.3, Steer = 1, Selector = GearSelector.Reverse };
            var ts = s.Body.State; var tr = s.TrailerBody.State;
            long before = GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 200; i++) s.Combo.Step(dt, ts, tr, input, s.Ground);
            long allocated = GC.GetAllocatedBytesForCurrentThread() - before;
            _out.WriteLine($"contact points {fw.ContactPoints}, allocated {allocated} B in 200 steps");
            Assert.Equal(0, allocated);
        }

        /// <summary>Definitions without body boxes keep the angular yaw stop (fallback); the runner's limit is then yawLimitDeg.</summary>
        [Fact]
        public void NoBodyBoxes_FallsBackToAngularStop()
        {
            var defs = DefinitionSet.LoadDirectory(RepoPaths.DefinitionsDir);
            defs.Vehicles["tractor_4x2_generic"].bodyBoxes = new BodyBoxDefinition[0];
            Assert.True(double.IsNaN(CouplingContact.FirstContactArticulationDeg(defs.Vehicles["tractor_4x2_generic"], defs.Trailers["curtainsider_tridem_13_6"])));
            var r = ScenarioRunner.Run(Suites.Find("jackknife_fold_120_reverse_comb@laden40"), new RunOptions(), defs);
            _out.WriteLine($"fallback: limit {r.ArticulationLimitDeg} deg, max articulation {r.Metric("max_articulation_deg"):F2} deg");
            Assert.Equal(90.0, r.ArticulationLimitDeg);
            Assert.InRange(r.Metric("max_articulation_deg"), 90.0, 93.5); // F1 / D59 tolerance 3.5 deg
            Assert.Equal(0.0, r.Metric("coupling_contact_s"));
        }

        /// <summary>
        /// Heavy landing (ADR 0158 Open 4): the 0.5 m drop of the laden combination with the pre-ADR-0228 elastic bump stops and
        /// undamped tyres returns most of the drop energy and takes off again; with the bump-stop hysteresis and tyre damping it
        /// passes drop_05m_comb.
        /// </summary>
        [Fact]
        public void Drop05_ElasticBefore_DampedAfter()
        {
            var sc = Suites.Find("drop_05m_comb@laden40");
            var defs = DefinitionSet.LoadDirectory(RepoPaths.DefinitionsDir);
            foreach (var v in defs.Vehicles.Values) foreach (var a in v.axles) a.suspension.bumpStopHysteresis = 0;
            foreach (var t in defs.Trailers.Values) foreach (var a in t.axles) a.suspension.bumpStopHysteresis = 0;
            foreach (var td in defs.Tires.Values) td.radialDamping = 0;
            var before = ScenarioRunner.Run(sc, new RunOptions(), defs);
            var after = ScenarioRunner.Run(sc);
            _out.WriteLine($"before: rebound {before.Metric("drop_rebound_ratio"):F3}, airborne again {before.Metric("drop_relaunch_s"):F2} s; after: {after.Metric("drop_rebound_ratio"):F3}, {after.Metric("drop_relaunch_s"):F2} s");
            Assert.True(before.Metric("drop_rebound_ratio") > 0.6);
            Assert.True(before.Metric("drop_relaunch_s") > 0.1);
            Assert.True(after.Passed, string.Join("\n", after.Checks.Where(c => !c.Passed)));
        }
    }
}
