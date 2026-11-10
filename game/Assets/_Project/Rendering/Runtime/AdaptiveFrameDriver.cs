using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// Runs <see cref="AdaptiveRenderScaleController"/> and <see cref="ThermalFpsGovernor"/> for tiers that enable them
    /// (QualityProfile.Tier.adaptiveScaleMin / thermalFallbackFps; High only, ADR 0046). GPU time from FrameTimingManager
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
        readonly FrameTiming[] m_Timing = new FrameTiming[1];
        UniversalRenderPipelineAsset m_Urp;
        float m_TierScale = 1f;
        bool m_ScaleOn, m_ThermalOn, m_Wrote;
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
            m_ScaleOn = allowed && m_Urp != null && t.adaptiveScaleMin > 0f && t.adaptiveScaleMin < m_TierScale && !RenderOverrides.RenderScale.HasValue;
            m_Scale.MinScale = t.adaptiveScaleMin;
            m_Scale.MaxScale = m_TierScale;
            m_Scale.Reset(m_TierScale);
            CurrentScale = m_TierScale;
            m_ThermalOn = allowed && t.thermalFallbackFps > 0;
            m_Thermal.FallbackFps = t.thermalFallbackFps;
            m_Thermal.Reset();
            m_RequestedFps = Application.targetFrameRate;
            m_NextPoll = 0f;
        }

        void Restore()
        {
            if (m_Wrote && m_Urp != null) m_Urp.renderScale = m_TierScale;
            m_Wrote = false;
            CurrentScale = m_TierScale;
            if (ThermalThrottled && m_RequestedFps > 0) Application.targetFrameRate = m_RequestedFps;
            ThermalThrottled = false;
        }

        void Update()
        {
            float now = Time.realtimeSinceStartup;
            if (m_ThermalOn)
            {
                if (!m_Thermal.Throttled) m_RequestedFps = Application.targetFrameRate;
                if (now >= m_NextPoll)
                {
                    m_NextPoll = now + ThermalPollS;
                    m_Status = ThermalStatusProvider != null ? ThermalStatusProvider() : null;
                }
                int fps = m_Thermal.Update(now, m_Status, m_RequestedFps);
                ThermalThrottled = m_Thermal.Throttled;
                if (fps > 0 && fps != Application.targetFrameRate)
                {
                    Application.targetFrameRate = fps;
                    Debug.Log(ThermalThrottled ? "[PERF] thermal fallback: 30 FPS cap (status >= 2 for 30 s)" : "[PERF] thermal recovered: frame cap restored");
                }
            }
            if (!m_ScaleOn) return;
            FrameTimingManager.CaptureFrameTimings();
            float gpu = FrameTimingManager.GetLatestTimings(1, m_Timing) > 0 ? (float)m_Timing[0].gpuFrameTime : 0f;
            int target = Application.targetFrameRate > 0 ? Application.targetFrameRate : 60;
            if (m_Scale.AddFrame(now, gpu, target))
            {
                m_Urp.renderScale = m_Scale.Scale;
                m_Wrote = true;
                CurrentScale = m_Scale.Scale;
                Debug.Log($"[PERF] adaptive render scale {m_Scale.Scale:F2} (GPU p90 {m_Scale.LastP90Ms:F1} ms, cap {target})");
            }
        }
    }
}
