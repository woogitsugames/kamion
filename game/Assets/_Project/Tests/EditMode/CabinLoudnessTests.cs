using Game.Core;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>
    /// D92 / ADR 0311: cab loudness bus. The exterior keeps unity gain (D92: exterior unchanged), the cab gets the measured
    /// calibration gain, the ramp inside a DSP block is continuous (no click on a view change) and a unity gain is a
    /// bit-exact pass-through.
    /// </summary>
    public sealed class CabinLoudnessTests
    {
        [Test]
        public void Target_IsD92()
        {
            Assert.AreEqual(-18f, CabinLoudness.TargetLufs);
            Assert.AreEqual(-1f, CabinLoudness.TruePeakCeilingDbtp);
        }

        [Test]
        public void CalibrationGains_AreInsideTheSanityRange()
        {
            foreach (float db in new[] { CabinLoudness.ElevenLabsCabGainDb, CabinLoudness.ProceduralCabGainDb })
            {
                Assert.GreaterOrEqual(db, CabinLoudness.MinGainDb);
                Assert.LessOrEqual(db, CabinLoudness.MaxGainDb);
            }
        }

        [Test]
        public void DbToLinear_MatchesDecibels()
        {
            Assert.AreEqual(1f, CabinLoudness.DbToLinear(0f), 1e-6f);
            Assert.AreEqual(2f, CabinLoudness.DbToLinear(6.0206f), 1e-4f);
            Assert.AreEqual(0.5f, CabinLoudness.DbToLinear(-6.0206f), 1e-4f);
            Assert.AreEqual(CabinLoudness.DbToLinear(CabinLoudness.MaxGainDb), CabinLoudness.DbToLinear(40f), 1e-6f, "clamped");
        }

        [Test]
        public void BusGain_ExteriorIsUnity_CabIsCalibrated()
        {
            float g = CabinLoudness.DbToLinear(3f);
            Assert.AreEqual(1f, CabinLoudness.BusGain(g, 0f), "exterior view: exactly unity (D92)");
            Assert.AreEqual(g, CabinLoudness.BusGain(g, 1f), 1e-6f);
            Assert.AreEqual(1f + (g - 1f) * 0.5f, CabinLoudness.BusGain(g, 0.5f), 1e-6f);
            Assert.AreEqual(g, CabinLoudness.BusGain(g, 3f), 1e-6f, "interior clamped");
        }

        [Test]
        public void ParseOverride_ReadsTheLaunchArgument()
        {
            Assert.IsNaN(CabinLoudness.ParseOverride(null));
            Assert.IsNaN(CabinLoudness.ParseOverride(new[] { "Kamion.exe", "-scene", "DrivingLab" }));
            Assert.AreEqual(2.5f, CabinLoudness.ParseOverride(new[] { "Kamion.exe", "-audio_cab_gain_db", "2.5" }));
            Assert.AreEqual(0f, CabinLoudness.ParseOverride(new[] { "-AUDIO_CAB_GAIN_DB", "0" }));
            Assert.IsNaN(CabinLoudness.ParseOverride(new[] { "-audio_cab_gain_db", "40" }), "outside the range: ignored");
            Assert.IsNaN(CabinLoudness.ParseOverride(new[] { "-audio_cab_gain_db" }), "no value");
        }

        [Test]
        public void Apply_UnityGain_IsBitExactPassThrough()
        {
            var data = new[] { 0.1f, -0.3f, 0.7f, -0.9f, 0.123456f, 1e-7f };
            var copy = (float[])data.Clone();
            CabinLoudness.Apply(data, 2, 1f, 1f);
            CollectionAssert.AreEqual(copy, data);
        }

        [Test]
        public void Apply_ConstantGain_ScalesEverySample()
        {
            var data = new[] { 0.5f, -0.25f, 0.1f, 0.2f };
            float r = CabinLoudness.Apply(data, 2, 2f, 2f);
            Assert.AreEqual(2f, r);
            CollectionAssert.AreEqual(new[] { 1f, -0.5f, 0.2f, 0.4f }, data);
        }

        [Test]
        public void Apply_Ramp_IsContinuousAcrossBlocks_AndSameOnBothChannels()
        {
            const int frames = 512, ch = 2;
            var a = new float[frames * ch];
            var b = new float[frames * ch];
            for (int i = 0; i < a.Length; i++) { a[i] = 1f; b[i] = 1f; }
            float g = CabinLoudness.Apply(a, ch, 1f, 1.4f);   // view change: ramp 1 -> 1.4 in one block
            CabinLoudness.Apply(b, ch, g, 1.4f);              // next block: steady
            float maxStep = 0f, prev = 1f;
            for (int f = 0; f < frames; f++)
            {
                Assert.AreEqual(a[f * ch], a[f * ch + 1], "same gain on both channels");
                maxStep = System.Math.Max(maxStep, System.Math.Abs(a[f * ch] - prev));
                Assert.GreaterOrEqual(a[f * ch], prev - 1e-6f, "monotonic");
                prev = a[f * ch];
            }
            Assert.AreEqual(1.4f, a[a.Length - 1], 1e-5f, "block ends on the target");
            Assert.AreEqual(1.4f, b[0], 1e-5f, "next block starts where the ramp ended");
            Assert.Less(maxStep, 0.4f / frames * 1.01f, "per-frame step = (to - from) / frames (no jump)");
        }

        [Test]
        public void Apply_DegenerateInput_DoesNotThrow()
        {
            Assert.AreEqual(2f, CabinLoudness.Apply(null, 2, 1f, 2f));
            Assert.AreEqual(2f, CabinLoudness.Apply(new float[0], 2, 1f, 2f));
            Assert.AreEqual(2f, CabinLoudness.Apply(new float[3], 0, 1f, 2f));
        }
    }
}
