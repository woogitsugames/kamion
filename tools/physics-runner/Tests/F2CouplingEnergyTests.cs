using System;
using Game.Vehicle.Physics;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>
    /// ADR 0201b (F2 energy source): the two mechanisms that put kinetic energy into the free fall of the F2 mutation run.
    /// 1. Compliant fifth-wheel stops gave stored spring energy back as relative velocity (rebound).
    /// 2. Raycast tyre contact at grazing incidence (suspension axis nearly parallel to the ground) produced
    ///    MN-level forces (the travel S = d / cos(tilt) - r is hypersensitive to the tilt).
    /// </summary>
    public class F2CouplingEnergyTests
    {
        readonly ITestOutputHelper _out;
        public F2CouplingEnergyTests(ITestOutputHelper output) { _out = output; }

        static Scenario Load(string id) =>
            Scenario.Load(System.IO.Path.Combine(RepoPaths.ScenariosDir, id + ".json"));

        /// <summary>
        /// Coupled tractor + 24 t trailer in free space (no gravity, no ground): the trailer pitches into the 12 deg
        /// plate stop at 2 rad/s relative. Total KE may never grow by more than 1 J per step (only coupling forces act).
        /// Control: with the old elastic stop (recovery rate unlimited) the stop rebound adds > 100 J in a step.
        /// </summary>
        [Fact]
        public void PitchStop_ImpactInFreeSpace_DoesNotRebound()
        {
            double gainNew = Run(null, out double maxPitchNew);
            double gainOld = Run(1e6, out double maxPitchOld);
            _out.WriteLine($"no-rebound stop: max KE gain/step {gainNew:F3} J, max plate pitch {maxPitchNew:F2} deg; elastic stop: {gainOld:F1} J, {maxPitchOld:F2} deg");
            Assert.True(maxPitchNew > 12.0, "the trailer must reach the pitch stop");
            Assert.True(gainNew <= 1.0, $"no-rebound stop gained {gainNew:F3} J in a step");
            Assert.True(gainOld > 100.0, $"control: the elastic stop should rebound (gained {gainOld:F1} J)");
        }

        double Run(double? recoveryRateDegS, out double maxPitchDeg)
        {
            var defs = DefinitionSet.LoadDirectory(RepoPaths.DefinitionsDir);
            if (recoveryRateDegS.HasValue) defs.Vehicles["tractor_4x2_generic"].fifthWheel.stopRecoveryRateDegS = recoveryRateDegS.Value;
            var sc = Load("fuzz_shrink_speed_runaway_fulllock");
            var s = ScenarioRunner.Setup(sc, new RunOptions { DisableBodyContact = true }, defs);
            var lift = new Vec3(0, 100, 0);
            s.Body.Position += lift; s.TrailerBody.Position += lift;
            s.Body.Gravity = Vec3.Zero; s.TrailerBody.Gravity = Vec3.Zero; s.Combo.Gravity = Vec3.Zero;
            s.Body.Velocity = Vec3.Zero; s.Body.AngularVelocity = Vec3.Zero;
            // Trailer pitching about the kingpin (kingpin velocity 0) at 2 rad/s about the tractor's lateral axis.
            Vec3 w = (s.Body.Rotation * Vec3.Right) * 2.0;
            Vec3 kp = s.TrailerBody.State.LocalToWorld(s.Trailer.KingpinLocal);
            s.TrailerBody.AngularVelocity = w;
            s.TrailerBody.Velocity = Vec3.Cross(w, s.TrailerBody.CenterOfMassWorld - kp);
            double dt = sc.dt, maxGain = 0, prev = s.Body.KineticEnergy + s.TrailerBody.KineticEnergy;
            maxPitchDeg = 0;
            for (int i = 0; i < 150; i++)
            {
                s.Combo.Step(dt, s.Body.State, s.TrailerBody.State, default(DriverInput), s.Ground);
                ScenarioRunner.StepBodies(s, dt);
                double e = s.Body.KineticEnergy + s.TrailerBody.KineticEnergy;
                maxGain = Math.Max(maxGain, e - prev);
                prev = e;
                maxPitchDeg = Math.Max(maxPitchDeg, Math.Abs(s.Combo.FifthWheel.PitchAngle) * MathUtil.Rad2Deg);
            }
            return maxGain;
        }

        /// <summary>
        /// Solo tractor tilted about its roll axis with the lowest wheel hardpoint 0.15 m above flat ground: at 70 deg the
        /// wheel still has tyre contact, beyond <see cref="SolverSettings.maxContactTiltDeg"/> (72.5 deg) there is none
        /// (the ray would reach the ground at 0.15 / cos 75 deg = 0.58 m, inside the 0.76 m ray length).
        /// </summary>
        [Theory]
        [InlineData(70.0, true)]
        [InlineData(75.0, false)]
        public void WheelContact_BeyondMaxTilt_IsRejected(double rollDeg, bool expectContact)
        {
            var sc = Load("brake_80_0_dry");
            var s = ScenarioRunner.Setup(sc, new RunOptions());
            var b = s.Body;
            b.Rotation = Quat.AngleAxis(rollDeg * MathUtil.Deg2Rad, b.Rotation * Vec3.Forward) * b.Rotation;
            b.Velocity = Vec3.Zero; b.AngularVelocity = Vec3.Zero;
            double lowest = double.MaxValue;
            foreach (var w in s.Tractor.Wheels) lowest = Math.Min(lowest, b.State.LocalToWorld(w.HardpointLocal).y);
            b.Position += new Vec3(0, 0.15 - lowest, 0);
            s.Combo.Step(sc.dt, b.State, default, default(DriverInput), s.Ground);
            int contacts = 0;
            foreach (var w in s.Tractor.Wheels) if (w.Contact) contacts++;
            _out.WriteLine($"roll {rollDeg} deg: {contacts} wheel contacts");
            Assert.Equal(expectContact, contacts > 0);
        }
    }
}
