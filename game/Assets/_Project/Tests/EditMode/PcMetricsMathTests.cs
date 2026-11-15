using System;
using Game.Telemetry;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>ADR 0266: pure logic of the PC metrics run. The same cases are in tools/pcperf/tests/test_pc_metrics.py
    /// (test_nearest_rank_*), so the in-game run.json "inGame" block and the Python report agree.</summary>
    public class PcMetricsMathTests
    {
        static float[] OneToHundredSorted()
        {
            var a = new float[100];
            for (int i = 0; i < 100; i++) a[i] = i + 1;
            return a;
        }

        [Test]
        public void NearestRank_OneToHundred()
        {
            var a = OneToHundredSorted();
            Assert.AreEqual(50f, PcMetricsMath.NearestRank(a, 100, 0.50));
            Assert.AreEqual(95f, PcMetricsMath.NearestRank(a, 100, 0.95));
            Assert.AreEqual(99f, PcMetricsMath.NearestRank(a, 100, 0.99));
            Assert.AreEqual(100f, PcMetricsMath.NearestRank(a, 100, 1.0));
            Assert.AreEqual(1f, PcMetricsMath.NearestRank(a, 100, 0.0));
        }

        [Test]
        public void NearestRank_SmallCounts_AndPrefixOfBuffer()
        {
            var a = new float[] { 10f, 20f, 30f, 999f };
            Assert.AreEqual(20f, PcMetricsMath.NearestRank(a, 3, 0.50));   // ceil(1.5) = 2
            Assert.AreEqual(30f, PcMetricsMath.NearestRank(a, 3, 0.95));   // only the first 3 values count
            Assert.AreEqual(10f, PcMetricsMath.NearestRank(a, 1, 0.99));
            Assert.AreEqual(0f, PcMetricsMath.NearestRank(a, 0, 0.5));
            Assert.AreEqual(0f, PcMetricsMath.NearestRank(null, 5, 0.5));
        }

        [Test]
        public void NearestRank_ExactProductIsNotRoundedUp()
        {
            // p·n landing on an integer must give that rank (19), not the next one (guarded by the -1e-9 in the rank).
            var a = new float[20];
            for (int i = 0; i < 20; i++) a[i] = i + 1;
            Assert.AreEqual(19f, PcMetricsMath.NearestRank(a, 20, 0.95));
        }

        [Test]
        public void CountOver_IsStrict()
        {
            var a = new float[] { 16.6f, 33.4f, 33.5f, 50f, 120f };
            Assert.AreEqual(3, PcMetricsMath.CountOver(a, a.Length, 33.4f));
            Assert.AreEqual(1, PcMetricsMath.CountOver(a, a.Length, 50f));
            Assert.AreEqual(1, PcMetricsMath.CountOver(a, a.Length, 100f));
            Assert.AreEqual(0, PcMetricsMath.CountOver(a, 2, 33.4f));
        }

        [Test]
        public void FrameCapacity_Clamped()
        {
            Assert.AreEqual(91000, PcMetricsMath.FrameCapacity(91f, 1000));
            Assert.AreEqual(1000, PcMetricsMath.FrameCapacity(0.1f, 10));
            Assert.AreEqual(2000000, PcMetricsMath.FrameCapacity(100000f, 1000));
        }

        [Test]
        public void Options_DisabledWithoutMetricsDir()
        {
            Assert.IsFalse(PcMetricsOptions.Parse(new[] { "Kamion.exe", "-tier", "High" }).Enabled);
            Assert.IsFalse(PcMetricsOptions.Parse(new[] { "Kamion.exe", "-metrics" }).Enabled);
            Assert.IsFalse(PcMetricsOptions.Parse(new[] { "Kamion.exe", "-metrics", "-metricsSeconds", "30" }).Enabled);
            Assert.IsFalse(PcMetricsOptions.Parse(null).Enabled);
        }

        [Test]
        public void Options_FullCommandLine()
        {
            var o = PcMetricsOptions.Parse(new[]
            {
                "Kamion.exe", "-tier", "High", "-METRICS", @"C:\m\run 1", "-metricsSeconds", "120.5", "-metricsWarmup", "10",
                "-metricsStart", "boot", "-scene", "knyszyn", "-metricsVsync", "0", "-metricsQuit", "0", "-metricsMaxFps", "500",
                "-metricsTimeout", "60", "-metricsLabel", "zalecany",
            });
            Assert.IsTrue(o.Enabled);
            Assert.AreEqual(@"C:\m\run 1", o.OutputDirectory);
            Assert.AreEqual(120.5f, o.Seconds);
            Assert.AreEqual(10f, o.WarmupSeconds);
            Assert.AreEqual(PcMetricsStart.Boot, o.Start);   // explicit start wins over -scene
            Assert.AreEqual(0, o.VSync);
            Assert.IsFalse(o.QuitWhenDone);
            Assert.AreEqual(500, o.MaxFps);
            Assert.AreEqual(60f, o.TimeoutSeconds);
            Assert.AreEqual("zalecany", o.Label);
        }

        [Test]
        public void Options_SceneImpliesRegionStart_DefaultsOtherwise()
        {
            var o = PcMetricsOptions.Parse(new[] { "k.exe", "-metrics", "out", "-scene", "knyszyn" });
            Assert.AreEqual(PcMetricsStart.Region, o.Start);
            Assert.AreEqual(PcMetricsOptions.DefaultSeconds, o.Seconds);
            Assert.AreEqual(PcMetricsOptions.DefaultWarmup, o.WarmupSeconds);
            Assert.AreEqual(-1, o.VSync);
            Assert.IsTrue(o.QuitWhenDone);

            var b = PcMetricsOptions.Parse(new[] { "k.exe", "-metrics", "out" });
            Assert.AreEqual(PcMetricsStart.Boot, b.Start);
        }

        [Test]
        public void Options_InvalidValuesIgnored_WarmupNotLongerThanWindow()
        {
            var o = PcMetricsOptions.Parse(new[]
            {
                "k.exe", "-metrics", "out", "-metricsSeconds", "-5", "-metricsVsync", "2", "-metricsStart", "later", "-metricsMaxFps", "abc",
            });
            Assert.AreEqual(PcMetricsOptions.DefaultSeconds, o.Seconds);
            Assert.AreEqual(-1, o.VSync);
            Assert.AreEqual(PcMetricsStart.Boot, o.Start);
            Assert.AreEqual(PcMetricsOptions.DefaultMaxFps, o.MaxFps);

            var w = PcMetricsOptions.Parse(new[] { "k.exe", "-metrics", "out", "-metricsSeconds", "4", "-metricsWarmup", "5" });
            Assert.AreEqual(0f, w.WarmupSeconds);
        }

        [Test]
        public void Options_ParsingIsCultureInvariant()
        {
            var prev = System.Threading.Thread.CurrentThread.CurrentCulture;
            try
            {
                System.Threading.Thread.CurrentThread.CurrentCulture = new System.Globalization.CultureInfo("pl-PL");
                var o = PcMetricsOptions.Parse(new[] { "k.exe", "-metrics", "out", "-metricsSeconds", "30.5" });
                Assert.AreEqual(30.5f, o.Seconds);
            }
            finally { System.Threading.Thread.CurrentThread.CurrentCulture = prev; }
        }
    }
}
