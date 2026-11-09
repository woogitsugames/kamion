using Game.Core;
using NUnit.Framework;

namespace Game.Tests
{
    public class FrameTimeStatsTests
    {
        [Test]
        public void Empty_ReturnsDefault()
        {
            var s = new FrameTimeStats(10).Compute();
            Assert.AreEqual(0, s.Samples);
            Assert.AreEqual(0f, s.MeanFps);
        }

        [Test]
        public void Percentiles_NearestRank_OneToHundred()
        {
            var stats = new FrameTimeStats(100);
            for (int i = 100; i >= 1; i--) stats.Add(i); // unsorted input
            var s = stats.Compute();
            Assert.AreEqual(100, s.Samples);
            Assert.AreEqual(50f, s.P50Ms);
            Assert.AreEqual(95f, s.P95Ms);
            Assert.AreEqual(99f, s.P99Ms);
            Assert.AreEqual(100f, s.MaxMs);
            Assert.AreEqual(50.5f, s.MeanMs, 1e-4f);
        }

        [Test]
        public void RollingWindow_DropsOldestSamples()
        {
            var stats = new FrameTimeStats(4);
            stats.Add(1000f);
            for (int i = 0; i < 4; i++) stats.Add(16.6f);
            var s = stats.Compute();
            Assert.AreEqual(4, s.Samples);
            Assert.AreEqual(16.6f, s.MaxMs, 1e-4f);
            Assert.AreEqual(1000f / 16.6f, s.MeanFps, 1e-2f);
        }
    }
}
