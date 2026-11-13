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
        static readonly object s_Zero = 0f;
        static readonly FieldInfo s_FastRetryUntil = T.GetField("s_FastRetryUntil", BindingFlags.NonPublic | BindingFlags.Static);
        static readonly FieldInfo s_NextFind = T.GetField("s_NextFind", BindingFlags.NonPublic | BindingFlags.Static);
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

        static int Measure(int frames, Action before)
        {
            for (int i = 0; i < 3; i++) { before?.Invoke(); Frame(); }   // warm-up: JIT, first discovery
            int control = GcAllocCounter.Count(() => GC.KeepAlive(new byte[64]));
            Assert.Greater(control, 0, "control: GC.Alloc Recorder must be live");
            int harness = before != null ? GcAllocCounter.Count(() => { for (int i = 0; i < frames; i++) before(); }) : 0;
            int total = GcAllocCounter.Count(() => { for (int i = 0; i < frames; i++) { before?.Invoke(); Frame(); } });
            return total - harness;
        }

        [Test] public void CompleteRigDoesNotAllocate()
        {
            Rig(true);
            Frame();
            Assert.AreEqual(1, Shader.GetGlobalVector("_FurnitureRetroState").x);
            int allocs = Measure(200, null);
            Debug.Log($"[RetroAlloc] complete rig: {allocs} GC.Alloc / 200 frames");
            Assert.AreEqual(0, allocs, $"complete rig allocated {allocs} GC.Alloc / 200 frames");
        }

        [Test] public void IncompleteRigWithUnchangedHierarchyDoesNotRescan()
        {
            Rig(false);
            Frame();
            // Past the scene-change fast retry, idle timer elapsed every frame: the old code rescanned (allocated) here.
            s_FastRetryUntil.SetValue(null, s_Zero);
            int allocs = Measure(200, () => s_NextFind.SetValue(null, s_Zero));
            Debug.Log($"[RetroAlloc] incomplete rig, timer forced every frame: {allocs} GC.Alloc / 200 frames");
            Assert.AreEqual(0, Shader.GetGlobalVector("_FurnitureRetroState").x);
            Assert.AreEqual(0, allocs, $"incomplete rig allocated {allocs} GC.Alloc / 200 frames");
        }

        [Test] public void NoTruckSteadyStateDoesNotAllocate()
        {
            Frame();
            s_FastRetryUntil.SetValue(null, s_Zero);
            Field("s_NextFind", Time.realtimeSinceStartup + 1000f);
            int idle = Measure(200, null);
            Debug.Log($"[RetroAlloc] no truck, between lookups: {idle} GC.Alloc / 200 frames");
            Assert.AreEqual(0, idle, $"no truck steady state allocated {idle} GC.Alloc / 200 frames");
            // The once-a-second lookup itself (FindAnyObjectByType): measured and logged, the bound is the 1 s timer.
            int lookup = Measure(50, () => s_NextFind.SetValue(null, s_Zero));
            Debug.Log($"[RetroAlloc] no truck, lookup forced every frame: {lookup} GC.Alloc / 50 lookups");
        }
    }
}
