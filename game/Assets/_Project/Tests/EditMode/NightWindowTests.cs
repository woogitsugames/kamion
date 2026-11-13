using Game.Rendering;
using Game.Rendering.Editor;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0192: lit windows (shares, data textures, material flags), twilight horizon without magenta, lamp glare mesh.</summary>
    public class NightWindowTests
    {
        [Test]
        public void SwitchOn_OffByDay_FullAtDusk_Monotone()
        {
            Assert.AreEqual(0f, NightWindows.SwitchOn(20f), 1e-6f);
            Assert.AreEqual(0f, NightWindows.SwitchOn(4f), 1e-6f);
            Assert.AreEqual(1f, NightWindows.SwitchOn(-6f), 1e-6f);
            float prev = -1f;
            for (float e = 6f; e >= -20f; e -= 0.5f)
            {
                float s = NightWindows.SwitchOn(e);
                Assert.GreaterOrEqual(s, prev - 1e-6f, $"switch-on not monotone at {e}");
                prev = s;
            }
        }

        [Test]
        public void Shares_PlausibleAtDuskAndNight()
        {
            var dusk = NightWindows.BaseShares(-6f);
            var night = NightWindows.BaseShares(-18f);
            Assert.That(dusk.x, Is.InRange(0.3f, 0.6f), "flats lit at the end of civil twilight");
            Assert.That(dusk.y, Is.GreaterThan(night.y), "offices empty later");
            Assert.That(night.x, Is.GreaterThanOrEqualTo(dusk.x), "more flats lit later");
            for (int i = 0; i < 4; i++) Assert.That(dusk[i], Is.InRange(0f, 1f));
        }

        [Test]
        public void NightData_TexturesLoadWithExactIdTexels()
        {
            foreach (var n in new[] { "Night/T_NightAtlasId", "Night/T_NightFarId" })
            {
                var t = Resources.Load<Texture2D>(n);
                Assert.IsNotNull(t, n);
                Assert.AreEqual(FilterMode.Point, t.filterMode, n + ": the id must be point sampled");
                Assert.AreEqual(1, t.mipmapCount, n + ": no mips on the id");
                Assert.AreEqual(TextureFormat.RGBA32, t.format, n + ": uncompressed (block compression splits windows)");
            }
            foreach (var n in new[] { "Night/T_NightAtlasT", "Night/T_NightFarT" })
            {
                var t = Resources.Load<Texture2D>(n);
                Assert.IsNotNull(t, n);
                Assert.Greater(t.mipmapCount, 1, n + ": transmission needs mips (no shimmer)");
            }
            Assert.IsNotNull(Resources.Load<Material>("Night/M_LampGlare"));
        }

        [Test]
        public void MaterialModes()
        {
            Assert.AreEqual(1, NightWindowAssets.ModeFor("facade_atlas"));
            Assert.AreEqual(1, NightWindowAssets.ModeFor("M_facade_atlas"));
            Assert.AreEqual(2, NightWindowAssets.ModeFor("plaster_grey__far_block"));
            Assert.AreEqual(0, NightWindowAssets.ModeFor("far_field_buildings"));
            Assert.AreEqual(0, NightWindowAssets.ModeFor("glass"));
            var m = new Material(Shader.Find("Kamion/World PBR"));
            try
            {
                Assert.IsTrue(NightWindowAssets.ApplyMaterial(m, "plaster_grey__far_office"));
                Assert.IsTrue(m.IsKeywordEnabled("_NIGHTWIN"));
                Assert.AreEqual(2f, m.GetFloat("_NightWindows"));
            }
            finally { Object.DestroyImmediate(m); }
        }

        [Test]
        public void DuskSky_NoMagentaInTheLowDome_HorizonTowardSunWarm()
        {
            var m = LightingPreset.CreateDusk().CreateModel();
            int magenta = 0, n = 0;
            for (int gi = 0; gi <= 18; gi++)
            for (int zi = 0; zi <= 6; zi++)
            {
                float cosT = Mathf.Sin(zi * 4f * Mathf.Deg2Rad);            // 0..24 deg above the horizon
                var c = m.ChromaAt(cosT, gi * 10f * Mathf.Deg2Rad);
                n++;
                if (c.r > c.g * 1.03f && c.b > c.g * 1.03f) magenta++;
            }
            Assert.AreEqual(0, magenta, $"magenta chroma in {magenta}/{n} samples of the low dome");
            var h = m.ChromaAt(Mathf.Sin(2f * Mathf.Deg2Rad), 0f);
            Assert.Less(h.b, h.g, $"horizon toward the sun must be orange-yellow (B < G): {h}");
            Assert.Greater(h.r, h.g, $"horizon toward the sun warm: {h}");
        }

        [Test]
        public void SuppressMagenta_LeavesBlueAndOrangeAlone()
        {
            var blue = new Color(0.6f, 0.9f, 1.8f);
            Assert.AreEqual(blue, SkyModel.SuppressTwilightMagenta(blue, 1f, 1f));
            var orange = new Color(1.6f, 0.9f, 0.4f);
            Assert.AreEqual(orange, SkyModel.SuppressTwilightMagenta(orange, 1f, 1f));
            var pink = SkyModel.SuppressTwilightMagenta(new Color(1.3f, 0.9f, 1.2f), 1f, 1f);
            Assert.Less(pink.b, pink.g);
        }

        [Test]
        public void LampGlare_FourVerticesPerHead_OffByDay()
        {
            try
            {
                var heads = new[] { new Vector3(0, 8, 0), new Vector3(30, 8, 0), new Vector3(60, 8, 5) };
                LampGlare.Sync(heads, 3, 1f, 0.06f, new Color(1f, 0.93f, 0.82f));
                Assert.AreEqual(3, LampGlare.Count);
                Assert.AreEqual(12, LampGlare.MeshForTests.vertexCount);
                Assert.AreEqual(18, LampGlare.MeshForTests.triangles.Length);
                Assert.IsTrue(LampGlare.MeshForTests.bounds.Contains(new Vector3(60, 8, 5)));
                LampGlare.Sync(heads, 3, 0f, 0.06f, Color.white);     // lamps off: hidden, mesh kept
                Assert.AreEqual(3, LampGlare.Count);
            }
            finally { LampGlare.Dispose(); }
        }
    }
}
