using System;
using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Data for the driver's hands on a heavy-truck steering wheel (ADR 0058). Loaded from
    /// <c>Resources/Controls/steering_feel.json</c>; the C# defaults are the same values, so a missing file changes nothing.
    /// Every number is a WORKING_VALUE (reasoning in ADR 0058) until the owner's feel test on the phone confirms it.
    /// </summary>
    [Serializable]
    public sealed class SteeringFeel
    {
        public const string ResourcePath = "Controls/steering_feel";

        /// <summary>Speed breakpoints [km/h] of <see cref="handRateDegS"/> (piecewise linear, flat outside).</summary>
        public float[] handRateSpeedsKmh = { 0f, 10f, 30f, 50f, 80f, 100f };
        /// <summary>Highest steering-wheel rate the driver's hands produce [deg/s] at those speeds: quick hand-over-hand
        /// when manoeuvring (ADR 0135: 720/600 at 0/10 km/h, was 540/480), calm corrections at motorway speed (a real driver at 80 km/h rarely exceeds ~100-150 deg/s).</summary>
        public float[] handRateDegS = { 720f, 600f, 300f, 200f, 130f, 110f };
        /// <summary>Time to reach the rate limit from rest [s] (acceleration limit = rate / rise): wheel + arm inertia, no snaps.</summary>
        public float rateRiseTimeS = 0.1f;
        /// <summary>Time constant of following a small finger motion [s] (perceived lag; kept below ~80 ms).</summary>
        public float trackingTauS = 0.05f;

        /// <summary>Self-centring (hands off): highest return rate [deg/s].</summary>
        public float centreRateMaxDegS = 300f;
        /// <summary>Speed at which the speed (caster) term of the return saturates [km/h].</summary>
        public float centreSpeedRefKmh = 30f;
        /// <summary>Steered-axle aligning torque at which the torque term saturates [N m].</summary>
        public float centreTorqueRefNm = 800f;
        /// <summary>Below this speed the wheel does not return (power steering at rest) [km/h].</summary>
        public float centreMinSpeedKmh = 2f;
        /// <summary>Time constant of the final approach to centre [s].</summary>
        public float centreTauS = 0.3f;

        /// <summary>Speed-sensitive mapping of the on-screen wheel: from this speed [km/h] the comfort gear-up starts to fade ...</summary>
        public float speedGainStartKmh = 20f;
        /// <summary>... and from this speed [km/h] the on-screen wheel drives the cab wheel at <see cref="highSpeedScreenToHandwheel"/>.</summary>
        public float speedGainEndKmh = 60f;
        /// <summary>Cab-wheel degrees per on-screen-wheel degree at speed (1 = the touch wheel is the real wheel).</summary>
        public float highSpeedScreenToHandwheel = 1f;
        /// <summary>Drag gesture (ADR 0135): on-screen wheel degrees per millimetre of sideways finger travel. 10.8 = the
        /// comfort range (270 deg) in 25 mm, i.e. full lock within a thumb sweep at manoeuvring speed. WORKING_VALUE.</summary>
        public float dragScreenDegPerMm = 10.8f;
        /// <summary>Drag gesture at speed (from <see cref="speedGainEndKmh"/>): cab-wheel degrees per millimetre (5 = a
        /// 20-30 deg lane-change correction is a 4-6 mm thumb slide; the rotate gesture on the reference phone gave ~3-6
        /// deg/mm at the rim). WORKING_VALUE.</summary>
        public float dragHighSpeedHandwheelDegPerMm = 5f;
        /// <summary>Gyro: fraction of full lock reachable at full tilt at speed (1 at low speed).</summary>
        public float gyroHighSpeedGain = 0.3f;

        /// <summary>Lock-to-lock half range of the cab wheel when the vehicle does not report one [deg] (40 deg x 20:1).</summary>
        public float fallbackLockDeg = 800f;

        public static SteeringFeel Defaults() => new SteeringFeel();

        public static SteeringFeel FromJson(string json)
        {
            var f = Defaults();
            if (string.IsNullOrWhiteSpace(json)) return f;
            try { JsonUtility.FromJsonOverwrite(json, f); }
            catch { return Defaults(); }
            if (f.handRateSpeedsKmh == null || f.handRateDegS == null || f.handRateSpeedsKmh.Length == 0
                || f.handRateSpeedsKmh.Length != f.handRateDegS.Length) { var d = Defaults(); f.handRateSpeedsKmh = d.handRateSpeedsKmh; f.handRateDegS = d.handRateDegS; }
            return f;
        }

        static SteeringFeel s_Loaded;

        /// <summary>The shipped tuning (Resources), cached.</summary>
        public static SteeringFeel LoadDefault()
        {
            if (s_Loaded == null) s_Loaded = FromJson(Resources.Load<TextAsset>(ResourcePath)?.text);
            return s_Loaded;
        }

        /// <summary>Hand rate limit [deg/s of the steering wheel] at a speed [km/h].</summary>
        public float HandRate(float speedKmh)
        {
            var x = handRateSpeedsKmh; var y = handRateDegS;
            float v = Mathf.Abs(speedKmh);
            if (v <= x[0]) return y[0];
            for (int i = 1; i < x.Length; i++)
                if (v <= x[i]) return Mathf.Lerp(y[i - 1], y[i], (v - x[i - 1]) / Mathf.Max(1e-3f, x[i] - x[i - 1]));
            return y[y.Length - 1];
        }

        /// <summary>0 at low speed .. 1 at speed (smoothstep between <see cref="speedGainStartKmh"/> and <see cref="speedGainEndKmh"/>).</summary>
        public float SpeedBlend(float speedKmh)
        {
            float t = Mathf.Clamp01((Mathf.Abs(speedKmh) - speedGainStartKmh) / Mathf.Max(1e-3f, speedGainEndKmh - speedGainStartKmh));
            return t * t * (3f - 2f * t);
        }

        /// <summary>
        /// Multiplier of the normalised on-screen wheel command: 1 at low speed (the comfort range reaches full lock),
        /// fading at speed to the value at which one on-screen degree is <see cref="highSpeedScreenToHandwheel"/> cab degrees.
        /// A range that already maps ~1:1 (simulator 900) stays at 1.
        /// </summary>
        public float WheelGain(float speedKmh, float screenRangeDeg, float lockDeg)
            => WheelGain(speedKmh, screenRangeDeg, lockDeg, highSpeedScreenToHandwheel);

        /// <summary>As above with an explicit cab-wheel-per-on-screen-degree ratio at speed (drag gesture, ADR 0135).</summary>
        public float WheelGain(float speedKmh, float screenRangeDeg, float lockDeg, float highScreenToHandwheel)
        {
            float high = Mathf.Min(1f, highScreenToHandwheel * Mathf.Max(1f, screenRangeDeg) / Mathf.Max(1f, lockDeg));
            return Mathf.Lerp(1f, high, SpeedBlend(speedKmh));
        }

        public float GyroGain(float speedKmh) => Mathf.Lerp(1f, Mathf.Clamp01(gyroHighSpeedGain), SpeedBlend(speedKmh));

        /// <summary>Return rate [deg/s] of a released wheel: speed (caster) and aligning-torque terms, none at standstill.</summary>
        public float CentreRate(float speedKmh, float aligningTorque)
        {
            float v = Mathf.Abs(speedKmh);
            if (v < centreMinSpeedKmh) return 0f;
            float k = 0.6f * Mathf.Clamp01(v / Mathf.Max(0.1f, centreSpeedRefKmh))
                    + 0.4f * Mathf.Clamp01(Mathf.Abs(aligningTorque) / Mathf.Max(1f, centreTorqueRefNm));
            return centreRateMaxDegS * Mathf.Clamp01(k);
        }
    }

    /// <summary>
    /// The simulated steering wheel in the cab (ADR 0058): its angle follows the driver's target (on-screen wheel,
    /// gyro, keyboard) like a heavy wheel turned by hands, rate-limited by a speed-dependent hand speed, acceleration-
    /// limited (no instant snaps) and with a short tracking lag; with the hands off it self-centres at a speed- and
    /// aligning-torque-dependent rate, not at all at standstill. Stepped in the fixed physics step; its angle divided by
    /// the lock is the command into <c>Steering</c> (whose rate limit is above the hand limit), so the in-cab wheel
    /// (road-wheel angle x ratio) shows exactly this angle. Allocation-free.
    /// </summary>
    public sealed class SteeringColumn
    {
        public SteeringFeel Feel;
        /// <summary>Half lock-to-lock of the cab wheel [deg] (road-wheel lock x overall ratio).</summary>
        public float LockDeg;
        /// <summary>Settings menu "Samocentrowanie": multiplier of the return rate (0 = stays where left).</summary>
        public float CentreStrength = 1f;

        /// <summary>Steering-wheel angle [deg], positive = clockwise = right.</summary>
        public float AngleDeg { get; private set; }
        /// <summary>Steering-wheel rate [deg/s].</summary>
        public float RateDegS { get; private set; }
        public float Normalized => AngleDeg / Mathf.Max(1f, LockDeg);

        public SteeringColumn(SteeringFeel feel = null, float lockDeg = 0f)
        {
            Feel = feel ?? SteeringFeel.Defaults();
            LockDeg = lockDeg > 0f ? lockDeg : Feel.fallbackLockDeg;
        }

        /// <summary>Puts the wheel at an angle at rest (reset, autopilot hand-over).</summary>
        public void SnapTo(float angleDeg)
        {
            AngleDeg = Mathf.Clamp(angleDeg, -LockDeg, LockDeg);
            RateDegS = 0f;
        }

        /// <param name="targetDeg">Where the driver wants the wheel [deg] (ignored with the hands off).</param>
        /// <param name="handsOn">Driver holds the wheel (finger on the touch wheel, gyro, key).</param>
        /// <param name="speedKmh">Vehicle speed [km/h].</param>
        /// <param name="aligningTorque">Steered-axle aligning torque from the tyre model [N m].</param>
        public void Step(float dt, float targetDeg, bool handsOn, float speedKmh, float aligningTorque)
        {
            if (dt <= 0f) return;
            var f = Feel;
            float handRate = f.HandRate(speedKmh);
            float accel = Mathf.Max(handRate, f.centreRateMaxDegS) / Mathf.Max(1e-3f, f.rateRiseTimeS);
            float goal, rateMax, tau;
            if (handsOn) { goal = Mathf.Clamp(targetDeg, -LockDeg, LockDeg); rateMax = handRate; tau = f.trackingTauS; }
            else { goal = 0f; rateMax = f.CentreRate(speedKmh, aligningTorque) * Mathf.Max(0f, CentreStrength); tau = f.centreTauS; }

            float e = goal - AngleDeg;
            float ae = Mathf.Abs(e);
            // Desired rate: proportional for small errors, braking curve (reach the goal at zero rate), hand limit.
            float mag = Mathf.Min(rateMax, Mathf.Min(ae / Mathf.Max(1e-3f, tau), Mathf.Sqrt(2f * accel * ae)));
            float desired = Mathf.Sign(e) * mag;
            if (ae < 1e-4f) desired = 0f;
            // Speeding up is limited by the arm; slowing down may be twice as quick (the hands stop the wheel).
            bool slowing = Mathf.Abs(desired) < Mathf.Abs(RateDegS) || desired * RateDegS < 0f;
            float a = slowing ? 2f * accel : accel;
            RateDegS = Mathf.MoveTowards(RateDegS, desired, a * dt);
            float next = AngleDeg + RateDegS * dt;
            // Never overshoot the goal (a crossing ends the motion there).
            if (ae > 0f && Mathf.Sign(goal - next) != Mathf.Sign(e)) { next = goal; RateDegS = 0f; }
            if (next > LockDeg) { next = LockDeg; RateDegS = Mathf.Min(0f, RateDegS); }
            else if (next < -LockDeg) { next = -LockDeg; RateDegS = Mathf.Max(0f, RateDegS); }
            AngleDeg = next;
        }
    }
}
