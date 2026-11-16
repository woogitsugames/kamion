using System;
using System.Collections;
using System.Collections.Generic;
using Game.World;
using Game.World.Streaming;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>
    /// D44 (ADR 0273 §6 dopisek): content tier and world budget of the streamer per (platform, quality tier). On desktop the
    /// PC tier decides (High / Ultra = High content 1450 / 2000 MB, explicit Low fallback without _High_Tile scenes); phones
    /// keep the start scene's content and their own budgets. Pure, no scenes.
    /// </summary>
    public class StreamingContentChoiceTests
    {
        const string Low = RegionScenes.LowTier, High = RegionScenes.HighTier;

        [TestCase("Low", false, Low, 640f)]
        [TestCase("Medium", false, Low, 800f)]
        [TestCase("High", false, High, 1450f)]
        [TestCase("Ultra", false, High, 2000f)]
        [TestCase("Low", true, High, 640f)]      // a High start scene stays High (counted with High memory)
        [TestCase("Medium", true, High, 800f)]
        [TestCase("High", true, High, 1450f)]
        [TestCase("Ultra", true, High, 2000f)]
        public void Desktop_PcTierPicksContentAndBudget(string tier, bool startHigh, string content, float budget)
        {
            var c = StreamingContentChoice.Choose(desktop: true, tier, startHigh, highTilesAvailable: true);
            Assert.AreEqual(content, c.contentTier, tier);
            Assert.AreEqual(budget, c.budgetMB, tier);
            Assert.IsFalse(c.highFallback);
        }

        /// <summary>The reported case: RTX 5070, tier High, start scene World_knyszyn (Low) -> High content, 1450 MB.</summary>
        [Test]
        public void Desktop_HighTier_LowStartScene_StreamsHigh()
        {
            var c = StreamingContentChoice.Choose(true, "High", startSceneHigh: false, highTilesAvailable: true);
            Assert.AreEqual(High, c.contentTier);
            Assert.AreEqual(1450f, c.budgetMB);
            StringAssert.Contains("desktop tier High", c.reason);
        }

        [TestCase("High", 1450f)]
        [TestCase("Ultra", 2000f)]
        public void Desktop_HighTier_NoHighTiles_ExplicitLowFallback(string tier, float budget)
        {
            var c = StreamingContentChoice.Choose(true, tier, false, highTilesAvailable: false);
            Assert.AreEqual(Low, c.contentTier);
            Assert.IsTrue(c.highFallback);
            Assert.AreEqual(budget, c.budgetMB, "the budget stays the tier's (ADR 0273 table)");
            StringAssert.Contains("FALLBACK", c.reason);
        }

        [TestCase("Low", false, Low, 200f)]
        [TestCase("Medium", false, Low, 400f)]
        [TestCase("High", false, Low, 600f)]     // phone: content follows the start scene, never upgraded
        [TestCase("High", true, High, 600f)]
        [TestCase("Ultra", true, High, 600f)]
        public void Phone_Unchanged(string tier, bool startHigh, string content, float budget)
        {
            var c = StreamingContentChoice.Choose(desktop: false, tier, startHigh, highTilesAvailable: true);
            Assert.AreEqual(content, c.contentTier);
            Assert.AreEqual(budget, c.budgetMB);
            Assert.IsFalse(c.highFallback);
        }

        [Test]
        public void Desktop_UnknownTier_LowContentLowBudget()
        {
            var c = StreamingContentChoice.Choose(true, null, false, true);
            Assert.AreEqual(Low, c.contentTier);
            Assert.AreEqual(640f, c.budgetMB);
        }

        [TestCase("World_knyszyn_High", true)]
        [TestCase("WorldC_High", true)]
        [TestCase("World_knyszyn", false)]
        [TestCase("World_knyszyn_High_Tile", false)]
        [TestCase(null, false)]
        public void IsHighScene(string scene, bool high) => Assert.AreEqual(high, StreamingContentChoice.IsHighScene(scene));

        // ------------------------------------------------------------------ neighbour availability

        sealed class Source : ITileSceneSource
        {
            public readonly HashSet<string> Scenes = new HashSet<string>();
            public bool IsAvailable(string region, string tier) => Scenes.Contains(RegionScenes.TileSceneNameFor(region, tier));
            public IEnumerator Acquire(string region, string tier, Action<bool> done) { done(IsAvailable(region, tier)); yield break; }
            public void Release(string region, string tier) { }
            public bool FromPack(string region, string tier) => false;
        }

        static TileGraph Line()   // a - b - c (W -> E), d alone
        {
            TileData T(string id, int c, params NeighborData[] n) => new TileData
            {
                id = id, xmin = c * 2048.0, ymin = 0, xmax = c * 2048.0 + 2048.0, ymax = 2048.0,
                anchorX = c * 2048.0 + 1024.0, anchorY = 1024.0, worldMemoryMB = 50f, worldMemoryHighMB = 120f, neighbors = n,
            };
            NeighborData N(string id, string side) => new NeighborData { id = id, side = side, seamM = 2048f };
            return new TileGraph(new TileGraphData
            {
                schema = TileGraph.Schema,
                tiles = new[] { T("a", 0, N("b", "E")), T("b", 1, N("a", "W"), N("c", "E")), T("c", 2, N("b", "W")), T("d", 5) },
            });
        }

        [Test]
        public void AnyNeighbourAvailable_LooksOnlyAtNeighboursOfTheTier()
        {
            var g = Line();
            var src = new Source();
            src.Scenes.Add(RegionScenes.TileSceneNameFor("b", Low));
            src.Scenes.Add(RegionScenes.TileSceneNameFor("a", High));   // the start tile itself does not count
            Assert.IsFalse(StreamingContentChoice.AnyNeighbourAvailable(g, "a", src, High));
            Assert.IsTrue(StreamingContentChoice.AnyNeighbourAvailable(g, "a", src, Low));
            src.Scenes.Add(RegionScenes.TileSceneNameFor("c", High));
            Assert.IsTrue(StreamingContentChoice.AnyNeighbourAvailable(g, "b", src, High));
            Assert.IsFalse(StreamingContentChoice.AnyNeighbourAvailable(g, "d", src, High), "no neighbours");
            Assert.IsFalse(StreamingContentChoice.AnyNeighbourAvailable(g, "zz", src, High), "not in the graph");
            Assert.IsFalse(StreamingContentChoice.AnyNeighbourAvailable(null, "a", src, High));
        }
    }
}
