using System;
using Game.Gameplay;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0147: phones (elongated windows) always run in landscape - also when the app launches in portrait because the
    /// phone lies flat (A16, manifest fullUser) - and the Fold inner screen (near-square) keeps the ADR 0135 r3 behaviour.
    /// </summary>
    public sealed class OrientationPhoneTests
    {
        static readonly (string name, int w, int h)[] Phones =
        {
            ("A16 1080x2340", 1080, 2340), ("S24+ 1440x3120", 1440, 3120), ("Fold cover 1080x2520", 1080, 2520),
            ("16:9 720x1280", 720, 1280), ("16:10 tablet 1600x2560", 1600, 2560), ("4:3 tablet 1536x2048", 1536, 2048),
        };

        [Test]
        public void Policy_ElongatedLandscapeOnly_NearSquareAll()
        {
            foreach (var p in Phones)
            {
                foreach (var a in new[] { ScreenOrientationPolicy.Decide(p.w, p.h), ScreenOrientationPolicy.Decide(p.h, p.w) })
                {
                    Assert.IsFalse(a.Portrait, p.name); Assert.IsFalse(a.PortraitUpsideDown, p.name);
                    Assert.IsTrue(a.LandscapeLeft, p.name); Assert.IsTrue(a.LandscapeRight, p.name);
                }
                Assert.That(ScreenOrientationPolicy.Aspect(p.w, p.h), Is.GreaterThan(ScreenOrientationPolicy.NearSquareMaxAspect), p.name);
            }
            foreach (var (w, h) in new[] { (2176, 1812), (1812, 2176), (2184, 1968), (1968, 2184) })
            {
                var a = ScreenOrientationPolicy.Decide(w, h);
                Assert.IsTrue(a.Portrait && a.PortraitUpsideDown && a.LandscapeLeft && a.LandscapeRight, w + "x" + h + ": Fold inner, every orientation");
            }
        }

        [Test]
        public void Phone_LaunchedPortraitFlat_ForcedToLandscape_ThenLR()
        {
            foreach (var p in Phones)
            {
                foreach (var device in new[] { DeviceOrientation.FaceUp, DeviceOrientation.Unknown, DeviceOrientation.Portrait, DeviceOrientation.FaceDown })
                {
                    var l = new ScreenOrientationLock();
                    // A16 bug: the first frame used to be AllowAuto (--LR) and the window stayed portrait.
                    Assert.AreEqual(OrientationCommand.Lock, l.Step(0f, p.w, p.h, ScreenOrientation.Portrait, false, device), p.name + " " + device);
                    Assert.AreEqual(ScreenOrientation.LandscapeLeft, l.LockTo, p.name + ": flat/upright -> standard landscape");
                    Assert.IsTrue(l.Forcing);
                    // OS still rotating: nothing more is requested (no loop).
                    for (float t = 0.05f; t < 0.5f; t += 0.05f)
                        Assert.AreEqual(OrientationCommand.None, l.Step(t, p.w, p.h, ScreenOrientation.LandscapeLeft, false, device), p.name);
                    // Window is landscape: allow L/R auto-rotation (sensor flips between the two landscapes).
                    Assert.AreEqual(OrientationCommand.AllowAuto, l.Step(0.6f, p.h, p.w, ScreenOrientation.LandscapeLeft, false, device), p.name);
                    Assert.IsFalse(l.Forcing); Assert.IsFalse(l.Locked);
                    Assert.IsFalse(l.Allowed.Portrait); Assert.IsTrue(l.Allowed.LandscapeLeft && l.Allowed.LandscapeRight);
                    for (float t = 0.7f; t < 20f; t += 0.5f)
                        Assert.AreEqual(OrientationCommand.None, l.Step(t, p.h, p.w, t < 10f ? ScreenOrientation.LandscapeLeft : ScreenOrientation.LandscapeRight, false, device), p.name + ": L<->R by sensor, no command");
                }
            }
        }

        [Test]
        public void Phone_HeldInLandscapeRight_ForcedToThatLandscape()
        {
            var l = new ScreenOrientationLock();
            Assert.AreEqual(OrientationCommand.Lock, l.Step(0f, 1080, 2340, ScreenOrientation.Portrait, false, DeviceOrientation.LandscapeRight));
            Assert.AreEqual(ScreenOrientation.LandscapeRight, l.LockTo, "no 180 deg turn against the hands");
            Assert.AreEqual(ScreenOrientation.LandscapeLeft, ScreenOrientationLock.ForcedLandscape(DeviceOrientation.LandscapeLeft));
            Assert.AreEqual(ScreenOrientation.LandscapeLeft, ScreenOrientationLock.ForcedLandscape(DeviceOrientation.PortraitUpsideDown));
        }

        [Test]
        public void Phone_LaunchedLandscape_AllowAutoAtOnce_AsBefore()
        {
            var l = new ScreenOrientationLock();
            Assert.AreEqual(OrientationCommand.AllowAuto, l.Step(0f, 2340, 1080, ScreenOrientation.LandscapeLeft, false, DeviceOrientation.FaceUp));
            Assert.IsFalse(l.Forcing);
            Assert.AreEqual(OrientationCommand.None, l.Step(5f, 2340, 1080, ScreenOrientation.LandscapeRight, false));
        }

        [Test]
        public void Phone_OrientationRequestIgnored_NoLoop()
        {
            var l = new ScreenOrientationLock();
            Assert.AreEqual(OrientationCommand.Lock, l.Step(0f, 1080, 2340, ScreenOrientation.Portrait, false));
            for (float t = 0.1f; t < 60f; t += 0.1f)
                Assert.AreEqual(OrientationCommand.None, l.Step(t, 1080, 2340, ScreenOrientation.Portrait, false), "a freeform window ignoring the request: one request, no spam");
            Assert.IsTrue(l.Forcing);
        }

        [Test]
        public void Phone_ForcedThenGyro_LocksAfterSettle()
        {
            var l = new ScreenOrientationLock();
            Assert.AreEqual(OrientationCommand.Lock, l.Step(0f, 1080, 2340, ScreenOrientation.Portrait, true));
            Assert.AreEqual(OrientationCommand.AllowAuto, l.Step(0.3f, 2340, 1080, ScreenOrientation.LandscapeLeft, true));
            Assert.AreEqual(OrientationCommand.None, l.Step(1.0f, 2340, 1080, ScreenOrientation.LandscapeLeft, true), "settle after the rotation");
            Assert.AreEqual(OrientationCommand.Lock, l.Step(1.6f, 2340, 1080, ScreenOrientation.LandscapeLeft, true), "gyro: lock current landscape");
            Assert.AreEqual(ScreenOrientation.LandscapeLeft, l.LockTo);
            Assert.AreEqual(OrientationCommand.AllowAuto, l.Step(5f, 2340, 1080, ScreenOrientation.LandscapeLeft, false), "gyro off: unlock");
        }

        [Test]
        public void Fold_Unfold_Fold_NoRestart_InnerKeepsHolding_CoverForcedLandscape()
        {
            var l = new ScreenOrientationLock();
            // Cover screen, held upright at launch: forced landscape.
            Assert.AreEqual(OrientationCommand.Lock, l.Step(0f, 1080, 2520, ScreenOrientation.Portrait, false, DeviceOrientation.Portrait));
            Assert.AreEqual(OrientationCommand.AllowAuto, l.Step(0.4f, 2520, 1080, ScreenOrientation.LandscapeLeft, false));
            // Unfold: inner screen (r3) - the orientation it already has is locked, never a rotation request.
            Assert.AreEqual(OrientationCommand.Lock, l.Step(5f, 1812, 2176, ScreenOrientation.Portrait, false, DeviceOrientation.Portrait));
            Assert.AreEqual(ScreenOrientation.Portrait, l.LockTo, "inner screen: picture follows holding (r3)");
            Assert.IsFalse(l.Forcing);
            for (float t = 5.1f; t < 15f; t += 0.5f) Assert.AreEqual(OrientationCommand.None, l.Step(t, 1812, 2176, ScreenOrientation.Portrait, true));
            // Unfolded during the forcing itself: r3 wins, forcing dropped.
            var m = new ScreenOrientationLock();
            Assert.AreEqual(OrientationCommand.Lock, m.Step(0f, 1080, 2520, ScreenOrientation.Portrait, false));
            Assert.AreEqual(OrientationCommand.Lock, m.Step(0.1f, 2176, 1812, ScreenOrientation.LandscapeLeft, false));
            Assert.AreEqual(ScreenOrientation.LandscapeLeft, m.LockTo); Assert.IsFalse(m.Forcing);
            // Fold again, held upright: forced landscape again.
            Assert.AreEqual(OrientationCommand.Lock, l.Step(20f, 1080, 2520, ScreenOrientation.Portrait, false));
            Assert.IsTrue(l.Forcing);
        }

        [Test]
        public void Step_ZeroGcPerFrame()
        {
            var l = new ScreenOrientationLock();
            l.Step(0f, 1080, 2340, ScreenOrientation.Portrait, false, DeviceOrientation.FaceUp);   // warm-up (JIT)
            l.Step(0.5f, 2340, 1080, ScreenOrientation.LandscapeLeft, false, DeviceOrientation.FaceUp);
            var n = new ScreenOrientationLock();
            n.Step(0f, 1812, 2176, ScreenOrientation.Portrait, false);
            GcAllocCounter.AssertZero(() =>
            {
                for (int i = 0; i < 10000; i++)
                {
                    float t = 1f + i * 0.016f;
                    l.Step(t, 2340, 1080, (i / 500) % 2 == 0 ? ScreenOrientation.LandscapeLeft : ScreenOrientation.LandscapeRight, i % 3000 < 1500, DeviceOrientation.FaceUp);
                    n.Step(t, 1812, 2176, ScreenOrientation.Portrait, true);
                    ScreenOrientationPolicy.Decide(1080, 2340);
                }
            }, message: "0 GC.Alloc in the per-frame path");
        }
    }
}
