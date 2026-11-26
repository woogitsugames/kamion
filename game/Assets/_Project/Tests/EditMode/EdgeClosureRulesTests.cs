using Game.World.Streaming;
using NUnit.Framework;

namespace Game.Tests
{
    public class EdgeClosureRulesTests
    {
        [TestCase(null, "knyszyn", true, null, true)]
        [TestCase("", "knyszyn", true, null, true)]
        [TestCase("0", "knyszyn", true, null, false)]
        [TestCase(null, "knyszyn", false, null, false)]
        [TestCase(null, "knyszyn-w", true, null, false)]
        [TestCase("1", "other", false, null, true)]
        [TestCase(null, "knyszyn", true, false, false)]
        [TestCase("0", "knyszyn", true, true, true)]
        [TestCase(null, null, true, null, false)]
        [TestCase(null, "unknown", true, null, false)]
        [TestCase("invalid", "knyszyn", true, null, false)]
        [TestCase("1", "knyszyn", true, false, false)]
        public void FlaggedDesktopStartLoadsRealNeighbours_ExplicitChoiceWins(
            string argument, string region, bool desktop, bool? forced, bool expected)
        {
            var graph = TileGraph.FromJson("{\"schema\":\"truck-sim-pl/tile-graph/1\",\"tiles\":[" +
                "{\"id\":\"knyszyn\",\"needsNeighbourContext\":true},{\"id\":\"knyszyn-w\"}]}");
            Assert.AreEqual(expected, EdgeClosureRules.StreamingRequested(argument, region, desktop, forced, graph));
        }

        [Test]
        public void NeighbourContextComesFromMetadata_RegardlessOfRegionName()
        {
            var graph = TileGraph.FromJson("{\"schema\":\"truck-sim-pl/tile-graph/1\",\"tiles\":[" +
                "{\"id\":\"synthetic\",\"needsNeighbourContext\":true},{\"id\":\"knyszyn\"}]}");
            Assert.IsTrue(EdgeClosureRules.NeedsNeighbourContext(graph, "synthetic"));
            Assert.IsTrue(EdgeClosureRules.StreamingRequested(null, "synthetic", true, null, graph));
            Assert.IsFalse(EdgeClosureRules.NeedsNeighbourContext(graph, "knyszyn"), "old graphs default to false");
            Assert.IsFalse(EdgeClosureRules.NeedsNeighbourContext(graph, "unknown"));
            Assert.IsFalse(EdgeClosureRules.NeedsNeighbourContext(null, "knyszyn"));
            Assert.IsFalse(EdgeClosureRules.StreamingRequested(null, "knyszyn", true, null));
            Assert.IsTrue(EdgeClosureRules.StreamingRequested("1", "unknown", false, null));
            Assert.IsTrue(EdgeClosureRules.StreamingRequested(null, "unknown", false, true));
        }

        [TestCase(TileSide.N, false)]
        [TestCase(TileSide.E, false)]
        [TestCase(TileSide.S, true)]
        [TestCase(TileSide.W, true)]
        public void FarField_ReservesCardinalAndCornerNeighboursBeforeLoading(TileSide sector, bool visible)
        {
            Assert.AreEqual(visible, EdgeSides.FarSectorMayShow(sector, new[] { TileSide.NE }));
            Assert.AreEqual(visible, EdgeSides.FarSectorMayShow(sector, new[] { TileSide.N, TileSide.E }));
        }

        [Test]
        public void FarField_DoesNotPopWhenNeighbourLoadsOrUnloads()
        {
            var graph = new TileGraph(new TileGraphData { schema = TileGraph.Schema, tiles = new[] {
                new TileData { id = "owner", xmin = 0, ymin = 0, xmax = 2048, ymax = 2048,
                    neighbors = new[] { new NeighborData { id = "next", side = "N", seamM = 2048 } } },
                new TileData { id = "next", xmin = 0, ymin = 2048, xmax = 2048, ymax = 4096 }
            } });
            var policy = new StreamingPolicy(graph, new StreamingSettings());
            foreach (var state in new[] { TileState.Unloaded, TileState.Loading, TileState.Activating,
                                         TileState.Ready, TileState.Unloading, TileState.Unloaded })
            {
                policy.SetState(1, state);
                Assert.IsFalse(EdgeSides.FarSectorMayShow(TileSide.N, graph.NeighborSides[0]), state.ToString());
                Assert.IsTrue(EdgeSides.FarSectorMayShow(TileSide.S, graph.NeighborSides[0]), state.ToString());
            }
            Assert.IsTrue(EdgeSides.FarSectorMayShow(TileSide.N, System.Array.Empty<TileSide>()));
            Assert.IsTrue(EdgeSides.FarSectorMayShow(TileSide.None, new[] { TileSide.NE }));
        }

        [Test]
        public void QaNeighbours_OnlyEdgeNeighboursBehindClosedSides()
        {
            // dw671-tykocin-03 layout: E and S edge neighbours, NE / SW corners; the route closes N (outer) and S.
            var graph = TileGraph.FromJson("{\"schema\":\"truck-sim-pl/tile-graph/1\",\"tiles\":[" +
                "{\"id\":\"t03\",\"neighbors\":[{\"id\":\"t02\",\"side\":\"E\",\"seamM\":2048},{\"id\":\"t04\",\"side\":\"S\",\"seamM\":2048}," +
                "{\"id\":\"t01\",\"side\":\"NE\",\"seamM\":0},{\"id\":\"t05\",\"side\":\"SW\",\"seamM\":0}]}," +
                "{\"id\":\"t01\"},{\"id\":\"t02\"},{\"id\":\"t04\"},{\"id\":\"t05\"}]}");
            int t03 = graph.IndexOf("t03");
            CollectionAssert.AreEqual(new[] { "t04" }, EdgeClosureRules.QaNeighbourIds(graph, t03, TileSide.N | TileSide.S));
            CollectionAssert.AreEqual(new[] { "t02", "t04" }, EdgeClosureRules.QaNeighbourIds(graph, t03, TileSide.S | TileSide.E));
            CollectionAssert.IsEmpty(EdgeClosureRules.QaNeighbourIds(graph, t03, TileSide.W), "outer edge stays closed");
            CollectionAssert.IsEmpty(EdgeClosureRules.QaNeighbourIds(graph, t03, TileSide.None));
            CollectionAssert.IsEmpty(EdgeClosureRules.QaNeighbourIds(graph, -1, TileSide.S));
            CollectionAssert.IsEmpty(EdgeClosureRules.QaNeighbourIds(null, 0, TileSide.S));
        }

        [TestCase(TileState.Unloaded, false)]
        [TestCase(TileState.Loading, false)]
        [TestCase(TileState.Activating, false)]
        [TestCase(TileState.Ready, true)]
        [TestCase(TileState.Unloading, false)]
        public void Seam_OpensAsSoonAsNeighbourIsReady_BeforeVehicleCrosses(TileState neighbour, bool expected)
        {
            Assert.AreEqual(expected, EdgeClosureRules.SeamReady(TileState.Ready, neighbour, true, false));
            Assert.IsFalse(EdgeClosureRules.SeamReady(TileState.Activating, neighbour, true, false));
            Assert.IsFalse(EdgeClosureRules.SeamReady(TileState.Ready, neighbour, false, false));
            Assert.IsFalse(EdgeClosureRules.SeamReady(TileState.Ready, neighbour, true, true));
        }

        [Test]
        public void NearbyClosuresOnDifferentSides_OpenIndependently()
        {
            // Both formerly fit into one 150 m cluster at the NE corner. Only the northern tile is ready.
            var north = EdgeSides.ClosureSide(984f, 964f, 0f, -1024f, -1024f, 1024f, 1024f);
            var east = EdgeSides.ClosureSide(964f, 984f, 90f, -1024f, -1024f, 1024f, 1024f);
            Assert.IsTrue(EdgeClosureRules.IsOpen(north, TileSide.N));
            Assert.IsFalse(EdgeClosureRules.IsOpen(east, TileSide.N));
            Assert.IsFalse(EdgeClosureRules.IsOpen(north, TileSide.None), "unloading closes the seam again");
            Assert.IsFalse(EdgeClosureRules.IsOpen(TileSide.None, TileSide.NE));
        }

        [TestCase("col_concrete", true, 1f, 0)] // roof of collision_building, 10-20 m above road
        [TestCase("col_asphalt", false, 1f, 0)] // another tile, overlapping in the import scene
        [TestCase("Closure_00", true, 1f, 0)]
        [TestCase("col_asphalt", true, 0.1f, 0)]
        [TestCase("col_terrain", true, 1f, 1)]
        [TestCase("col_asphalt", true, 1f, 2)]
        [TestCase("col_paving_stones", true, 1f, 2)]
        public void HeightSources_RejectRoofsObstaclesAndOtherTiles(string name, bool own, float normalY, int rank)
        {
            Assert.AreEqual(rank, EdgeClosureRules.HeightPriority(name, own, normalY));
        }

        [TestCase(false)]
        [TestCase(true)]
        public void RoadElevation_WinsOverTerrainAndRoof_RegardlessOfRaycastOrder(bool reverse)
        {
            string[] names = { "col_terrain", "col_concrete", "col_asphalt", "col_asphalt" };
            float[] heights = { 140f, 160f, 141f, 190f };
            int bestRank = 0;
            float y = float.NegativeInfinity;
            for (int j = 0; j < names.Length; j++)
            {
                int i = reverse ? names.Length - 1 - j : j;
                int rank = EdgeClosureRules.HeightPriority(names[i], i != 3, 1f);
                EdgeClosureRules.ConsiderHeight(rank, heights[i], ref bestRank, ref y);
            }
            Assert.AreEqual(2, bestRank);
            Assert.AreEqual(141f, y);
            EdgeClosureRules.ConsiderHeight(2, float.NaN, ref bestRank, ref y);
            Assert.AreEqual(141f, y);
        }

        [Test]
        public void TerrainFallback_AndMissingSurface_DoNotInventAHeight()
        {
            int rank = 0;
            float y = float.NegativeInfinity;
            EdgeClosureRules.ConsiderHeight(0, 160f, ref rank, ref y);
            Assert.AreEqual(0, rank);
            EdgeClosureRules.ConsiderHeight(1, 139.5f, ref rank, ref y);
            Assert.AreEqual(1, rank);
            Assert.AreEqual(139.5f, y);
        }

        [Test]
        public void AbsoluteElevation_IsStableAcrossDifferentTileAnchorsAndHorizontalRebase()
        {
            var a = TilePlacement.For(750000, 590000, 137, 750000, 590000, 137);
            var b = TilePlacement.For(750000, 590000, 137, 752048, 590000, 155);
            const float roadElevation = 142f;
            Assert.AreEqual(5f, a.posY + roadElevation);
            Assert.AreEqual(5f, b.posY + roadElevation);
            var rebased = TilePlacement.For(752048, 590000, 137, 752048, 590000, 155);
            Assert.AreEqual(b.posY + roadElevation, rebased.posY + roadElevation);
        }
    }
}
