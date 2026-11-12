using System;
using System.Reflection;
using Game.Gameplay.Furniture;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.TestTools.Constraints;
using Is = UnityEngine.TestTools.Constraints.Is;

namespace Game.Tests
{
    /// <summary>ADR 0131: the retro-reflection bridge runs in beginCameraRendering every frame; it must not allocate,
    /// with a complete rig, with an incomplete rig whose hierarchy is unchanged, or without any truck.</summary>
    public class FurnitureRetroSourceAllocTests
    {
        static readonly Type T = typeof(FurnitureRetroSource);
        static readonly MethodInfo Initialize = T.GetMethod("Initialize", BindingFlags.NonPublic | BindingFlags.Static);
        static readonly MethodInfo Begin = T.GetMethod("BeginCamera", BindingFlags.NonPublic | BindingFlags.Static);
        static readonly object[] Args = { default(ScriptableRenderContext), null };
        static void Frame() => Begin.Invoke(null, Args);
        static void Field(string name, object v) => T.GetField(name, BindingFlags.NonPublic | BindingFlags.Static).SetValue(null, v);

        GameObject m_Go;
        Light m_Sun;

        [SetUp] public void SetUp() { m_Sun = RenderSettings.sun; RenderSettings.sun = null; Initialize.Invoke(null, null); }
        [TearDown] public void TearDown()
        {
            if (m_Go != null) UnityEngine.Object.DestroyImmediate(m_Go);
            RenderSettings.sun = m_Sun; Initialize.Invoke(null, null);
        }

        TruckLights Rig(bool sockets)
        {
            m_Go = new GameObject("alloc rig");
            var lamps = m_Go.AddComponent<TruckLights>(); lamps.forceLowBeam = true;
            if (sockets)
                foreach (string n in new[] { "LIGHT_LowBeam_L", "LIGHT_LowBeam_R", "LIGHT_HighBeam_L", "LIGHT_HighBeam_R" })
                    new GameObject(n).transform.SetParent(m_Go.transform, false);
            return lamps;
        }

        static long Measure(int frames, Action before)
        {
            for (int i = 0; i < 3; i++) { before?.Invoke(); Frame(); }   // warm-up: JIT, first discovery
            long a = GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < frames; i++) { before?.Invoke(); Frame(); }
            return GC.GetAllocatedBytesForCurrentThread() - a;
        }

        [Test] public void CompleteRigDoesNotAllocate()
        {
            Rig(true);
            Frame();
            Assert.AreEqual(1, Shader.GetGlobalVector("_FurnitureRetroState").x);
            long bytes = Measure(200, null);
            Debug.Log($"[RetroAlloc] complete rig: {bytes} B / 200 frames");
            Assert.That(() => Frame(), Is.Not.AllocatingGCMemory());
        }

        [Test] public void IncompleteRigWithUnchangedHierarchyDoesNotRescan()
        {
            Rig(false);
            Frame();
            // Past the scene-change fast retry, idle timer elapsed every frame: the old code rescanned (allocated) here.
            Field("s_FastRetryUntil", 0f);
            long bytes = Measure(200, () => Field("s_NextFind", 0f));
            Debug.Log($"[RetroAlloc] incomplete rig, timer forced every frame: {bytes} B / 200 frames");
            Assert.AreEqual(0, Shader.GetGlobalVector("_FurnitureRetroState").x);
            Assert.That(() => Frame(), Is.Not.AllocatingGCMemory());
        }

        [Test] public void NoTruckSteadyStateDoesNotAllocate()
        {
            Frame();
            Field("s_FastRetryUntil", 0f);
            Field("s_NextFind", Time.realtimeSinceStartup + 1000f);
            long idle = Measure(200, null);
            Debug.Log($"[RetroAlloc] no truck, between lookups: {idle} B / 200 frames");
            Assert.That(() => Frame(), Is.Not.AllocatingGCMemory());
            // The once-a-second lookup itself (FindAnyObjectByType): measured and logged, the bound is the 1 s timer.
            long lookup = Measure(50, () => Field("s_NextFind", 0f));
            Debug.Log($"[RetroAlloc] no truck, lookup forced every frame: {lookup} B / 50 lookups");
        }
    }
}
