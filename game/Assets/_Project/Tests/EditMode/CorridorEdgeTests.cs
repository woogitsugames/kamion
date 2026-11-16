using System.Collections.Generic;
using Game.World.Streaming;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0273 §10 pkt 5 (D36, s23): the world safety net warns ("Koniec mapy") and stops the vehicle on the OUTER edges of
    /// the streamed corridor, not on the seams of Ready tiles. Pure logic of <see cref="CorridorEdge"/> on synthetic
    /// 2048 m tiles (frame = metres from the south-west corner of tile (0, 0)): outer edge vs seam, an L of three tiles
    /// (inner corner), an unloaded neighbour turning its seam back into an edge, drivable rectangles inset from their tiles,
    /// and zero GC per query (<see cref="GcAllocCounter"/>, ADR 0244 / PR #118 pattern).
    /// </summary>
    public class CorridorEdgeTests
    {
        const float S = 2048f;

        /// <summary>Tiles at the given (column, row) cells; neighbours (sides and corners) from the lattice, like tile_graph.py.</summary>
        static TileGraph Lattice(params (int c, int r)[] cells)
        {
            var tiles = new List<TileData>();
            foreach (var (c, r) in cells)
                tiles.Add(new TileData
                {
                    id = Id(c, r), xmin = c * S, ymin = r * S, xmax = (c + 1) * S, ymax = (r + 1) * S,
                    anchorX = (c + 0.5) * S, anchorY = (r + 0.5) * S, anchorZ = 100.0, worldMemoryMB = 50f,
                });
            var sides = new (int dc, int dr, string side)[] { (0, 1, "N"), (1, 0, "E"), (0, -1, "S"), (-1, 0, "W"), (1, 1, "NE"), (1, -1, "SE"), (-1, -1, "SW"), (-1, 1, "NW") };
            for (int i = 0; i < cells.Length; i++)
            {
                var ns = new List<NeighborData>();
                foreach (var (dc, dr, side) in sides)
                    foreach (var (c, r) in cells)
                        if (c == cells[i].c + dc && r == cells[i].r + dr)
                            ns.Add(new NeighborData { id = Id(c, r), side = side, seamM = side.Length == 1 ? S : 0f });
                tiles[i].neighbors = ns.ToArray();
            }
            return new TileGraph(new TileGraphData { schema = TileGraph.Schema, tiles = tiles.ToArray() });
        }

        static string Id(int c, int r) => "t" + c + "_" + r;

        /// <summary>Tile rectangles of the graph in the test frame; drivable = tile shrunk by <paramref name="insetM"/>.</summary>
        static void Rects(TileGraph g, float insetM, out EdgeRect[] drivable, out EdgeRect[] tile)
        {
            drivable = new EdgeRect[g.Count];
            tile = new EdgeRect[g.Count];
            for (int i = 0; i < g.Count; i++)
            {
                var t = g.Tiles[i];
                tile[i] = new EdgeRect((float)t.xmin, (float)t.ymin, (float)t.xmax, (float)t.ymax);
                drivable[i] = new EdgeRect(tile[i].minE + insetM, tile[i].minN + insetM, tile[i].maxE - insetM, tile[i].maxN - insetM);
            }
        }

        static float Inside(TileGraph g, TileState[] state, float e, float n, float insetM = 0f)
        {
            Rects(g, insetM, out var d, out var t);
            Assert.IsTrue(CorridorEdge.InsideDistance(g, state, d, t, e, n, out float inside), "some tile is Ready");
            return inside;
        }

        const TileState R = TileState.Ready, U = TileState.Unloaded;

        [Test]
        public void TwoTiles_SeamIsNotAnEdge_OuterEdgesAre()
        {
            var g = Lattice((0, 0), (1, 0));   // A west, B east: seam at e = 2048
            var ready = new[] { R, R };
            Assert.AreEqual(1000f, Inside(g, ready, S - 10f, 1000f), 1e-2f, "10 m before the seam: nearest outer edge is S (1000 m)");
            Assert.AreEqual(1000f, Inside(g, ready, S + 10f, 1000f), 1e-2f, "10 m past the seam, in B");
            Assert.AreEqual(1000f, Inside(g, ready, S, 1000f), 1e-2f, "on the seam");
            Assert.AreEqual(10f, Inside(g, ready, 1000f, S - 10f), 1e-2f, "10 m before the outer north edge of A");
            Assert.AreEqual(10f, Inside(g, ready, 2 * S - 10f, 1000f), 1e-2f, "10 m before the outer east edge of B");
            Assert.AreEqual(-5f, Inside(g, ready, 1000f, -5f), 1e-2f, "5 m beyond the outer south edge: negative");
        }

        [Test]
        public void LShape_InnerCornerIsAPoint_OuterEdgesOfEveryTileCount()
        {
            // A (0,0); B (0,1) north of A; C (1,1) east of B. (1,0) does not exist: the inner corner of the L is (2048, 2048).
            var g = Lattice((0, 0), (0, 1), (1, 1));
            var ready = new[] { R, R, R };
            Assert.AreEqual(8f, Inside(g, ready, S - 8f, 1000f), 1e-2f, "east edge of A is outer (nothing east of A)");
            Assert.AreEqual(1000f, Inside(g, ready, 1000f, S - 8f), 1e-2f, "A/B seam: not an edge");
            Assert.AreEqual(1000f, Inside(g, ready, S + 8f, S + 1000f), 1e-2f, "B/C seam: not an edge");
            Assert.AreEqual(12f, Inside(g, ready, S + 100f, S + 12f), 1e-2f, "south edge of C is outer");
            // In B next to the inner corner: B's E and S sides are open, its SE diagonal does not exist -> distance to the corner.
            Assert.AreEqual(UnityLength(8f, 12f), Inside(g, ready, S - 8f, S + 12f), 1e-2f, "inner corner of the L counts as a point");
            // In A next to the inner corner: A's east side is closed -> the edge itself (8 m), not the corner.
            Assert.AreEqual(8f, Inside(g, ready, S - 8f, S - 12f), 1e-2f);
            Assert.Less(Inside(g, ready, S + 5f, S - 5f), 0f, "the missing tile of the L is outside");
        }

        static float UnityLength(float a, float b) => (float)System.Math.Sqrt(a * a + b * b);

        [Test]
        public void UnloadedNeighbour_ItsSeamBecomesAnOuterEdge()
        {
            var g = Lattice((0, 0), (0, 1), (1, 1));
            var ready = new[] { R, R, U };   // C unloaded (left behind, not in the build, over budget)
            Assert.AreEqual(8f, Inside(g, ready, S - 8f, S + 1452f), 1e-2f, "B's east seam is an outer edge while C is not Ready");
            Assert.Less(Inside(g, ready, S + 8f, S + 1000f), 0f, "inside C's rectangle = outside the world while C is not Ready");
            Assert.AreEqual(1000f, Inside(g, ready, 1000f, S + 4f), 1e-2f, "A/B seam still open");
            ready[2] = R;
            Assert.AreEqual(596f, Inside(g, ready, S - 8f, S + 1452f), 1e-2f, "C Ready again: seam open (nearest outer edge = north, 596 m)");
            ready[0] = TileState.Unloading;   // the start tile unloading behind the truck
            Assert.AreEqual(8f, Inside(g, ready, 1000f, S + 8f), 1e-2f, "B's south seam is an outer edge once A is gone");
        }

        [Test]
        public void NeighbourOnItsWay_LoadingOrActivating_KeepsTheSeamOpen()
        {
            // The streamer is bringing the neighbour in: its closures still stand (a loading stall, not the end of the map),
            // so no "Koniec mapy" warning and no out-of-bounds stop at the seam - but its area is not drivable yet.
            var g = Lattice((0, 0), (1, 0));
            foreach (var st in new[] { TileState.Loading, TileState.Activating })
            {
                var state = new[] { R, st };
                Assert.AreEqual(1000f, Inside(g, state, S - 2f, 1000f), 1e-2f, st + ": seam open");
                Assert.Less(Inside(g, state, S + 50f, 1000f), 0f, st + ": the neighbour's area is not part of the world yet");
            }
            foreach (var st in new[] { TileState.Unloaded, TileState.Unloading })
                Assert.AreEqual(2f, Inside(g, new[] { R, st }, S - 2f, 1000f), 1e-2f, st + ": seam is an outer edge");
        }

        [Test]
        public void DrivableInset_GapAtAnOpenSeamIsInside_ClosedSideKeepsTheDrivableEdge()
        {
            var g = Lattice((0, 0), (1, 0));
            var ready = new[] { R, R };
            const float inset = 100f;   // drivable rectangles 100 m inside their tiles (gap of 200 m across the seam)
            Assert.AreEqual(1000f - inset, Inside(g, ready, S - 50f, 1000f, inset), 1e-2f, "in the gap before the seam: inside A");
            Assert.AreEqual(1000f - inset, Inside(g, ready, S + 50f, 1000f, inset), 1e-2f, "in the gap after the seam: inside B");
            Assert.AreEqual(10f, Inside(g, ready, 1000f, S - inset - 10f, inset), 1e-2f, "closed north side: the drivable edge");
            ready[1] = U;
            Assert.AreEqual(50f, Inside(g, ready, S - inset - 50f, 1000f, inset), 1e-2f, "B not Ready: A's east drivable edge");
        }

        [Test]
        public void SingleTile_MatchesTheRegionRectangle_AndNoReadyTileIsFalse()
        {
            var g = Lattice((0, 0));
            Assert.AreEqual(300f, Inside(g, new[] { R }, 300f, 1000f), 1e-2f);
            Rects(g, 0f, out var d, out var t);
            Assert.IsFalse(CorridorEdge.InsideDistance(g, new[] { TileState.Activating }, d, t, 300f, 1000f, out _), "no Ready tile");
        }

        [Test]
        public void OpenSides_And_MissingCorners_FromTheGraph()
        {
            var g = Lattice((0, 0), (0, 1), (1, 1));
            var ready = new[] { R, R, R };
            Assert.AreEqual(TileSide.N, CorridorEdge.OpenSides(g, ready, 0));
            var openB = CorridorEdge.OpenSides(g, ready, 1);
            Assert.AreEqual(TileSide.S | TileSide.E, openB);
            Assert.AreEqual(EdgeSides.CornerBit(TileSide.SE), CorridorEdge.MissingCorners(g, ready, 1, openB));
            ready[1] = U;
            Assert.AreEqual(TileSide.None, CorridorEdge.OpenSides(g, ready, 0), "an Unloaded neighbour closes the seam");
            Assert.AreEqual(TileSide.None, CorridorEdge.OpenSides(g, ready, 1), "a tile that is not Ready has no open side");
        }

        [Test]
        public void InsideDistance_AllocatesNothing()
        {
            // The shipped corridor size: 21 tiles in an L-ish chain; every 4th not Ready.
            var cells = new List<(int, int)>();
            for (int k = 0; k < 11; k++) cells.Add((0, k));
            for (int k = 1; k < 11; k++) cells.Add((k, 10));
            var g = Lattice(cells.ToArray());
            var ready = new TileState[g.Count];
            for (int i = 0; i < ready.Length; i++) ready[i] = i % 4 == 3 ? U : i % 4 == 2 ? TileState.Loading : R;
            Rects(g, 0f, out var d, out var t);
            float sink = 0f;
            void Loop()
            {
                for (int f = 0; f < 600; f++)
                    if (CorridorEdge.InsideDistance(g, ready, d, t, 1000f + f, 1000f + 30f * f, out float v)) sink += v;
            }
            GcAllocCounter.AssertZero(Loop, warmup: Loop, message: "CorridorEdge.InsideDistance must not allocate (safety-net check in the fixed step)");
            Assert.IsFalse(float.IsNaN(sink));
        }
    }
}
