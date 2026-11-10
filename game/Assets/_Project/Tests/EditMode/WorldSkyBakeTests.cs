using Game.Rendering;
using Game.Rendering.Editor;
using NUnit.Framework;
using UnityEngine;
using static Game.Rendering.Editor.GroundSkyBakeMath;

namespace Game.Tests
{
    /// <summary>ADR 0064: grid math of the baked ground sky visibility / sun visibility and the runtime switches.</summary>
    public class WorldSkyBakeTests
    {
        const int N = 96;

        static BakeGrid FlatGround()
        {
            var g = new BakeGrid(0f, 0f, N, N, 1f);
            for (int i = 0; i < g.Ground.Length; i++) { g.Ground[i] = 0f; g.Top[i] = 0f; }
            return g;
        }

        // Solid block x in [x0, x1), z in [z0, z1) of height h.
        static void Block(BakeGrid g, int x0, int x1, int z0, int z1, float h)
        {
            for (int z = z0; z < z1; z++)
                for (int x = x0; x < x1; x++) g.Top[z * g.W + x] = h;
        }

        [Test]
        public void OpenGround_SeesTheWholeSky()
        {
            var g = FlatGround();
            var vis = SkyVisibility(g);
            Assert.That(vis[48 * N + 48], Is.GreaterThan(0.98f));
        }

        [Test]
        public void FootOfALongTallWall_SeesAboutHalfTheSky()
        {
            var g = FlatGround();
            Block(g, 0, N, 50, 51, 40f);            // 40 m high wall along x at z = 50
            var vis = SkyVisibility(g);
            float foot = vis[49 * N + 48];          // texel next to the wall
            float far = vis[10 * N + 48];           // 40 m away: horizon 45 deg over half the azimuths
            Assert.That(foot, Is.InRange(0.38f, 0.6f), "foot " + foot);
            Assert.That(far, Is.GreaterThan(foot + 0.15f), "far " + far);
            Assert.That(far, Is.LessThan(0.95f));
        }

        [Test]
        public void UnderATreeCrown_IsDarkButNotBlack()
        {
            var g = FlatGround();
            Disc(g, 48.5f, 48.5f, 4f, 3f, 10f);
            var vis = SkyVisibility(g);
            float under = vis[48 * N + 48];
            Assert.That(under, Is.InRange(0.08f, 0.4f), "under " + under);
            Assert.That(vis[10 * N + 10], Is.GreaterThan(0.95f));
        }

        [Test]
        public void SunShadowOfAWall_HasTheRightLength()
        {
            var g = FlatGround();
            Block(g, 0, N, 70, 72, 10f);            // 10 m wall, sun from the north (+z) at 30 deg: shadow 17.3 m
            float el = 30f * Mathf.Deg2Rad;
            var sun = new Vector3(0f, Mathf.Sin(el), Mathf.Cos(el));
            var s = SunVisibility(g, sun);
            Assert.That(s[65 * N + 48], Is.EqualTo(0f), "5 m from the wall");
            Assert.That(s[56 * N + 48], Is.EqualTo(0f), "14 m from the wall");
            Assert.That(s[45 * N + 48], Is.EqualTo(1f), "25 m from the wall");
            Assert.That(s[80 * N + 48], Is.EqualTo(1f), "sun side");
        }

        [Test]
        public void SunThroughACrown_IsDappledNotBlack()
        {
            var g = FlatGround();
            Disc(g, 48.5f, 52.5f, 3f, 3f, 9f);
            var sun = new Vector3(0f, 1f, 1f).normalized;   // 45 deg from the north
            var s = SunVisibility(g, sun);
            float shade = s[46 * N + 48];
            Assert.That(shade, Is.InRange(0.03f, 0.6f), "shade " + shade);
        }

        [Test]
        public void NormaliseToRoads_MakesTheMedianRoadOne_AndKeepsContactContrast()
        {
            var g = FlatGround();
            var vis = new float[g.Ground.Length];
            for (int i = 0; i < vis.Length; i++) vis[i] = 0.9f;
            for (int x = 0; x < N; x++) g.Road[20 * N + x] = true;
            vis[40 * N + 40] = 0.45f;
            float med = NormaliseToRoads(g, vis);
            Assert.That(med, Is.EqualTo(0.9f).Within(1e-5f));
            Assert.That(vis[20 * N + 5], Is.EqualTo(1f).Within(1e-5f));
            Assert.That(vis[40 * N + 40], Is.EqualTo(0.5f).Within(1e-4f));
        }

        [Test]
        public void Runtime_SunChannelFollowsTheBakedDirectionOnly()
        {
            var go = new GameObject("gi");
            try
            {
                var c = go.AddComponent<WorldSkyVisibility>();
                var low = new Vector3(0.5f, 0.16f, 0.85f).normalized;
                var clear = new Vector3(-0.25f, 0.67f, -0.7f).normalized;
                c.sunDirs = new[] { low, clear };
                Assert.That(c.SunWeights(low), Is.EqualTo(new Vector2(1f, 0f)));
                Assert.That(c.SunWeights(clear), Is.EqualTo(new Vector2(0f, 1f)));
                var off = Quaternion.AngleAxis(10f, Vector3.up) * low;
                Assert.That(c.SunWeights(off), Is.EqualTo(Vector2.zero));
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void LaunchArgs_SwitchTheBakeOffPerTier()
        {
            try
            {
                RenderOverrides.Parse(k => k == "rq_worldgi" ? "0" : k == "rq_worldsun" ? "0" : null);
                var t = RenderOverrides.ApplyTo(default(QualityProfile.Tier));
                Assert.That(t.worldSkyVisOff, Is.True);
                Assert.That(t.worldBakedSunOff, Is.True);
                Assert.That(default(QualityProfile.Tier).worldSkyVisOff, Is.False, "tiers saved before ADR 0064 keep it on");
            }
            finally { RenderOverrides.Parse(_ => null); }
        }
    }
}
