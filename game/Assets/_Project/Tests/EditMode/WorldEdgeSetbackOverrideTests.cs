using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Game.World;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0287 (review 2026-11-18 P1-3): authored closure setbacks (Data/Regions/&lt;id&gt;/world_edge.authored.json).
    /// Knyszyn: the closures of DK65 and DW671 on the west edge stand 12 m inside the edge instead of 60 m (out of the
    /// roundabout); every closure stays inside the drivable rectangle, and the resolved list has no conflicts.
    /// </summary>
    public class WorldEdgeSetbackOverrideTests
    {
        const string Region = "knyszyn";
        static readonly System.Type Builder = System.Type.GetType("Game.World.Import.WorldEdgeBuilder, Game.World.Import.Editor", true);

        static T Call<T>(string method, params object[] args) =>
            (T)Builder.GetMethod(method, BindingFlags.Public | BindingFlags.Static).Invoke(null, args);

        [Test]
        public void Knyszyn_WestArmsOfTheRoundabout_CloseNearTheEdge()
        {
            var raw = Call<List<WorldBoundary.Closure>>("PlanRegionClosures", Region);
            // west edge of the tile: e = -1024; DK65 leaves it at n = -533.3, DW671 at n = -642.5 (roads.graph.json)
            var west = raw.Where(c => c.localPos.x < -1024f + 61f && c.localPos.z < -480f && c.localPos.z > -700f).ToList();
            Assert.AreEqual(2, west.Count, "DK65 and DW671 leave the tile west of the roundabout");
            foreach (var c in west)
            {
                float inside = c.localPos.x + 1024f;
                Assert.That(inside, Is.InRange(8f * 0.4f, 12.5f), $"{c.road}: {inside:F1} m inside the west edge (authored setback 12 m along the road)");
            }
            // every other closure of the region keeps the default: none of them moved to the edge
            int nearEdge = raw.Count(c => Mathf.Min(Mathf.Min(c.localPos.x + 1024f, 1024f - c.localPos.x), Mathf.Min(c.localPos.z + 1024f, 1024f - c.localPos.z)) < 13f);
            Assert.LessOrEqual(nearEdge, 2, "only the two authored closures stand within 13 m of the edge");
            var resolved = Call<List<WorldBoundary.Closure>>("ResolveClosures", raw);
            Assert.AreEqual(0, Call<List<(int a, int b, float gapM)>>("FindClosureConflicts", resolved).Count);
        }

        [Test]
        public void SetbackFor_ClampsAndPicksTheNearestEntry()
        {
            var ovType = Builder.GetNestedType("SetbackOverride");
            var list = (System.Collections.IList)System.Activator.CreateInstance(typeof(List<>).MakeGenericType(ovType));
            object Ov(float e, float n, float r, float s)
            {
                object o = System.Activator.CreateInstance(ovType);
                ovType.GetField("nearEN").SetValue(o, new Vector2(e, n));
                ovType.GetField("radiusM").SetValue(o, r);
                ovType.GetField("setbackM").SetValue(o, s);
                return o;
            }
            list.Add(Ov(0f, 0f, 15f, 12f));
            list.Add(Ov(10f, 0f, 15f, 30f));
            float def = (float)Builder.GetField("ClosureSetbackM").GetValue(null);
            Assert.AreEqual(12f, Call<float>("SetbackFor", list, new Vector2(2f, 0f)));
            Assert.AreEqual(30f, Call<float>("SetbackFor", list, new Vector2(9f, 0f)));
            Assert.AreEqual(def, Call<float>("SetbackFor", list, new Vector2(100f, 0f)));
            Assert.AreEqual(def, Call<float>("SetbackFor", null, new Vector2(0f, 0f)));
        }
    }
}
