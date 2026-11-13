// ADR 0168 (open points of the Mistral r6 review): roundabout exit counting policy, at most three voice
// announcements per manoeuvre without repeats on distance drift, ETA throttled to 1 Hz, zero GC via GcAllocCounter.
// Mirrored 1:1 by game/Assets/_Project/Tests/EditMode/Nav0168Tests.cs (NUnit); keep both in sync.
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using Game.Core.Navigation;
using UnityEngine;
using Xunit;

namespace NavRunner.Tests
{
    public class Nav0168Tests
    {
        const string Region = "bialystok-industrial-c";

        // ------------------------------------------------------------------ synthetic graphs

        static RouteGraph Build(Vector2[] nodes, (int a, int b, byte flags, string name)[] edges)
        {
            var g = new RouteGraph();
            var names = new List<string> { "" };
            g.NodePos = nodes; g.NodeFlags = new byte[nodes.Length];
            int n = edges.Length;
            g.EdgeFrom = new int[n]; g.EdgeTo = new int[n]; g.EdgeLength = new float[n]; g.EdgeClass = new byte[n]; g.EdgeFlags = new byte[n];
            g.EdgeName = new ushort[n]; g.EdgeMaxSpeed = new byte[n]; g.EdgeMaxSpeedOsm = new bool[n]; g.EdgeStart = new int[n + 1];
            g.EdgeMaxWeightC = new ushort[n]; g.EdgeMaxAxleLoadC = new ushort[n]; g.EdgeMaxHeightCm = new ushort[n]; g.EdgeMaxLengthCm = new ushort[n];
            var pts = new List<Vector2>();
            for (int i = 0; i < n; i++)
            {
                var (a, b, f, nm) = edges[i];
                g.EdgeFrom[i] = a; g.EdgeTo[i] = b; g.EdgeFlags[i] = f; g.EdgeClass[i] = 1;
                if (!names.Contains(nm)) names.Add(nm);
                g.EdgeName[i] = (ushort)names.IndexOf(nm);
                g.EdgeStart[i] = pts.Count;
                pts.Add(nodes[a]); pts.Add(nodes[b]);
                g.EdgeLength[i] = Vector2.Distance(nodes[a], nodes[b]);
            }
            g.EdgeStart[n] = pts.Count;
            g.Points = pts.ToArray();
            g.Names = names.ToArray();
            g.BuildAdjacency();
            return g;
        }

        /// <summary>Counter-clockwise ring (as in Poland) with arms W (entry), S, E, N; the S arm is edge 5 with
        /// <paramref name="southFlags"/> and runs ring -> arm unless <paramref name="southInbound"/> (arm -> ring).</summary>
        static RouteGraph Ring(byte southFlags, bool southInbound)
        {
            float r = 30f;
            var nodes = new[]
            {
                new Vector2(-r, 0), new Vector2(0, -r), new Vector2(r, 0), new Vector2(0, r),
                new Vector2(-200, 0), new Vector2(0, -200), new Vector2(200, 0), new Vector2(0, 200),
            };
            byte rb = RouteGraph.FlagRoundabout | RouteGraph.FlagOneway;
            return Build(nodes, new (int, int, byte, string)[]
            {
                (0, 1, rb, "Rondo"), (1, 2, rb, "Rondo"), (2, 3, rb, "Rondo"), (3, 0, rb, "Rondo"),
                (4, 0, 0, "Zachodnia"), southInbound ? (5, 1, southFlags, "Południowa") : (1, 5, southFlags, "Południowa"),
                (2, 6, 0, "Wschodnia"), (3, 7, 0, "Północna"),
            });
        }

        static int ExitWestToNorth(RouteGraph g, ExitCountPolicy policy)
        {
            var planner = new RoutePlanner(g) { ExitCounting = policy };
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(-150, 0), 90f, new Vector2(0, 150), p));
            Assert.Equal(Maneuver.Roundabout, p.ManType[0]);
            Assert.Equal("Północna", g.Names[p.ManName[0]]);
            return p.ManExit[0];
        }

        [Fact]
        public void Exit_OnewayEntryNeverCounts()
        {
            byte ow = RouteGraph.FlagOneway;
            Assert.Equal(3, ExitWestToNorth(Ring(0, false), ExitCountPolicy.AnyMotorVehicle));    // S two-way: S, E, N
            Assert.Equal(2, ExitWestToNorth(Ring(ow, true), ExitCountPolicy.AnyMotorVehicle));    // S one-way INTO the ring
            Assert.Equal(2, ExitWestToNorth(Ring(ow, true), ExitCountPolicy.ThisTruck));
            Assert.Equal(3, ExitWestToNorth(Ring(ow, false), ExitCountPolicy.AnyMotorVehicle));   // S one-way OUT of the ring
        }

        [Fact]
        public void Exit_TruckBannedExit_CountsOnlyForAnyMotorVehicle()
        {
            Assert.Equal(ExitCountPolicy.AnyMotorVehicle, RoutePlanner.DefaultExitCounting);
            var noTruck = Ring(RouteGraph.FlagNoTruck, false);
            Assert.True(ExitWestToNorth(noTruck, RoutePlanner.DefaultExitCounting) == 3, "the driver sees and counts the B-5 exit");
            Assert.Equal(2, ExitWestToNorth(noTruck, ExitCountPolicy.ThisTruck));
            var heavy = Ring(0, false); heavy.EdgeMaxWeightC[5] = 1500;   // 15 t limit (B-18)
            Assert.Equal(3, ExitWestToNorth(heavy, ExitCountPolicy.AnyMotorVehicle));
            Assert.Equal(2, ExitWestToNorth(heavy, ExitCountPolicy.ThisTruck));
            var axle = Ring(0, false); axle.EdgeMaxAxleLoadC[5] = 800;    // 8 t axle load (B-19)
            Assert.Equal(2, ExitWestToNorth(axle, ExitCountPolicy.ThisTruck));
            var dest = Ring(RouteGraph.FlagHgvDestination, false);       // hgv=destination: not a through exit for the truck
            Assert.Equal(2, ExitWestToNorth(dest, ExitCountPolicy.ThisTruck));
            var exactLimit = Ring(0, false); exactLimit.EdgeMaxWeightC[5] = RoutePlanner.TruckMaxWeightCt;   // limit == GCW: allowed
            Assert.Equal(3, ExitWestToNorth(exactLimit, ExitCountPolicy.ThisTruck));
        }

        /// <summary>The region rings (Rondo Putry, Rondo Pamięci Bieżeństwa) have no exit closed to the truck, so both policies
        /// give the golden exit numbers - checked on every golden route.</summary>
        [Fact]
        public void Exit_GoldenRoutes_SameUnderBothPolicies()
        {
            var g = RouteGraph.Load(Region);
            var any = new RoutePlanner(g) { ExitCounting = ExitCountPolicy.AnyMotorVehicle };
            var truck = new RoutePlanner(g) { ExitCounting = ExitCountPolicy.ThisTruck };
            var p = RoutePath.For(g); var q = RoutePath.For(g);
            int rings = 0;
            foreach (var r in Golden())
            {
                var a = new Vector2((float)r.from[0], (float)r.from[1]); var b = new Vector2((float)r.to[0], (float)r.to[1]);
                Assert.Equal(PlanStatus.Ok, any.Plan(a, float.NaN, b, p));
                Assert.Equal(PlanStatus.Ok, truck.Plan(a, float.NaN, b, q));
                Assert.Equal(r.maneuvers.Count, p.ManCount);
                for (int k = 0; k < p.ManCount; k++)
                {
                    Assert.Equal(r.maneuvers[k].exit, p.ManExit[k]);
                    Assert.Equal(p.ManExit[k], q.ManExit[k]);
                    if (p.ManType[k] == Maneuver.Roundabout) rings++;
                }
            }
            Assert.True(rings >= 25, $"golden routes cross a roundabout often enough ({rings})");
        }

        // ------------------------------------------------------------------ voice tiers

        [Fact]
        public void Voice_TierTriggers_SpeedDependent()
        {
            float v30 = 30f / 3.6f, v50 = 50f / 3.6f, v80 = 80f / 3.6f;
            Assert.Equal(500f, NavVoiceDriver.FarM(v50)); Assert.Equal(200f, NavVoiceDriver.NearM(v50)); Assert.Equal(53.0, NavVoiceDriver.NowM(v50), 0.1);
            Assert.Equal(1000f, NavVoiceDriver.FarM(v80)); Assert.Equal(300f, NavVoiceDriver.NearM(v80)); Assert.Equal(115.6, NavVoiceDriver.NowM(v80), 0.1);
            Assert.Equal(500f, NavVoiceDriver.FarM(v30)); Assert.Equal(100f, NavVoiceDriver.NearM(v30)); Assert.Equal(NavVoiceDriver.NowMinM, NavVoiceDriver.NowM(v30));
            Assert.Equal(NavVoiceDriver.TierNone, NavVoiceDriver.TierFor(600f, v50));
            Assert.Equal(NavVoiceDriver.TierFar, NavVoiceDriver.TierFor(480f, v50));
            Assert.Equal(NavVoiceDriver.TierNear, NavVoiceDriver.TierFor(190f, v50));
            Assert.Equal(NavVoiceDriver.TierNow, NavVoiceDriver.TierFor(50f, v50));
            Assert.Equal(2, NavVoiceDriver.BandForTier(NavVoiceDriver.TierFar, 480f));     // "za 500 m"
            Assert.Equal(1, NavVoiceDriver.BandForTier(NavVoiceDriver.TierFar, 990f));     // "za 1 km"
            Assert.Equal(4, NavVoiceDriver.BandForTier(NavVoiceDriver.TierNear, 190f));    // "za 200 m"
            Assert.Equal(NavVoice.NowBand, NavVoiceDriver.BandForTier(NavVoiceDriver.TierNow, 50f));
        }

        /// <summary>Drives every golden route at 30 / 50 / 80 km/h (2 m steps) and counts the announcements per manoeuvre:
        /// at most 3, tiers strictly increasing (far -> near -> now), the first manoeuvre seen from far away gets all three.</summary>
        [Fact]
        public void Voice_GoldenRoutes_AtMostThreePerManeuver_Ordered()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            var tr = new RouteTracker(); var drv = new NavVoiceDriver(); var q = new NavVoiceQueue();
            int routes = 0, maxPer = 0, threes = 0;
            foreach (var r in Golden())
            {
                Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2((float)r.from[0], (float)r.from[1]), float.NaN, new Vector2((float)r.to[0], (float)r.to[1]), p));
                foreach (float kmh in new[] { 30f, 50f, 80f })
                {
                    var count = new int[p.ManCount]; var lastTier = new int[p.ManCount];
                    tr.Reset(); drv.Reset(); q.Clear();
                    var gd = new NavGuidance();
                    float v = kmh / 3.6f;
                    for (float s = 0f; s <= p.Length; s += 2f)
                    {
                        Pose(p, s, out Vector2 pos, out float hdg);
                        tr.Update(p, pos, hdg, v, 2f / v, ref gd);
                        int enq = drv.Update(g, p, ref gd, v, q);
                        while (q.TryDequeue(out _)) { }
                        int m = drv.CurrentManeuver;
                        if (m < 0) continue;
                        if (drv.LastTier != lastTier[m])
                        {
                            Assert.True(drv.LastTier > lastTier[m], $"{r.id} @{kmh}: tier goes forward only");
                            Assert.True(enq > 0 || p.ManType[m] == Maneuver.Continue, $"{r.id} @{kmh}: a new tier says something");
                            lastTier[m] = drv.LastTier; count[m]++;
                        }
                    }
                    for (int k = 0; k < p.ManCount; k++)
                    {
                        Assert.True(count[k] <= 3, $"{r.id} @{kmh} km/h manoeuvre {k} ({p.ManType[k]}): {count[k]} announcements");
                        maxPer = Mathf.Max(maxPer, count[k]);
                        if (count[k] == 3) threes++;
                    }
                }
                routes++;
            }
            Assert.True(routes >= 30);
            Assert.Equal(3, maxPer);
            Assert.True(threes > 0);
        }

        /// <summary>Distance drift (jitter / stopping / reversing a few metres) and the guidance flipping back to a passed
        /// manoeuvre never repeat a sentence; a closer tier is still said once.</summary>
        [Fact]
        public void Voice_DriftAndFlipBack_NoRepeats()
        {
            var g = RouteGraph.Load(Region);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, new RoutePlanner(g).Plan(new Vector2(-225.64f, -239.35f), float.NaN, new Vector2(-513.81f, -500.29f), p));   // G07
            int k = -1;
            for (int i = 0; i < p.ManCount; i++) if (p.ManType[i] == Maneuver.Right && g.Names[p.ManName[i]] == "Wileńska") k = i;
            Assert.True(k > 0);
            float v = 50f / 3.6f;
            var drv = new NavVoiceDriver(); var q = new NavVoiceQueue();
            var gd = new NavGuidance { Next = k, Then = -1, NextLaneSrc = -1 };
            int Say(float dist) { gd.Next = k; gd.NextM = dist; int n = drv.Update(g, p, ref gd, v, q); while (q.TryDequeue(out _)) { } return n; }
            Assert.True(Say(480f) > 0, "far");
            int extra = 0;
            for (int i = 0; i < 400; i++) extra += Say(480f + 30f * Mathf.Sin(i * 0.7f));   // drift across the 500 m trigger
            Assert.True(Say(195f) > 0, "near");
            for (int i = 0; i < 400; i++) extra += Say(195f + 20f * Mathf.Sin(i * 0.9f));   // drift across the 200 m trigger
            for (int i = 0; i < 50; i++) extra += Say(400f);                                  // reversing far back
            Assert.Equal(0, extra);
            Assert.True(Say(40f) > 0, "now");
            for (int i = 0; i < 100; i++) extra += Say(40f + 40f * Mathf.Sin(i));
            Assert.Equal(0, extra);
            // Flip back: the next manoeuvre becomes k + 1, the tracker briefly reports k again (projection noise at the node).
            gd.Next = k + 1; gd.NextM = 150f; drv.Update(g, p, ref gd, v, q); while (q.TryDequeue(out _)) { }
            gd.Next = k; gd.NextM = 0.5f;
            Assert.Equal(0, drv.Update(g, p, ref gd, v, q));
            // A new route starts over.
            Assert.Equal(PlanStatus.Ok, new RoutePlanner(g).Plan(new Vector2(-225.64f, -239.35f), float.NaN, new Vector2(-513.81f, -500.29f), p));
            gd.Next = k; gd.NextM = 480f;
            Assert.True(drv.Update(g, p, ref gd, v, q) > 0, "re-planned route: far said again");
        }

        [Fact]
        public void Voice_ZeroGc_GoldenDrive()
        {
            var g = RouteGraph.Load(Region);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, new RoutePlanner(g).Plan(new Vector2(-1.7f, -897.8f), float.NaN, new Vector2(-457.95f, -55.97f), p));   // G02
            var tr = new RouteTracker(); var drv = new NavVoiceDriver(); var q = new NavVoiceQueue();
            var gd = new NavGuidance();
            float v = 50f / 3.6f;
            void Drive()
            {
                tr.Reset(); drv.Reset();
                for (float s = 0f; s <= p.Length; s += 2f)
                {
                    Pose(p, s, out Vector2 pos, out float hdg);
                    tr.Update(p, pos, hdg, v, 2f / v, ref gd);
                    drv.Update(g, p, ref gd, v, q);
                    while (q.TryDequeue(out _)) { }
                }
            }
            GcAllocCounter.AssertZero(Drive, warmup: Drive, message: "tracker (1 Hz ETA) + 3-tier voice driver allocate nothing");
        }

        // ------------------------------------------------------------------ ETA throttling

        [Fact]
        public void Eta_ThrottledTo1Hz_ImmediateOnNewRoute()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(-1.7f, -897.8f), float.NaN, new Vector2(-172f, -298f), p));   // G01
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            float v = 50f / 3.6f, dt = 0.02f;   // 50 Hz frames
            Pose(p, 0f, out Vector2 pos0, out float h0);
            tr.Update(p, pos0, h0, v, dt, ref gd);
            Assert.Equal(1, tr.EtaComputations);
            Assert.Equal(NavEta.RemainingSeconds(p, gd.RouteS), gd.RemainingSeconds, 0.01);
            float s = 0f, lastEta = gd.RemainingSeconds, computedAt = gd.RouteS;
            int frames = 500;   // 10 s
            for (int i = 0; i < frames; i++)
            {
                s += v * dt;
                Pose(p, s, out Vector2 pos, out float hdg);
                int before = tr.EtaComputations;
                tr.Update(p, pos, hdg, v, dt, ref gd);
                if (tr.EtaComputations != before) { computedAt = gd.RouteS; lastEta = gd.RemainingSeconds; }
                else Assert.Equal(lastEta, gd.RemainingSeconds);   // held between refreshes
                Assert.Equal(NavEta.RemainingSeconds(p, computedAt), gd.RemainingSeconds, 0.01);
            }
            Assert.InRange(tr.EtaComputations, 10, 12);   // 1 + 10 s at 1 Hz (float accumulation)
            // A new route is computed on the first frame.
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(-172f, -298f), float.NaN, new Vector2(-1.7f, -897.8f), p));
            int c0 = tr.EtaComputations;
            Pose(p, 0f, out pos0, out h0);
            tr.Update(p, pos0, h0, v, dt, ref gd);
            Assert.Equal(c0 + 1, tr.EtaComputations);
            Assert.Equal(NavEta.RemainingSeconds(p, gd.RouteS), gd.RemainingSeconds, 0.01);
        }

        // ------------------------------------------------------------------ helpers

        static void Pose(RoutePath p, float s, out Vector2 pos, out float headingDeg)
        {
            int i = 1;
            while (i < p.Count - 1 && p.S[i] < s) i++;
            float l = p.S[i] - p.S[i - 1];
            float t = l > 1e-4f ? Mathf.Clamp01((s - p.S[i - 1]) / l) : 1f;
            Vector2 a = p.Points[i - 1], b = p.Points[i];
            pos = a + (b - a) * t;
            Vector2 d = b - a;
            headingDeg = Mathf.Atan2(d.x, d.y) * Mathf.Rad2Deg;
        }

        static List<GoldenRoutesTests.GoldenRoute> Golden()
        {
            string file = Path.Combine(System.AppContext.BaseDirectory, "golden_routes.json");
            return JsonSerializer.Deserialize<GoldenRoutesTests.GoldenDoc>(File.ReadAllText(file)).routes;
        }
    }
}
