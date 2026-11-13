using System;
using NUnit.Framework;
using UnityEngine.Profiling;

namespace Game.Tests
{
    /// <summary>
    /// Shared GC allocation counter using <see cref="Recorder"/> for the "GC.Alloc" profiler marker.
    /// <see cref="GC.GetAllocatedBytesForCurrentThread"/> returns 0 under Mono in the Unity editor,
    /// whereas <c>Recorder.Get("GC.Alloc").sampleBlockCount</c> captures real managed allocations in both
    /// EditMode and PlayMode.
    /// </summary>
    public static class GcAllocCounter
    {
        /// <summary>Number of GC.Alloc samples on the current thread while executing <paramref name="action"/>.</summary>
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

        /// <summary>
        /// Runs optional <paramref name="warmup"/>, verifies the GC.Alloc counter is live with a 64 B control
        /// allocation, then measures <paramref name="measured"/> and asserts 0 net GC.Alloc samples.
        /// </summary>
        public static void AssertZero(Action measured, Action warmup = null, int baselineSamples = 0, string message = null)
        {
            if (measured == null) throw new ArgumentNullException(nameof(measured));
            warmup?.Invoke();
            int control = Count(() => GC.KeepAlive(new byte[64]));
            Assert.Greater(control, 0, "control: GC.Alloc Recorder must see a 64 B allocation in this run");
            int net = Count(measured) - baselineSamples;
            Assert.AreEqual(0, net, message ?? $"Expected 0 GC.Alloc samples, got {net}");
        }
    }
}
