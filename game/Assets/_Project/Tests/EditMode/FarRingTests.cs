using Game.World.Streaming;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0354: far field as a ring beyond the loaded tiles (C# twin of KamionFarRing.hlsl + sector cull).</summary>
    public class FarRingTests
    {
        const float H = 1024f;

        // Tile rectangle centred at (cx, cz), 2048 m.
        static Vector4 Tile(float cx, float cz) => new Vector4(cx - H, cz - H, cx + H, cz + H);

        [Test]
        public void NoLoadedTiles_NothingIsHidden()
        {
            Assert.IsFalse(FarRing.Hidden(1500f, 0f, 0f, 0f, new Vector4[FarRing.MaxRects], 0));
            Assert.IsFalse(FarRing.Hidden(1500f, 0f, 0f, 0f, null, 3));
            Assert.IsTrue(FarRing.SectorVisible(new Vector4(1024f, -1024f, 1684f, 1024f), 0f, 0f, null, 0));
        }

        [Test]
        public void FarFieldInsideALoadedNeighbour_IsHidden_BeyondItShows()
        {
            // A at the origin, B east of it, both loaded: A's east band (1024..1684) lies in B.
            var rects = new[] { Tile(0f, 0f), Tile(2048f, 0f) };
            Assert.IsTrue(FarRing.Hidden(1200f, 0f, 0f, 0f, rects, 2), "A's backdrop over B's real geometry");
            Assert.IsTrue(FarRing.Hidden(1030f, 500f, 0f, 0f, rects, 2), "just past the seam");
            // A's west band: nothing loaded there - shows.
            Assert.IsFalse(FarRing.Hidden(-1300f, 0f, 0f, 0f, rects, 2));
            // B's own far field beyond B (east): shows; beyond A (west) it is A's spot.
            Assert.IsFalse(FarRing.Hidden(3300f, 0f, 2048f, 0f, rects, 2));
            Assert.IsTrue(FarRing.Hidden(-1300f, 0f, 2048f, 0f, rects, 2));
        }

        [Test]
        public void CollinearBorders_NearestTileOwnsTheBand_NoDuplicate()
        {
            // A and B side by side; north of B belongs to B (A's NE-corner backdrop there is dropped), north of A to A.
            var rects = new[] { Tile(0f, 0f), Tile(2048f, 0f) };
            Assert.IsTrue(FarRing.Hidden(1500f, 1300f, 0f, 0f, rects, 2), "A's NE corner content north of B");
            Assert.IsFalse(FarRing.Hidden(1500f, 1300f, 2048f, 0f, rects, 2), "B draws north of B");
            Assert.IsFalse(FarRing.Hidden(500f, 1300f, 0f, 0f, rects, 2), "A draws north of A");
            Assert.IsTrue(FarRing.Hidden(500f, 1300f, 2048f, 0f, rects, 2), "B's NW corner content north of A");
            // Exactly one of the two draws at every probe north of the pair (except the tie line x = 1024).
            for (float x = -1500f; x <= 3500f; x += 97f)
            {
                if (Mathf.Abs(x - 1024f) < 1f) continue;
                for (float z = 1030f; z <= 1690f; z += 110f)
                {
                    bool a = !FarRing.Hidden(x, z, 0f, 0f, rects, 2), b = !FarRing.Hidden(x, z, 2048f, 0f, rects, 2);
                    Assert.AreEqual(1, (a ? 1 : 0) + (b ? 1 : 0), $"({x}, {z})");
                }
            }
        }

        [Test]
        public void DiagonalPair_SplitsAlongTheDiagonal_AndKeepsTheFreeSide()
        {
            // dw671-tykocin-03 (A) and its NE diagonal dw671-tykocin-01 (C): north of A stays A's backdrop
            // (ADR 0353: the old rule hid A's whole north sector because of C - empty fog over the fields).
            var rects = new[] { Tile(0f, 0f), Tile(2048f, 2048f) };
            Assert.IsFalse(FarRing.Hidden(-300f, 1400f, 0f, 0f, rects, 2), "north of A, far from C");
            Assert.IsTrue(FarRing.Hidden(1300f, 1300f, 0f, 0f, rects, 2), "A's NE corner content inside C");
            // Region north of A and west of C: split on the diagonal through the shared corner (1024, 1024).
            Assert.IsFalse(FarRing.Hidden(800f, 1100f, 0f, 0f, rects, 2), "nearer A");
            Assert.IsTrue(FarRing.Hidden(800f, 1100f, 2048f, 2048f, rects, 2));
            Assert.IsTrue(FarRing.Hidden(950f, 1600f, 0f, 0f, rects, 2), "nearer C");
            Assert.IsFalse(FarRing.Hidden(950f, 1600f, 2048f, 2048f, rects, 2));
        }

        [Test]
        public void OwnerRectangleComesFromTheLoadedSet_NonSquareTile()
        {
            // Owner loaded with a 3000 x 2048 rectangle: a point 1200 m east of its centre is inside it (never hidden).
            var own = new Vector4(-1500f, -1024f, 1500f, 1024f);
            var rects = new[] { own, new Vector4(1500f, -1024f, 3548f, 1024f) };
            Assert.IsFalse(FarRing.Hidden(1200f, 0f, 0f, 0f, rects, 2));
            Assert.IsTrue(FarRing.Hidden(1600f, 0f, 0f, 0f, rects, 2));
            // Not loaded itself (Unloading): +-1024 default, a loaded neighbour still takes its spot.
            Assert.IsTrue(FarRing.Hidden(1600f, 0f, 0f, 0f, new[] { rects[1] }, 1));
        }

        [Test]
        public void SectorCull_IsConservative()
        {
            var a = Tile(0f, 0f);
            var east = new Vector4(1024f, -1024f, 1684f, 1024f);     // A's east band (side part)
            var north = new Vector4(-1344f, 1024f, 1684f, 1684f);    // A's north sector incl. NE corner quadrant
            // East neighbour loaded: the side band is inside it - off.
            Assert.IsFalse(FarRing.SectorVisible(east, 0f, 0f, new[] { a, Tile(2048f, 0f) }, 2));
            // Only the diagonal NE tile loaded: most of the north band is A's - on.
            Assert.IsTrue(FarRing.SectorVisible(north, 0f, 0f, new[] { a, Tile(2048f, 2048f) }, 2));
            // North neighbour + NE + NW loaded: the band is inside them - off.
            Assert.IsFalse(FarRing.SectorVisible(north, 0f, 0f,
                new[] { a, Tile(0f, 2048f), Tile(2048f, 2048f), Tile(-2048f, 2048f) }, 4));
            // Nothing else loaded: on. Empty mesh bounds: off.
            Assert.IsTrue(FarRing.SectorVisible(north, 0f, 0f, new[] { a }, 1));
            Assert.IsFalse(FarRing.SectorVisible(new Vector4(1f, 1f, -1f, -1f), 0f, 0f, new[] { a }, 1));
        }

        [Test]
        public void SectorCull_NeverHidesASectorWithAVisiblePixel()
        {
            // Random loaded sets on the 2048 grid; whenever the cull says off, no probe of the box may be drawn.
            var rng = new System.Random(354);
            var boxes = new[]
            {
                new Vector4(-1344f, 1024f, 1684f, 1684f), new Vector4(1024f, -1684f, 1684f, 1024f),
                new Vector4(-1684f, -1684f, 1024f, -1024f), new Vector4(-1684f, -1024f, -1024f, 1684f),
            };
            for (int trial = 0; trial < 200; trial++)
            {
                var rects = new Vector4[FarRing.MaxRects];
                int n = 0;
                rects[n++] = Tile(0f, 0f);
                for (int gx = -1; gx <= 1; gx++)
                    for (int gz = -1; gz <= 1; gz++)
                        if ((gx != 0 || gz != 0) && rng.NextDouble() < 0.45) rects[n++] = Tile(gx * 2048f, gz * 2048f);
                foreach (var box in boxes)
                {
                    if (FarRing.SectorVisible(box, 0f, 0f, rects, n)) continue;
                    for (float x = box.x + 0.5f; x <= box.z; x += 37f)      // not on the owner's border itself
                        for (float z = box.y + 0.5f; z <= box.w; z += 37f)
                            Assert.IsTrue(FarRing.Hidden(x, z, 0f, 0f, rects, n), $"trial {trial}: ({x}, {z}) drawn in a culled sector");
                }
            }
        }

        [Test]
        public void Switch_CommandLineWinsOverEnvironment()
        {
            Assert.IsTrue(FarRing.ReadSwitch(null, null));
            Assert.IsFalse(FarRing.ReadSwitch(null, "off"));
            Assert.IsFalse(FarRing.ReadSwitch(new[] { "Kamion.exe", "-farRing", "off" }, null));
            Assert.IsTrue(FarRing.ReadSwitch(new[] { "Kamion.exe", "-farRing", "on" }, "off"));
            Assert.IsFalse(FarRing.ReadSwitch(new[] { "Kamion.exe", "-FARRING", "0" }, null));
            Assert.IsTrue(FarRing.ReadSwitch(new[] { "Kamion.exe", "-farRing" }, null), "dangling flag = default");
        }

        [Test]
        public void TykocinGraph_NorthOf03IsDrawnWithItsNeighboursLoaded()
        {
            // The case of ADR 0353 (auto/edge-north.png): 03 with 02 (E), 04 (S) and 01 (NE) loaded.
            var graph = TileGraph.LoadDefault();
            Assume.That(graph, Is.Not.Null);
            int i03 = graph.IndexOf("dw671-tykocin-03");
            Assume.That(i03, Is.GreaterThanOrEqualTo(0));
            var t03 = graph.Tiles[i03];
            double ox = t03.anchorX, oy = t03.anchorY;   // Unity origin at 03's anchor (QA start tile)
            var rects = new Vector4[FarRing.MaxRects];
            int n = 0;
            foreach (var id in new[] { "dw671-tykocin-03", "dw671-tykocin-02", "dw671-tykocin-04", "dw671-tykocin-01" })
            {
                var t = graph.Tiles[graph.IndexOf(id)];
                rects[n++] = new Vector4((float)(t.xmin - ox), (float)(t.ymin - oy), (float)(t.xmax - ox), (float)(t.ymax - oy));
            }
            // North band of 03, west part (forest / HV line of edge-north): drawn by 03.
            Assert.IsFalse(FarRing.Hidden(-400f, 1350f, 0f, 0f, rects, n));
            Assert.IsTrue(FarRing.SectorVisible(new Vector4(-1344f, 1024f, 1684f, 1684f), 0f, 0f, rects, n));
            // Same spot is not drawn twice by 01 (its west band reaches there): 03 is nearer.
            float c01x = (float)(graph.Tiles[graph.IndexOf("dw671-tykocin-01")].anchorX - ox);
            float c01z = (float)(graph.Tiles[graph.IndexOf("dw671-tykocin-01")].anchorY - oy);
            Assert.IsTrue(FarRing.Hidden(-400f, 1350f, c01x, c01z, rects, n));
            // 03's east band lies in 02: dropped.
            Assert.IsTrue(FarRing.Hidden(1300f, 0f, 0f, 0f, rects, n));
        }
    }
}
