using System;
using System.IO;
using Game.Controls;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    /// <summary>
    /// Finger on the phone's steering wheel (ADR 0149): drives the game's own touch chain — <see cref="TouchSteeringWheel"/>
    /// (drag gesture, mm of thumb travel) -> <see cref="SteeringColumn"/> (hand-rate limit, inertia, self-centring) ->
    /// <c>DriverInput.Steer</c> — exactly as <c>DrivingLabBootstrap.FixedUpdate</c> does, so the gain curve and the column
    /// are the shipped code. The finger is either replayed (keys measured from the owner's video) or moved by a human
    /// model: preview lane keeper (aim point v x previewS ahead), perception delay humanDelayS, thumb lag neuroTauS, a fixed
    /// thumb gain fingerGainMmPerM (a person does not re-tune the thumb with every km/h — the reason the gain per mm must
    /// stay consistent across speed). Speed held by the PI controller. Allocation-free per step.
    /// </summary>
    public sealed class TouchDriver : IDriver
    {
        public static string FeelPath => Path.Combine(RepoPaths.Root, "game", "Assets", "_Project", "Input", "Resources", "Controls", "steering_feel.json");

        readonly DriverSpec _d;
        readonly SpeedController _sc;
        readonly Vec3 _p0, _f0, _l0;
        readonly double[] _delay;
        int _delayHead;
        bool _held;
        double _headingRate;

        public readonly TouchSteeringWheel Wheel;
        public readonly SteeringColumn Column;
        /// <summary>Thumb position [mm, right +] (absolute; the wheel only sees its increments).</summary>
        public double FingerMm { get; private set; }
        /// <summary>Lateral offset from the start line [m, left +] and heading [rad, left +].</summary>
        public double LateralM { get; private set; }
        public double HeadingRad { get; private set; }
        public double TargetM { get; private set; }
        public bool Held => _held;

        public TouchDriver(DriverSpec d, SimContext s, double dt)
        {
            _d = d;
            _sc = new SpeedController(d.targetKmh / 3.6);
            _p0 = s.Body.Position;
            Vec3 f = s.Body.Rotation * Vec3.Forward;
            _f0 = new Vec3(f.x, 0, f.z).Normalized;
            _l0 = new Vec3(-_f0.z, 0, _f0.x);
            var feel = SteeringFeel.FromJson(File.Exists(FeelPath) ? File.ReadAllText(FeelPath) : null);
            if (d.touchLatAccelMatchKmh >= 0) feel.dragLatAccelMatchKmh = (float)d.touchLatAccelMatchKmh;
            if (d.touchCapAbove >= 0) feel.dragLatAccelCapAboveMatch = d.touchCapAbove > 0;
            var st = s.Tractor.Steering;
            float lockDeg = (float)(st.MaxAngle * MathUtil.Rad2Deg * st.Def.steeringRatio);
            Column = new SteeringColumn(feel, lockDeg);
            Wheel = new TouchSteeringWheel { Feel = feel, Grab = WheelGrab.Drag, HalfRangeDeg = 270f, SpeedSensitive = true };
            _delay = new double[Math.Max(1, (int)Math.Round(d.humanDelayS / dt)) + 1];
        }

        /// <summary>Lateral offset of the reference path at distance x [m] (+ = left): single or double cosine lane change.</summary>
        public double Offset(double x)
        {
            double s0 = _d.startDistance, L = _d.length, A = _d.offset;
            if (x < s0) return 0;
            if (x < s0 + L) return 0.5 * A * (1 - Math.Cos(Math.PI * (x - s0) / L));
            if (!_d.doubleChange) return A;
            double s1 = s0 + L + _d.holdLength;
            if (x < s1) return A;
            if (x < s1 + L) return 0.5 * A * (1 + Math.Cos(Math.PI * (x - s1) / L));
            return 0;
        }

        public DriverInput Update(double t, double dt, SimContext s)
        {
            var m = s.Tractor;
            double v = m.SpeedForward;
            _sc.Update(Math.Abs(v), dt, out double th, out double br);

            Vec3 rel = s.Body.Position - _p0;
            double x = Vec3.Dot(rel, _f0);
            LateralM = Vec3.Dot(rel, _l0);
            Vec3 fw = s.Body.Rotation * Vec3.Forward;
            double h = Math.Atan2(Vec3.Dot(fw, _l0), Vec3.Dot(fw, _f0));
            if (t > 0) _headingRate += ((h - HeadingRad) / dt - _headingRate) * (1 - Math.Exp(-dt / 0.05));
            HeadingRad = h;

            bool held;
            if (_d.touchMode == "replay")
            {
                var k = _d.fingerKeys;
                int i = 0;
                while (i + 1 < k.Length && k[i + 1][0] <= t) i++;
                double xm = k[i][1];
                if (i + 1 < k.Length && t > k[i][0])
                    xm += (k[i + 1][1] - k[i][1]) * Math.Min(1, (t - k[i][0]) / Math.Max(1e-6, k[i + 1][0] - k[i][0]));
                FingerMm = xm;
                held = k[i][2] > 0.5;
                TargetM = 0;
            }
            else
            {
                double ahead = Math.Max(1.0, Math.Abs(v)) * _d.previewS;
                TargetM = Offset(x + ahead);
                // Predicted lateral position at the aim point: heading and heading rate (second-order prediction, the usual
                // preview-driver form; the rate term is what a driver reads from the flow of the road and damps the loop).
                double predicted = LateralM + ahead * Math.Sin(HeadingRad) + 0.5 * ahead * _d.previewS * _headingRate;
                double e = TargetM - predicted; // left +
                _delay[_delayHead] = e;
                _delayHead = (_delayHead + 1) % _delay.Length;
                double eDelayed = _delay[_delayHead]; // oldest sample = humanDelayS ago
                double cmd = -_d.fingerGainMmPerM * eDelayed; // target left -> thumb left (negative)
                double a = _d.neuroTauS <= 1e-6 ? 1 : 1 - Math.Exp(-dt / _d.neuroTauS);
                FingerMm += (cmd - FingerMm) * a;
                held = true;
            }

            // Finger on the top of the rim (fromCentre = straight up): the drag gesture uses the horizontal travel only.
            var fromCentre = new UnityEngine.Vector2(0f, 200f);
            var mm = new UnityEngine.Vector2((float)FingerMm, 0f);
            if (held && !_held) Wheel.PointerDown(fromCentre, mm);
            else if (held) Wheel.PointerDrag(fromCentre, mm);
            else if (_held) Wheel.PointerUp();
            _held = held;

            var fb = new VehicleFeedback
            {
                ForwardSpeed = (float)v, AligningTorque = (float)m.AligningTorqueTotal,
                RoadWheelAngleNormalized = (float)(m.Steering.Angle / Math.Max(1e-6, m.Steering.MaxAngle)), HandwheelLockDeg = Column.LockDeg,
            };
            var intent = default(DriverIntent);
            Wheel.Sample((float)dt, fb, ref intent);
            Column.Step((float)dt, intent.Steer * Column.LockDeg, intent.HandsOn, (float)(v * 3.6), (float)m.AligningTorqueTotal);
            Wheel.FollowColumn(Column.Normalized);
            return new DriverInput { Throttle = th, Brake = br, Steer = Column.Normalized, Selector = GearSelector.Drive, RetarderLever = _d.retarderLever };
        }
    }
}
