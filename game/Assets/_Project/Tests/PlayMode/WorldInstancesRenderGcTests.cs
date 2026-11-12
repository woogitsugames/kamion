using System;
using Game.World;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Profiling;

namespace Game.Tests
{
    /// <summary>
    /// M32 GC audit, instanced world render path: <see cref="WorldInstances.Render"/> (called from
    /// beginCameraRendering for every camera - main, mirrors, reversing camera - every frame) issues one
    /// Graphics.RenderMeshInstanced per batch per submesh, and used to allocate a `new RenderParams` per draw.
    /// Now one RenderParams instance is reused per component (Graphics.* consume it synchronously).
    /// Measured with ProfilerRecorder on the "GC.Alloc" marker - Mono's GC.GetAllocatedBytesForCurrentThread
    /// returns 0 in the editor. A control allocation proves the recorder is live in this run.
    /// </summary>
    public class WorldInstancesRenderGcTests
    {
        static WorldInstanceSet MiniSet(out Mesh mesh, out Material mat)
        {
            mesh = new Mesh { name = "M32_quad", hideFlags = HideFlags.DontSave };
            mesh.vertices = new[] { new Vector3(0f, 0f, 0f), new Vector3(1f, 0f, 0f), new Vector3(1f, 1f, 0f), new Vector3(0f, 1f, 0f) };
            mesh.triangles = new[] { 0, 1, 2, 0, 2, 3 };
            mat = new Material(Shader.Find("Hidden/InternalErrorShader")) { name = "M32_test", hideFlags = HideFlags.DontSave };
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

            wi.Render(cam);   // warm-up: Allocate(), ReadTier(), JIT, first draws
            wi.Render(cam);
            Assert.Greater(WorldInstances.Last.Draws, 0, "the mini set must actually issue draws");

            object sink = null;
            using (var ctrl = ProfilerRecorder.StartNew(ProfilerCategory.Internal, "GC.Alloc", 16))
            {
                sink = new byte[64];
                GC.KeepAlive(sink);
                Assert.Greater(ctrl.SampleCount, 0, "control: the GC.Alloc recorder must see a 64 B allocation in this run");
            }

            long bytes;
            using (var rec = ProfilerRecorder.StartNew(ProfilerCategory.Internal, "GC.Alloc", 1 << 16))
            {
                for (int i = 0; i < 60; i++) wi.Render(cam);
                bytes = 0;
                for (int i = 0; i < rec.SampleCount; i++)
                {
                    rec.GetSample(i, out var s);
                    bytes += s.Value;
                }
            }
            Assert.AreEqual(0, bytes, $"60 per-camera renders of the instanced world must not allocate GC ({bytes} B seen)");

            Object.DestroyImmediate(camGo);
            Object.DestroyImmediate(go);
            Object.DestroyImmediate(set);
            Object.DestroyImmediate(mesh);
            Object.DestroyImmediate(mat);
        }
    }
}
