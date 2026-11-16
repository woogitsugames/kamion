using System.Collections.Generic;
using Game.Gameplay;
using Game.World;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0277 (review 0262 P2-2, P2-3, P2-4, P2-8): the pure start search - zones between the region-edge closures,
    /// forward then back search, no place = NoSpace (never a start inside a collider). No physics, no scene: the same
    /// file runs in Unity EditMode and in the .NET runner (tools/spawn-runner, UnityEngine shim).
    /// </summary>
    public class StartSearchTests
    {
        // ------------------------------------------------------------------ helpers

        static List<StartClearance.Crossing> Rows(params (float s, bool entry)[] rows)
        {
            var l = new List<StartClearance.Crossing>();
            foreach (var r in rows) l.Add(new StartClearance.Crossing { s = r.s, entry = r.entry });
            return l;
        }

        /// <summary>Probe of plain data: the combination is blocked at every s inside one of the intervals; records every probe.</summary>
        sealed class FakeProbe : IStartSpaceProbe
        {
            public readonly List<(float lo, float hi, StartBlock kind)> blocked = new List<(float, float, StartBlock)>();
            public readonly List<float> probed = new List<float>();
            public FakeProbe Block(float lo, float hi, StartBlock kind = StartBlock.Collider) { blocked.Add((lo, hi, kind)); return this; }
            public StartBlock Probe(float s)
            {
                probed.Add(s);
                foreach (var b in blocked) if (s >= b.lo && s <= b.hi) return b.kind;
                return StartBlock.Free;
            }
        }

        /// <summary>Allocation-free probe (struct, generic call: no boxing) for the GC test.</summary>
        struct FreeAbove : IStartSpaceProbe
        {
            public float from;
            public StartBlock Probe(float s) => s >= from ? StartBlock.Free : StartBlock.Collider;
        }

        static StartSearchResult Run(List<StartClearance.Crossing> rows, float length, float requested, FakeProbe probe = null)
        {
            probe = probe ?? new FakeProbe();
            return StartSearch.Resolve(rows, length, requested, ref probe);
        }

        const float Behind = StartClearance.BehindClosureM;

        // ------------------------------------------------------------------ zones

        [Test]
        public void NoClosures_TheRequestedStartStays()
        {
            var r = Run(Rows(), 2400f, StartClearance.DefaultStartS);
            Assert.AreEqual(StartOutcome.Unchanged, r.outcome, "region C: start at 12 m, nothing on the route");
            Assert.AreEqual(12f, r.s, 1e-4f);
            Assert.AreEqual(StartMoveReason.None, r.reasons);
        }

        [Test]
        public void EntryClosure_StartMovesBehindIt_AsAdr0262()
        {
            var rows = Rows((60f, true));
            var a = Run(rows, 300f, 12f);
            Assert.AreEqual(StartOutcome.Moved, a.outcome);
            Assert.AreEqual(60f + Behind, a.s, 1e-4f, "old baked 12 m spawn outside the closure -> 25 m behind the row");
            Assert.AreEqual(StartMoveReason.EntryClosure, a.reasons);
            Assert.AreEqual(60f + Behind, Run(rows, 300f, 62f).s, 1e-4f, "inside the row");
            var c = Run(rows, 300f, 200f);
            Assert.AreEqual(StartOutcome.Unchanged, c.outcome);
            Assert.AreEqual(200f, c.s, 1e-4f);
        }

        [Test]
        public void ExitClosure_StartMovesBackInFrontOfIt_AsAdr0262P2_1()
        {
            var rows = Rows((60f, true), (240f, false));
            foreach (float want in new[] { 230f, 290f })
            {
                var r = Run(rows, 300f, want);
                Assert.AreEqual(240f - Behind, r.s, 1e-4f, "start " + want + " m");
                Assert.AreEqual(StartMoveReason.ExitClosure, r.reasons);
            }
            Assert.AreEqual(StartOutcome.Unchanged, Run(rows, 300f, 120f).outcome);
        }

        /// <summary>P2-3: an entry row far ahead (the route leaves the tile and comes back) no longer pulls the start there.</summary>
        [Test]
        public void RouteLeavesAndReentersTheTile_OnlyTheRowsAroundTheStartCount()
        {
            var rows = Rows((60f, true), (300f, false), (400f, true), (900f, false));
            Assert.AreEqual(150f, Run(rows, 1000f, 150f).s, 1e-4f, "old SafeStartS gave 425 m (max over every entry row)");
            Assert.AreEqual(300f - Behind, Run(rows, 1000f, 330f).s, 1e-4f, "outside, nearer the first zone: back");
            Assert.AreEqual(400f + Behind, Run(rows, 1000f, 380f).s, 1e-4f, "outside, nearer the second zone: forward");
            Assert.AreEqual(400f + Behind, Run(rows, 1000f, 350f).s, 1e-4f, "tie: forward");
            Assert.AreEqual(500f, Run(rows, 1000f, 500f).s, 1e-4f);
        }

        /// <summary>P2-4: a stretch too short for 25 m at both ends keeps the physical footprint; too short for that = no zone.</summary>
        [Test]
        public void ShortStretch_FootprintOnly_ThenNoZone()
        {
            Assert.AreEqual(60f + Behind, Run(Rows((60f, true)), 100f, 12f).s, 1e-4f, "route end is not a row: 25 m behind the entry is enough");

            var r = Run(Rows((60f, true), (100f, false)), 200f, 12f);
            float lo = 60f + StartClearance.RearM + StartClearance.BoardsM + StartClearance.MarginM;
            float hi = 100f - StartClearance.FrontM - StartClearance.BoardsM - StartClearance.MarginM;
            Assert.AreEqual(StartOutcome.Moved, r.outcome);
            Assert.AreEqual(lo, r.s, 1e-3f, "40 m between the rows: trailer rear just clear of the entry boards");
            Assert.AreEqual(lo, r.zoneLo, 1e-3f); Assert.AreEqual(hi, r.zoneHi, 1e-3f);

            var probe = new FakeProbe();
            var none = Run(Rows((60f, true), (75f, false)), 200f, 12f, probe);
            Assert.AreEqual(StartOutcome.NoSpace, none.outcome, "15 m between the rows: the 16.45 m combination does not fit");
            Assert.AreEqual(0, probe.probed.Count, "no zone: nothing to probe");
            Assert.AreEqual(StartOutcome.NoSpace, Run(Rows((0f, true), (10f, false)), 10f, 5f).outcome);
        }

        // ------------------------------------------------------------------ probe: forward, back, nothing

        [Test]
        public void Blocked_SearchGoesForwardFirst_AsAdr0262()
        {
            var probe = new FakeProbe().Block(195f, 205.5f);
            var r = Run(Rows((60f, true)), 600f, 200f, probe);
            Assert.AreEqual(StartOutcome.Moved, r.outcome);
            Assert.AreEqual(206f, r.s, 1e-4f, "first free place 2 m steps ahead");
            Assert.AreEqual(StartMoveReason.Blocked, r.reasons);
            Assert.AreEqual(StartBlock.Collider, r.firstBlock);
        }

        /// <summary>P2-2: nothing free ahead (zone ends at the exit closure) -> back towards the entry closure.</summary>
        [Test]
        public void BlockedAhead_SearchGoesBack_NotBeforeTheEntryClosure()
        {
            var rows = Rows((60f, true), (240f, false));     // zone 85 .. 215
            var probe = new FakeProbe().Block(199f, 300f);
            var r = Run(rows, 300f, 200f, probe);
            Assert.AreEqual(StartOutcome.Moved, r.outcome);
            Assert.AreEqual(198f, r.s, 1e-4f, "nearest free place behind");
            Assert.AreEqual(StartMoveReason.Blocked | StartMoveReason.SearchedBack, r.reasons);
            foreach (float s in probe.probed)
            {
                Assert.LessOrEqual(s, 215f + 1e-3f, "never past the exit zone end");
                Assert.GreaterOrEqual(s, 85f - 1e-3f, "never before the entry zone start");
            }
            CollectionAssert.Contains(probe.probed, 214f, "forward probes up to the zone end");
        }

        /// <summary>P2-2: nothing free anywhere in the zone -> NoSpace, never a blocked place.</summary>
        [Test]
        public void NothingFree_NoSpace_AndTheSearchStaysBounded()
        {
            var rows = Rows((60f, true));
            var probe = new FakeProbe().Block(0f, 10000f);
            var r = Run(rows, 10000f, 1000f, probe);
            Assert.AreEqual(StartOutcome.NoSpace, r.outcome);
            int max = 1 + (int)(StartSearch.MaxForwardM / StartSearch.StepM) + (int)(StartSearch.MaxBackM / StartSearch.StepM);
            Assert.AreEqual(max, r.probes, "forward and back limits (WORKING_VALUE)");
            Assert.AreEqual(max, probe.probed.Count);
            Assert.AreEqual(1000f + StartSearch.MaxForwardM, Max(probe.probed), 1e-3f);
            Assert.AreEqual(1000f - StartSearch.MaxBackM, Min(probe.probed), 1e-3f);

            var near = Run(rows, 10000f, 100f, new FakeProbe().Block(0f, 10000f));
            Assert.AreEqual(StartOutcome.NoSpace, near.outcome, "back search stops at the entry zone start (85 m)");
        }

        [Test]
        public void CurveAndOverflow_CountAsTaken()
        {
            var probe = new FakeProbe().Block(80f, 130f, StartBlock.Curve);
            var r = Run(Rows(), 2000f, 90f, probe);
            Assert.AreEqual(132f, r.s, 1e-4f, "past the roundabout");
            Assert.AreEqual(StartBlock.Curve, r.firstBlock);
            var o = Run(Rows(), 2000f, 90f, new FakeProbe().Block(89f, 91f, StartBlock.Overflow));
            Assert.AreEqual(92f, o.s, 1e-4f);
            Assert.AreEqual(StartBlock.Overflow, o.firstBlock);
        }

        [Test]
        public void Describe_NamesEveryReason()
        {
            Assert.AreEqual("region-edge closure on the route", StartSearch.Describe(StartMoveReason.EntryClosure, StartBlock.Free, null));
            Assert.AreEqual("region-edge closure ahead on the route + collider 'Bar', searched back",
                StartSearch.Describe(StartMoveReason.ExitClosure | StartMoveReason.Blocked | StartMoveReason.SearchedBack, StartBlock.Collider, "Bar"));
            Assert.AreEqual("route bends under the combination", StartSearch.Describe(StartMoveReason.Blocked, StartBlock.Curve, null));
        }

        // ------------------------------------------------------------------ bend (P2-8)

        static void Arc(float radius, float length, out Vector3[] pts, out float[] dist)
        {
            int n = (int)(length / 1f) + 1;
            pts = new Vector3[n]; dist = new float[n];
            for (int i = 0; i < n; i++)
            {
                float a = i * 1f / radius;
                pts[i] = new Vector3(radius * Mathf.Sin(a), 0f, radius - radius * Mathf.Cos(a));
                if (i > 0) dist[i] = dist[i - 1] + Vector3Distance(pts[i - 1], pts[i]);
            }
        }

        static float Vector3Distance(Vector3 a, Vector3 b)
        {
            float dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
            return Mathf.Sqrt(dx * dx + dy * dy + dz * dz);
        }

        [Test]
        public void LateralOffset_StraightIsZero_RoundaboutIsLarge_GentleBendIsSmall()
        {
            var straight = new Vector3[101]; var ds = new float[101];
            for (int i = 0; i < 101; i++) { straight[i] = new Vector3(0.6f * 2f * i, 0f, 0.8f * 2f * i); ds[i] = 2f * i; }
            Assert.Less(StartSearch.MaxLateralOffset(straight, ds, 100f, StartClearance.RearM, StartClearance.FrontM), 0.01f);
            Arc(20f, 100f, out var tight, out var dt);       // roundabout ring
            float t = StartSearch.MaxLateralOffset(tight, dt, 50f, StartClearance.RearM, StartClearance.FrontM);
            Assert.Greater(t, StartSearch.MaxCurveOffsetM, "R 20 m: the straight trailer leaves the lane");
            Assert.AreEqual(StartClearance.RearM * StartClearance.RearM / (2f * 20f), t, 0.4f, "sagitta of the trailer rear end");
            Arc(500f, 200f, out var gentle, out var dg);
            Assert.Less(StartSearch.MaxLateralOffset(gentle, dg, 100f, StartClearance.RearM, StartClearance.FrontM), StartSearch.MaxCurveOffsetM, "R 500 m road bend");
        }

        // ------------------------------------------------------------------ importer (P2-6, pure part)

        [Test]
        public void BakedSpawn_UsesTheSameZoneRuleAsTheRuntime()
        {
            // Route northwards from the south tile edge; entry row at 60 m, exit row at 940 m (as StartClearanceTests).
            int n = 501;
            var pts = new Vector3[n]; var dist = new float[n];
            for (int i = 0; i < n; i++) { pts[i] = new Vector3(1.75f, 0f, 2f * i); dist[i] = 2f * i; }
            var closures = new List<WorldBoundary.Closure>
            {
                new WorldBoundary.Closure { localPos = new Vector3(0f, 0f, 60f), headingDeg = 180f, widthM = 7f, road = "t" },
                new WorldBoundary.Closure { localPos = new Vector3(0f, 0f, 940f), headingDeg = 0f, widthM = 7f, road = "t" },
            };
            Assert.IsTrue(StartSearch.BakedSpawnS(pts, dist, closures, StartClearance.DefaultStartS, out float a));
            Assert.AreEqual(60f + Behind, a, 0.01f, "old fixed 12 m catalog start -> behind the entry row");
            Assert.IsTrue(StartSearch.BakedSpawnS(pts, dist, closures, 90f, out float b));
            Assert.AreEqual(90f, b, 0.01f, "catalog 90 m (ADR 0262) stays");
            Assert.IsTrue(StartSearch.BakedSpawnS(pts, dist, closures, 990f, out float c));
            Assert.AreEqual(940f - Behind, c, 0.01f, "never outside the exit row");
        }

        // ------------------------------------------------------------------ zero GC

        [Test]
        public void Resolve_WithAStructProbe_AllocatesNothing()
        {
            var rows = Rows((60f, true), (240f, false));
            var probe = new FreeAbove { from = 150f };
            StartSearch.Resolve(rows, 300f, 100f, ref probe);   // warm-up (JIT)
#if UNITY_5_3_OR_NEWER
            // Repo convention for zero-GC tests (GcAllocCounter: Recorder "GC.Alloc" with a 64 B control); int-h3-s23: the
            // Is.Not.AllocatingGCMemory() extension did not compile here (CS1061, missing UnityEngine.TestTools.Constraints).
            GcAllocCounter.AssertZero(
                () => { StartSearch.Resolve(rows, 300f, 100f, ref probe); StartSearch.Resolve(rows, 300f, 12f, ref probe); },
                message: "two start searches with a struct probe must not allocate");
#else
            long before = System.GC.GetAllocatedBytesForCurrentThread();
            var r = StartSearch.Resolve(rows, 300f, 100f, ref probe);
            var r2 = StartSearch.Resolve(rows, 300f, 12f, ref probe);
            long after = System.GC.GetAllocatedBytesForCurrentThread();
            Assert.AreEqual(0L, after - before, "bytes allocated by two searches");
            Assert.AreEqual(150f, r.s, 1e-4f);
            Assert.AreEqual(151f, r2.s, 1e-4f, "12 m -> zone start 85 m, then 2 m steps to the first free place");
#endif
        }

        static float Max(List<float> l) { float m = float.NegativeInfinity; foreach (var v in l) m = Mathf.Max(m, v); return m; }
        static float Min(List<float> l) { float m = float.PositiveInfinity; foreach (var v in l) m = Mathf.Min(m, v); return m; }
    }
}
