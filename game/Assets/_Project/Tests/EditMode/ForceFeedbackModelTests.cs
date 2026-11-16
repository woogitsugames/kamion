using Game.Controls;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>
    /// Steering force feedback from synthetic tyre forces (ADR 0263): sign and size of the aligning term, zero at
    /// standstill, damping/friction oppose the rim, soft-lock wall, clamp and slew limit, stop on inactive, road feel only
    /// from load changes. No device: <see cref="RecordingForceFeedbackSink"/>. Pure logic (also run outside Unity).
    /// </summary>
    public class ForceFeedbackModelTests
    {
        const float Dt = 0.01f;   // 100 Hz fixed step

        static ForceFeedbackSettings Plain()
        {
            var s = ForceFeedbackSettings.Defaults();
            s.dampingNmPerRadS = 0f; s.frictionNm = 0f; s.roadFeelLeverM = 0f; s.maxSlewPerS = 1000f;
            return s;
        }

        static ForceFeedbackInputs Driving(float speed, float mz) => new ForceFeedbackInputs
        {
            Active = true, ForwardSpeed = speed, AligningTorqueNm = mz, SteeringRatio = 20f, CabPerDeviceDeg = 1f,
        };

        static float Settle(ForceFeedbackModel m, ForceFeedbackInputs inp, IForceFeedbackSink sink, int steps = 200)
        {
            float o = 0f;
            for (int i = 0; i < steps; i++) o = m.Step(Dt, inp, sink);
            return o;
        }

        [Test]
        public void Aligning_SizeFollowsRatioAssistAndFullScale()
        {
            var s = Plain(); s.powerAssist = 0.85f; s.fullScaleRimTorqueNm = 8f; s.gain = 1f;
            var m = new ForceFeedbackModel(s);
            // Mz 400 N m / 20 x 0.15 = 3 N m at the rim -> 3 / 8 = 0.375.
            float o = Settle(m, Driving(20f, 400f), new RecordingForceFeedbackSink());
            Assert.AreEqual(3f, m.AligningNm, 1e-3f);
            Assert.AreEqual(0.375f, o, 1e-3f);
        }

        [Test]
        public void Aligning_SignPushesRimTheWayTheTyresPush()
        {
            // Turning right: Fy > 0 (to the right) -> Mz = -trail x Fy < 0 -> rim pushed back to the left (negative).
            float trail = 0.06f, fy = 20000f;
            var m = new ForceFeedbackModel(Plain());
            float o = Settle(m, Driving(15f, -trail * fy), null);
            Assert.Less(o, 0f);
            m.Reset();
            Assert.Greater(Settle(m, Driving(15f, trail * fy), null), 0f);
            m.Reset();
            Assert.Less(Settle(m, Driving(-3f, -trail * fy), null), 0f, "reversing: same physics sign, fade uses |v|");
        }

        [Test]
        public void Standstill_StillRim_IsZero()
        {
            var m = new ForceFeedbackModel(ForceFeedbackSettings.Defaults());
            var inp = Driving(0f, 900f);
            inp.SteeredLoadLeftN = 30000f; inp.SteeredLoadRightN = 32000f;   // static split: not a bump
            float o = Settle(m, inp, null);
            Assert.AreEqual(0f, o, 1e-4f);
        }

        [Test]
        public void SpeedFade_IsMonotonicAndBounded()
        {
            float prev = -1f;
            for (float v = 0f; v <= 5f; v += 0.1f)
            {
                float f = ForceFeedbackModel.SpeedFade(v, 0.3f, 2.5f);
                Assert.GreaterOrEqual(f, prev);
                Assert.That(f, Is.InRange(0f, 1f));
                prev = f;
            }
            Assert.AreEqual(0f, ForceFeedbackModel.SpeedFade(0.2f, 0.3f, 2.5f));
            Assert.AreEqual(1f, ForceFeedbackModel.SpeedFade(-3f, 0.3f, 2.5f));
        }

        [Test]
        public void DampingAndFriction_OpposeRimMotion_EvenAtStandstill()
        {
            var s = ForceFeedbackSettings.Defaults(); s.maxSlewPerS = 1000f;
            var m = new ForceFeedbackModel(s);
            var inp = Driving(0f, 0f); inp.DeviceRateDegS = 200f;
            float o = Settle(m, inp, null, 20);
            Assert.Less(m.DampingNm, 0f);
            Assert.Less(m.FrictionNm, 0f);
            Assert.Less(o, 0f);
            inp.DeviceRateDegS = -200f;
            Assert.Greater(Settle(m, inp, null, 20), 0f);
        }

        [Test]
        public void SoftLock_PushesBackAndDampsOnlyIntoTheWall()
        {
            var s = Plain(); s.softLockNmPerDeg = 1f; s.softLockDampingNmPerRadS = 1f;
            var m = new ForceFeedbackModel(s);
            var inp = Driving(10f, 0f); inp.PastSoftLockDeg = 5f;
            Settle(m, inp, null, 5);
            Assert.AreEqual(-5f, m.SoftLockNm, 1e-3f);
            inp.DeviceRateDegS = 90f;   // going further in
            Settle(m, inp, null, 1);
            Assert.Less(m.SoftLockNm, -5f);
            inp.DeviceRateDegS = -90f;  // coming out: no extra damping from the wall
            Settle(m, inp, null, 1);
            Assert.AreEqual(-5f, m.SoftLockNm, 1e-3f);
            inp.PastSoftLockDeg = -5f; inp.DeviceRateDegS = 0f;
            Settle(m, inp, null, 1);
            Assert.AreEqual(5f, m.SoftLockNm, 1e-3f);
        }

        [Test]
        public void Output_ClampedToMaxOutputAndSlewLimited()
        {
            var s = Plain(); s.maxOutput = 0.6f; s.maxSlewPerS = 10f;
            var m = new ForceFeedbackModel(s);
            var sink = new RecordingForceFeedbackSink();
            m.Step(Dt, Driving(20f, 100000f), sink);
            Assert.AreEqual(0.1f, sink.Last, 1e-4f, "10 /s x 0.01 s");
            float o = Settle(m, Driving(20f, 100000f), sink);
            Assert.AreEqual(0.6f, o, 1e-4f);
            Assert.LessOrEqual(sink.MaxAbs, 0.6f + 1e-5f);
            for (int i = 1; i < 50; i++) Assert.LessOrEqual(System.Math.Abs(sink.Recent(i - 1) - sink.Recent(i)), 0.1f + 1e-5f);
        }

        [Test]
        public void Inactive_StopsOnceAndOutputsZero()
        {
            var m = new ForceFeedbackModel(Plain());
            var sink = new RecordingForceFeedbackSink();
            Settle(m, Driving(20f, 400f), sink, 50);
            Assert.Greater(sink.Last, 0f);
            var off = Driving(20f, 400f); off.Active = false;
            for (int i = 0; i < 10; i++) Assert.AreEqual(0f, m.Step(Dt, off, sink));
            Assert.AreEqual(1, sink.StopCount, "Stop sent on the transition only");
            Assert.AreEqual(0f, sink.Last);
            Assert.AreEqual(0f, m.Output);
        }

        [Test]
        public void NaNInputs_DoNotReachTheDevice()
        {
            var m = new ForceFeedbackModel(Plain());
            var sink = new RecordingForceFeedbackSink();
            var inp = Driving(20f, float.NaN);
            m.Step(Dt, inp, sink);
            Assert.IsFalse(float.IsNaN(sink.Last));
        }

        [Test]
        public void RoadFeel_OnlyFromLoadChanges()
        {
            var s = Plain(); s.roadFeelLeverM = 0.05f; s.powerAssist = 0f; s.fullScaleRimTorqueNm = 1f;
            var m = new ForceFeedbackModel(s);
            var inp = Driving(15f, 0f); inp.SteeredLoadLeftN = 30000f; inp.SteeredLoadRightN = 30000f;
            Settle(m, inp, null, 50);
            Assert.AreEqual(0f, m.RoadFeelNm, 1e-4f);
            inp.SteeredLoadRightN = 34000f;   // right wheel hits a bump
            m.Step(Dt, inp, null);
            Assert.Greater(m.RoadFeelNm, 0f);
            Settle(m, inp, null, 200);
            Assert.AreEqual(0f, m.RoadFeelNm, 1e-3f, "a steady load split is not felt");
        }

        [Test]
        public void VirtualGearing_ScalesTorque()
        {
            var m = new ForceFeedbackModel(Plain());
            var inp = Driving(20f, 400f); inp.CabPerDeviceDeg = 2f;
            Settle(m, inp, null, 5);
            Assert.AreEqual(6f, m.AligningNm, 1e-3f);
        }

        [Test]
        public void Settings_SanitizeFixesGarbage()
        {
            var s = new ForceFeedbackSettings { gain = float.NaN, powerAssist = 5f, fullScaleRimTorqueNm = -1f, maxOutput = 3f, aligningFadeStartMs = 5f, aligningFadeFullMs = 1f };
            s.Sanitize();
            Assert.AreEqual(1f, s.gain);
            Assert.LessOrEqual(s.powerAssist, 0.99f);
            Assert.GreaterOrEqual(s.fullScaleRimTorqueNm, 0.5f);
            Assert.AreEqual(1f, s.maxOutput);
            Assert.Greater(s.aligningFadeFullMs, s.aligningFadeStartMs);
        }
    }
}
