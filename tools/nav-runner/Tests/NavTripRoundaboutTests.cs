using System.IO;
using System.Text.RegularExpressions;
using Game.Core.Navigation;
using Game.UI.Navigation;
using UnityEngine;
using Xunit;

namespace NavRunner.Tests
{
    public class NavTripRoundaboutTests
    {
        static (bool ok, double x, double y) Anchor(string id)
        {
            string file = Path.Combine(Application.dataPath, "..", "..", "Data", "Regions", id, "region.yaml");
            var match = Regex.Match(File.ReadAllText(file), @"origin:\s*\r?\n\s+x: ([\d.]+)\s*\r?\n\s+y: ([\d.]+)");
            return (match.Success, double.Parse(match.Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture),
                double.Parse(match.Groups[2].Value, System.Globalization.CultureInfo.InvariantCulture));
        }

        [Fact]
        public void Tykocin_ComposeAndTileSwitchKeepCurrentRoundaboutUntilExit()
        {
            string file = Path.Combine(Application.dataPath, "_Project", "Gameplay", "Resources", "Nav", "nav_trips.json");
            var data = JsonUtility.FromJson<NavTripsData>(File.ReadAllText(file)).Find("tykocin");
            var trip = new NavTrip(data, Anchor);
            trip.SetCurrent("dk65-05");
            var start = trip.Legs[trip.Current];
            while (!trip.StepPlan(start.Entry, start.EntryHeadingDeg)) { }
            Assert.False(trip.Failed, trip.FailReason);
            var anchor = Anchor("dk65-05");
            trip.Compose(anchor.x, anchor.y);
            CheckRoundabout(trip, anchor.x, anchor.y);
            trip.SetCurrent("dk65-06");
            anchor = Anchor("dk65-06");
            trip.Compose(anchor.x, anchor.y);
            CheckRoundabout(trip, anchor.x, anchor.y);
        }

        static void CheckRoundabout(NavTrip trip, double frameX, double frameY)
        {
            var leg = trip.Legs[trip.IndexOf("dk65-06")];
            var local = leg.Path;
            int rb = -1;
            for (int k = 0; k < local.ManCount; k++)
                if (local.ManType[k] == Maneuver.Roundabout) { rb = k; break; }
            Assert.True(rb >= 0);
            var p = trip.Combined;
            var offset = new Vector2((float)(leg.AnchorX - frameX), (float)(leg.AnchorY - frameY));
            Vector2 entry = local.Points[local.ManPoint[rb]] + offset;
            Vector2 exit = local.Points[local.ManEndPoint[rb]] + offset;
            int combined = -1;
            for (int k = 0; k < p.ManCount; k++)
                if (p.ManType[k] == Maneuver.Roundabout && Vector2.Distance(p.Points[p.ManPoint[k]], entry) < 0.1f)
                    combined = k;
            Assert.True(combined >= 0);
            Assert.True(Vector2.Distance(p.Points[p.ManEndPoint[combined]], exit) < 0.1f);
            var copy = new RoutePath(p.Points.Length, p.Directed.Length);
            copy.CopyFrom(p);
            Assert.Equal(p.ManEndPoint[combined], copy.ManEndPoint[combined]);
            var tracker = new RouteTracker();
            var guidance = new NavGuidance();
            for (int i = copy.ManPoint[combined]; i <= copy.ManEndPoint[combined]; i++)
            {
                tracker.Update(copy, copy.Points[i], 0f, 0f, 0.02f, ref guidance);
                Assert.Equal(combined, guidance.Next);
                Assert.Equal(2, (int)guidance.NextExit);
            }
            int nextPoint = copy.ManEndPoint[combined] + 1;
            tracker.Update(copy, copy.Points[nextPoint], 0f, 0f, 0.02f, ref guidance);
            Assert.True(guidance.Next > combined);
            Assert.Equal(Maneuver.Roundabout, copy.ManType[guidance.Next]);
            Assert.Equal(3, (int)guidance.NextExit);
            Assert.True(guidance.NextM > 10000f, "the later Knyszyn roundabout appears after the exit");
            GcAllocCounter.AssertZero(() =>
            {
                for (int n = 0; n < 100; n++)
                    tracker.Update(copy, exit, 0f, 0f, 0.02f, ref guidance);
            }, message: "roundabout tracking allocates nothing");
        }
    }
}
