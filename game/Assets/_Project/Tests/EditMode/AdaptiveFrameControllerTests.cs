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
            Assert.IsTrue(c.AtFloor);
        }

        [Test]
        public void FirstStepIs085UnderModerateLoad_HeavyLoadJumpsToTheFloor()
        {
            var d = NewScale(); float t = 0f;
            Assert.AreEqual(0.85f, Run(d, ref t, 2.2f, 17.5f), 1e-4f, "17.5 ms: the pixel model needs 0.89 -> the 0.85 first step");
            Assert.Greater(Run(d, ref t, 20f, 17.5f), 0.85f - 1e-4f, "12.6 ms at 0.85 is under budget: never drops to 0.80");
            // ADR 0062: S24+ r8 had GPU p90 25.8 ms at 1.0; the old walk needed 2 windows per step and stopped at 0.80.
            var c = NewScale(); t = 0f;
            Assert.AreEqual(0.80f, Run(c, ref t, 2.2f, 30f), 1e-4f, "30 ms at 1.0 needs 0.68: straight to the floor in one window");
            var h = new AdaptiveRenderScaleController { MinScale = 0.70f, MaxScale = 1.00f }; t = 0f;
            Assert.AreEqual(0.70f, Run(h, ref t, 2.2f, 25.8f), 1e-4f, "High floor 0.70 (D36) reached in the first window");
        }

        [Test]
        public void HighTierDefaults_D36()
        {
            QualityProfile.Tier high = default;
            foreach (var x in QualityProfile.Defaults()) if (x.name == "High") high = x;
            Assert.AreEqual(0.70f, high.adaptiveScaleMin, 1e-4f, "owner decision D36: High floor 0.70");
            Assert.AreEqual(UnityEngine.Rendering.Universal.UpscalingFilterSelection.FSR, high.upscalingFilter, "ADR 0062: FSR 1.0 below scale 1");
            Assert.AreEqual(30, high.pacingFallbackFps);
            foreach (var x in QualityProfile.Defaults())
            {
                Assert.Greater(x.lampPools, 0, x.name + ": lamp pools on every tier (review r8 N-20)");
                Assert.LessOrEqual(x.lampPools, StreetLamps.MaxPools);
                if (x.name == "Low") Assert.AreEqual(0, x.streetLights, "Low: no point lights");
            }
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

        /// <summary>Feeds the pacing governor: frames at <paramref name="frameMs"/>, GPU time <paramref name="gpuMs"/>.</summary>
        static int RunPacing(FramePacingGovernor g, ref float t, float seconds, float frameMs, float gpuMs, bool atFloor, int req = 60,
            float scale = 0.70f, float floor = 0.70f)
        {
            int fps = req;
            float dt = frameMs / 1000f;
            int n = (int)(seconds / dt);
            for (int i = 0; i < n; i++) { t += dt; fps = g.Update(t, frameMs, gpuMs, 10f, atFloor, scale, floor, req); }
            return fps;
        }

        [Test]
        public void Pacing_JudderAtTheFloorDropsTo30_NotBeforeTheScaleIsSpent()
        {
            // S24+ r8: every 3rd frame 33 ms (43-47 FPS). Alternate 16.7/16.7/33.3.
            var g = new FramePacingGovernor(); float t = 0f;
            int fps = 60;
            for (int i = 0; i < 400; i++) { float ms = i % 3 == 2 ? 33.3f : 16.7f; t += ms / 1000f; fps = g.Update(t, ms, 19f, 12f, false, 0.85f, 0.70f, 60); }
            Assert.AreEqual(60, fps, "scale not at the floor yet: the render scale acts first");
            t = 0f; g.Reset();
            float tDrop = -1f;
            for (int i = 0; i < 600; i++)
            {
                float ms = i % 3 == 2 ? 33.3f : 16.7f; t += ms / 1000f;
                fps = g.Update(t, ms, 19f, 12f, true, 0.70f, 0.70f, 60);
                if (fps == 30 && tDrop < 0f) tDrop = t;
            }
            Assert.AreEqual(30, fps);
            Assert.That(tDrop, Is.InRange(5.9f, 8.5f), "three bad 2 s windows");
        }

        [Test]
        public void Pacing_SteadyFramesNeverDrop()
        {
            var g = new FramePacingGovernor(); float t = 0f;
            Assert.AreEqual(60, RunPacing(g, ref t, 60f, 16.7f, 14f, true));
            Assert.IsFalse(g.Throttled);
        }

        [Test]
        public void Pacing_RecoversWhenTheGpuHasRoom_AndBacksOffAfterARelapse()
        {
            var g = new FramePacingGovernor(); float t = 0f;
            Assert.AreEqual(30, RunPacing(g, ref t, 8f, 33.3f, 19f, true));
            // At 30 FPS the scale climbs back to 1.0: GPU 19 ms at 1.0 projects to 9.3 ms at 0.70 (optimistic model).
            Assert.AreEqual(30, RunPacing(g, ref t, 15f, 33.3f, 19f, false, scale: 1.0f), "not before 20 s of headroom");
            Assert.AreEqual(60, RunPacing(g, ref t, 10f, 33.3f, 19f, false, scale: 1.0f), "projected 9.3 ms < 13.3 ms for 20 s");
            Assert.AreEqual(30, RunPacing(g, ref t, 8f, 33.3f, 19f, true), "relapse");
            Assert.AreEqual(40f, g.RecoverAfterS, 1e-3f, "relapse soon after a recovery doubles the wait");
            Assert.AreEqual(30, RunPacing(g, ref t, 60f, 33.3f, 30f, false, scale: 0.70f), "30 ms at the floor: stays at 30");
        }

        [Test]
        public void Pacing_IgnoresA30FpsRequest()
        {
            var g = new FramePacingGovernor(); float t = 0f;
            Assert.AreEqual(30, RunPacing(g, ref t, 20f, 50f, 40f, true, req: 30));
            Assert.IsFalse(g.Throttled);
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
