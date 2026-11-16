using System;

namespace Game.Controls
{
    /// <summary>
    /// Where the computed steering-wheel force goes (ADR 0263). The game side computes one normalised torque per fixed
    /// step; a backend (native plugin, later) turns it into a constant-force effect on the device. Implementations must
    /// not allocate in <see cref="SetConstantForce"/>.
    /// </summary>
    public interface IForceFeedbackSink
    {
        /// <summary>A device that can take the force is connected and open.</summary>
        bool Available { get; }
        /// <summary>Normalised torque -1..1 on the wheel rim, positive = pushes the rim clockwise (to the right).</summary>
        void SetConstantForce(float normalized);
        /// <summary>Removes every force (pause, menu, focus lost, device lost, quit).</summary>
        void Stop();
    }

    /// <summary>No device / no backend: swallows the output.</summary>
    public sealed class NullForceFeedbackSink : IForceFeedbackSink
    {
        public static readonly NullForceFeedbackSink Instance = new NullForceFeedbackSink();
        public bool Available => false;
        public void SetConstantForce(float normalized) { }
        public void Stop() { }
    }

    /// <summary>
    /// Records the last <see cref="Capacity"/> outputs in a preallocated ring (tests, telemetry, tuning without a wheel).
    /// </summary>
    public sealed class RecordingForceFeedbackSink : IForceFeedbackSink
    {
        readonly float[] m_Ring;
        int m_Head;
        public RecordingForceFeedbackSink(int capacity = 1024) { m_Ring = new float[Math.Max(1, capacity)]; }
        public bool Available { get; set; } = true;
        public int Capacity => m_Ring.Length;
        /// <summary>Total number of SetConstantForce calls since construction.</summary>
        public int Count { get; private set; }
        public int StopCount { get; private set; }
        public float Last { get; private set; }
        public float MaxAbs { get; private set; }

        public void SetConstantForce(float normalized)
        {
            Last = normalized;
            if (Math.Abs(normalized) > MaxAbs) MaxAbs = Math.Abs(normalized);
            m_Ring[m_Head] = normalized;
            m_Head = (m_Head + 1) % m_Ring.Length;
            Count++;
        }

        public void Stop() { Last = 0f; StopCount++; }

        /// <summary>The i-th most recent output (0 = last).</summary>
        public float Recent(int i)
        {
            int n = Math.Min(Count, m_Ring.Length);
            if ((uint)i >= (uint)n) return 0f;
            int idx = (m_Head - 1 - i) % m_Ring.Length;
            if (idx < 0) idx += m_Ring.Length;
            return m_Ring[idx];
        }
    }

    /// <summary>
    /// Tuning of the steering force (ADR 0263). Every number is a WORKING_VALUE (reasoning in the ADR) until a feel
    /// test on a real wheel; none is a measured truck value. Plain data (JsonUtility-compatible).
    /// </summary>
    [Serializable]
    public sealed class ForceFeedbackSettings
    {
        /// <summary>Master gain 0..2 (player setting).</summary>
        public float gain = 1f;
        /// <summary>Hydraulic power-steering share of the column torque: the driver feels (1 - assist) of
        /// aligning torque / steering ratio. WORKING_VALUE (heavy-truck power steering carries most of the load; no source yet).</summary>
        public float powerAssist = 0.85f;
        /// <summary>Rim torque [N m] that maps to a normalised output of 1 (device independent). WORKING_VALUE.</summary>
        public float fullScaleRimTorqueNm = 8f;
        /// <summary>Below this speed the aligning term fades to zero (tyre model has no meaningful trail at rest) [m/s].</summary>
        public float aligningFadeStartMs = 0.3f;
        /// <summary>Speed at which the aligning term reaches full strength [m/s].</summary>
        public float aligningFadeFullMs = 2.5f;
        /// <summary>Viscous damping on the rim [N m per rad/s] (power-steering valve + column). WORKING_VALUE.</summary>
        public float dampingNmPerRadS = 0.35f;
        /// <summary>Coulomb friction of the column [N m] (smoothed). WORKING_VALUE.</summary>
        public float frictionNm = 0.4f;
        /// <summary>Rim speed at which the friction reaches ~76 % (tanh 1) [deg/s] (smooth sign, no chatter at rest).</summary>
        public float frictionSmoothDegS = 8f;
        /// <summary>Soft-lock wall stiffness [N m per deg past the lock]. WORKING_VALUE.</summary>
        public float softLockNmPerDeg = 1.5f;
        /// <summary>Soft-lock wall damping [N m per rad/s] while past the lock (stops the rim bouncing off the wall).</summary>
        public float softLockDampingNmPerRadS = 0.8f;
        /// <summary>Road-feel gain: high-passed left-right load difference of the steered axle [N] → rim torque [N m]
        /// via a lever [m] (scrub radius x kingpin geometry, not in the vehicle data yet → WORKING_VALUE).</summary>
        public float roadFeelLeverM = 0.01f;
        /// <summary>High-pass time constant of the road-feel term [s] (only changes are felt, not a static load split).</summary>
        public float roadFeelTauS = 0.05f;
        /// <summary>Fastest change of the normalised output per second (no kicks; device slew). WORKING_VALUE.</summary>
        public float maxSlewPerS = 20f;
        /// <summary>Hard clamp of the normalised output (device protection, comfort).</summary>
        public float maxOutput = 1f;

        public static ForceFeedbackSettings Defaults() => new ForceFeedbackSettings();
        public ForceFeedbackSettings Clone() => (ForceFeedbackSettings)MemberwiseClone();

        public void Sanitize()
        {
            gain = Fix(gain, 0f, 2f, 1f);
            powerAssist = Fix(powerAssist, 0f, 0.99f, 0.85f);
            fullScaleRimTorqueNm = Fix(fullScaleRimTorqueNm, 0.5f, 50f, 8f);
            aligningFadeStartMs = Fix(aligningFadeStartMs, 0f, 10f, 0.3f);
            aligningFadeFullMs = Fix(aligningFadeFullMs, aligningFadeStartMs + 0.01f, 20f, Math.Max(2.5f, aligningFadeStartMs + 0.01f));
            dampingNmPerRadS = Fix(dampingNmPerRadS, 0f, 5f, 0.35f);
            frictionNm = Fix(frictionNm, 0f, 5f, 0.4f);
            frictionSmoothDegS = Fix(frictionSmoothDegS, 0.1f, 200f, 8f);
            softLockNmPerDeg = Fix(softLockNmPerDeg, 0f, 20f, 1.5f);
            softLockDampingNmPerRadS = Fix(softLockDampingNmPerRadS, 0f, 10f, 0.8f);
            roadFeelLeverM = Fix(roadFeelLeverM, 0f, 0.1f, 0.01f);
            roadFeelTauS = Fix(roadFeelTauS, 0.005f, 1f, 0.05f);
            maxSlewPerS = Fix(maxSlewPerS, 0.5f, 1000f, 20f);
            maxOutput = Fix(maxOutput, 0f, 1f, 1f);
        }

        static float Fix(float v, float lo, float hi, float def) => float.IsNaN(v) || float.IsInfinity(v) ? def : WheelAxisMath.Clamp(v, lo, hi);
    }

    /// <summary>Per-step physics and device state the force is computed from (filled from the vehicle model; no Unity types).</summary>
    public struct ForceFeedbackInputs
    {
        /// <summary>Output allowed (driving, not paused, window focused, wheel source active).</summary>
        public bool Active;
        /// <summary>Signed speed along the vehicle's forward axis [m/s].</summary>
        public float ForwardSpeed;
        /// <summary>Sum of the steered wheels' aligning torque about the steering axes [N m], positive = turns the road
        /// wheels to the right (VehicleModel.AligningTorqueTotal, from the tyre model: -pneumatic trail x Fy).</summary>
        public float AligningTorqueNm;
        /// <summary>Overall steering ratio (handwheel deg / road-wheel deg).</summary>
        public float SteeringRatio;
        /// <summary>Cab-wheel degrees per device degree (<see cref="WheelSteeringMap.CabPerDeviceDeg"/>).</summary>
        public float CabPerDeviceDeg;
        /// <summary>Physical rim speed [deg/s], positive = clockwise.</summary>
        public float DeviceRateDegS;
        /// <summary>Device angle past the soft lock [deg] (<see cref="WheelSteeringMap.PastSoftLockDeg"/>), 0 inside.</summary>
        public float PastSoftLockDeg;
        /// <summary>Normal load of the steered axle's left / right wheel end [N] (0 when airborne).</summary>
        public float SteeredLoadLeftN, SteeredLoadRightN;
    }

    /// <summary>
    /// Steering-wheel force from the physics (ADR 0263, docs/04 §2.5): aligning torque of the front axle from the tyre
    /// model, divided by the steering ratio and reduced by the power assist; plus column damping and friction, a soft
    /// lock and an optional road-feel term from the steered wheels' load changes. No animation-driven effects. Zero
    /// when inactive; at standstill only damping/friction act, and both are zero while the rim is still. Output is
    /// clamped and slew-limited. Stepped in the fixed physics step; allocation-free.
    /// </summary>
    public sealed class ForceFeedbackModel
    {
        public ForceFeedbackSettings Settings;

        /// <summary>Components of the last step [N m at the rim, device side] for telemetry and tests.</summary>
        public float AligningNm { get; private set; }
        public float DampingNm { get; private set; }
        public float FrictionNm { get; private set; }
        public float SoftLockNm { get; private set; }
        public float RoadFeelNm { get; private set; }
        public float TotalNm { get; private set; }
        /// <summary>Last normalised output -1..1 sent to the sink.</summary>
        public float Output { get; private set; }

        float m_PrevLoadDiff, m_HighPass;
        bool m_HasPrev, m_Stopped;

        public ForceFeedbackModel(ForceFeedbackSettings settings = null)
        {
            Settings = settings ?? ForceFeedbackSettings.Defaults();
        }

        public void Reset()
        {
            AligningNm = DampingNm = FrictionNm = SoftLockNm = RoadFeelNm = TotalNm = Output = 0f;
            m_PrevLoadDiff = m_HighPass = 0f;
            m_HasPrev = false;
        }

        /// <summary>0 below the fade start, 1 above the full speed, smoothstep between.</summary>
        public static float SpeedFade(float speedMs, float start, float full)
        {
            float v = Math.Abs(speedMs);
            if (v <= start) return 0f;
            if (v >= full) return 1f;
            float t = (v - start) / Math.Max(1e-4f, full - start);
            return t * t * (3f - 2f * t);
        }

        /// <summary>Computes the force for one fixed step and sends it to <paramref name="sink"/> (may be null).</summary>
        public float Step(float dt, in ForceFeedbackInputs inp, IForceFeedbackSink sink)
        {
            var s = Settings;
            if (!inp.Active || dt <= 0f)
            {
                Reset();
                if (!m_Stopped) { sink?.Stop(); m_Stopped = true; }
                return 0f;
            }
            m_Stopped = false;

            float ratio = inp.SteeringRatio > 0.1f ? inp.SteeringRatio : 20f;
            float gearing = inp.CabPerDeviceDeg > 0f ? inp.CabPerDeviceDeg : 1f;
            float driverShare = 1f - WheelAxisMath.Clamp(s.powerAssist, 0f, 0.99f);
            float rateRad = inp.DeviceRateDegS * (float)(Math.PI / 180.0);

            // Aligning torque of the road wheels → cab rim (÷ ratio, x driver share) → device rim (x virtual gearing:
            // when one device degree turns the cab wheel by k degrees, the device feels k times the cab torque).
            float fade = SpeedFade(inp.ForwardSpeed, s.aligningFadeStartMs, s.aligningFadeFullMs);
            AligningNm = inp.AligningTorqueNm / ratio * driverShare * gearing * fade;

            DampingNm = -s.dampingNmPerRadS * rateRad;
            FrictionNm = -s.frictionNm * (float)Math.Tanh(inp.DeviceRateDegS / Math.Max(0.1f, s.frictionSmoothDegS));

            SoftLockNm = 0f;
            if (inp.PastSoftLockDeg != 0f)
            {
                SoftLockNm = -s.softLockNmPerDeg * inp.PastSoftLockDeg;
                // Damp only motion that goes further into the wall.
                if (rateRad * inp.PastSoftLockDeg > 0f) SoftLockNm -= s.softLockDampingNmPerRadS * rateRad;
            }

            // Road feel: high-pass of the right-left load difference (bumps, kerbs, ruts — the physics' own contact loads).
            float diff = inp.SteeredLoadRightN - inp.SteeredLoadLeftN;
            if (!m_HasPrev) { m_PrevLoadDiff = diff; m_HasPrev = true; }
            float a = s.roadFeelTauS / (s.roadFeelTauS + dt);
            m_HighPass = a * (m_HighPass + diff - m_PrevLoadDiff);
            m_PrevLoadDiff = diff;
            RoadFeelNm = m_HighPass * s.roadFeelLeverM / ratio * driverShare * gearing * fade;

            TotalNm = AligningNm + DampingNm + FrictionNm + SoftLockNm + RoadFeelNm;
            float target = TotalNm / Math.Max(0.1f, s.fullScaleRimTorqueNm) * s.gain;
            float lim = WheelAxisMath.Clamp(s.maxOutput, 0f, 1f);
            target = WheelAxisMath.Clamp(target, -lim, lim);
            if (float.IsNaN(target)) target = 0f;
            float step = s.maxSlewPerS * dt;
            float o = Output;
            o = target > o ? Math.Min(target, o + step) : Math.Max(target, o - step);
            Output = o;
            sink?.SetConstantForce(o);
            return o;
        }
    }
}
