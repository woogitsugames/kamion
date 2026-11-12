using Game.Cameras;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.EditMode
{
    /// <summary>ADR 0152: the cab head-sway spring must stay stable at low frame rates (Fold Ultra / A16 High ~8-10 FPS).</summary>
    public class CameraHeadSpringTests
    {
        const float Hz = 1.8f, Zeta = 0.7f;

        /// <summary>Runs <paramref name="frames"/> frames of <paramref name="dt"/> from a 1 mm kick (desired 0); returns the
        /// largest |x| of the last 20 frames and how many of them flipped sign against the previous frame.</summary>
        static (float maxAbs, int flips) Run(float dt, bool legacy, int frames = 120)
        {
            Vector3 p = new Vector3(0.001f, 0f, 0f), v = Vector3.zero;
            float maxAbs = 0f, prev = p.x; int flips = 0;
            for (int i = 0; i < frames; i++)
            {
                CameraRig.StepHeadSpring(Vector3.zero, dt, Hz, Zeta, ref p, ref v, legacy);
                p = Vector3.ClampMagnitude(p, 0.06f);   // the rig's clamp (headMaxOffset 0.04 x 1.5)
                if (i >= frames - 20) { maxAbs = Mathf.Max(maxAbs, Mathf.Abs(p.x)); if (p.x * prev < 0f) flips++; }
                prev = p.x;
            }
            return (maxAbs, flips);
        }

        [Test]
        public void LegacyStepOscillatesEveryFrameBelowElevenFps()
        {
            // Reproduces the owner's Fold video: at 0.12 s per frame the old single step diverges, the offset
            // alternates sign every frame and sits on the 6 cm clamp.
            var r = Run(0.12f, legacy: true);
            Assert.Greater(r.maxAbs, 0.05f);
            Assert.GreaterOrEqual(r.flips, 18);
        }

        [TestCase(1f / 120f)]
        [TestCase(1f / 30f)]
        [TestCase(0.1f)]
        [TestCase(0.12f)]
        [TestCase(0.2f)]
        public void SubSteppedSpringDecaysAtAnyFrameTime(float dt)
        {
            var r = Run(dt, legacy: false);
            Assert.Less(r.maxAbs, 1e-4f);   // decays (a damped 1.8 Hz wobble may still cross zero at a few micrometres)
        }

        [Test]
        public void SubSteppingMatchesSixtyFpsResponse()
        {
            // Same settled offset for a constant braking pull whatever the frame rate (no frame-rate dependent look).
            Vector3 d = new Vector3(0f, 0f, 0.03f);
            Vector3 a = Vector3.zero, av = Vector3.zero, b = Vector3.zero, bv = Vector3.zero;
            for (int i = 0; i < 300; i++) CameraRig.StepHeadSpring(d, 1f / 60f, Hz, Zeta, ref a, ref av);
            for (int i = 0; i < 50; i++) CameraRig.StepHeadSpring(d, 0.1f, Hz, Zeta, ref b, ref bv);
            Assert.AreEqual(a.z, b.z, 1e-4f);
        }
    }
}
