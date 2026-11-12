using System.IO;
using Game.World;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0136: the tight impostor polygon encloses every opaque texel of every view and is much smaller than the quad.</summary>
    public class ImpostorTrimTests
    {
        [Test]
        public void SyntheticBlob_IsEnclosed_AndSmallerThanQuad()
        {
            const int views = 6, w = 32, h = 48, width = views * w;
            var a = new byte[width * h];
            for (int k = 0; k < views; k++)
                for (int y = 10; y < 40; y++)
                    for (int x = 12 + k % 2; x < 20 + k % 3; x++)
                        a[y * width + k * w + x] = 255;
            a[5 * width + 3 * w + 16] = 3;   // below the alpha floor: may be cut
            var p = ImpostorTrim.Fit(a, width, h, views, 4, 2);
            Assert.That(p.HasValue);
            Assert.That(ImpostorTrim.Encloses(p.Value, a, width, h, views));
            Assert.That(p.Value.Area, Is.LessThan(0.5f));
            Assert.That(p.Value.Uv.Length, Is.EqualTo(10));
            Assert.That(p.Value.Triangles.Length, Is.EqualTo(24));
        }

        [Test]
        public void EmptyAtlas_ReturnsNull()
        {
            Assert.That(ImpostorTrim.Fit(new byte[12 * 4], 12, 4, 6).HasValue, Is.False);
        }

        [Test]
        public void Positions_FollowShaderConvention()
        {
            var p = new ImpostorTrim.Polygon { Uv = new[] { new Vector2(0.25f, 0f), new Vector2(0.75f, 1f) }, Triangles = new int[0] };
            var pos = ImpostorTrim.Positions(p, 2f, -0.3f, 9.7f);
            Assert.That(Mathf.Abs(pos[0].x), Is.EqualTo(2f).Within(1e-5f));   // shader: (uv.x * 2 - 1) * |x|
            Assert.That(Mathf.Abs(pos[1].x), Is.EqualTo(2f).Within(1e-5f));
            Assert.That(pos[0].y, Is.EqualTo(-0.3f).Within(1e-5f));
            Assert.That(pos[1].y, Is.EqualTo(9.7f).Within(1e-5f));
        }

        [Test]
        public void ShippedImpostorAtlases_AreEnclosed()
        {
            string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "art-source", "world", "vegetation"));
            var files = Directory.Exists(dir) ? Directory.GetFiles(dir, "impostor_tree_*.png") : new string[0];
            int n = 0;
            foreach (var f in files)
            {
                if (f.EndsWith("_n.png")) continue;
                var img = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);
                Assert.That(img.LoadImage(File.ReadAllBytes(f)), f);
                var px = img.GetPixels32();
                var a = new byte[px.Length];
                for (int i = 0; i < px.Length; i++) a[i] = px[i].a;
                var p = ImpostorTrim.Fit(a, img.width, img.height, 6);
                Assert.That(p.HasValue, f);
                Assert.That(ImpostorTrim.Encloses(p.Value, a, img.width, img.height, 6), f);
                Assert.That(p.Value.Area, Is.LessThan(0.6f), f);
                Object.DestroyImmediate(img);
                n++;
            }
            if (n == 0) Assert.Ignore("art-source/world/vegetation impostor atlases not present");
        }
    }
}
