using NUnit.Framework;
using TruckSim.Audio;

namespace Game.Tests
{
    /// <summary>ADR 0176: retarder laws (LayerMath, mirror of tools/audio/synth0176_ab.py) and the driveline event detector (pure maths).</summary>
    public sealed class DrivelineSfxTests
    {
        const int Drive = 2;
        const float Dt = 1f / 60f, Tau = 0.25f; // EngineDefinition.engineBrakeTimeConstant

        [Test]
        public void ShaftRpm_FollowsRoadSpeed()
        {
            // 85 km/h, r 0.51 m, final drive 3.4 -> 1503 rpm (synth0176_ab.py checks.json)
            Assert.AreEqual(1503f, LayerMath.ShaftRpm(85f / 3.6f, 0.51f, 3.4f), 2f);
            Assert.AreEqual(0f, LayerMath.ShaftRpm(0f, 0.51f, 3.4f), 1e-6f);
        }

        [Test]
        public void RetarderTone_IsFaintAtWalkingPaceAndFullAtSpeed()
        {
            float slow = LayerMath.RetarderToneGain(1f, 177f, 0.5f);   // 10 km/h
            float fast = LayerMath.RetarderToneGain(1f, 1600f, 0.5f);
            Assert.AreEqual(0.5f * LayerMath.RetarderToneMix, fast, 1e-5f);
            Assert.Less(slow, fast * 0.05f, "hydrodynamic retarder is almost silent at walking pace (< -26 dB)");
            Assert.AreEqual(0f, LayerMath.RetarderToneGain(0f, 1600f, 0.5f), 1e-6f, "empty retarder = no tone");
            Assert.AreEqual(fast, LayerMath.RetarderToneGain(1f, 3000f, 0.5f), 1e-6f, "clamped above the full-level speed");
        }

        [Test]
        public void RetarderFlow_FollowsSqrtOfPower()
        {
            Assert.AreEqual(0.5f * LayerMath.RetarderFlowMix, LayerMath.RetarderFlowGain(600e3f, 600e3f, 0.5f), 1e-5f);
            Assert.AreEqual(0.5f * LayerMath.RetarderFlowMix * 0.5f, LayerMath.RetarderFlowGain(150e3f, 600e3f, 0.5f), 1e-5f);
            Assert.AreEqual(0f, LayerMath.RetarderFlowGain(-10f, 600e3f, 0.5f), 1e-6f);
        }

        [Test]
        public void RetarderPitch_IsShaftOverReference_Clamped()
        {
            Assert.AreEqual(1f, LayerMath.RetarderTonePitch(LayerMath.RetarderRefShaftRpm), 1e-6f);
            Assert.AreEqual(0.2f, LayerMath.RetarderTonePitch(10f), 1e-6f);
            Assert.AreEqual(2.5f, LayerMath.RetarderTonePitch(5000f), 1e-6f);
        }

        [Test]
        public void EngineBrakeRelease_IsLouderAtHighRpm()
        {
            Assert.AreEqual(0.2f, LayerMath.EngineBrakeReleaseLevel(800f, 0.5f), 1e-6f);
            Assert.AreEqual(0.5f, LayerMath.EngineBrakeReleaseLevel(2100f, 0.5f), 1e-6f);
        }

        static float FirstOrder(float x, float target) => x + (target - x) * (1f - UnityEngine.Mathf.Exp(-Dt / Tau));

        [Test]
        public void EngineBrake_OneEngageAndOneRelease_PerLeverApplication()
        {
            var d = new DrivelineSfx();
            float s = 0f;
            int engage = 0, release = 0, engageFrame = -1, releaseFrame = -1;
            for (int i = 0; i < 360; i++) // lever on 1.0-3.0 s, 60 Hz
            {
                bool lever = i >= 60 && i < 180;
                s = FirstOrder(s, lever ? 1f : 0f);
                int ev = d.Step(Drive, s, lever);
                if ((ev & DrivelineSfx.EbrakeEngage) != 0) { engage++; engageFrame = i; }
                if ((ev & DrivelineSfx.EbrakeRelease) != 0) { release++; releaseFrame = i; }
            }
            Assert.AreEqual(1, engage);
            Assert.AreEqual(1, release);
            Assert.LessOrEqual(engageFrame - 60, 4, "engage within ~70 ms of the lever");
            Assert.LessOrEqual(releaseFrame - 180, 4, "release within ~70 ms of letting go");
            Assert.Greater(d.LastReleaseDepth, 0.95f);
        }

        [Test]
        public void EngineBrake_ShortBlip_StillPairsEvents_WithShallowDepth()
        {
            var d = new DrivelineSfx();
            float s = 0f;
            int engage = 0, release = 0;
            for (int i = 0; i < 120; i++)
            {
                bool lever = i >= 10 && i < 16; // 0.1 s
                s = FirstOrder(s, lever ? 1f : 0f);
                int ev = d.Step(Drive, s, lever);
                if ((ev & DrivelineSfx.EbrakeEngage) != 0) engage++;
                if ((ev & DrivelineSfx.EbrakeRelease) != 0) release++;
            }
            Assert.AreEqual(1, engage);
            Assert.AreEqual(1, release);
            Assert.Less(d.LastReleaseDepth, 0.5f, "flap barely closed: quiet dump");
        }

        [Test]
        public void AmtShift_GivesDisengageEngageAndClutchClosed_InOrder()
        {
            var d = new DrivelineSfx();
            int[] states = { Drive, Drive, 3, 3, 4, 4, 5, 5, 6, 6, Drive, Drive };
            int[] seen = new int[states.Length];
            for (int i = 0; i < states.Length; i++) seen[i] = d.Step(states[i], 0f, false);
            Assert.AreEqual(0, seen[2], "torque ramp-down is silent");
            Assert.AreEqual(DrivelineSfx.AmtDisengage, seen[4]);
            Assert.AreEqual(DrivelineSfx.AmtEngage, seen[8]);
            Assert.AreEqual(DrivelineSfx.AmtClutchClosed, seen[10]);
            int total = 0;
            foreach (int e in seen) if (e != 0) total++;
            Assert.AreEqual(3, total);
        }

        [Test]
        public void EngineBrake_IsFrozenDuringShift_NoFalseRelease()
        {
            var d = new DrivelineSfx();
            float s = 0f;
            int release = 0, engage = 0;
            for (int i = 0; i < 300; i++)
            {
                bool shifting = i >= 120 && i < 150;
                int amt = shifting ? (i < 128 ? 3 : i < 137 ? 4 : i < 143 ? 5 : 6) : Drive;
                // lever held all the time; the model cuts the flap during the shift (state decays), then it closes again
                s = FirstOrder(s, shifting ? 0f : 1f);
                int ev = d.Step(amt, s, true);
                if ((ev & DrivelineSfx.EbrakeRelease) != 0) release++;
                if ((ev & DrivelineSfx.EbrakeEngage) != 0) engage++;
            }
            Assert.AreEqual(1, engage, "one engage for the whole hold");
            Assert.AreEqual(0, release, "a shift is not a lever release");
            Assert.IsTrue(d.EngineBrakeOn);
        }

        [Test]
        public void EngineBrake_LeverLetGoDuringShift_TurnsOffSilently()
        {
            var d = new DrivelineSfx();
            float s = 0f;
            int release = 0;
            for (int i = 0; i < 300; i++)
            {
                bool shifting = i >= 120 && i < 150;
                bool lever = i < 135;
                int amt = shifting ? 4 : Drive;
                s = FirstOrder(s, !shifting && lever ? 1f : 0f);
                if ((d.Step(amt, s, lever) & DrivelineSfx.EbrakeRelease) != 0) release++;
            }
            Assert.AreEqual(0, release);
            Assert.IsFalse(d.EngineBrakeOn);
        }

        [Test]
        public void FirstStepAndReset_AreSilent()
        {
            var d = new DrivelineSfx();
            Assert.AreEqual(0, d.Step(6, 1f, true));
            d.Reset();
            Assert.AreEqual(0, d.Step(Drive, 0f, false));
        }
    }
}
