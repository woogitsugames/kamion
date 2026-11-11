// INACTIVE ARTIFACT SKETCH. Outside Assets; not compiled or installed.
// Compile UNVERIFIED against URP 17.3.0 / Unity 6000.3.
// Logs camera configuration and material state, NEVER claims GPU-pass execution.
using System;
using System.Reflection;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.Universal;

namespace C13ArtifactOnly
{
    public sealed class C13CameraProbeFeature : ScriptableRendererFeature
    {
        ProbePass pass;
        public override void Create() => pass = new ProbePass();
        public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData data)
        {
            // CameraData is the compatibility wrapper even when RG is enabled.
            object universal = Probe.Read(data.cameraData, "universalCameraData");
            Probe.Emit(universal, "AddRenderPasses/config-only");
            renderer.EnqueuePass(pass);
        }

        sealed class ProbePass : ScriptableRenderPass
        {
            public ProbePass() => renderPassEvent = RenderPassEvent.BeforeRenderingPostProcessing;
            public override void Execute(ScriptableRenderContext context, ref RenderingData data)
                => Probe.Emit(Probe.Read(data.cameraData, "universalCameraData"), "compat/Execute/before-post");
            public override void RecordRenderGraph(RenderGraph graph, ContextContainer frameData)
            {
                // CPU recording only. No new GPU pass, draw, readback, texture or keyword.
                Probe.Emit(frameData.Get<UniversalCameraData>(), "RG/record/before-post/NOT-execution");
            }
        }
    }

    public static class Probe
    {
        const BindingFlags Flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
        public static object Read(object value, string name)
        {
            if (value == null) return null;
            try
            {
                for (Type t = value.GetType(); t != null; t = t.BaseType)
                {
                    var f = t.GetField(name, Flags | BindingFlags.DeclaredOnly);
                    if (f != null) return f.GetValue(value);
                    var p = t.GetProperty(name, Flags | BindingFlags.DeclaredOnly);
                    if (p != null) return p.GetValue(value);
                }
            }
            catch (Exception e) { Debug.Log("[C13_PROBE] reflection-error " + name + " " + e.GetType().Name); }
            return null; // fail closed: MISSING is not a guessed profile value
        }

        public static void Emit(object data, string stage)
        {
            if (data == null) { Debug.Log("[C13_PROBE] " + stage + " camera-data=MISSING"); return; }
            var camera = Read(data, "camera") as Camera;
            var d = Read(data, "cameraTargetDescriptor");
            string descriptor = d is RenderTextureDescriptor rt
                ? rt.width + "x" + rt.height + "/msaa=" + rt.msaaSamples + "/" + rt.graphicsFormat
                : "MISSING";
            string fields = "";
            foreach (string n in new[] { "pixelWidth", "pixelHeight", "scaledWidth", "scaledHeight", "renderScale",
                         "imageScalingMode", "upscalingFilter", "fsrOverrideSharpness", "fsrSharpness", "postProcessEnabled" })
                fields += " " + n + "=" + (Read(data, n)?.ToString() ?? "MISSING");
            Debug.Log("[C13_PROBE] stage=" + stage + " camera=" + camera?.name + " id=" + camera?.GetInstanceID()
                + " cameraPixel=" + camera?.pixelWidth + "x" + camera?.pixelHeight
                + " targetRT=" + (camera?.targetTexture != null ? camera.targetTexture.width + "x" + camera.targetTexture.height : "screen")
                + " cameraDescriptor=" + descriptor + fields
                + " scalableBuffer=" + ScalableBufferManager.widthScaleFactor + "," + ScalableBufferManager.heightScaleFactor
                + " GPU-pass-execution=UNVERIFIED");
        }

        // Optional late CPU material observation. Caller MUST Disarm in finally.
        // No InitializeOnLoad, MenuItem, automatic registration or asset mutation.
        public static void ArmEndCameraAudit()
        {
            Disarm();
            RenderPipelineManager.endCameraRendering += EndCamera;
        }
        public static void Disarm() => RenderPipelineManager.endCameraRendering -= EndCamera;
        static void EndCamera(ScriptableRenderContext context, Camera camera)
        {
            var extra = camera.GetComponent<UniversalAdditionalCameraData>();
            if (extra == null) return;
            var renderer = extra.scriptableRenderer;
            // Both may exist. This does NOT select which backend actually executed.
            DumpLibrary(Read(renderer, "m_PostProcessPassRenderGraph"), "RG", camera);
            DumpLibrary(Read(renderer, "finalPostProcessPass"), "compat/final", camera);
        }
        static void DumpLibrary(object owner, string backend, Camera camera)
        {
            object library = Read(owner, "m_Materials");
            foreach (string role in new[] { "easu", "finalPass" })
            {
                var m = Read(library, role) as Material;
                Debug.Log("[C13_PROBE] end-camera=" + camera.name + " id=" + camera.GetInstanceID()
                    + " candidateBackend=" + backend + " role=" + role
                    + " shader=" + (m != null ? m.shader.name : "MISSING")
                    + " materialId=" + (m != null ? m.GetInstanceID().ToString() : "MISSING")
                    + " localKeywords=" + (m != null ? string.Join(",", m.shaderKeywords) : "MISSING")
                    + " observation=CPU-material-state-NOT-draw-proof");
            }
        }
    }
}
