using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Game.World;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0169: one list of region-edge closures (runtime data = colliders = boards) and no object built twice at the
    /// same place. The duplicate rule of the task: the same kind of object (a barrier row) within 0.5 m.
    /// </summary>
    public class WorldEdgeClosureDuplicateTests
    {
        const string Region = "bialystok-industrial-c";
        static readonly System.Type Builder = System.Type.GetType("Game.World.Import.WorldEdgeBuilder, Game.World.Import.Editor", true);

        static T Call<T>(string method, params object[] args) =>
            (T)Builder.GetMethod(method, BindingFlags.Public | BindingFlags.Static).Invoke(null, args);

        static List<WorldBoundary.Closure> Resolve(List<WorldBoundary.Closure> raw) => Call<List<WorldBoundary.Closure>>("ResolveClosures", raw);
        static List<(int a, int b, float gapM)> Conflicts(List<WorldBoundary.Closure> list) => Call<List<(int a, int b, float gapM)>>("FindClosureConflicts", list);
        static float Span(WorldBoundary.Closure c) => (float)Builder.GetMethod("ClosureSpan", new[] { typeof(WorldBoundary.Closure) }).Invoke(null, new object[] { c });

        static WorldBoundary.Closure Closure(float e, float n, float width, float heading = 0f) =>
            new WorldBoundary.Closure { localPos = new Vector3(e, 130f, n), headingDeg = heading, widthM = width, road = "t" };

        /// <summary>End points of the barrier row (east, north).</summary>
        static (Vector2 a, Vector2 b) Row(WorldBoundary.Closure c)
        {
            float h = c.headingDeg * Mathf.Deg2Rad;
            var right = new Vector2(Mathf.Cos(h), -Mathf.Sin(h));
            var p = new Vector2(c.localPos.x, c.localPos.z);
            return (p - right * Span(c) * 0.5f, p + right * Span(c) * 0.5f);
        }

        [Test]
        public void Detector_FindsTheSameRowTwice_AndCrossingRows_ButNotNeighbours()
        {
            var list = new List<WorldBoundary.Closure>
            {
                Closure(0f, 0f, 7f), Closure(0.3f, 0.4f, 7f),          // the same row 0.4 m further along: duplicate
                Closure(100f, 0f, 7f), Closure(103f, -2f, 4f, 85f),    // rows through each other
                Closure(300f, 0f, 7f), Closure(300f, 0.6f, 7f),        // 0.6 m apart: outside the 0.5 m rule
                Closure(500f, 0f, 7f), Closure(516f, 0f, 7f),          // two carriageways, rows end 4 m apart
            };
            var found = Conflicts(list);
            CollectionAssert.AreEquivalent(new[] { (0, 1), (2, 3) }, found.Select(f => (f.a, f.b)).ToList());
            Assert.That(found.First(f => f.a == 0).gapM, Is.EqualTo(0.4f).Within(0.01f));
            Assert.That(found.First(f => f.a == 2).gapM, Is.EqualTo(0f));
        }

        [Test]
        public void CommittedGraph_RawClosuresCollide_ResolvedListHasNoDuplicates()
        {
            var raw = Call<List<WorldBoundary.Closure>>("PlanRegionClosures", Region);
            Assert.Greater(raw.Count, 20, "roads leaving the region (roads.graph.json boundary nodes)");
            // The defect this guards against: Maczka x trunk_link twice (west edge, ADR 0141), Kombatantow x service
            // (south edge) and Batorego x service (east edge) - 4 pairs in the graph of 2026-11-13.
            var rawConflicts = Conflicts(raw);
            Assert.GreaterOrEqual(rawConflicts.Count, 1, "the committed graph no longer has close exits: remove the resolve step or update this test");

            var resolved = Resolve(raw);
            var left = Conflicts(resolved);
            Assert.IsEmpty(left, "closure rows within 0.5 m of each other: " +
                string.Join("; ", left.Select(f => $"{resolved[f.a].road} x {resolved[f.b].road} at E {resolved[f.a].localPos.x:F1} N {resolved[f.a].localPos.z:F1} ({f.gapM:F2} m)")));
            Assert.Less(resolved.Count, raw.Count, "slip lanes merged into their carriageway");
            // Same position / same type: no two closure centres within 0.5 m either.
            for (int i = 0; i < resolved.Count; i++)
                for (int j = i + 1; j < resolved.Count; j++)
                    Assert.Greater(Vector3.Distance(resolved[i].localPos, resolved[j].localPos), 0.5f, $"{resolved[i].road} x {resolved[j].road}");
            Debug.Log($"[EDGE-0169] {Region}: {raw.Count} graph closures, {rawConflicts.Count} colliding pairs -> {resolved.Count} resolved, {left.Count} colliding pairs");
        }

        [Test]
        public void NeighbouringCarriageways_ClosedAFewMetresApart_EndAtTheMiddleOfTheMedian()
        {
            // Andersa at the east edge: two 10 m carriageways 12 m apart, closed 21.6 m apart along the road. Rows of
            // 15 m reached 1.5 m into each other's span and overlapped across the median when seen from the cab.
            var raw = new List<WorldBoundary.Closure> { Closure(996.23f, -951.18f, 10f, 118.3f), Closure(971.53f, -951.45f, 10f, 118.5f) };
            var res = Resolve(raw);
            Assert.AreEqual(2, res.Count);
            float h = 118.3f * Mathf.Deg2Rad;
            var right = new Vector2(Mathf.Cos(h), -Mathf.Sin(h));
            var (a0, a1) = Row(res[0]); var (b0, b1) = Row(res[1]);
            float aLo = Mathf.Min(Vector2.Dot(a0, right), Vector2.Dot(a1, right)), aHi = Mathf.Max(Vector2.Dot(a0, right), Vector2.Dot(a1, right));
            float bLo = Mathf.Min(Vector2.Dot(b0, right), Vector2.Dot(b1, right)), bHi = Mathf.Max(Vector2.Dot(b0, right), Vector2.Dot(b1, right));
            float overlap = Mathf.Min(aHi, bHi) - Mathf.Max(aLo, bLo);
            Assert.That(overlap, Is.LessThan(0.1f), "rows do not reach into each other's span");
            Assert.That(overlap, Is.GreaterThan(-0.1f), "and leave no gap in the median");
            foreach (var c in res)
            {
                Assert.That(c.widthM, Is.EqualTo(10f), "still a carriageway: keeps its B-1");
                Assert.That(Span(c), Is.GreaterThan(10f + 2f), "the row still covers the carriageway and the outer shoulder");
            }
        }

        [Test]
        public void CrossingClosuresAtAJunction_MeetInACorner()
        {
            // Batorego (7 m) and a service road (3 m) leave one junction 9 m inside the east edge; the closures stood
            // 3.2 m apart at 83 degrees and their barrier rows ran through each other.
            var raw = new List<WorldBoundary.Closure> { Closure(1016.53f, -891.34f, 7f, 53.8f), Closure(1016.36f, -894.58f, 3f, 137.0f) };
            Assert.AreEqual(1, Conflicts(raw).Count);
            var res = Resolve(raw);
            Assert.AreEqual(2, res.Count, "two roads, two closures");
            Assert.IsEmpty(Conflicts(res));
            var (a0, a1) = Row(res[0]); var (b0, b1) = Row(res[1]);
            float corner = new[] { Vector2.Distance(a0, b0), Vector2.Distance(a0, b1), Vector2.Distance(a1, b0), Vector2.Distance(a1, b1) }.Min();
            Assert.That(corner, Is.InRange(0.5f, 2.0f), "row ends meet in a corner a truck cannot pass (2.55 m wide)");
            Assert.That(Span(res[0]), Is.LessThan(12f)); Assert.That(Span(res[1]), Is.LessThan(8f));
            // Each closure is still on its own road: the centre moved along the row only.
            for (int i = 0; i < 2; i++)
            {
                float h = raw[i].headingDeg * Mathf.Deg2Rad;
                Vector3 d = res[i].localPos - raw[i].localPos;
                Assert.That(Mathf.Abs(d.x * Mathf.Sin(h) + d.z * Mathf.Cos(h)), Is.LessThan(0.01f));
                Assert.That(res[i].headingDeg, Is.EqualTo(raw[i].headingDeg));
            }
        }

        [Test]
        public void Resolve_IsIdempotent_AndLeavesLoneClosuresAlone()
        {
            var raw = Call<List<WorldBoundary.Closure>>("PlanRegionClosures", Region);
            var once = Resolve(raw);
            var twice = Resolve(once);
            Assert.AreEqual(once.Count, twice.Count);
            for (int i = 0; i < once.Count; i++)
            {
                Assert.That(Vector3.Distance(once[i].localPos, twice[i].localPos), Is.LessThan(0.01f), once[i].road);
                Assert.That(Span(twice[i]), Is.EqualTo(Span(once[i])).Within(0.01f), once[i].road);
            }
            var lone = new List<WorldBoundary.Closure> { Closure(0f, 0f, 7f), Closure(400f, 0f, 4f, 90f) };
            var res = Resolve(lone);
            Assert.AreEqual(0f, res[0].spanM); Assert.AreEqual(0f, res[1].spanM);
            Assert.AreEqual(lone[0].localPos, res[0].localPos);
        }
    }
}
