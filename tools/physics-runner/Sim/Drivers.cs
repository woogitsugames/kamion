using System;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    public interface IDriver
    {
        DriverInput Update(double t, double dt, SimContext s);
    }

    public static class Selectors
    {
        public static GearSelector Parse(string s)
        {
            switch ((s ?? "D").ToUpperInvariant())
            {
                case "D": return GearSelector.Drive;
                case "R": return GearSelector.Reverse;
                case "N": return GearSelector.Neutral;
                default: throw new ArgumentException($"Unknown selector '{s}'");
            }
        }
    }

    /// <summary>Open-loop timeline; values held stepwise from key to key.</summary>
    public sealed class TimelineDriver : IDriver
    {
        readonly KeySpec[] _keys;
        public TimelineDriver(KeySpec[] keys)
        {
            if (keys.Length == 0) throw new ArgumentException("timeline needs keys");
            _keys = keys;
        }

        public DriverInput Update(double t, double dt, SimContext s)
        {
            int i = 0;
            while (i + 1 < _keys.Length && _keys[i + 1].t <= t + 1e-9) i++;
            var a = _keys[i];
            return new DriverInput
            {
                Throttle = a.throttle, Brake = a.brake, Steer = a.steer,
                ParkingBrake = a.parkingBrake, Selector = Selectors.Parse(a.selector),
                RetarderLever = a.retarderLever, ManualMode = a.manual, ShiftUp = a.shiftUp, ShiftDown = a.shiftDown,
            };
        }
    }

    /// <summary>PI speed controller (throttle / brake).</summary>
    public sealed class SpeedController
    {
        double _integral;
        public double TargetMs;
        public SpeedController(double targetMs) { TargetMs = targetMs; }

        public void Update(double v, double dt, out double throttle, out double brake)
        {
            double e = TargetMs - v;
            _integral = MathUtil.Clamp(_integral + e * dt, -5, 10);
            throttle = MathUtil.Clamp01(0.25 * e + 0.06 * _integral);
            brake = e < -0.5 ? MathUtil.Clamp01(-0.15 * (e + 0.5)) : 0;
            if (brake > 0) { throttle = 0; _integral = Math.Min(_integral, 0); }
        }
    }

    /// <summary>Straight-line speed hold with constant steer; optional endurance-only braking or brake pumping.</summary>
    public sealed class SpeedHoldDriver : IDriver
    {
        readonly SpeedController _sc;
        readonly DriverSpec _d;
        readonly GearSelector _sel;
        public SpeedHoldDriver(DriverSpec d)
        {
            _d = d;
            _sc = new SpeedController(d.targetKmh / 3.6);
            _sel = Selectors.Parse(d.selector);
        }

        public DriverInput Update(double t, double dt, SimContext s)
        {
            double v = Math.Abs(s.Tractor.SpeedForward);
            _sc.Update(v, dt, out double th, out double br);
            int lever = _d.retarderLever;
            double cruise = 0;
            if (_d.enduranceOnly)
            {
                // Driver sets the downhill speed control and keeps off the pedals once above the set speed.
                br = 0;
                cruise = _d.targetKmh;
                if (v * 3.6 > _d.targetKmh - 0.5) th = 0;
            }
            else if (_d.pumpPeriod > 0 && br > 0)
            {
                // Brake pumping: full pedal half of the period, released the other half.
                br = (t % _d.pumpPeriod) < 0.5 * _d.pumpPeriod ? 0.6 : 0;
            }
            return new DriverInput { Throttle = th, Brake = br, Steer = _d.steer, Selector = _sel, RetarderLever = lever, BrakeCruiseKmh = cruise };
        }
    }

    /// <summary>Pure-pursuit steering on the tractor rear-axle point (vehicle origin).</summary>
    static class PurePursuit
    {
        public static double Steer(SimContext s, Vec3 target, double ld, double wheelbase)
        {
            Vec3 p = s.Body.Position;
            Vec3 local = s.Body.Rotation.InverseRotate(target - p);
            double alpha = Math.Atan2(local.x, local.z);
            double delta = Math.Atan(2 * wheelbase * Math.Sin(alpha) / ld);
            return MathUtil.Clamp(delta / s.Tractor.Steering.MaxAngle, -1, 1);
        }
    }

    /// <summary>
    /// Constant-radius circle: pure pursuit + PI speed hold. Optional speed ramp (rollover threshold) and a
    /// hard brake at brakeAt, optionally freezing the steering wheel (driver error for the jackknife test).
    /// </summary>
    public sealed class CircleDriver : IDriver
    {
        readonly SpeedController _sc;
        readonly DriverSpec _d;
        readonly double _r, _baseKmh;
        readonly int _dir;
        public readonly Vec3 Center;
        readonly double _wheelbase;
        double _heldSteer;
        bool _braking;

        public CircleDriver(DriverSpec d, int direction, Vec3 center, double wheelbase)
        {
            _d = d;
            _sc = new SpeedController(d.targetKmh / 3.6);
            _baseKmh = d.targetKmh;
            _r = d.radius; _dir = direction >= 0 ? 1 : -1; Center = center; _wheelbase = wheelbase;
        }

        public DriverInput Update(double t, double dt, SimContext s)
        {
            if (_d.rampKmhPerS > 0 && t > _d.rampStart) _sc.TargetMs = (_baseKmh + _d.rampKmhPerS * (t - _d.rampStart)) / 3.6;
            _sc.Update(Math.Abs(s.Tractor.SpeedForward), dt, out double th, out double br);
            Vec3 p = s.Body.Position;
            double phi = Math.Atan2(p.x - Center.x, p.z - Center.z);
            double ld = Math.Max(6.0, 0.9 * Math.Abs(s.Tractor.SpeedForward));
            double phiT = phi + _dir * ld / _r;
            Vec3 target = Center + new Vec3(_r * Math.Sin(phiT), 0, _r * Math.Cos(phiT));
            double steer = PurePursuit.Steer(s, target, ld, _wheelbase);
            if (_d.brakeAt >= 0 && t >= _d.brakeAt)
            {
                if (!_braking) { _braking = true; _heldSteer = s.Tractor.Steering.Angle / s.Tractor.Steering.MaxAngle; }
                th = 0; br = _d.brakeLevel;
                if (_d.holdSteerOnBrake) steer = _heldSteer;
            }
            return new DriverInput { Throttle = th, Brake = br, Steer = steer, Selector = GearSelector.Drive, RetarderLever = _d.retarderLever };
        }
    }

    /// <summary>Single or double lane change (cosine transitions) with pure pursuit + PI speed hold.</summary>
    public sealed class LaneChangeDriver : IDriver
    {
        readonly SpeedController _sc;
        readonly DriverSpec _d;
        readonly Vec3 _p0, _f0, _r0;
        readonly double _wheelbase;

        public LaneChangeDriver(DriverSpec d, Vec3 start, Vec3 forward, double wheelbase)
        {
            _d = d;
            _sc = new SpeedController(d.targetKmh / 3.6);
            _p0 = start;
            _f0 = new Vec3(forward.x, 0, forward.z).Normalized;
            _r0 = new Vec3(_f0.z, 0, -_f0.x);
            _wheelbase = wheelbase;
        }

        /// <summary>Lateral offset of the reference path at distance x [m] (+ = to the left).</summary>
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
            _sc.Update(Math.Abs(s.Tractor.SpeedForward), dt, out double th, out double br);
            Vec3 p = s.Body.Position;
            double x = Vec3.Dot(p - _p0, _f0);
            double ld = Math.Max(8.0, 1.0 * Math.Abs(s.Tractor.SpeedForward));
            double xt = x + ld;
            Vec3 target = _p0 + _f0 * xt - _r0 * Offset(xt);
            double steer = PurePursuit.Steer(s, target, ld, _wheelbase);
            if (_d.brakeAt >= 0 && t >= _d.brakeAt) { th = 0; br = _d.brakeLevel; }
            return new DriverInput { Throttle = th, Brake = br, Steer = steer, Selector = GearSelector.Drive, RetarderLever = _d.retarderLever };
        }
    }

    /// <summary>
    /// Repeating drive cycle for the soak test: accelerate to targetKmh, cruise with a double lane change,
    /// brake to a stop, stand still with the brake applied; period cyclePeriod. Straight reference line.
    /// </summary>
    public sealed class SoakDriver : IDriver
    {
        readonly DriverSpec _d;
        readonly SpeedController _sc;
        readonly Vec3 _p0, _f0, _r0;
        readonly double _wheelbase;
        double _cycleStartX;
        int _cycle = -1;

        public SoakDriver(DriverSpec d, Vec3 start, Vec3 forward, double wheelbase)
        {
            _d = d;
            _sc = new SpeedController(d.targetKmh / 3.6);
            _p0 = start;
            _f0 = new Vec3(forward.x, 0, forward.z).Normalized;
            _r0 = new Vec3(_f0.z, 0, -_f0.x);
            _wheelbase = wheelbase;
        }

        double Offset(double x)
        {
            double u = x - _cycleStartX;
            const double L = 40, A = 3.5;
            if (u < 400) return 0;
            if (u < 400 + L) return 0.5 * A * (1 - Math.Cos(Math.PI * (u - 400) / L));
            if (u < 480) return A;
            if (u < 480 + L) return 0.5 * A * (1 + Math.Cos(Math.PI * (u - 480) / L));
            return 0;
        }

        public DriverInput Update(double t, double dt, SimContext s)
        {
            double P = _d.cyclePeriod;
            int cycle = (int)(t / P);
            double tc = t - cycle * P;
            Vec3 p = s.Body.Position;
            double x = Vec3.Dot(p - _p0, _f0);
            if (cycle != _cycle) { _cycle = cycle; _cycleStartX = x; }
            double ld = Math.Max(8.0, Math.Abs(s.Tractor.SpeedForward));
            double xt = x + ld;
            Vec3 target = _p0 + _f0 * xt - _r0 * Offset(xt);
            double steer = PurePursuit.Steer(s, target, ld, _wheelbase);
            double th = 0, br = 0;
            if (tc < 0.6 * P) _sc.Update(Math.Abs(s.Tractor.SpeedForward), dt, out th, out br);
            else if (tc < 0.85 * P) br = Math.Abs(s.Tractor.SpeedForward) > 0.2 ? 0.45 : 1.0;
            else br = 1.0;
            if (Math.Abs(s.Tractor.SpeedForward) < 1.0) steer = 0;
            return new DriverInput { Throttle = th, Brake = br, Steer = steer, Selector = GearSelector.Drive };
        }
    }
}
