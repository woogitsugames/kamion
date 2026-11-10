using System;

namespace Game.Rendering
{
    /// <summary>
    /// Adaptive render scale for the High tier (ADR 0046). Pure logic, no Unity calls, allocation-free after construction.
    /// GPU frame times are collected in a tumbling window (<see cref="WindowS"/>); at the end of each window the p90 decides:
    /// - p90 &lt; <see cref="FullScaleBelowFraction"/> of the frame interval (13 ms at 60 FPS): step up towards 1.0, but only
    ///   when the pixel model (GPU ∝ scale²) predicts the next step stays below the step-down threshold (no ping-pong);
    /// - p90 &gt; <see cref="StepDownAboveFraction"/> of the interval (15 ms at 60 FPS): from full scale to
    ///   <see cref="FirstStepScale"/> (0.85), below it one <see cref="Step"/> per window down to <see cref="MinScale"/>;
    /// - otherwise hold (hysteresis band).
    /// Steps are multiples of <see cref="Step"/> (0.05); at most one change per window (2 s). Windows with too few valid GPU
    /// samples (device does not report GPU time) change nothing, so such devices stay at <see cref="MaxScale"/>.
    /// </summary>
    public sealed class AdaptiveRenderScaleController
    {
        public float MinScale = 0.80f;
        public float MaxScale = 1.00f;
        public float Step = 0.05f;
        public float WindowS = 2f;
        public float FullScaleBelowFraction = 13f / (1000f / 60f);   // 0.78
        public float StepDownAboveFraction = 15f / (1000f / 60f);    // 0.90
        public int MinSamples = 30;
        /// <summary>First step down from <see cref="MaxScale"/> (ADR 0046: 1.00 → 0.85, then 0.80 only under sustained load).</summary>
        public float FirstStepScale = 0.85f;

        readonly float[] m_Samples;
        readonly float[] m_Scratch;
        int m_Count;
        float m_WindowStart = -1f;

        public float Scale { get; private set; }
        public float LastP90Ms { get; private set; }
        public int Changes { get; private set; }

        public AdaptiveRenderScaleController(int capacity = 512)
        {
            m_Samples = new float[capacity];
            m_Scratch = new float[capacity];
            Scale = MaxScale;
        }

        public void Reset(float scale)
        {
            Scale = Clamp(scale);
            m_Count = 0;
            m_WindowStart = -1f;
        }

        /// <summary>Adds one frame. Returns true when <see cref="Scale"/> changed.</summary>
        /// <param name="timeS">Monotonic time (s, unscaled).</param>
        /// <param name="gpuMs">GPU frame time; ≤ 0 = not reported (ignored).</param>
        /// <param name="targetFps">Current frame-rate cap (thresholds are fractions of its interval).</param>
        public bool AddFrame(float timeS, float gpuMs, int targetFps)
        {
            if (m_WindowStart < 0f) m_WindowStart = timeS;
            if (gpuMs > 0f && m_Count < m_Samples.Length) m_Samples[m_Count++] = gpuMs;
            if (timeS - m_WindowStart < WindowS) return false;
            int n = m_Count;
            m_Count = 0;
            m_WindowStart = timeS;
            if (n < MinSamples) return false;
            Array.Copy(m_Samples, m_Scratch, n);
            Array.Sort(m_Scratch, 0, n);
            float p90 = m_Scratch[Math.Min(n - 1, (int)Math.Ceiling(0.9 * n) - 1)];
            LastP90Ms = p90;
            float interval = 1000f / Math.Max(1, targetFps);
            float next = Decide(Scale, p90, interval);
            if (Math.Abs(next - Scale) < 1e-4f) return false;
            Scale = next;
            Changes++;
            return true;
        }

        /// <summary>The scale after a window with GPU p90 <paramref name="p90Ms"/> at <paramref name="scale"/>.</summary>
        public float Decide(float scale, float p90Ms, float intervalMs)
        {
            float down = StepDownAboveFraction * intervalMs, up = FullScaleBelowFraction * intervalMs;
            if (p90Ms > down)
            {
                // From full scale the first step goes to FirstStepScale (0.85, visual-critic PASS); below it one Step per
                // window, so the floor (0.80, conditional PASS) is only reached when p90 is still over the line at 0.85.
                if (scale >= MaxScale - 1e-4f && FirstStepScale < scale) return Clamp(FirstStepScale);
                return Clamp(Quantize(scale, floor: false) - Step);
            }
            if (p90Ms < up && scale < MaxScale - 1e-4f)
            {
                float s = Clamp(Quantize(scale, floor: false) + Step);
                if (scale + Step > MaxScale) s = MaxScale;
                float predicted = p90Ms * (s / scale) * (s / scale);
                return predicted < down ? s : scale;
            }
            return Clamp(scale);
        }

        float Quantize(float s, bool floor)
        {
            double k = s / Step;
            k = floor ? Math.Floor(k + 1e-4) : Math.Round(k);
            return (float)(k * Step);
        }

        float Clamp(float s) => s < MinScale ? MinScale : s > MaxScale ? MaxScale : s;
    }

    /// <summary>
    /// Thermal frame-rate fallback (ADR 0046): thermal status ≥ <see cref="ThrottleAtStatus"/> sustained for
    /// <see cref="ThrottleAfterS"/> → cap <see cref="FallbackFps"/>; back to the requested cap after status ≤
    /// <see cref="RecoverAtOrBelowStatus"/> sustained for <see cref="RecoverAfterS"/>. Unknown status (null) resets both timers.
    /// Pure logic, allocation-free.
    /// </summary>
    public sealed class ThermalFpsGovernor
    {
        public int ThrottleAtStatus = 2;
        public float ThrottleAfterS = 30f;
        public int RecoverAtOrBelowStatus = 1;
        public float RecoverAfterS = 60f;
        public int FallbackFps = 30;

        float m_HotSince = -1f, m_CoolSince = -1f;
        public bool Throttled { get; private set; }

        public void Reset() { Throttled = false; m_HotSince = m_CoolSince = -1f; }

        /// <summary>The frame-rate cap for this moment. <paramref name="requestedFps"/> is the player's / launch cap.</summary>
        public int Update(float timeS, int? thermalStatus, int requestedFps)
        {
            if (requestedFps <= FallbackFps) { Reset(); return requestedFps; }
            if (!thermalStatus.HasValue) { m_HotSince = m_CoolSince = -1f; return Throttled ? FallbackFps : requestedFps; }
            int st = thermalStatus.Value;
            if (!Throttled)
            {
                if (st >= ThrottleAtStatus)
                {
                    if (m_HotSince < 0f) m_HotSince = timeS;
                    if (timeS - m_HotSince >= ThrottleAfterS) { Throttled = true; m_HotSince = -1f; m_CoolSince = -1f; }
                }
                else m_HotSince = -1f;
            }
            else
            {
                if (st <= RecoverAtOrBelowStatus)
                {
                    if (m_CoolSince < 0f) m_CoolSince = timeS;
                    if (timeS - m_CoolSince >= RecoverAfterS) { Throttled = false; m_CoolSince = -1f; m_HotSince = -1f; }
                }
                else m_CoolSince = -1f;
            }
            return Throttled ? FallbackFps : requestedFps;
        }
    }
}
