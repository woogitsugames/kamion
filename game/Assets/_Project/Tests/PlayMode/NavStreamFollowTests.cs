using Game.Core.Navigation;
using Game.Gameplay;
using Game.UI.CabDisplays;
using Game.UI.Navigation;
using Game.World.Streaming;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0300: the GPS follows the streamed tile. Owner's run Bialystok -> Tykocin (s24): the minimap showed the start
    /// region's streets behind the truck and nothing under it - the GPS stayed on the start region (only that region had a
    /// map, its frame was destroyed when the region unloaded). Checks: every corridor tile has a routing graph and a map;
    /// a region switch measures the truck in the new tile's frame (on a road of its graph) and an origin rebase moves
    /// nothing; neighbour maps are drawn around the current tile; the follower's seam hysteresis.
    /// </summary>
    public class NavStreamFollowTests
    {
        const string From = "bialystok-kleeberga", To = "bialystok-knyszynska";
        // first point of the knyszynska start route (Data/Regions/bialystok-knyszynska/route_start.json, region-local)
        static readonly Vector2 k_KnyStart = new Vector2(1021.99f, -711.892f);

        GameObject m_Host, m_Truck, m_RootA, m_RootB;

        [TearDown]
        public void TearDown()
        {
            foreach (var go in new[] { m_Host, m_Truck, m_RootA, m_RootB }) if (go != null) Object.DestroyImmediate(go);
        }

        static TileGraph Graph() { var g = TileGraph.LoadDefault(); Assert.NotNull(g, "Resources/WorldStreaming/tile_graph"); return g; }

        [Test]
        public void EveryCorridorTileHasARoutingGraphAndAMap()
        {
            var g = Graph();
            var links = RouteLinks.LoadDefault(g);
            Assert.NotNull(links);
            int n = 0;
            foreach (var c in links.Corridors)
                foreach (var id in c.tiles)
                {
                    Assert.NotNull(RouteGraph.Load(id), "Resources/CabDisplay/Nav/" + id + "_route.bytes");
                    var m = NavMapData.Load(id);
                    Assert.NotNull(m, "Resources/CabDisplay/Nav/" + id + ".bytes (tools/ui/build_nav_map.py --region " + id + ")");
                    Assert.Greater(m.RoadCount, 0, id);
                    n++;
                }
            Assert.Greater(n, 20);
        }

        [Test]
        public void ShiftedMapMovesGeometryAndCombinedStaticHoldsBoth()
        {
            var a = NavMapData.Load(From);
            var b = NavMapData.Load(To);
            var off = new Vector2(-2048f, 0f);
            var s = b.Shifted(off);
            Assert.AreEqual(b.RoadPoints[0] + off, s.RoadPoints[0]);
            Assert.AreEqual(b.Min + off, s.Min);
            Assert.AreEqual(b.RoadPoints.Length, s.RoadPoints.Length);
            Assert.AreNotSame(b.RoadPoints, s.RoadPoints, "the source map is not modified");
            var ma = NavLayout.BuildStatic(a, DisplayPalette.NavDay, 1.6f);
            var mb = NavLayout.BuildStatic(s, DisplayPalette.NavDay, 1.6f);
            var mab = NavLayout.BuildStatic(new[] { a, s }, DisplayPalette.NavDay, 1.6f);
            try
            {
                Assert.AreEqual(ma.vertexCount + mb.vertexCount, mab.vertexCount);
                Assert.Less(mab.bounds.min.x, ma.bounds.min.x - 1000f, "neighbour drawn west of the current tile");
            }
            finally { Object.DestroyImmediate(ma); Object.DestroyImmediate(mb); Object.DestroyImmediate(mab); }
        }

        [Test]
        public void SwitchRegionMeasuresInTheNewTileAndRebaseMovesNothing()
        {
            var g = Graph();
            var ta = g.Tiles[g.IndexOf(From)];
            var tb = g.Tiles[g.IndexOf(To)];
            // world: tile A's root at the Unity origin, tile B's root at its origin difference (as TilePlacement places them)
            m_RootA = new GameObject("A");
            m_RootB = new GameObject("B");
            m_RootB.transform.position = new Vector3((float)(tb.anchorX - ta.anchorX), 0f, (float)(tb.anchorY - ta.anchorY));
            m_Truck = new GameObject("truck");
            m_Truck.transform.position = m_RootB.transform.position + new Vector3(k_KnyStart.x, 0f, k_KnyStart.y);
            m_Host = new GameObject("nav");
            var nav = NavigationService.Install(m_Host, m_Truck.transform, null, m_RootA.transform, From);
            Assert.IsTrue(nav.Ready);
            nav.SampleForTest();
            Assert.Less(nav.Position.x, -1000f, "in A's frame the truck stands beyond A's west edge (the s24 bug: no road under it)");
            int v0 = nav.MapVersion;

            var oldToNew = new Vector2((float)(ta.anchorX - tb.anchorX), (float)(ta.anchorY - tb.anchorY));
            Assert.IsTrue(nav.SwitchRegion(To, m_RootB.transform, oldToNew));
            Assert.AreEqual(To, nav.regionId);
            Assert.Greater(nav.MapVersion, v0);
            nav.SampleForTest();
            Assert.Less(Vector2.Distance(nav.Position, k_KnyStart), 0.01f);
            Assert.GreaterOrEqual(nav.Graph.Snap(nav.Position, 8f, out _, out _, out _), 0, "a road of the new tile under the truck");
            Assert.NotNull(nav.StaticMap(false));

            // origin rebase: every root and the truck move by the same offset (WorldStreamer.Rebase)
            var shift = new Vector3(-2048f, 0f, 0f);
            foreach (var t in new[] { m_RootA.transform, m_RootB.transform, m_Truck.transform }) t.position += shift;
            nav.SampleForTest();
            Assert.Less(Vector2.Distance(nav.Position, k_KnyStart), 0.01f, "no jump after a rebase");

            // neighbours around the current tile
            int v1 = nav.MapVersion;
            int vtx = nav.StaticMap(false).vertexCount;
            nav.SetNeighbourMaps(new[] { NavMapData.Load(From).Shifted(oldToNew) });
            Assert.Greater(nav.MapVersion, v1);
            Assert.AreEqual(1, nav.NeighbourCount);
            Assert.Greater(nav.StaticMap(false).vertexCount, vtx);
        }

        [Test]
        public void SwitchToARegionWithoutGraphChangesNothing()
        {
            m_Host = new GameObject("nav");
            m_Truck = new GameObject("truck");
            var nav = NavigationService.Install(m_Host, m_Truck.transform, null, null, From);
            Assert.IsFalse(nav.SwitchRegion("no-such-tile", null, Vector2.zero));
            Assert.AreEqual(From, nav.regionId);
        }

        [Test]
        public void FollowerHysteresisNeedsTheTruckInsideTheNextTile()
        {
            var t = new TileData { xmin = 0, ymin = 0, xmax = 2048, ymax = 2048 };
            Assert.AreEqual(5.0, NavStreamFollower.InsideM(t, 5, 1000), 1e-9);
            Assert.AreEqual(-3.0, NavStreamFollower.InsideM(t, 2051, 1000), 1e-9);
            Assert.AreEqual(10.0, NavStreamFollower.InsideM(t, 1000, 2038), 1e-9);
        }
    }
}
