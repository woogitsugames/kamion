using System.Collections.Generic;
using Game.Controls;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0350 (build #9, dk65-06 -autopilot route): the baked start at route_s 340 m was never sought, the follower began
    /// at 0 m and its 20-segment window locked on a local minimum (telemetry route_s stuck at 102.06 m); pure pursuit aimed
    /// ~240 m away, steered 0.46 deg, the combination left the road on the right at t = 12 s and rolled over at t = 19 s
    /// (artifacts/spawn-flip-s24/dk65-06-b9-drive.csv).
    /// </summary>
    public class PathFollowerStartTests
    {
        /// <summary>U-turn path: 100 m north, 20 m west, 200 m south (2 m points). Going north from the start moves away
        /// from a vehicle standing on the southbound leg below the start: the start point is a local minimum.</summary>
        static Vector3[] UTurn()
        {
            var pts = new List<Vector3>();
            for (int i = 0; i <= 50; i++) pts.Add(new Vector3(0f, 0f, 2f * i));
            for (int i = 1; i <= 10; i++) pts.Add(new Vector3(-2f * i, 0f, 100f));
            for (int i = 1; i <= 100; i++) pts.Add(new Vector3(-20f, 0f, 100f - 2f * i));
            return pts.ToArray();
        }

        static float Sample(PathFollowerDriverInput d, Vector3 pos, Vector3 fwd)
        {
            var fb = new VehicleFeedback { Position = pos, Forward = fwd, ForwardSpeed = 3f };
            var intent = new DriverIntent();
            d.Sample(0.02f, fb, ref intent);
            return intent.Steer;
        }

        [Test]
        public void VehicleFarAlongThePath_WithoutSeek_IsReacquired()
        {
            var d = new PathFollowerDriverInput();
            d.SetPath(UTurn());
            // On the southbound leg at z = -40, heading south: s = 100 + 20 + 140 = 260 m.
            Sample(d, new Vector3(-20f, 0f, -40f), Vector3.back);
            Assert.That(d.Progress, Is.EqualTo(260f).Within(0.5f), "window locked on a local minimum behind the vehicle");
            Assert.That(d.CrossTrackError, Is.LessThan(0.5f));
        }

        [Test]
        public void SeekTo_StartsAtTheGivenDistance()
        {
            var d = new PathFollowerDriverInput();
            d.SetPath(UTurn());
            d.SeekTo(260f);
            Sample(d, new Vector3(-20f, 0f, -40f), Vector3.back);
            Assert.That(d.Progress, Is.EqualTo(260f).Within(0.5f));
        }

        [Test]
        public void NearThePath_StaysMonotonic_NoJumpToALaterLeg()
        {
            // At the start, heading north, 1 m off the line: the southbound leg 20 m west must not capture the driver.
            var d = new PathFollowerDriverInput();
            d.SetPath(UTurn());
            Sample(d, new Vector3(1f, 0f, 10f), Vector3.forward);
            Assert.That(d.Progress, Is.EqualTo(10f).Within(0.5f));
            float steer = Sample(d, new Vector3(1f, 0f, 10f), Vector3.forward);
            Assert.That(steer, Is.LessThan(0f), "1 m right of the line: steer left");
        }
    }
}
