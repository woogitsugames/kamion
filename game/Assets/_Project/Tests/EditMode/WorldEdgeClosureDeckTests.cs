using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Game.World;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0321 (vqa-wave5 dk8-wasilkow-01 w01_br1_on_deck): the tertiary road w1220009817 leaves the tile on the west
    /// edge and passes under the DK8 viaduct (w145631572, bridge, 9.5 m) about 60 m inside the edge. Its closure stood
    /// at the default setback right under the deck, RoadY took the deck height and the barrier row stood on the deck
    /// along the right lane of DK8. The closure now slides towards the edge until the whole row clears the deck.
    /// </summary>
    public class WorldEdgeClosureDeckTests
    {
        static readonly System.Type Builder = System.Type.GetType("Game.World.Import.WorldEdgeBuilder, Game.World.Import.Editor", true);

        static T Call<T>(string method, params object[] args) =>
            (T)Builder.GetMethod(method, BindingFlags.Public | BindingFlags.Static).Invoke(null, args);

        [Test]
        public void Dk8Wasilkow01_TertiaryUnderTheViaduct_ClosesWestOfTheDeck()
        {
            var raw = Call<List<WorldBoundary.Closure>>("PlanRegionClosures", "dk8-wasilkow-01");
            // the road crosses the west edge at n = 390 and runs east to (-936, 422); DK8 deck axis at e ~ -960
            var c = raw.Where(k => k.localPos.x > -1024f && k.localPos.x < -930f && k.localPos.z > 380f && k.localPos.z < 430f).ToList();
            Assert.AreEqual(1, c.Count, "one closure on the tertiary road west of DK8");
            float span = c[0].widthM + 5f;
            float clear = 0.5f * 9.5f + 0.5f * span + 2f;
            Assert.Less(c[0].localPos.x, -960f - clear + 1.5f, $"closure at e = {c[0].localPos.x:F1}: the row must clear the DK8 deck");
            Assert.Greater(c[0].localPos.x, -1024f + 8f * 0.9f, "still inside the tile, at least the minimum setback");
            // the barrier row stays across its own road (east-west), not along DK8
            Assert.Greater(Mathf.Abs(Mathf.Sin(c[0].headingDeg * Mathf.Deg2Rad)), 0.8f, $"closure heading {c[0].headingDeg:F0} deg = the tertiary road (east-west)");
            var resolved = Call<List<WorldBoundary.Closure>>("ResolveClosures", raw);
            Assert.AreEqual(0, Call<List<(int a, int b, float gapM)>>("FindClosureConflicts", resolved).Count);
        }
    }
}
