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

        /// <summary>
        /// Review P1 (s22 #113): the coupling outline of the trailer front follows the art model's rounded front (measured swing
        /// radius 2.0294 m, art-source/truck/trailer/export/trailer_manifest.json) instead of the flat graybox box (2.063 m, 7 mm
        /// to the cab): every coupling-box corner ahead of the kingpin stays within 2.04 m (96/53/EC) and >= 4 cm from the cab back.
        /// </summary>
        [Fact]
        public void TrailerFrontSwing_FollowsArtModel()
        {
            double swing = 0;
            foreach (var bx in Trailer.bodyBoxes)
            {
                if (!bx.coupling) continue;
                double zf = bx.center.z + bx.size.z / 2, hx = bx.size.x / 2;
                if (zf > 0) swing = Math.Max(swing, Math.Sqrt(zf * zf + hx * hx));
            }
            double cabBack = 1e9;
            foreach (var bx in Tractor.bodyBoxes) if (bx.coupling && bx.name == "Cab") cabBack = bx.center.z - bx.size.z / 2 - Tractor.fifthWheel.position.z;
            _out.WriteLine($"trailer coupling front swing {swing:F4} m, cab back {cabBack:F3} m ahead of the kingpin, clearance {cabBack - swing:F4} m");
            Assert.InRange(swing, 2.0280, 2.0295);
            Assert.True(swing <= 2.04, "96/53/EC Annex I 1.6: front swing radius <= 2.04 m");
            Assert.True(cabBack - swing >= 0.04, $"clearance {cabBack - swing:F4} m");
            // The ground set keeps the full graybox Body box (PhysX collider mirror); only the coupling set is rounded.
            Assert.Contains(Trailer.bodyBoxes, bx => bx.name == "Body" && bx.ground && !bx.coupling);
        }

        static bool TouchesUpTo110(CouplingContact c, double pitchDeg, double rollDeg, out string where)
        {
            where = "";
            for (int side = -1; side <= 1; side += 2)
                for (double yaw = 0; yaw <= 110; yaw += 1)
                {
                    Quat q = Quat.AngleAxis(side * yaw * MathUtil.Deg2Rad, Vec3.Up) * Quat.AngleAxis(pitchDeg * MathUtil.Deg2Rad, Vec3.Right)
                             * Quat.AngleAxis(rollDeg * MathUtil.Deg2Rad, Vec3.Forward);
                    var a = new ChassisState { Rotation = Quat.Identity };
                    var b = new ChassisState { Rotation = q, Position = Tractor.fifthWheel.position - q * new Vec3(0, Trailer.kingpinHeight, 0) };
                    c.Detect(a, b);
                    for (int k = 0; k < c.Count; k++)
                        if (c.Separation[k] < 0) { where = $"yaw {side * yaw} pitch {pitchDeg:F2} roll {rollDeg:F2}: penetration {c.Separation[k]:F4} m (tractor box {c.TractorBox[k]}, trailer box {c.TrailerBox[k]})"; return true; }
                }
            return false;
        }

        /// <summary>The combination clears the cab at every articulation up to 110 deg, level and a little pitched / rolled on the plate.</summary>
        [Theory]
        [InlineData(0.0, 0.0)]
        [InlineData(0.5, 0.0)]
        [InlineData(-0.5, 0.0)]
        [InlineData(0.0, 0.5)]
        [InlineData(0.0, -0.5)]
        public void TightTurn_NoContactBelowSideWallAngle(double pitchDeg, double rollDeg)
        {
            var c = new CouplingContact { Margin = 0 };
            c.SetGeometry(Tractor.bodyBoxes, Trailer.bodyBoxes);
            Assert.False(TouchesUpTo110(c, pitchDeg, rollDeg, out string where), where);
        }

        /// <summary>
        /// How much relative plate pitch / roll the 4.1 cm front clearance tolerates before the trailer front's top corner reaches
        /// the cab back (any articulation up to 110 deg). Pinned so a geometry change that eats the margin fails; the remaining
        /// sensitivity (post-stop rocking of the 40 t combination) is ADR 0228 "Otwarte".
        /// </summary>
        [Fact]
        public void FrontClearance_ToleratesPlatePitchAndRoll()
        {
            var c = new CouplingContact { Margin = 0 };
            c.SetGeometry(Tractor.bodyBoxes, Trailer.bodyBoxes);
            double Limit(bool roll)
            {
                double lo = 0, hi = 3;
                for (int it = 0; it < 14; it++)
                {
                    double mid = 0.5 * (lo + hi);
                    bool hit = TouchesUpTo110(c, roll ? 0 : mid, roll ? mid : 0, out _) || TouchesUpTo110(c, roll ? 0 : -mid, roll ? -mid : 0, out _);
                    if (hit) hi = mid; else lo = mid;
                }
                return lo;
            }
            double pitch = Limit(false), roll = Limit(true);
            _out.WriteLine($"no contact up to 110 deg articulation for |relative pitch| <= {pitch:F2} deg, |relative roll| <= {roll:F2} deg");
            Assert.True(pitch >= 0.7, $"pitch tolerance {pitch:F2} deg");
            Assert.True(roll >= 0.7, $"roll tolerance {roll:F2} deg");
        }

        /// <summary>Review P2 (s22 #113): more coupling boxes than the fixed point buffers hold fail loudly at setup instead of losing points.</summary>
        [Fact]
        public void SetGeometry_RejectsMoreBoxesThanCapacity()
        {
            var many = new BodyBoxDefinition[5];
            for (int i = 0; i < many.Length; i++) many[i] = new BodyBoxDefinition { name = "B" + i, center = new Vec3(0, 2, -i), size = new Vec3(2, 2, 1) };
            var c = new CouplingContact();
            Assert.Equal(4, CouplingContact.CountCoupling(Tractor.bodyBoxes));
            var ex = Assert.Throws<FormatException>(() => c.SetGeometry(Tractor.bodyBoxes, many));
            _out.WriteLine(ex.Message);
            c.SetGeometry(Tractor.bodyBoxes, Trailer.bodyBoxes); // 4 x 4 x 4 = 64 = capacity
            Assert.True(c.HasGeometry);
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
            Assert.Equal(4, c.TrailerBoxCount); // BodyCoupling, Nose, Beams, RearUnderrun (Body is ground-only)
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
            Assert.Equal(0, c.TrailerBox[deep]); // BodyCoupling
            Assert.InRange(Math.Abs(p.x), 1.20, 1.25);          // cab rear corner, x = 2.49 / 2
            Assert.InRange(p.z, 2.74, 2.80);                     // cab rear face z = 3.70 - 0.95
            // The trailer is pushed along its own lateral axis (away from the cab).
            Vec3 lateral = b.Rotation * Vec3.Right;
            Assert.True(Math.Abs(Math.Abs(Vec3.Dot(n, lateral)) - 1) < 1e-6, $"normal {n} not along the trailer lateral axis {lateral}");
            Assert.InRange(-c.Separation[deep], 0.02, 0.06);    // d/dphi (n.c) = 2.05 m/rad -> 0.9 deg ~ 0.032 m
        }

        /// <summary>
        /// Coupled combination in free space (no gravity, no ground), trailer yawing into the cab at 1 rad/s relative:
        /// the contact stops it near the geometric angle and does not rebound: KE + coupling spring energy never grows in the impact
        /// window, the yaw rate away from the cab after the release stays         /// the contact stops it near the geometric angle, does not rebound and never adds kinetic energy. Control: an elasticlt;= 15 % of the approach rate. Control: an elastic
        /// contact (unlimited recovery speed, no damping) gives its spring energy back (> 100 J in a step).
        /// </summary>
        [Fact]
        public void YawImpact_InFreeSpace_StopsAtCab_NoRebound_NoEnergyGain()
        {
            var plastic = YawImpact(null, out double gain, out double maxArt, out double rateAfter, out double maxPen);
            _out.WriteLine($"no-rebound contact: max energy gain/step {gain:F3} J, max articulation {maxArt:F2} deg, rate after {rateAfter:F3} rad/s, penetration {maxPen:F4} m");
            var elastic = YawImpact(1e6, out double gainE, out double maxArtE, out double rateAfterE, out double maxPenE);
            _out.WriteLine($"elastic control: max energy gain/step {gainE:F1} J, max articulation {maxArtE:F2} deg, rate after {rateAfterE:F3} rad/s");
            double limit = CouplingContact.FirstContactArticulationDeg(Tractor, Trailer);
            Assert.True(plastic, "trailer must reach the cab");
            Assert.InRange(maxArt, limit, limit + 2.5);
            Assert.True(maxPen < 0.07, $"penetration {maxPen:F4} m");
            Assert.True(gain <= 1.0, $"impact window gained {gain:F3} J in a step");
            Assert.True(rateAfter <= 0.15, $"rebound {rateAfter:F3} rad/s (approach 1 rad/s; the rest is the free-space tumble)");
            Assert.True(elastic);
            Assert.True(gainE > 100, $"control: the elastic contact should give its spring energy back (gain {gainE:F1} J)");
        }

        /// <summary>Returns true when the trailer touched the cab; rateAfter = largest relative yaw rate away from the cab after the first contact (rad/s, + = rebound).</summary>
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
            // Energy of the closed system: KE of both bodies + elastic energy in the coupling (roll spring, pitch / roll stops,
            // contact springs), all evaluated at the start of each solve.
            // In free space the impact (at cab height, not through the CoMs) also sets the pair tumbling, which later changes the
            // measured articulation without any energy input; the checks therefore look at the impact window only.
            const int n = 150;
            double dt = sc.dt;
            var e = new double[n]; var art = new double[n]; var cp = new int[n];
            maxArtDeg = 0; maxPen = 0;
            for (int i = 0; i < n; i++)
            {
                double ke = s.Body.KineticEnergy + s.TrailerBody.KineticEnergy;
                s.Combo.Step(dt, s.Body.State, s.TrailerBody.State, default(DriverInput), s.Ground);
                e[i] = ke + fw.RollSpringEnergy + fw.StopSpringEnergy;
                art[i] = Math.Abs(fw.Articulation);
                cp[i] = fw.ContactPoints;
                maxPen = Math.Max(maxPen, fw.ContactPenetration);
                maxArtDeg = Math.Max(maxArtDeg, art[i] * MathUtil.Rad2Deg);
                ScenarioRunner.StepBodies(s, dt);
            }
            int first = Array.FindIndex(cp, x => x > 0), last = Array.FindLastIndex(cp, x => x > 0);
            maxGain = 0; rateAfter = 0;
            if (first < 0) return false;
            for (int i = Math.Max(1, first - 5); i <= Math.Min(n - 1, last + 20); i++) maxGain = Math.Max(maxGain, e[i] - e[i - 1]);
            // Rate away from the cab (+ = rebound) in the 10 steps after the contact released.
            for (int i = last + 1; i <= Math.Min(n - 1, last + 10); i++) rateAfter = Math.Max(rateAfter, -(art[i] - art[i - 1]) / dt);
            return true;
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
        /// Heavy landing (ADR 0158 Open 4): the 0.5 m drop of the laden combination with the pre-ADR-0228 elastic bump stops
        /// returns most of the drop energy and takes off again; with the bump-stop unloading hysteresis it
        /// passes drop_05m_comb.
        /// </summary>
        [Fact]
        public void Drop05_ElasticBefore_DampedAfter()
        {
            var sc = Suites.Find("drop_05m_comb@laden40");
            var defs = DefinitionSet.LoadDirectory(RepoPaths.DefinitionsDir);
            foreach (var v in defs.Vehicles.Values) foreach (var a in v.axles) a.suspension.bumpStopHysteresis = 0;
            foreach (var t in defs.Trailers.Values) foreach (var a in t.axles) a.suspension.bumpStopHysteresis = 0;
            var before = ScenarioRunner.Run(sc, new RunOptions(), defs);
            var after = ScenarioRunner.Run(sc);
            _out.WriteLine($"before: rebound {before.Metric("drop_rebound_ratio"):F3}, airborne again {before.Metric("drop_relaunch_s"):F2} s; after: {after.Metric("drop_rebound_ratio"):F3}, {after.Metric("drop_relaunch_s"):F2} s");
            Assert.True(before.Metric("drop_rebound_ratio") > 0.6);
            Assert.True(before.Metric("drop_relaunch_s") > 0.1);
            Assert.True(after.Passed, string.Join("\n", after.Checks.Where(c => !c.Passed)));
        }
    }
}
