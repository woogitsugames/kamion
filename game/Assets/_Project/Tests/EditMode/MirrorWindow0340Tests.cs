using Game.Cameras;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0340 (D70 mirror windows as convex glass in a housing; the mirror cameras clip their own glass rim). Pure maths:
    /// the barrel map of the window glass, its rim shade, and the near clip beyond the glass bounds.
    /// </summary>
    public class MirrorWindow0340Tests
    {
        const float Aspect = 0.55f;

        [Test]
        public void Barrel_KeepsCornersAndCentre()
        {
            float k = MirrorWindowLayout.GlassCurvature;
            foreach (float s in new[] { 0f, 1f })
            foreach (float t in new[] { 0f, 1f })
            {
                Vector2 uv = MirrorWindowLayout.Barrel(s, t, Aspect, k);
                Assert.AreEqual(s, uv.x, 1e-5f); Assert.AreEqual(t, uv.y, 1e-5f);
            }
            Vector2 c = MirrorWindowLayout.Barrel(0.5f, 0.5f, Aspect, k);
            Assert.AreEqual(0.5f, c.x, 1e-6f); Assert.AreEqual(0.5f, c.y, 1e-6f);
        }

        [Test]
        public void Barrel_StaysInsideTexture_IsMonotonic_AndMagnifiesTheCentre()
        {
            float k = MirrorWindowLayout.GlassCurvature;
            for (int j = 0; j <= 20; j++)
            {
                float prev = -1f;
                for (int i = 0; i <= 20; i++)
                {
                    Vector2 uv = MirrorWindowLayout.Barrel(i / 20f, j / 20f, Aspect, k);
                    Assert.That(uv.x, Is.InRange(-1e-5f, 1f + 1e-5f)); Assert.That(uv.y, Is.InRange(-1e-5f, 1f + 1e-5f));
                    Assert.Greater(uv.x, prev, "no fold-over across the glass");
                    prev = uv.x;
                }
            }
            // Centre magnification = 1 / scale at r = 0 = 1 + k (1 + aspect^2): visible, not a fisheye.
            float span = MirrorWindowLayout.Barrel(0.55f, 0.5f, Aspect, k).x - MirrorWindowLayout.Barrel(0.45f, 0.5f, Aspect, k).x;
            float mag = 0.1f / span;
            Assert.That(mag, Is.InRange(1.03f, 1.15f), "centre magnification " + mag);
            // k = 0 is the identity (the flat picture).
            Vector2 id = MirrorWindowLayout.Barrel(0.3f, 0.8f, Aspect, 0f);
            Assert.AreEqual(0.3f, id.x, 1e-6f); Assert.AreEqual(0.8f, id.y, 1e-6f);
        }

        [Test]
        public void GlassShade_ClearMiddle_DarkerRim_Bounded()
        {
            float v = MirrorWindowLayout.GlassVignette;
            Assert.AreEqual(1f, MirrorWindowLayout.GlassShade(0.5f, 0.5f, v), 1e-6f);
            Assert.AreEqual(1f, MirrorWindowLayout.GlassShade(0.5f, 0.75f, v), 1e-6f, "the middle of the glass is not dimmed");
            Assert.AreEqual(1f - v, MirrorWindowLayout.GlassShade(0f, 0f, v), 1e-5f);
            Assert.Less(MirrorWindowLayout.GlassShade(0f, 0.5f, v), 1f);
            Assert.That(v, Is.InRange(0.1f, 0.4f), "a lip shadow, the view stays usable (D70)");
        }

        [Test]
        public void NearClipBeyondGlass_PassesTheWholeTiltedGlass()
        {
            // Camera 1.2 m behind a 0.20 x 0.39 m glass tilted 25 deg about the vertical axis.
            Vector3 cam = Vector3.zero, fwd = Vector3.forward;
            var rot = Quaternion.Euler(0f, 25f, 0f);
            Vector3 centre = new Vector3(0.03f, 0f, 1.2f);
            var b = new Bounds(centre, Vector3.zero);
            float far = 0f;
            foreach (float x in new[] { -0.1f, 0.1f })
            foreach (float y in new[] { -0.195f, 0.195f })
            {
                Vector3 p = centre + rot * new Vector3(x, y, 0f);
                b.Encapsulate(p);
                far = Mathf.Max(far, Vector3.Dot(p - cam, fwd));
            }
            float near = MirrorOptics.NearClipBeyondGlass(cam, fwd, b);
            Assert.Greater(near, far + 0.009f, "past the far glass edge and the 9 mm rim");
            Assert.Less(near, far + 0.05f, "no more than a few centimetres of the scene in front of the glass are cut");
            // The old plane (2 % in front of the glass centre) cut through the glass: the rim crossed it.
            Assert.Less(MirrorOptics.NearClipFor(2, Vector3.Distance(cam, centre)), far);
            Assert.AreEqual(0.1f, MirrorOptics.NearClipBeyondGlass(cam, fwd, new Bounds(new Vector3(0f, 0f, 0.01f), Vector3.zero)), 1e-6f, "floor");
        }
    }
}
