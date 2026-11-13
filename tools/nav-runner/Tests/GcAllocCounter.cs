// Same API as game/Assets/_Project/Tests/PlayMode/GcAllocCounter.cs (ADR 0157): Recorder("GC.Alloc") on the current
// thread, a control allocation proves the counter is live, then the measured action must allocate nothing (ADR 0168).
// In the .NET runner the Recorder is the shim in Sim/UnityShim.cs (bytes instead of samples; 0 means 0 either way).
// Asserts stay OUTSIDE the measured action (xUnit asserts allocate).
using System;
using UnityEngine.Profiling;
using Xunit;

namespace NavRunner.Tests
{
    public static class GcAllocCounter
    {
        public static int Count(Action action)
        {
            if (action == null) throw new ArgumentNullException(nameof(action));
            var r = Recorder.Get("GC.Alloc");
            r.enabled = false;
            r.FilterToCurrentThread();
            r.enabled = true;
            action();
            r.enabled = false;
            int samples = r.sampleBlockCount;
            r.CollectFromAllThreads();
            return samples;
        }

        public static void AssertZero(Action measured, Action warmup = null, int baselineSamples = 0, string message = null)
        {
            if (measured == null) throw new ArgumentNullException(nameof(measured));
            warmup?.Invoke();
            int control = Count(() => GC.KeepAlive(new byte[64]));
            Assert.True(control > 0, "control: GC.Alloc Recorder must see a 64 B allocation in this run");
            int net = Count(measured) - baselineSamples;
            Assert.True(net == 0, (message ?? "Expected 0 GC.Alloc") + $" (got {net})");
        }
    }
}
