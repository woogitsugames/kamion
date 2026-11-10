using Game.Rendering;
using NUnit.Framework;

namespace Game.Tests.EditMode
{
    /// <summary>ADR 0046: adaptive render scale (High) and the thermal frame-cap fallback.</summary>
    public class AdaptiveFrameControllerTests
    {
        const float Dt = 1f / 60f;

        static AdaptiveRenderScaleController NewScale() => new AdaptiveRenderScaleController { MinScale = 0.80f, MaxScale = 1.00f };

        /// <summary>Feeds frames for <paramref name="seconds"/>; GPU time follows the pixel model gpuAtFull · scale².</summary>
        static float Run(AdaptiveRenderScaleController c, ref float t, float seconds, float gpuAtFullMs, int fps = 60)
        {
            int n = (int)(seconds / Dt);
            for (int i = 0; i < n; i++) { t += Dt; c.AddFrame(t, gpuAtFullMs * c.Scale * c.Scale, fps); }
            return c.Scale;
        }

        [Test]
        public void StaysAtFullScaleWhenGpuIsBelow13ms()
        {
            var c = NewScale(); float t = 0f;
            Assert.AreEqual(1.00f, Run(c, ref t, 20f, 12.0f), 1e-4f);
            Assert.AreEqual(0, c.Changes);
        }

        [Test]
        public void HoldsInTheHysteresisBand()
        {
            var c = NewScale(); float t = 0f;
            Assert.AreEqual(1.00f, Run(c, ref t, 20f, 14.5f), 1e-4f);   // 13 < p90 < 15: no change
        }

        [Test]
        public void StepsDownWhenOverBudgetAndNeverBelowFloor()
        {
            var c = NewScale(); float t = 0f;
            float s = Run(c, ref t, 2.2f, 16.5f);
            Assert.Less(s, 1.0f);
            Assert.AreEqual(0f, (s / 0.05f) - UnityEngine.Mathf.Round(s / 0.05f), 1e-3f, "scale is a multiple of 0.05");
            Assert.AreEqual(0.80f, Run(c, ref t, 30f, 40f), 1e-4f, "clamped at the floor");
        }

        [Test]
        public void ChangesAtMostOncePerWindow()
        {
            var c = NewScale(); float t = 0f;
            Run(c, ref t, 1.9f, 30f);
            Assert.AreEqual(0, c.Changes, "no change inside the first 2 s window");
            Run(c, ref t, 10f, 30f);
            Assert.LessOrEqual(c.Changes, 6);
        }

        [Test]
        public void ConvergesWithoutPingPong()
        {
            var c = NewScale(); float t = 0f;
            Run(c, ref t, 20f, 17.0f);                   // 17 ms at 1.0 -> settles where p90 is in the band
            int changes = c.Changes;
            float s = c.Scale;
            Run(c, ref t, 60f, 17.0f);
            Assert.AreEqual(changes, c.Changes, "stable load: no further changes");
            Assert.AreEqual(s, c.Scale, 1e-4f);
            float gpu = 17f * s * s;
            Assert.Less(gpu, 15f); Assert.Greater(s, 0.80f - 1e-4f);
        }

        [Test]
        public void RecoversToFullScaleWhenLoadDrops()
        {
            var c = NewScale(); float t = 0f;
            Run(c, ref t, 20f, 20f);
            Assert.Less(c.Scale, 1.0f);
            Assert.AreEqual(1.00f, Run(c, ref t, 30f, 10f), 1e-4f);
        }

        [Test]
        public void NoGpuTimingsKeepTheTierScale()
        {
            var c = NewScale(); float t = 0f;
            for (int i = 0; i < 600; i++) { t += Dt; c.AddFrame(t, 0f, 60); }
            Assert.AreEqual(1.00f, c.Scale, 1e-4f);
        }

        [Test]
        public void ThresholdsFollowTheFrameCap()
        {
            var c = NewScale(); float t = 0f;
            Assert.AreEqual(1.00f, Run(c, ref t, 20f, 20f, fps: 30), 1e-4f, "20 ms is fine at a 30 FPS cap");
        }

        [Test]
        public void ThermalFallbackAfter30sAtStatus2AndRecoveryAfter60sAtOrBelow1()
        {
            var g = new ThermalFpsGovernor();
            float t = 0f;
            int fps = 60;
            for (; t < 29f; t += 0.5f) fps = g.Update(t, 2, 60);
            Assert.AreEqual(60, fps, "not yet 30 s");
            for (; t < 31f; t += 0.5f) fps = g.Update(t, 3, 60);
            Assert.AreEqual(30, fps);
            for (; t < 60f; t += 0.5f) fps = g.Update(t, 1, 60);
            Assert.AreEqual(30, fps, "cool for < 60 s");
            fps = g.Update(t, 2, 60);                                  // warm again: recovery timer restarts
            float coolStart = t + 0.5f;
            for (t = coolStart; t < coolStart + 59f; t += 0.5f) fps = g.Update(t, 0, 60);
            Assert.AreEqual(30, fps);
            for (; t < coolStart + 61f; t += 0.5f) fps = g.Update(t, 0, 60);
            Assert.AreEqual(60, fps);
        }

        [Test]
        public void ThermalShortSpikeDoesNotThrottle()
        {
            var g = new ThermalFpsGovernor();
            int fps = 60;
            for (float t = 0f; t < 120f; t += 1f) fps = g.Update(t, (int)t % 40 < 20 ? 2 : 1, 60);   // 20 s hot, 20 s cool
            Assert.AreEqual(60, fps);
            Assert.IsFalse(g.Throttled);
        }

        [Test]
        public void ThermalIgnoresA30FpsRequestAndUnknownStatus()
        {
            var g = new ThermalFpsGovernor();
            Assert.AreEqual(30, g.Update(0f, 3, 30));
            Assert.AreEqual(60, g.Update(100f, null, 60));
            Assert.IsFalse(g.Throttled);
        }
    }
}
