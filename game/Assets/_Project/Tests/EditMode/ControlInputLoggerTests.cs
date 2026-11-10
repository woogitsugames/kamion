using System.Collections.Generic;
using Game.Controls;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>The [CONTROLS] input log: change-driven, rate-limited, silent when idle, one line per command.</summary>
    public class ControlInputLoggerTests
    {
        static DriverIntent Axes(float steer, float thr, float brk) => new DriverIntent { Steer = steer, SteerActive = true, Throttle = thr, Brake = brk };

        [Test]
        public void IdleFrames_WriteNothing()
        {
            var lines = new List<string>();
            var log = new ControlInputLogger(lines.Add);
            for (int i = 0; i < 100; i++) log.Observe(i * 0.016f, default, 0f);
            Assert.AreEqual(0, lines.Count);
        }

        [Test]
        public void Axes_AreLoggedOnChange_RateLimited_AndOnReturnToRest()
        {
            var lines = new List<string>();
            var log = new ControlInputLogger(lines.Add);
            log.Observe(10f, Axes(0f, 0.6f, 0f), 12.34f);
            Assert.AreEqual(1, lines.Count);
            StringAssert.StartsWith("[CONTROLS] in t=0.00 steer=+0.00 thr=0.60 brk=0.00 v=12.3", lines[0]);
            log.Observe(10.05f, Axes(0.5f, 0.6f, 0f), 12.4f);        // inside the 0.25 s window
            Assert.AreEqual(1, lines.Count);
            log.Observe(10.30f, Axes(-0.5f, 0.6f, 0f), 13f);          // window elapsed, steering changed
            Assert.AreEqual(2, lines.Count);
            StringAssert.Contains("steer=-0.50", lines[1]);
            log.Observe(10.60f, Axes(-0.52f, 0.6f, 0f), 13f);         // change below the threshold
            Assert.AreEqual(2, lines.Count);
            log.Observe(11f, Axes(0f, 0f, 0f), 13f);                  // everything released: one rest line
            Assert.AreEqual(3, lines.Count);
            log.Observe(11.5f, Axes(0f, 0f, 0f), 13f);
            Assert.AreEqual(3, lines.Count, "no repeated rest lines");
        }

        [Test]
        public void Commands_AreLoggedTheFrameTheyHappen()
        {
            var lines = new List<string>();
            var log = new ControlInputLogger(lines.Add);
            log.Observe(1f, new DriverIntent { Selector = SelectorRequest.Reverse, ShiftDelta = -1, ToggleParkingBrake = true }, 0f);
            Assert.AreEqual(1, lines.Count);
            StringAssert.Contains("cmd", lines[0]);
            StringAssert.Contains("selector=Reverse", lines[0]);
            StringAssert.Contains("shift=-1", lines[0]);
            StringAssert.Contains("parking=toggle", lines[0]);
            log.Event(2f, "camera mode=Chase");
            StringAssert.Contains("[CONTROLS] event t=1.00 camera mode=Chase", lines[1]);
        }
    }
}
