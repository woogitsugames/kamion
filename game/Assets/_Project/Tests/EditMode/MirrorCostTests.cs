using System.Collections.Generic;
using Game.Core;
using Game.Rendering;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0068: mirror cost reduction keeps the optics. Due-based schedule (High) has the ADR 0046 cadence while driving,
    /// renders less while standing, never exceeds the cap and does not allocate; the extra-view LOD bias is applied only
    /// while the mirror renders and restored afterwards; a mirror render does not change the camera's field of view, aspect,
    /// position or aim (UN R46 fields: MirrorFieldOfVisionTests).
    /// Order as built by TruckAssetBuilder: MainL, MainR (class II), WideL, WideR (IV), Kerb (V), Front (VI).
    /// </summary>
    public class MirrorCostTests
    {
        static readonly int[] k_Class = { 2, 2, 4, 4, 5, 6 };

        static MirrorRefreshSchedule.Entry[] Six(bool standing, params bool[] visible)
        {
            var e = new MirrorRefreshSchedule.Entry[6];
            for (int i = 0; i < 6; i++)
                e[i] = new MirrorRefreshSchedule.Entry
                {
                    phase = i, main = i < 2, weight = i < 2 ? 1f : 0.5f, candidate = visible.Length == 0 || visible[i],
                    interval = VehicleCameraBudget.MirrorIntervalFor(2, k_Class[i], standing), fill = k_Class[i] <= 4,
                };
            return e;
        }

        static (HashSet<int>[] iv, int max, float mean) Run(MirrorRefreshSchedule.Entry[] e, int cap, bool fill, int frames = 192, int warmup = 32)
        {
            var last = new int[e.Length];
            var iv = new HashSet<int>[e.Length];
            for (int i = 0; i < e.Length; i++) { last[i] = -1; iv[i] = new HashSet<int>(); }
            int max = 0, sum = 0;
            for (int f = 0; f < warmup + frames; f++)
            {
                int n = MirrorRefreshSchedule.StepDue(e, e.Length, cap, fill);
                Assert.LessOrEqual(n, cap);
                for (int i = 0; i < e.Length; i++)
                {
                    if (!e[i].selected) continue;
                    Assert.IsTrue(e[i].candidate);
                    if (f >= warmup && last[i] >= 0) iv[i].Add(f - last[i]);
                    last[i] = f;
                }
                if (f >= warmup) { sum += n; if (n > max) max = n; }
            }
            return (iv, max, sum / (float)frames);
        }

        static void Every(HashSet<int>[] iv, int i, int frames) =>
            CollectionAssert.AreEquivalent(new[] { frames }, iv[i], $"mirror {i}: intervals {string.Join(",", iv[i])}, expected a steady {frames}");

        [Test]
        public void High_Driving_AllSix_SameCadenceAsAdr0046_EvenLoad()
        {
            var (iv, max, mean) = Run(Six(false), 2, true);
            Every(iv, 0, 2); Every(iv, 1, 2);
            for (int i = 2; i < 6; i++) Every(iv, i, 4);
            Assert.AreEqual(2, max);
            Assert.AreEqual(2f, mean, 1e-3f, "two renders every frame (even load, no 0/2 bunching)");
        }

        [Test]
        public void High_Driving_OneSide_MainAndWide_EveryFrame()
        {
            var (iv, _, _) = Run(Six(false, true, false, true, false, false, false), 2, true);
            Every(iv, 0, 1); Every(iv, 2, 1);
        }

        [Test]
        public void High_Standing_ClassII_Steady30Hz_ConvexSlower_FewerRenders()
        {
            var (iv, max, mean) = Run(Six(true), 2, false, frames: 384);
            Every(iv, 0, 2); Every(iv, 1, 2);
            Every(iv, 2, 8); Every(iv, 3, 8);
            Every(iv, 4, 16); Every(iv, 5, 16);
            Assert.LessOrEqual(max, 2);
            Assert.AreEqual(1f + 2f / 8f + 2f / 16f, mean, 0.02f);
        }

        [Test]
        public void StepDue_DoesNotAllocate()
        {
            var e = Six(false);
            for (int f = 0; f < 32; f++) MirrorRefreshSchedule.StepDue(e, 6, 2, true);
            long before = System.GC.GetAllocatedBytesForCurrentThread();
            for (int f = 0; f < 1000; f++) MirrorRefreshSchedule.StepDue(e, 6, 2, true);
            Assert.AreEqual(0, System.GC.GetAllocatedBytesForCurrentThread() - before);
        }

        [Test]
        public void Budget_High_LodScale_OtherTiersUnchanged()
        {
            Assert.AreEqual(0.5f, VehicleCameraBudget.MirrorLodScaleFor(2, true));
            Assert.AreEqual(0.3f, VehicleCameraBudget.MirrorLodScaleFor(2, false));
            for (int lvl = 0; lvl < 4; lvl++)
            {
                if (lvl == 2) continue;
                Assert.AreEqual(1f, VehicleCameraBudget.MirrorLodScaleFor(lvl, true), $"level {lvl}");
                Assert.AreEqual(1f, VehicleCameraBudget.MirrorLodScaleFor(lvl, false), $"level {lvl}");
                Assert.IsFalse(VehicleCameraBudget.DueScheduleFor(lvl), $"level {lvl} keeps the round-robin");
            }
            Assert.IsTrue(VehicleCameraBudget.DueScheduleFor(2));
            // ADR 0068 does not change the per-frame caps, texture heights or far clips.
            Assert.AreEqual(2, VehicleCameraBudget.MirrorsPerFrameFor(2));
            Assert.AreEqual(384, VehicleCameraBudget.MirrorHeightFor(2));
            Assert.AreEqual(400f, VehicleCameraBudget.MirrorFarClipFor(2));
        }

        [Test]
        public void ExtraViewLod_EffectiveBias_PerCamera()
        {
            var go = new GameObject("ev");
            var cam = go.AddComponent<Camera>();
            var plain = new GameObject("plain").AddComponent<Camera>();
            try
            {
                var tag = go.AddComponent<ExtraViewTag>();
                tag.lodScale = 0.25f;
                float b = QualitySettings.lodBias;
                Assert.AreEqual(b * 0.25f, ExtraViewLod.EffectiveLodBias(cam), 1e-5f);
                Assert.AreEqual(b, ExtraViewLod.EffectiveLodBias(plain), 1e-5f);
                Assert.IsFalse(ExtraViewLod.Swapped);
            }
            finally { Object.DestroyImmediate(go); Object.DestroyImmediate(plain.gameObject); }
        }

        [Test]
        public void MirrorRender_KeepsOptics_RestoresLodBias()
        {
            int level = QualitySettings.GetQualityLevel();
            var root = new GameObject("mirror-test");
            try
            {
                QualitySettings.SetQualityLevel(2, false);
                var glass = GameObject.CreatePrimitive(PrimitiveType.Quad);
                glass.transform.SetParent(root.transform, false);
                var camGo = new GameObject("MIRROR_MainL_Camera");
                camGo.transform.SetParent(root.transform, false);
                camGo.transform.SetPositionAndRotation(new Vector3(-1.4f, 2.3f, 1.2f), Quaternion.Euler(8f, 190f, 0f));
                var cam = camGo.AddComponent<Camera>();
                RenderTextureMirror.ConfigureCheapCamera(cam, 44f, 1.0f, 250f);
                var mir = camGo.AddComponent<RenderTextureMirror>();
                mir.glass = glass.GetComponent<Renderer>();
                mir.aspect = 0.55f;
                mir.fovAspect = 0.55f;
                mir.main = true;
                float bias = QualitySettings.lodBias;
                Vector3 pos = cam.transform.position, fwd = cam.transform.forward;
                mir.RenderNow();
                float fov = cam.fieldOfView, aspect = cam.aspect;
                mir.RenderNow();
                Assert.AreEqual(44f, fov, 1e-4f, "vertical field");
                Assert.AreEqual(fov, cam.fieldOfView, 1e-5f);
                Assert.AreEqual(0.55f, aspect, 1e-4f, "R46 horizontal field (camera aspect)");
                Assert.AreEqual(aspect, cam.aspect, 1e-5f);
                Assert.Less((cam.transform.position - pos).magnitude, 1e-6f);
                Assert.Less(Vector3.Angle(cam.transform.forward, fwd), 1e-4f);
                Assert.AreEqual(bias, QualitySettings.lodBias, 1e-6f, "LOD bias restored after the mirror render");
                Assert.IsFalse(ExtraViewLod.Swapped);
                Assert.AreEqual(0.5f, mir.LodScale, 1e-6f);
                Assert.AreEqual(400f, cam.farClipPlane, 1e-3f);
                Assert.IsNotNull(mir.Texture);
                Assert.AreEqual(384, mir.Texture.height);
            }
            finally
            {
                Object.DestroyImmediate(root);
                QualitySettings.SetQualityLevel(level, false);
            }
        }
    }
}
