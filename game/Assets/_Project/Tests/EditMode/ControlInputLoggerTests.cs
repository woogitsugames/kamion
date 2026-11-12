using System;
using System.Collections.Generic;
using Game.Controls;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>The [CONTROLS] input log: change-driven, rate-limited, silent when idle, batched, zero GC while recording.</summary>
    public class ControlInputLoggerTests
    {
        static DriverIntent Axes(float steer, float thr, float brk) => new DriverIntent { Steer = steer, SteerActive = true, Throttle = thr, Brake = brk };

        [Test]
        public void IdleFrames_WriteNothing()
        {
            var lines = new List<string>();
            var log = new ControlInputLogger(lines.Add);
            for (int i = 0; i < 100; i++) log.Observe(i * 0.016f, default, 0f);
            log.Flush();
            Assert.AreEqual(0, lines.Count);
        }

        [Test]
        public void Axes_AreRecordedOnChange_RateLimited_AndOnReturnToRest()
        {
            var lines = new List<string>();
            var log = new ControlInputLogger(lines.Add);
            log.Observe(10f, Axes(0f, 0.6f, 0f), 12.34f);
            log.Observe(10.05f, Axes(0.5f, 0.6f, 0f), 12.4f);        // inside the 0.25 s window
            log.Observe(10.30f, Axes(-0.5f, 0.6f, 0f), 13f);          // window elapsed, steering changed
            log.Observe(10.60f, Axes(-0.52f, 0.6f, 0f), 13f);         // change below the threshold
            log.Observe(11f, Axes(0f, 0f, 0f), 13f);                  // everything released: one rest line
            log.Observe(11.5f, Axes(0f, 0f, 0f), 13f);                // no repeated rest lines
            Assert.AreEqual(0, lines.Count, "nothing is written on the hot path");
            Assert.AreEqual(3, log.Pending);
            log.Flush();
            Assert.AreEqual(3, lines.Count);
            StringAssert.StartsWith("[CONTROLS] in t=0.00 steer=+0.00 thr=0.60 brk=0.00 v=12.3", lines[0]);
            StringAssert.Contains("steer=-0.50", lines[1]);
            StringAssert.Contains("thr=0.00", lines[2]);
            Assert.AreEqual(0, log.Pending);
        }

        [Test]
        public void Commands_AreRecordedTheFrameTheyHappen()
        {
            var lines = new List<string>();
            var log = new ControlInputLogger(lines.Add);
            log.Observe(1f, new DriverIntent { Selector = SelectorRequest.Reverse, ShiftDelta = -1, ToggleParkingBrake = true }, 0f);
            log.Event(2f, "camera mode=Chase");
            log.Flush();
            Assert.AreEqual(2, lines.Count);
            StringAssert.Contains("[CONTROLS] cmd t=0.00", lines[0]);
            StringAssert.Contains("selector=Reverse", lines[0]);
            StringAssert.Contains("shift=-1", lines[0]);
            StringAssert.Contains("parking=toggle", lines[0]);
            StringAssert.Contains("[CONTROLS] event t=1.00 camera mode=Chase", lines[1]);
        }

        [Test]
        public void TryFlush_WaitsForIdleAndInterval_AndFlushesWhenRingIsNearlyFull()
        {
            var lines = new List<string>();
            var log = new ControlInputLogger(lines.Add);
            log.Observe(0f, Axes(0f, 0.5f, 0f), 1f);
            Assert.IsFalse(log.TryFlush(0f, true));
            Assert.IsFalse(log.TryFlush(5f, true), "interval not elapsed");
            Assert.IsFalse(log.TryFlush(11f, false), "input active: not now");
            Assert.IsTrue(log.TryFlush(11f, true));
            Assert.AreEqual(1, lines.Count);
            for (int i = 0; i < ControlInputLogger.Capacity * 3 / 4; i++) log.Event(20f, "x");
            Assert.IsTrue(log.TryFlush(20f, false), "ring nearly full flushes regardless");
        }

        [Test]
        public void RingOverflow_DropsOldest_AndReportsIt()
        {
            var lines = new List<string>();
            var log = new ControlInputLogger(lines.Add);
            for (int i = 0; i < ControlInputLogger.Capacity + 5; i++) log.Event(i, "e");
            Assert.AreEqual(ControlInputLogger.Capacity, log.Pending);
            log.Flush();
            StringAssert.Contains("dropped=5", lines[0]);
        }

        [Test]
        public void Recording_AllocatesNoManagedMemory_InSteadyDrivingWithInputChanges()
        {
            var cmd = new DriverIntent { ShiftDelta = 1, ToggleParkingBrake = true };
            const int frames = 1500;
            static void RunDrive(ControlInputLogger target, in DriverIntent command)
            {
                for (int i = 0; i < frames; i++)
                {
                    float t = 10f + i * 0.016f;
                    target.Observe(t, Axes((float)Math.Sin(i * 0.05), 0.5f + 0.5f * (float)Math.Sin(i * 0.02), i % 300 < 20 ? 0.8f : 0f), 40f + i * 0.01f);
                    if (i % 200 == 0) target.Observe(t, command, 40f);
                    if (i % 250 == 0) target.Event(t, "camera mode=Chase");
                    target.TryFlush(t, false);   // never flushes while input is active and the ring has room
                }
            }
            // Warm up (JIT, ring touch, all branches) on a separate instance so m_LastAxisT on `log` stays -Infinity.
            var warm = new ControlInputLogger(_ => { });
            var log = new ControlInputLogger(_ => { });
            GcAllocCounter.AssertZero(
                () => RunDrive(log, cmd),
                warmup: () => { RunDrive(warm, cmd); warm.Flush(); },
                message: "recording must not allocate");
            Assert.Greater(log.Pending, 20, "the drive really recorded entries");
        }
    }
}
