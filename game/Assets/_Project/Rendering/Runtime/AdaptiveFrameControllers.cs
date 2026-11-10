using System;

namespace Game.Rendering
{
    /// <summary>
    /// Adaptive render scale for the High tier (ADR 0046, floor and step-down revised in ADR 0062). Pure logic, no Unity
    /// calls, allocation-free after construction. GPU frame times are collected in a tumbling window (<see cref="WindowS"/>);
    /// at the end of each window the p90 decides:
    /// - p90 &lt; <see cref="FullScaleBelowFraction"/> of the frame interval (13 ms at 60 FPS): step up towards the tier
    ///   scale, but only when the pixel model (GPU ∝ scale²) predicts the next step stays below the step-down threshold;
    /// - p90 &gt; <see cref="StepDownAboveFraction"/> of the interval (15 ms at 60 FPS): from full scale at least to
    ///   <see cref="FirstStepScale"/> (0.85), below it at least one <see cref="Step"/>; ADR 0062: when the pixel model says
    ///   a bigger cut is needed to land in the band (p90 · (s'/s)² ≤ <see cref="TargetFraction"/>), jump there directly
    ///   (quantised down to <see cref="Step"/>, clamped to <see cref="MinScale"/>). The pixel model over-predicts the saving
    ///   (shadow maps, mirrors and the reflection capture do not scale), so the jump never overshoots the real need;
    /// - otherwise hold (hysteresis band).
    /// At most one change per window (2 s). Windows with too few valid GPU samples (device does not report GPU time) change
    /// nothing, so such devices stay at <see cref="MaxScale"/>.
    /// </summary>
    public sealed class AdaptiveRenderScaleController
    {
        public float MinScale = 0.70f;
        public float MaxScale = 1.00f;
        public float Step = 0.05f;
        public float WindowS = 2f;
        public float FullScaleBelowFraction = 13f / (1000f / 60f);   // 0.78
        public float StepDownAboveFraction = 15f / (1000f / 60f);    // 0.90
        /// <summary>ADR 0062: where a predictive step-down aims (14 ms at 60 FPS, middle of the 13-15 ms band).</summary>
        public float TargetFraction = 14f / (1000f / 60f);           // 0.84
        public int MinSamples = 30;
        /// <summary>First step down from <see cref="MaxScale"/> (ADR 0046: 1.00 → 0.85; deeper only when the load needs it).</summary>
        public float FirstStepScale = 0.85f;

        readonly float[] m_Samples;
        readonly float[] m_Scratch;
        int m_Count;
        float m_WindowStart = -1f;

        public float Scale { get; private set; }
        /// <summary>True when the scale sits on <see cref="MinScale"/> (nothing left to give: the pacing fallback may act).</summary>
        public bool AtFloor => Scale <= MinScale + 1e-4f;
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
                // Minimum cut: from full scale to FirstStepScale (0.85, visual-critic PASS), below it one Step.
                float stepped = scale >= MaxScale - 1e-4f && FirstStepScale < scale ? FirstStepScale : Quantize(scale, floor: false) - Step;
                // ADR 0062: the scale the pixel model needs to land on TargetFraction; S24+ r8 had GPU p90 25 ms at 1.0,
                // which the old one-step-per-window walk took 4 s (0.85, 0.80) to answer and then stopped at the floor.
                float needed = scale * (float)Math.Sqrt(TargetFraction * intervalMs / p90Ms);
                float jump = Quantize(needed, floor: true);
                return Clamp(Math.Min(stepped, jump));
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

    /// <summary>
    /// Frame-pacing fallback (ADR 0062). A 60 FPS cap that the device misses every 3rd-4th frame shows as 43-47 FPS with
    /// judder (S24+ High r8: p50 16.7 ms, p95 33.4 ms) - worse than a steady 30 (owner D36 ranking: option (d) "leave it" is
    /// not recommended). When the render scale has nothing left to give (<c>atFloor</c>, or no adaptive scale) and more than
    /// <see cref="MissRate"/> of the frames in a window take longer than <see cref="MissFactor"/> × the interval, for
    /// <see cref="DropAfterWindows"/> consecutive windows, the cap drops to <see cref="FallbackFps"/>.
    /// Recovery: at the fallback cap the GPU time is still measured; when the GPU p90 projected to the floor scale
    /// (pixel model, optimistic) and the CPU main-thread p90 both stay under <see cref="RecoverBelowFraction"/> of the
    /// requested interval for <see cref="RecoverAfterS"/>, the requested cap returns. Each recovery that is followed by a
    /// new drop doubles <see cref="RecoverAfterS"/> (up to <see cref="MaxRecoverAfterS"/>), so a scene that cannot hold 60
    /// does not ping-pong. Pure logic, allocation-free after construction.
    /// </summary>
    public sealed class FramePacingGovernor
    {
        public float WindowS = 2f;
        public float MissFactor = 1.25f;
        public float MissRate = 0.10f;
        public int DropAfterWindows = 3;
        public float RecoverBelowFraction = 0.80f;
        public float BaseRecoverAfterS = 20f;
        public float MaxRecoverAfterS = 160f;
        public int FallbackFps = 30;
        public int MinSamples = 20;

        readonly float[] m_Gpu, m_Cpu, m_Scratch;
        int m_GpuCount, m_CpuCount, m_Frames, m_Missed, m_BadWindows;
        float m_WindowStart = -1f, m_GoodSince = -1f, m_LastRecoverTime = -1f;

        public bool Throttled { get; private set; }
        public float RecoverAfterS { get; private set; }
        public float LastMissRate { get; private set; }
        public float LastGpuP90Ms { get; private set; }
        public int Drops { get; private set; }

        public FramePacingGovernor(int capacity = 512)
        {
            m_Gpu = new float[capacity]; m_Cpu = new float[capacity]; m_Scratch = new float[capacity];
            RecoverAfterS = BaseRecoverAfterS;
        }

        public void Reset()
        {
            Throttled = false; RecoverAfterS = BaseRecoverAfterS;
            m_GpuCount = m_CpuCount = m_Frames = m_Missed = m_BadWindows = 0;
            m_WindowStart = m_GoodSince = m_LastRecoverTime = -1f;
        }

        /// <summary>One frame. Returns the frame cap for this moment.</summary>
        /// <param name="frameMs">wall-clock frame time (unscaled delta)</param>
        /// <param name="gpuMs">GPU frame time, ≤ 0 = not reported</param>
        /// <param name="cpuMs">CPU main-thread frame time, ≤ 0 = not reported</param>
        /// <param name="atFloor">the render scale cannot go lower (or there is no adaptive scale)</param>
        /// <param name="scale">current render scale</param>
        /// <param name="floorScale">lowest render scale the adaptive controller may use</param>
        /// <param name="requestedFps">the player's / launch cap</param>
        public int Update(float timeS, float frameMs, float gpuMs, float cpuMs, bool atFloor, float scale, float floorScale, int requestedFps)
        {
            if (requestedFps <= FallbackFps) { if (Throttled) Reset(); return requestedFps; }
            if (m_WindowStart < 0f) m_WindowStart = timeS;
            float intervalReq = 1000f / requestedFps;
            m_Frames++;
            if (frameMs > MissFactor * intervalReq) m_Missed++;
            if (gpuMs > 0f && m_GpuCount < m_Gpu.Length) m_Gpu[m_GpuCount++] = gpuMs;
            if (cpuMs > 0f && m_CpuCount < m_Cpu.Length) m_Cpu[m_CpuCount++] = cpuMs;
            if (timeS - m_WindowStart < WindowS) return Throttled ? FallbackFps : requestedFps;

            int frames = m_Frames, missed = m_Missed, ng = m_GpuCount, nc = m_CpuCount;
            m_Frames = m_Missed = m_GpuCount = m_CpuCount = 0;
            m_WindowStart = timeS;
            if (frames < MinSamples) return Throttled ? FallbackFps : requestedFps;
            LastMissRate = (float)missed / frames;

            if (!Throttled)
            {
                m_BadWindows = atFloor && LastMissRate > MissRate ? m_BadWindows + 1 : 0;
                if (m_BadWindows >= DropAfterWindows)
                {
                    Throttled = true;
                    Drops++;
                    m_BadWindows = 0;
                    m_GoodSince = -1f;
                    // Dropped again soon after a recovery: the scene cannot hold the cap, wait longer next time.
                    if (m_LastRecoverTime >= 0f && timeS - m_LastRecoverTime < 2f * RecoverAfterS + 10f)
                        RecoverAfterS = Math.Min(MaxRecoverAfterS, RecoverAfterS * 2f);
                }
            }
            else
            {
                if (ng < MinSamples) { m_GoodSince = -1f; return FallbackFps; }   // no GPU timings: stay safe
                float gpuP90 = P90(m_Gpu, ng);
                float s = scale > 1e-3f ? floorScale / scale : 1f;
                float projected = gpuP90 * Math.Min(1f, s * s);
                LastGpuP90Ms = gpuP90;
                bool cpuOk = nc < MinSamples || P90(m_Cpu, nc) < RecoverBelowFraction * intervalReq;
                if (projected < RecoverBelowFraction * intervalReq && cpuOk)
                {
                    if (m_GoodSince < 0f) m_GoodSince = timeS - WindowS;
                    if (timeS - m_GoodSince >= RecoverAfterS)
                    {
                        Throttled = false;
                        m_GoodSince = -1f;
                        m_LastRecoverTime = timeS;
                    }
                }
                else m_GoodSince = -1f;
            }
            return Throttled ? FallbackFps : requestedFps;
        }

        float P90(float[] src, int n)
        {
            Array.Copy(src, m_Scratch, n);
            Array.Sort(m_Scratch, 0, n);
            return m_Scratch[Math.Min(n - 1, (int)Math.Ceiling(0.9 * n) - 1)];
        }
    }
}
