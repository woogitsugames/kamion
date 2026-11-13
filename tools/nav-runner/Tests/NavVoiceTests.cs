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
            bool sawB07_2 = false, sawB14_1 = false;
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
                    if (c == new VoiceClip(14, 1)) sawB14_1 = true;   // "na rondzie Putry"
                }
            }
            Assert.True(sawB07_2, "B07 #2 (second exit) announced");
            Assert.True(sawB14_1, "B14 #1 (Rondo Putry) announced");
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
