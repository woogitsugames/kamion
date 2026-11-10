using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// Runs <see cref="AdaptiveRenderScaleController"/>, <see cref="ThermalFpsGovernor"/> and <see cref="FramePacingGovernor"/>
    /// for tiers that enable them (QualityProfile.Tier.adaptiveScaleMin / thermalFallbackFps / pacingFallbackFps; High only,
    /// ADR 0046 and 0062). The frame cap is the lowest of the requested cap and both fallbacks. The current scale and the
    /// fallback state go to <see cref="Game.Core.RenderState"/> for the [DIAG] line and the frame CSV. GPU time from FrameTimingManager
    /// (PlayerSettings "Frame Timing Stats"); without GPU timings the scale stays at the tier value. Writes the scale to the
    /// active URP asset and restores the tier value on disable / tier change. Added by <see cref="QualityProfileApplier"/>
    /// in play mode. No per-frame allocation; the thermal status is polled every <see cref="ThermalPollS"/> s (a JNI call).
    /// Disabled while a profiling render-scale override (rq_scale) is given.
    /// </summary>
    [DefaultExecutionOrder(1000)]
    public sealed class AdaptiveFrameDriver : MonoBehaviour
    {
        /// <summary>Thermal status source (Android PowerManager THERMAL_STATUS_*), set by the bootstrap.</summary>
        public static Func<int?> ThermalStatusProvider;
        /// <summary>The editor does not adapt by default (it would write the URP asset during play mode).</summary>
        public static bool AllowInEditor;
        public static float CurrentScale { get; private set; } = 1f;
        public static bool ThermalThrottled { get; private set; }
        public const float ThermalPollS = 5f;

        readonly AdaptiveRenderScaleController m_Scale = new AdaptiveRenderScaleController();
        readonly ThermalFpsGovernor m_Thermal = new ThermalFpsGovernor();
        readonly FramePacingGovernor m_Pacing = new FramePacingGovernor();
        public static bool PacingThrottled { get; private set; }
        readonly FrameTiming[] m_Timing = new FrameTiming[1];
        UniversalRenderPipelineAsset m_Urp;
        float m_TierScale = 1f;
        bool m_ScaleOn, m_ThermalOn, m_PacingOn, m_Wrote;
        int m_RequestedFps;
        int? m_Status;
        float m_NextPoll;

        void OnEnable()
        {
            QualityProfileApplier.Applied += OnTier;
            if (QualityProfileApplier.HasCurrent) OnTier(QualityProfileApplier.Current);
        }

        void OnDisable()
        {
            QualityProfileApplier.Applied -= OnTier;
            Restore();
        }

        void OnApplicationQuit() => Restore();

        void OnTier(QualityProfile.Tier t)
        {
            Restore();
            bool allowed = !Application.isEditor || AllowInEditor;
            m_Urp = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            m_TierScale = m_Urp != null ? m_Urp.renderScale : t.renderScale;
            float floor = RenderOverrides.ScaleMin ?? t.adaptiveScaleMin;
            m_ScaleOn = allowed && m_Urp != null && floor > 0f && floor < m_TierScale && !RenderOverrides.RenderScale.HasValue;
            m_Scale.MinScale = floor;
            m_Scale.MaxScale = m_TierScale;
            m_Scale.Reset(m_TierScale);
            CurrentScale = m_TierScale;
            Game.Core.RenderState.RenderScale = m_TierScale;
            m_ThermalOn = allowed && t.thermalFallbackFps > 0;
            m_Thermal.FallbackFps = t.thermalFallbackFps;
            m_Thermal.Reset();
            int pacing = RenderOverrides.Pacing == false ? 0 : t.pacingFallbackFps;
            m_PacingOn = allowed && pacing > 0;
            m_Pacing.FallbackFps = pacing;
            m_Pacing.Reset();
            m_RequestedFps = Application.targetFrameRate;
            m_NextPoll = 0f;
        }

        void Restore()
        {
            if (m_Wrote && m_Urp != null) m_Urp.renderScale = m_TierScale;
            m_Wrote = false;
            CurrentScale = m_TierScale;
            Game.Core.RenderState.RenderScale = m_TierScale;
            if ((ThermalThrottled || PacingThrottled) && m_RequestedFps > 0) Application.targetFrameRate = m_RequestedFps;
            ThermalThrottled = PacingThrottled = false;
            Game.Core.RenderState.ThermalFallback = Game.Core.RenderState.PacingFallback = false;
        }

        void Update()
        {
            float now = Time.realtimeSinceStartup;
            if (!m_Thermal.Throttled && !m_Pacing.Throttled) m_RequestedFps = Application.targetFrameRate;
            float gpu = 0f, cpu = 0f;
            if (m_ScaleOn || m_PacingOn)
            {
                FrameTimingManager.CaptureFrameTimings();
                if (FrameTimingManager.GetLatestTimings(1, m_Timing) > 0)
                {
                    gpu = (float)m_Timing[0].gpuFrameTime;
                    cpu = (float)m_Timing[0].cpuMainThreadFrameTime;
                }
            }
            int fps = m_RequestedFps;
            if (m_ThermalOn)
            {
                if (now >= m_NextPoll)
                {
                    m_NextPoll = now + ThermalPollS;
                    m_Status = ThermalStatusProvider != null ? ThermalStatusProvider() : null;
                }
                fps = Math.Min(fps, m_Thermal.Update(now, m_Status, m_RequestedFps));
                ThermalThrottled = m_Thermal.Throttled;
            }
            if (m_PacingOn)
            {
                bool atFloor = !m_ScaleOn || m_Scale.AtFloor;
                fps = Math.Min(fps, m_Pacing.Update(now, Time.unscaledDeltaTime * 1000f, gpu, cpu, atFloor, m_Scale.Scale,
                    m_ScaleOn ? m_Scale.MinScale : m_Scale.Scale, m_RequestedFps));
                PacingThrottled = m_Pacing.Throttled;
            }
            Game.Core.RenderState.ThermalFallback = ThermalThrottled;
            Game.Core.RenderState.PacingFallback = PacingThrottled;
            if ((m_ThermalOn || m_PacingOn) && fps > 0 && fps != Application.targetFrameRate)
            {
                Application.targetFrameRate = fps;
                if (fps < m_RequestedFps)
                    Debug.Log(ThermalThrottled
                        ? $"[PERF] thermal fallback: {fps} FPS cap (status >= 2 for 30 s)"
                        : $"[PERF] pacing fallback: {fps} FPS cap (scale {m_Scale.Scale:F2} at floor, {m_Pacing.LastMissRate * 100f:F0} % frames missed vsync; retry after {m_Pacing.RecoverAfterS:F0} s)");
                else
                    Debug.Log($"[PERF] frame cap restored: {fps} FPS (GPU p90 {m_Pacing.LastGpuP90Ms:F1} ms)");
            }
            if (!m_ScaleOn) return;
            int target = Application.targetFrameRate > 0 ? Application.targetFrameRate : 60;
            if (m_Scale.AddFrame(now, gpu, target))
            {
                m_Urp.renderScale = m_Scale.Scale;
                m_Wrote = true;
                CurrentScale = m_Scale.Scale;
                Game.Core.RenderState.RenderScale = m_Scale.Scale;
                Debug.Log($"[PERF] adaptive render scale {m_Scale.Scale:F2} (GPU p90 {m_Scale.LastP90Ms:F1} ms, cap {target}, floor {m_Scale.MinScale:F2}, upscaler {m_Urp.upscalingFilter})");
            }
        }
    }
}
