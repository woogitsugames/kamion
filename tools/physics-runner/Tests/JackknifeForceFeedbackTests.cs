using System;
using Game.Controls;
using Game.Vehicle.Physics;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>
    /// ADR 0228 x ADR 0263 (wheel force feedback, #132): the tractor-trailer body contact must not reach the steering wheel as a
    /// kick. Path: the contact force / torque acts on the tractor and trailer bodies (CombinationModel.Step); it is not added to
    /// <see cref="VehicleModel.AligningTorqueTotal"/> directly, but it reverses the tractor's yaw in ~0.1 s and drags the steered
    /// axle sideways, so the tyres' aligning torque (pneumatic trail x Fy) swings through its peak. AligningTorqueTotal feeds
    /// <see cref="ForceFeedbackModel"/> (and the touch-wheel return). The fix smooths the feedback estimate while the bodies
    /// touch (<see cref="SteeringDefinition.contactFeedbackLagS"/>); the tyre forces on the vehicle are unchanged.
    /// These tests drive the contact scenarios step by step and feed the real FFB model as DrivingLabBootstrap does.
    /// </summary>
    public class JackknifeForceFeedbackTests
    {
        readonly ITestOutputHelper _out;
        public JackknifeForceFeedbackTests(ITestOutputHelper output) { _out = output; }

        /// <summary>Largest change of the FFB rim torque target per 10 ms step allowed in the contact window [N m]: 7.5 % of the
        /// default full scale (8 N m), well under the device slew step (20/s x 10 ms x 8 N m = 1.6 N m), so the slew limiter never
        /// shapes a contact event. Measured without the smoothing: 2.0-4.5 N m (full-scale reversal in ~0.1 s).</summary>
        const double MaxFfbStepNm = 0.6;

        struct Trace
        {
            public int ContactSteps;
            /// <summary>Largest per-step change of the FFB torque before the slew limit [N m at the rim], in / outside the contact window.</summary>
            public double DTotalContact, DTotalFree;
            /// <summary>Largest per-step change of AligningTorqueTotal [N m], in / outside the contact window.</summary>
            public double DMzContact, DMzFree;
            /// <summary>Largest per-step change of the device output [normalised].</summary>
            public double DOutMax;
            public double MaxContactForceKn;
            /// <summary>|AligningTorqueTotal - AligningTorqueRaw| at the end of the run [N m].</summary>
            public double FinalFeedbackOffset;
        }

        /// <summary>Contact window: the steps with contact points plus this many steps after the last one.</summary>
        const int Tail = 50;

        static Trace Run(string id, DefinitionSet defs = null)
        {
            var sc = Suites.Find(id);
            var s = ScenarioRunner.Setup(sc, new RunOptions(), defs);
            var driver = ScenarioRunner.CreateDriver(sc, s, out _);
            var ffb = new ForceFeedbackModel();
            var sink = new RecordingForceFeedbackSink(8);
            double dt = sc.dt, t = 0;
            int steps = (int)Math.Round(sc.duration / dt), window = 0;
            var tr = new Trace();
            double prevTotal = 0, prevMz = 0, prevOut = 0;
            bool first = true;
            for (int i = 0; i < steps; i++)
            {
                DriverInput inp = driver.Update(t, dt, s);
                ChassisState a = s.Body.State, b = s.TrailerBody != null ? s.TrailerBody.State : default;
                s.Combo.Step(dt, a, b, inp, s.Ground);
                ScenarioRunner.StepBodies(s, dt);
                t += dt;
                var m = s.Tractor;
                float loadL = 0, loadR = 0;
                foreach (var w in m.Wheels)
                {
                    if (!w.Steered || !w.Contact) continue;
                    if (w.Side < 0) loadL += (float)w.Fz; else loadR += (float)w.Fz;
                }
                // As DrivingLabBootstrap.FixedUpdate -> PcWheel.StepForceFeedback (device at rest, 1:1 gearing, default settings).
                var fin = new ForceFeedbackInputs
                {
                    Active = true, ForwardSpeed = (float)m.SpeedForward, AligningTorqueNm = (float)m.AligningTorqueTotal,
                    SteeringRatio = (float)m.Steering.Def.steeringRatio, CabPerDeviceDeg = 1f,
                    SteeredLoadLeftN = loadL, SteeredLoadRightN = loadR,
                };
                double o = ffb.Step((float)dt, fin, sink);
                var fw = s.Combo.FifthWheel;
                if (fw.ContactPoints > 0) { window = Tail; tr.ContactSteps++; }
                tr.MaxContactForceKn = Math.Max(tr.MaxContactForceKn, fw.ContactForceOnTrailer.Magnitude / 1000);
                if (!first)
                {
                    double dTot = Math.Abs(ffb.TotalNm - prevTotal), dMz = Math.Abs(m.AligningTorqueTotal - prevMz);
                    if (window > 0) { tr.DTotalContact = Math.Max(tr.DTotalContact, dTot); tr.DMzContact = Math.Max(tr.DMzContact, dMz); }
                    else if (t > 1.5) { tr.DTotalFree = Math.Max(tr.DTotalFree, dTot); tr.DMzFree = Math.Max(tr.DMzFree, dMz); }
                    tr.DOutMax = Math.Max(tr.DOutMax, Math.Abs(o - prevOut));
                }
                if (window > 0) window--;
                prevTotal = ffb.TotalNm; prevMz = m.AligningTorqueTotal; prevOut = o; first = false;
                tr.FinalFeedbackOffset = Math.Abs(m.AligningTorqueTotal - m.AligningTorqueRaw);
            }
            return tr;
        }

        static string Line(string id, Trace tr) =>
            $"{id}: contact steps {tr.ContactSteps}, peak contact {tr.MaxContactForceKn:F0} kN; dFFB/step contact {tr.DTotalContact:F3} vs free {tr.DTotalFree:F3} N m; " +
            $"dMz/step contact {tr.DMzContact:F0} vs free {tr.DMzFree:F0} N m; dOut/step max {tr.DOutMax:F3}; final |Mz - raw| {tr.FinalFeedbackOffset:F2} N m";

        /// <summary>
        /// Jackknife contact (fold into the cab and keep pushing, fast swing impact, counter-steer): per 10 ms step the FFB rim
        /// torque target changes by at most <see cref="MaxFfbStepNm"/> while the bodies touch, and the device output stays under
        /// half the FFB slew step (the limiter never clips a contact event).
        /// </summary>
        [Theory]
        [InlineData("jackknife_fold_120_reverse_comb@laden40")]
        [InlineData("jackknife_fold_120_reverse_comb@empty")]
        [InlineData("jackknife_fast_fold_impact_comb@laden40")]
        [InlineData("jackknife_fast_fold_impact_comb@empty")]
        [InlineData("jackknife_reverse_countersteer_comb@empty")]
        public void BodyContact_DoesNotKickTheWheel(string id)
        {
            var tr = Run(id);
            _out.WriteLine(Line(id, tr));
            Assert.True(tr.ContactSteps > 0, "scenario must reach the cab");
            Assert.True(tr.DTotalContact <= MaxFfbStepNm, $"contact kicks the wheel: {tr.DTotalContact:F3} N m per step > {MaxFfbStepNm}");
            var set = ForceFeedbackSettings.Defaults();
            Assert.True(tr.DOutMax <= 0.5 * set.maxSlewPerS * 0.01 + 1e-6, $"output step {tr.DOutMax:F4} > half the slew step");
        }

        /// <summary>After the combination is pulled straight (the counter-steer scenario runs ~20 s past the last contact), the
        /// feedback estimate is the raw tyre value again: the smoothing is only a contact transient.</summary>
        [Fact]
        public void ContactSmoothing_HandsBackToRawValue()
        {
            var tr = Run("jackknife_reverse_countersteer_comb@empty");
            _out.WriteLine(Line("countersteer@empty", tr));
            Assert.True(tr.ContactSteps > 0);
            Assert.Equal(0.0, tr.FinalFeedbackOffset, 6);
        }

        /// <summary>Mutation check: with the smoothing off (contactFeedbackLagS = 0) the same contact gives a kick the test catches.</summary>
        [Fact]
        public void WithoutSmoothing_TheContactKicks()
        {
            var defs = DefinitionSet.LoadDirectory(RepoPaths.DefinitionsDir);
            foreach (var v in defs.Vehicles.Values) v.steering.contactFeedbackLagS = 0;
            var tr = Run("jackknife_fold_120_reverse_comb@laden40", defs);
            _out.WriteLine("no smoothing: " + Line("fold_120@laden40", tr));
            Assert.True(tr.DTotalContact > 2 * MaxFfbStepNm, $"expected a kick without smoothing, got {tr.DTotalContact:F3} N m per step");
        }

        /// <summary>
        /// Reference (no contact): the same FFB measure on ordinary events, for the ADR table. Kerbs reach the slew limit through
        /// the road-feel term (ADR 0263 design); a lane change at 80 km/h is smooth. Only asserts that nothing touches.
        /// </summary>
        [Theory]
        [InlineData("curb_15cm_left_comb@laden40")]
        [InlineData("curb_strike_14cm_50kmh_comb@laden40")]
        [InlineData("lane_change_80@laden40")]
        public void Reference_OrdinaryDriving(string id)
        {
            var tr = Run(id);
            _out.WriteLine($"REF {id}: dFFB/step max {tr.DTotalFree:F3} N m, dMz/step {tr.DMzFree:F0} N m, dOut/step {tr.DOutMax:F3}");
            Assert.Equal(0, tr.ContactSteps);
        }

        /// <summary>Review P1 (s22 #113): a tight forward turn with a hard stop never touches, so nothing from the contact reaches the wheel.</summary>
        [Theory]
        [InlineData("jackknife_tight_turn_forward_comb@laden40")]
        [InlineData("jackknife_tight_turn_forward_comb@empty")]
        public void TightForwardTurn_NoContact(string id)
        {
            var tr = Run(id);
            _out.WriteLine(Line(id, tr));
            Assert.Equal(0, tr.ContactSteps);
            Assert.Equal(0.0, tr.FinalFeedbackOffset, 9);
        }
    }
}
