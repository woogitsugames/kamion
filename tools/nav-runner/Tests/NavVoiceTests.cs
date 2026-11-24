// Voice sentence choice (M35 point 5): pure functions of (manoeuvre, distance, speed, lanes, street, next manoeuvre)
// -> GPS_Bxx #n clips from docs/owner/ELEVENLABS-GPS-VOICE.md; speed-dependent distance bands with the WORKING_VALUE
// reaction + braking rachunek; queue without repeats; zero allocation. Simulated on golden routes.
using System.Collections.Generic;
using Game.Core.Navigation;
using UnityEngine;
using Xunit;

namespace NavRunner.Tests
{
    public class NavVoiceTests
    {
        const string Region = "bialystok-industrial-c";

        [Fact]
        public void SafeAnnounce_Derivation()
        {
            // d(v) = v*1.5 + v^2/6: 80 km/h = 22.22 m/s -> 115.6 m; 50 km/h = 13.89 m/s -> 53.0 m.
            Assert.Equal(115.6, NavVoice.SafeAnnounceM(80f / 3.6f), 0.1);
            Assert.Equal(53.0, NavVoice.SafeAnnounceM(50f / 3.6f), 0.1);
        }

        [Fact]
        public void BandFor_SpeedDependent()
        {
            float v80 = 80f / 3.6f, v50 = 50f / 3.6f;
            Assert.Equal(-1, NavVoice.BandFor(2500f, v50));                 // too far: no announcement
            Assert.Equal(0, NavVoice.BandFor(1500f, v50));                  // 2 km band
            Assert.Equal(2, NavVoice.BandFor(450f, v50));                   // 500 m
            Assert.Equal(3, NavVoice.BandFor(300f, v50));                   // 300 m
            Assert.Equal(5, NavVoice.BandFor(100f, v50));                   // 100 m (50 km/h: safe = 53 m < 100)
            Assert.Equal(NavVoice.NowBand, NavVoice.BandFor(100f, v80));    // 80 km/h: safe = 116 m > 100 -> "now"
            Assert.Equal(NavVoice.NowBand, NavVoice.BandFor(50f, v50));
            Assert.Equal(3, NavVoice.BandFor(300f, v80));                   // 300 m still allowed at 80 km/h
        }

        [Fact]
        public void ClipMappings_MatchThePack()
        {
            Assert.Equal(1, NavVoice.ManIndex(Maneuver.Right));
            Assert.Equal(2, NavVoice.ManIndex(Maneuver.Left));
            Assert.Equal(8, NavVoice.ManIndex(Maneuver.Roundabout));
            Assert.Equal(6, NavVoice.ManIndexKm(Maneuver.Right, true));    // B06 #6 = "za dwa kilometry skręć w prawo"
            Assert.Equal(1, NavVoice.ManIndexKm(Maneuver.Right, false));
            var w = NavVoice.StreetClip("Wileńska");
            Assert.Equal(new VoiceClip(12, 10), w);                          // GPS_B12 #10 = "w Wileńską"
            Assert.Equal(new VoiceClip(12, 1), NavVoice.StreetClip("Generała Władysława Andersa"));
            Assert.Equal(new VoiceClip(0, 0), NavVoice.StreetClip("coś nie z packa"));
            Assert.Equal(new VoiceClip(14, 1), NavVoice.RoundaboutNameClip("Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP"));
            Assert.Equal(new VoiceClip(14, 2), NavVoice.RoundaboutNameClip("Rondo Pamięci Bieżeństwa 1915 roku"));
            Assert.Equal(new VoiceClip(15, 1), NavVoice.RoundaboutNominativeClip("Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP"));
            Assert.Equal(new VoiceClip(15, 2), NavVoice.RoundaboutNominativeClip("Rondo Pamięci Bieżeństwa 1915 roku"));
            Assert.Equal(new VoiceClip(0, 0), NavVoice.RoundaboutNominativeClip("Rondo Radosława"));
            Assert.Equal(new VoiceClip(0, 0), NavVoice.RoundaboutNominativeClip(null));
            Assert.Equal(new VoiceClip(7, 4), NavVoice.RoundaboutExitClip(-100f, 4));
            Assert.Equal(new VoiceClip(7, 6), NavVoice.RoundaboutExitClip(-178f, 4));   // turn round on the roundabout
            Assert.Equal(new VoiceClip(8, 7), NavVoice.ThenClip(Maneuver.Arrive));
            Assert.Equal(new VoiceClip(9, 1), NavVoice.LaneClip(3, 0b100u));             // rightmost lane
            Assert.Equal(new VoiceClip(9, 2), NavVoice.LaneClip(3, 0b001u));             // leftmost lane
            Assert.Equal(new VoiceClip(0, 0), NavVoice.LaneClip(1, 0b1u));               // single lane: no guidance
        }

        [Fact]
        public void Queue_NoRepeats_ZeroAlloc()
        {
            var q = new NavVoiceQueue();
            var a = new VoiceClip(4, 1); var b = new VoiceClip(12, 10); var c = new VoiceClip(3, 2); var d = new VoiceClip(5, 1);
            // Only the queue calls are inside the measured window (xUnit asserts allocate); results checked afterwards.
            var ok = new bool[12]; var outs = new VoiceClip[5];
            q.Enqueue(a); q.Clear(); q.TryDequeue(out _);   // JIT warm-up
            int count = 0;
            GcAllocCounter.AssertZero(() =>
            {
                ok[0] = q.Enqueue(a);
                ok[1] = !q.Enqueue(a);   // immediate repeat dropped
                ok[2] = q.Enqueue(b);
                ok[3] = !q.Enqueue(b);
                ok[4] = !q.Enqueue(a);   // repeat inside the 3-clip window dropped
                ok[5] = q.Enqueue(c);
                ok[6] = q.Enqueue(d);
                ok[7] = q.Enqueue(a);    // repeat after 3 different clips allowed
                count = q.Count;
                for (int i = 0; i < 5; i++) q.TryDequeue(out outs[i]);
                ok[8] = !q.TryDequeue(out _);
            }, message: "voice queue allocates nothing");
            for (int i = 0; i <= 8; i++) Assert.True(ok[i], "queue step " + i);
            Assert.Equal(5, count);
            Assert.Equal(new[] { a, b, c, d, a }, outs);
        }

        [Fact]
        public void GoldenRoute_AndersaToWilenska_AnnouncesB03_1_AndB12_10()
        {
            // G07: Andersa -> Wileńska; the third manoeuvre is Right (59°) onto Wileńska.
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(-225.64f, -239.35f), float.NaN, new Vector2(-513.81f, -500.29f), p));
            int rightIdx = -1;
            for (int k = 0; k < p.ManCount; k++) if (p.ManType[k] == Maneuver.Right && g.Names[p.ManName[k]] == "Wileńska") rightIdx = k;
            Assert.True(rightIdx >= 0, "right turn onto Wileńska on the route");

            var tr = new RouteTracker();
            var driver = new NavVoiceDriver();
            var queue = new NavVoiceQueue();
            var gd = new NavGuidance();
            float speed = 50f / 3.6f;   // 50 km/h
            bool sawB03_1 = false, sawB12_10 = false;
            for (int i = 0; i < p.Count; i++)
            {
                Vector2 pos = p.Points[i];
                Vector2 ahead = p.Points[System.Math.Min(i + 1, p.Count - 1)];
                Vector2 d = ahead - pos;
                float heading = d.sqrMagnitude > 1e-6f ? Mathf.Atan2(d.x, d.y) * Mathf.Rad2Deg : 0f;
                tr.Update(p, pos, heading, speed, 0.1f, ref gd);
                driver.Update(g, p, ref gd, speed, queue);
                while (queue.TryDequeue(out var c))
                {
                    if (c == new VoiceClip(3, 1)) sawB03_1 = true;    // "Za dwieście metrów skręć w prawo" (near tier at 50 km/h, ADR 0168)
                    if (c == new VoiceClip(12, 10)) sawB12_10 = true;  // "w Wileńską"
                }
            }
            Assert.True(sawB03_1, "B03 #1 announced at the 200 m band (near tier at 50 km/h)");
            Assert.True(sawB12_10, "B12 #10 (Wileńska) suffix announced");
        }

        [Fact]
        public void GoldenRoute_Roundabout_AnnouncesExitAndRingName()
        {
            // G03: Andersa -> Kombatantów enters Rondo Putry with exit 2.
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(-225.64f, -239.35f), float.NaN, new Vector2(-205.02f, -854.88f), p));
            int rbIdx = -1;
            for (int k = 0; k < p.ManCount; k++) if (p.ManType[k] == Maneuver.Roundabout) rbIdx = k;
            Assert.True(rbIdx >= 0);

            var tr = new RouteTracker();
            var driver = new NavVoiceDriver();
            var queue = new NavVoiceQueue();
            var gd = new NavGuidance();
            float speed = 50f / 3.6f;
            bool sawB07_2 = false, sawB14 = false, sawB15_1 = false, b15AfterB07 = false;
            VoiceClip prev = default;
            for (int i = 0; i < p.Count; i++)
            {
                Vector2 pos = p.Points[i];
                Vector2 ahead = p.Points[System.Math.Min(i + 1, p.Count - 1)];
                Vector2 d = ahead - pos;
                float heading = d.sqrMagnitude > 1e-6f ? Mathf.Atan2(d.x, d.y) * Mathf.Rad2Deg : 0f;
                tr.Update(p, pos, heading, speed, 0.1f, ref gd);
                driver.Update(g, p, ref gd, speed, queue);
                while (queue.TryDequeue(out var c))
                {
                    if (c == new VoiceClip(7, 2)) sawB07_2 = true;    // "Na rondzie zjedź drugim zjazdem"
                    if (c.Block == 14) sawB14 = true;   // "na rondzie Putry" - would repeat "na rondzie" (ADR 0329)
                    if (c == new VoiceClip(15, 1)) { sawB15_1 = true; if (prev == new VoiceClip(7, 2)) b15AfterB07 = true; }   // "Rondo Putry." (nominative)
                    prev = c;
                }
            }
            Assert.True(sawB07_2, "B07 #2 (second exit) announced");
            Assert.True(sawB15_1, "B15 #1 (Rondo Putry, nominative) announced");
            Assert.True(b15AfterB07, "B15 #1 directly after B07 #2 (Na rondzie zjedz drugim zjazdem. Rondo Putry.)");
            Assert.False(sawB14, "B14 (na rondzie X) is not announced after B07 (Na rondzie zjedz ...): double na rondzie, ADR 0329");
        }

        [Fact]
        public void Announcer_LogsRoundaboutLineWithRingName_OnlyWhenEnabled()
        {
            // G03: Andersa -> Kombatantów enters Rondo Putry. NAVVOICE log (-nav_log): one line per announcement, only when enabled.
            var g = RouteGraph.Load(Region);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, new RoutePlanner(g).Plan(new Vector2(-225.64f, -239.35f), float.NaN, new Vector2(-205.02f, -854.88f), p));
            float speed = 50f / 3.6f;
            List<string> Drive(bool enabled)
            {
                var lines = new List<string>();
                var ann = new NavVoiceAnnouncer { LogEnabled = enabled, Sink = lines.Add, Spoken = (c, n) => { } };
                var tr = new RouteTracker();
                var gd = new NavGuidance();
                float t = 0f;
                for (int i = 0; i < p.Count; i++)
                {
                    Vector2 pos = p.Points[i];
                    Vector2 d = p.Points[System.Math.Min(i + 1, p.Count - 1)] - pos;
                    float heading = d.sqrMagnitude > 1e-6f ? Mathf.Atan2(d.x, d.y) * Mathf.Rad2Deg : 0f;
                    tr.Update(p, pos, heading, speed, 0.1f, ref gd);
                    ann.Update(g, p, ref gd, speed, t += 0.1f);
                }
                return lines;
            }
            var on = Drive(true);
            Assert.NotEmpty(on);
            Assert.All(on, l => Assert.StartsWith("NAVVOICE t=", l));
            Assert.DoesNotContain(on, l => l.Contains("B14#"));
            Assert.Contains(on, l => l.Contains("B07#2,B15#1"));   // ADR 0329 addendum: nominative ring name after the exit sentence
            Assert.Contains(on, l => l.Contains("B07#2") && l.Contains("ring=\"Rondo Krzysztofa Jakuba Putry"));
            Assert.Empty(Drive(false));   // flag off: Spoken still fires, but nothing is logged
        }

        [Fact]
        public void Arrive_IsSpokenOnlyAtTheDestination_AndAlone()
        {
            // ADR 0329: the pack has no "za X metrow cel" - "Jestes u celu" (B10 #11) only in the now band, as the only clip.
            var g = RouteGraph.Load(Region);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, new RoutePlanner(g).Plan(new Vector2(-225.64f, -239.35f), float.NaN, new Vector2(-205.02f, -854.88f), p));
            int last = p.ManCount - 1;
            Assert.Equal(Maneuver.Arrive, p.ManType[last]);
            var buf = new VoiceClip[6];
            var gd = new NavGuidance { Next = last, Then = -1, NextM = 450f, NextLaneCount = 3, NextLanesRec = 1u };
            for (int band = -1; band < NavVoice.NowBand; band++)
                Assert.Equal(0, NavVoice.PlanBand(g, p, ref gd, band, buf));
            Assert.Equal(1, NavVoice.PlanBand(g, p, ref gd, NavVoice.NowBand, buf));
            Assert.Equal(new VoiceClip(10, 11), buf[0]);
            // Whole drive at 80 km/h and 50 km/h: B10 #11 is announced at most once, alone, and only within the now distance.
            foreach (float kmh in new[] { 80f, 50f })
            {
                float v = kmh / 3.6f;
                var ann = new NavVoiceAnnouncer { Spoken = (c, n) => { } };
                var drv = new NavVoiceDriver(); var q = new NavVoiceQueue(); var tr = new RouteTracker(); var g2 = new NavGuidance();
                int arrive = 0;
                for (int i = 0; i < p.Count; i++)
                {
                    Vector2 pos = p.Points[i];
                    Vector2 d = p.Points[System.Math.Min(i + 1, p.Count - 1)] - pos;
                    float heading = d.sqrMagnitude > 1e-6f ? Mathf.Atan2(d.x, d.y) * Mathf.Rad2Deg : 0f;
                    tr.Update(p, pos, heading, v, 0.1f, ref g2);
                    int n = drv.Update(g, p, ref g2, v, q);
                    int cnt = 0; bool has = false;
                    while (q.TryDequeue(out var c)) { cnt++; if (c == new VoiceClip(10, 11)) has = true; }
                    if (!has) continue;
                    arrive++;
                    Assert.Equal(1, cnt);
                    Assert.True(g2.NextM <= NavVoiceDriver.NowM(v) + 1f, "B10 #11 only at the destination, NextM=" + g2.NextM);
                }
                Assert.Equal(1, arrive);
            }
        }

        [Fact]
        public void RingName_SkipsUnnamedEntryLink()
        {
            // Regression (graph after wave 6): the path segment at the roundabout manoeuvre point is an unnamed entry link;
            // the ring name must come from the first named segment after it.
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(-225.64f, -239.35f), float.NaN, new Vector2(-205.02f, -854.88f), p));
            int rb = -1;
            for (int k = 0; k < p.ManCount; k++) if (p.ManType[k] == Maneuver.Roundabout) rb = k;
            Assert.True(rb >= 0);
            Assert.Equal(new VoiceClip(14, 1), NavVoice.RoundaboutNameClip(NavVoice.RingName(g, p, rb)));
        }

        [Fact]
        public void RingName_NamedIncomingRoadWithAxisGap_StillResolvesRingAndB15()
        {
            // Regression (ADR 0329 addendum): shifted carriageway axes can leave a >1 cm gap between a named incoming road
            // and the first ring edge; ManPoint must point to the ring, not the incoming road (G05 Putry, G18 Biezenstwa).
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);

            // G05: Al. Tysiaclecia -> Rondo Putry (0.375 m entry axis gap; used to return "Aleja Tysiaclecia..." and drop B15#1).
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(-289.19f, -883.86f), float.NaN, new Vector2(-555.60f, -10.18f), p));
            int rb = -1;
            for (int k = 0; k < p.ManCount; k++) if (p.ManType[k] == Maneuver.Roundabout) rb = k;
            Assert.True(rb >= 0);
            string ring = NavVoice.RingName(g, p, rb);
            Assert.StartsWith("Rondo Krzysztofa Jakuba Putry", ring);
            Assert.Equal(new VoiceClip(15, 1), NavVoice.RoundaboutNominativeClip(ring));

            // G18: Bitwy Bialostockiej -> Andersa via Rondo Pamieci Biezenstwa (0.251 m entry axis gap; used to drop B15#2).
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(507.36f, -810.43f), float.NaN, new Vector2(-225.64f, -239.35f), p));
            rb = -1;
            for (int k = 0; k < p.ManCount; k++) if (p.ManType[k] == Maneuver.Roundabout) rb = k;
            Assert.True(rb >= 0);
            ring = NavVoice.RingName(g, p, rb);
            Assert.StartsWith("Rondo Pamięci Bieżeństwa", ring);
            Assert.Equal(new VoiceClip(15, 2), NavVoice.RoundaboutNominativeClip(ring));
        }

        [Fact]
        public void RingName_UnnamedRoundabouts_ReturnNullAndNeverLeakAdjacentRoads()
        {
            // Build #7 audit (ADR 0329 addendum):
            // 1) dk65-06 DK65 roundabout (announced from dk65-05 at t~1326-1367 s) is genuinely unnamed in OSM/BDOT10k -> null.
            var gDk65 = RouteGraph.Load("dk65-06");
            var pDk65 = RoutePath.For(gDk65);
            var plDk65 = new RoutePlanner(gDk65) { AllowTileExit = true, RelaxTruckLimits = true };
            Assert.Equal(PlanStatus.Ok, plDk65.Plan(new Vector2(-94.1f, -1016f), float.NaN, new Vector2(-1016f, 306.5f), pDk65));
            int rb = -1;
            for (int k = 0; k < pDk65.ManCount; k++) if (pDk65.ManType[k] == Maneuver.Roundabout) rb = k;
            Assert.True(rb >= 0);
            Assert.Null(NavVoice.RingName(gDk65, pDk65, rb));
            Assert.Equal(new VoiceClip(0, 0), NavVoice.RoundaboutNominativeClip(NavVoice.RingName(gDk65, pDk65, rb)));

            // 2) knyszyn DK65/DW671 roundabout (t~2173-2211 s) is unnamed in OSM between named "Obozowa" and "Tykocka";
            //    RingName must return null and never leak incoming "Obozowa" or exit "Tykocka".
            var gKny = RouteGraph.Load("knyszyn");
            var pKny = RoutePath.For(gKny);
            var plKny = new RoutePlanner(gKny) { AllowTileExit = true, RelaxTruckLimits = true };
            Assert.Equal(PlanStatus.Ok, plKny.Plan(new Vector2(-623.9f, -1019.8f), 0f, new Vector2(-1021f, -638.5f), pKny));
            rb = -1;
            for (int k = 0; k < pKny.ManCount; k++) if (pKny.ManType[k] == Maneuver.Roundabout) rb = k;
            Assert.True(rb >= 0);
            Assert.Equal("Tykocka", gKny.Names[pKny.ManName[rb]]);
            Assert.Null(NavVoice.RingName(gKny, pKny, rb));
        }

        [Fact]
        public void RingName_SyntheticUnnamedRing_DoesNotLeakExitNameWhenNoGap()
        {
            // Zero-gap synthetic ring: unnamed ring between named "Wjazdowa" and "Wyjazdowa" must yield RingName == null.
            float r = 30f;
            var g = new RouteGraph
            {
                Names = new[] { "", "Wjazdowa", "Wyjazdowa" },
                NodePos = new[]
                {
                    new Vector2(-r, 0), new Vector2(0, -r), new Vector2(r, 0), new Vector2(0, r),
                    new Vector2(-200, 0), new Vector2(0, 200),
                },
                NodeFlags = new byte[6],
                EdgeFrom = new[] { 0, 1, 2, 3, 4, 3 },
                EdgeTo = new[] { 1, 2, 3, 0, 0, 5 },
                EdgeClass = new byte[] { 2, 2, 2, 2, 2, 2 },
                EdgeFlags = new byte[]
                {
                    RouteGraph.FlagRoundabout | RouteGraph.FlagOneway,
                    RouteGraph.FlagRoundabout | RouteGraph.FlagOneway,
                    RouteGraph.FlagRoundabout | RouteGraph.FlagOneway,
                    RouteGraph.FlagRoundabout | RouteGraph.FlagOneway,
                    0, 0,
                },
                EdgeName = new ushort[] { 0, 0, 0, 0, 1, 2 },
                EdgeMaxSpeed = new byte[6],
                EdgeMaxSpeedOsm = new bool[6],
                EdgeStart = new[] { 0, 2, 4, 6, 8, 10, 12 },
                Points = new[]
                {
                    new Vector2(-r, 0), new Vector2(0, -r),
                    new Vector2(0, -r), new Vector2(r, 0),
                    new Vector2(r, 0), new Vector2(0, r),
                    new Vector2(0, r), new Vector2(-r, 0),
                    new Vector2(-200, 0), new Vector2(-r, 0),
                    new Vector2(0, r), new Vector2(0, 200),
                },
                EdgeLength = new[] { 42.4f, 42.4f, 42.4f, 42.4f, 170f, 170f },
            };
            g.BuildAdjacency();
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, new RoutePlanner(g).Plan(new Vector2(-150, 0), 90f, new Vector2(0, 150), p));
            Assert.Equal(Maneuver.Roundabout, p.ManType[0]);
            Assert.Equal("Wyjazdowa", g.Names[p.ManName[0]]);
            Assert.Null(NavVoice.RingName(g, p, 0));
        }

        [Fact]
        public void Voice_NeverThrows_WhenPathNamesBelongToAnotherGraph()
        {
            // Regression (build #6): a multi-tile trip's Combined path carries TRIP name indices; voice used the start region's
            // graph and threw IndexOutOfRange in RingName after the first region change (22x, then silence). The service now
            // passes NavTrip.NamesGraph; NavVoice itself must also tolerate a foreign index.
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(-225.64f, -239.35f), float.NaN, new Vector2(-205.02f, -854.88f), p));
            var small = new RouteGraph { Names = new[] { "" } };   // every path name index >= 1 is foreign here
            int rb = -1;
            for (int k = 0; k < p.ManCount; k++) if (p.ManType[k] == Maneuver.Roundabout) rb = k;
            Assert.True(rb >= 0);
            Assert.Null(NavVoice.RingName(small, p, rb));
            var gd = new NavGuidance { Next = rb, Then = -1, HasRoute = true, OnRoute = true };
            var buf = new VoiceClip[8];
            for (int band = -1; band <= NavVoice.NowBand; band++) NavVoice.PlanBand(small, p, ref gd, band, buf);
        }

        [Fact]
        public void VoiceLoop_ZeroAllocation()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(-1.7f, -897.8f), float.NaN, new Vector2(-172f, -298f), p));
            var tr = new RouteTracker();
            var driver = new NavVoiceDriver();
            var queue = new NavVoiceQueue();
            var gd = new NavGuidance();
            float speed = 50f / 3.6f;
            tr.Update(p, p.Points[0], 0f, speed, 0.1f, ref gd);
            driver.Update(g, p, ref gd, speed, queue);
            GcAllocCounter.AssertZero(() =>
            {
                for (int i = 0; i < p.Count; i++)
                {
                    tr.Update(p, p.Points[i], 0f, speed, 0.1f, ref gd);
                    driver.Update(g, p, ref gd, speed, queue);
                    while (queue.TryDequeue(out _)) { }
                }
            }, message: "tracker + voice driver + queue allocate nothing");
        }
    }
}
