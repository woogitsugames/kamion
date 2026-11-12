using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Core
{
    /// <summary>Kind of an extra (off-screen) view rendered besides the main camera (ADR 0068).</summary>
    public enum ExtraViewKind { Mirror = 0, Capture = 1, Reverse = 2 }

    /// <summary>
    /// Marks a camera as an extra view (vehicle mirror, reflection capture face, reversing camera). Implemented by a
    /// component on the camera's GameObject; read by <see cref="ExtraViewLod"/>, the instanced world
    /// (Game.World.WorldInstances) and the pass-cost monitor (Game.Rendering.ExtraViewCostMonitor).
    /// </summary>
    public interface IExtraViewCamera
    {
        ExtraViewKind Kind { get; }
        /// <summary>Multiplier on the tier LOD bias while this camera renders (1 = the main view's LOD; ADR 0068).</summary>
        float LodScale { get; }
    }

    /// <summary>
    /// Per-camera LOD bias for extra views (ADR 0068). A class II mirror is a 384 px render texture over a 35-44 deg field
    /// (≈ 9-11 px/deg) while the main view has ≈ 25 px/deg, so at the tier LOD bias the mirror selected the same LODs as
    /// the main view: 2-3x more vertices than its pixels can show. While a camera with <see cref="IExtraViewCamera"/>
    /// renders, <c>QualitySettings.lodBias</c> is the tier value × <see cref="IExtraViewCamera.LodScale"/> (LODGroups are
    /// selected during the camera's culling, after beginCameraRendering) and is restored at endCameraRendering.
    /// The instanced world reads <see cref="EffectiveLodBias"/>, which does not depend on the order of the
    /// beginCameraRendering handlers. No allocation.
    /// </summary>
    public static class ExtraViewLod
    {
        static bool s_Hooked;
        /// <summary>True between beginCameraRendering and endCameraRendering of an extra view with a LOD scale.</summary>
        public static bool Swapped { get; private set; }
        /// <summary>The tier LOD bias saved while <see cref="Swapped"/>.</summary>
        public static float BaseLodBias { get; private set; } = 1f;

        /// <summary>Subscribes the begin/end camera handlers once (called by every extra-view component on enable).</summary>
        public static void Hook()
        {
            if (s_Hooked) return;
            s_Hooked = true;
            RenderPipelineManager.beginCameraRendering += OnBegin;
            RenderPipelineManager.endCameraRendering += OnEnd;
        }

        /// <summary>The LOD scale of an extra-view camera, 1 for any other camera.</summary>
        public static float ScaleFor(Camera cam)
        {
            if (cam == null || !cam.TryGetComponent(out IExtraViewCamera ev)) return 1f;
            float s = ev.LodScale;
            return s > 0.01f ? s : 1f;
        }

        /// <summary>Tier LOD bias × the camera's extra-view scale, independent of handler order.</summary>
        public static float EffectiveLodBias(Camera cam) => (Swapped ? BaseLodBias : QualitySettings.lodBias) * ScaleFor(cam);

        static void OnBegin(ScriptableRenderContext ctx, Camera cam)
        {
            if (Swapped) Restore();
            float s = ScaleFor(cam);
            if (Mathf.Abs(s - 1f) < 1e-3f) return;
            BaseLodBias = QualitySettings.lodBias;
            QualitySettings.lodBias = BaseLodBias * s;
            Swapped = true;
        }

        static void OnEnd(ScriptableRenderContext ctx, Camera cam)
        {
            if (Swapped) Restore();
        }

        static void Restore()
        {
            QualitySettings.lodBias = BaseLodBias;
            Swapped = false;
        }
    }

    /// <summary>
    /// Launch-argument overrides and A/B switches of the vehicle mirrors (ADR 0068), set by Game.Rendering.RenderOverrides
    /// (rq_mirror_*) and the pass A/B toggler (rq_ab). Read by Game.Vehicle.Runtime.VehicleCameraBudget. null = tier value.
    /// </summary>
    public static class MirrorOverrides
    {
        /// <summary>rq_mirror_cap: hard cap of mirror renders per frame.</summary>
        public static int? Cap;
        /// <summary>rq_mirror_lod: LOD scale of the class II mirrors (convex = 0.6 × this); 1 = main-view LOD.</summary>
        public static float? LodScale;
        /// <summary>rq_mirror_far: far clip of the class II mirrors (m); convex = half.</summary>
        public static float? FarClip;
        /// <summary>rq_mirror_res: render-texture height multiplier.</summary>
        public static float? Resolution;
        /// <summary>ADR 0136 r2: the active quality tier's mirror texture height multiplier (QualityProfile.Tier.mirrorResolutionScale,
        /// set by QualityProfileApplier; Low 0.75 = the Low main-view render scale). rq_mirror_res replaces it.</summary>
        public static float TierResolution = 1f;
        /// <summary>rq_mirror_rate 0: the ADR 0046 fill-the-cap schedule instead of the due-based one on High.</summary>
        public static bool? DueSchedule;
        /// <summary>rq_mirror_legacy 1 (or the A/B toggler): the complete pre-ADR 0068 mirror configuration.</summary>
        public static bool Legacy;
        /// <summary>rq_mirror_off 1 (or the A/B toggler): no mirror renders at all (cost of the mirrors as a whole).</summary>
        public static bool Suspended;

        public static bool Any => Cap.HasValue || LodScale.HasValue || FarClip.HasValue || Resolution.HasValue || DueSchedule.HasValue || Legacy || Suspended;
    }

    /// <summary>
    /// Cost of the fixed passes per frame (ADR 0068), published every window by Game.Rendering.ExtraViewCostMonitor and
    /// printed in the [DIAG] line. CPU = main-thread time between begin- and endCameraRendering (culling, render-graph
    /// record, submit). GPU = Recorder time of a sampler around the view, only in development players (-1 otherwise).
    /// </summary>
    public static class ExtraViewStats
    {
        public static float MirrorRendersPerFrame;
        public static float MirrorCpuMs;
        public static float MirrorGpuMs = -1f;
        public static float CaptureFacesPerFrame;
        public static float CaptureCpuMs;
        public static float CaptureGpuMs = -1f;
        public static float ShadowGpuMs = -1f;
        /// <summary>Main-thread time of all non-extra cameras (main view + UI) per frame.</summary>
        public static float MainCpuMs;
        /// <summary>Current A/B state label of the pass toggler (rq_ab), null when off.</summary>
        public static string AbState;
        /// <summary>A/B state for the frame CSV: -1 off, 0 = A (shipping configuration), 1 = B (variant).</summary>
        public static int AbIndex = -1;
        /// <summary>Mirror renders in the last completed frame (frame CSV column mirror_n).</summary>
        public static int LastFrameMirrorRenders;
    }
}
