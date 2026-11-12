using System;
using Game.World;
using NUnit.Framework;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    /// <summary>
    /// M32 GC audit, instanced world render path: <see cref="WorldInstances.Render"/> (called from
    /// beginCameraRendering for every camera - main, mirrors, reversing camera - every frame) must not allocate.
    /// Integration r5: the PR's premise was wrong - UnityEngine.RenderParams is a struct (no heap allocation per
    /// draw), so the runtime change was dropped; this test stays as the regression guard of the render path.
    /// Counted with <see cref="GcAllocCounter"/> (Profiling.Recorder("GC.Alloc").sampleBlockCount);
    /// a control allocation proves the counter is live.
    /// </summary>
    public class WorldInstancesRenderGcTests
    {

        static WorldInstanceSet MiniSet(out Mesh mesh, out Material mat)
        {
            mesh = new Mesh { name = "M32_quad", hideFlags = HideFlags.DontSave };
            mesh.vertices = new[] { new Vector3(0f, 0f, 0f), new Vector3(1f, 0f, 0f), new Vector3(1f, 1f, 0f), new Vector3(0f, 1f, 0f) };
            mesh.triangles = new[] { 0, 1, 2, 0, 2, 3 };
            mat = new Material(Shader.Find("Hidden/InternalErrorShader")) { name = "M32_test", hideFlags = HideFlags.DontSave, enableInstancing = true };   // RenderMeshInstanced requires instancing (InvalidOperationException otherwise)
            var set = ScriptableObject.CreateInstance<WorldInstanceSet>();
            set.prototypes = new[]
            {
                new WorldInstanceSet.Prototype
                {
                    name = "prop_m32",
                    lods = new[] { mesh },
                    lodEndM = new[] { 1000f },
                    materialStart = new[] { 0 },
                    shadowLodMask = 0,
                }
            };
            set.materials = new[] { mat };
            set.cells = new[]
            {
                new WorldInstanceSet.Cell { bounds = new Bounds(Vector3.zero, new Vector3(1e5f, 1e5f, 1e5f)), runStart = 0, runCount = 1, hlod = 0 }
            };
            set.runs = new[] { new WorldInstanceSet.Run { prototype = 0, start = 0, count = 5 } };
            var mats = new Matrix4x4[5];
            for (int i = 0; i < mats.Length; i++) mats[i] = Matrix4x4.Translate(new Vector3(i, 0f, 0f));
            set.matrices = mats;
            return set;
        }

        [Test]
        public void Render_PerCameraPerFrame_ZeroGcAlloc()
        {
            var set = MiniSet(out var mesh, out var mat);
            var go = new GameObject("M32_WorldInstances");
            var wi = go.AddComponent<WorldInstances>();
            wi.set = set;
            var camGo = new GameObject("M32_cam");
            var cam = camGo.AddComponent<Camera>();
            cam.transform.position = new Vector3(0f, 1f, -10f);
            cam.farClipPlane = 2000f;

            // Warm-up through the real per-camera entry (OnBeginCamera: ReadTier + Allocate, then Render) - Render alone
            // expects Allocate() to have run (integration r5: NullReferenceException on m_Ends otherwise).
            var begin = typeof(WorldInstances).GetMethod("OnBeginCamera", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic);
            Assert.NotNull(begin, "WorldInstances.OnBeginCamera");
            begin.Invoke(wi, new object[] { default(UnityEngine.Rendering.ScriptableRenderContext), cam });
            wi.Render(cam);
            Assert.Greater(WorldInstances.Last.Draws, 0, "the mini set must actually issue draws");

            int control = GcAllocCounter.Count(() => GC.KeepAlive(new byte[64]));
            Assert.Greater(control, 0, "control: the GC.Alloc counter must see a 64 B allocation in this run");

            int allocs = GcAllocCounter.Count(() => { for (int i = 0; i < 60; i++) wi.Render(cam); });
            Debug.Log($"[WorldInstancesGc] 60 renders, {WorldInstances.Last.Draws} draws/render: {allocs} GC.Alloc (control {control})");
            Assert.AreEqual(0, allocs, $"60 per-camera renders of the instanced world must not allocate GC ({allocs} GC.Alloc samples)");

            Object.DestroyImmediate(camGo);
            Object.DestroyImmediate(go);
            Object.DestroyImmediate(set);
            Object.DestroyImmediate(mesh);
            Object.DestroyImmediate(mat);
        }
    }
}
