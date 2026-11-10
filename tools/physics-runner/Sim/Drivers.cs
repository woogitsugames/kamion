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
        public static double Steer(SimContext s, Vec3 target, double ld, double wheelbase, double yawRateGain = 0)
        {
            Vec3 p = s.Body.Position;
            Vec3 local = s.Body.Rotation.InverseRotate(target - p);
            double alpha = Math.Atan2(local.x, local.z);
            double kappa = 2 * Math.Sin(alpha) / ld;
            double delta = Math.Atan(wheelbase * kappa);
            // Optional yaw-rate feedback (driver / lane-keeping style): damps the driver-vehicle loop.
            if (yawRateGain > 0) delta += yawRateGain * (s.Tractor.SpeedForward * kappa - s.Tractor.YawRate);
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
            double ld = Math.Max(8.0, _d.lookaheadGain * Math.Abs(s.Tractor.SpeedForward));
            double xt = x + ld;
            Vec3 target = _p0 + _f0 * xt - _r0 * Offset(xt);
            double steer = PurePursuit.Steer(s, target, ld, _wheelbase, 0.3);
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
            double steer = PurePursuit.Steer(s, target, ld, _wheelbase, 0.3);
            double th = 0, br = 0;
            if (tc < 0.6 * P) _sc.Update(Math.Abs(s.Tractor.SpeedForward), dt, out th, out br);
            else if (tc < 0.85 * P) br = Math.Abs(s.Tractor.SpeedForward) > 0.2 ? 0.45 : 1.0;
            else br = 1.0;
            if (Math.Abs(s.Tractor.SpeedForward) < 1.0) steer = 0;
            return new DriverInput { Throttle = th, Brake = br, Steer = steer, Selector = GearSelector.Drive };
        }
    }

    /// <summary>
    /// Closed-loop path follower for swept-path checks (tests/physics/swept_path_gate3.py): Stanley steering on the
    /// steer-axle centre (heading error + atan(k e / v)), so the cab stays on the given line the way a driver keeps
    /// the cab in the lane and the trailer off-tracks freely; PI speed hold on a per-point speed profile with a
    /// short preview. path = [x, z, vKmh] in the sim frame (x = E, z = N). Brakes to a stop at the path end.
    /// </summary>
    public sealed class PathDriver : IDriver
    {
        readonly double[][] _p;
        readonly SpeedController _sc;
        readonly double _wheelbase, _k;
        int _i;

        public PathDriver(DriverSpec d, double wheelbase)
        {
            if (d.path == null || d.path.Length < 3) throw new ArgumentException("path driver needs >= 3 points");
            _p = d.path;
            _wheelbase = wheelbase;
            _k = d.stanleyGain;
            _sc = new SpeedController(_p[0][2] / 3.6);
        }

        public DriverInput Update(double t, double dt, SimContext s)
        {
            Vec3 pf = s.Body.State.LocalToWorld(new Vec3(0, 0, _wheelbase));
            Vec3 fwd = s.Body.Rotation * Vec3.Forward;
            double psi = Math.Atan2(fwd.x, fwd.z);
            // nearest segment, searched forward from the last one (monotone progress)
            int n = _p.Length, best = _i;
            double bestD = double.MaxValue, bestU = 0;
            for (int j = Math.Max(0, _i - 2); j < Math.Min(n - 1, _i + 40); j++)
            {
                double ax = _p[j][0], az = _p[j][1], bx = _p[j + 1][0], bz = _p[j + 1][1];
                double dx = bx - ax, dz = bz - az, l2 = dx * dx + dz * dz;
                double u = l2 > 1e-12 ? MathUtil.Clamp(((pf.x - ax) * dx + (pf.z - az) * dz) / l2, 0, 1) : 0;
                double ex = ax + u * dx - pf.x, ez = az + u * dz - pf.z, d2 = ex * ex + ez * ez;
                if (d2 < bestD) { bestD = d2; best = j; bestU = u; }
            }
            _i = best;
            double sx = _p[best + 1][0] - _p[best][0], sz = _p[best + 1][1] - _p[best][1];
            double psiP = Math.Atan2(sx, sz);
            double cx = _p[best][0] + bestU * sx - pf.x, cz = _p[best][1] + bestU * sz - pf.z;
            // + = path lies to the right of the steer axle (right = (cos psi, -sin psi) in x/z)
            double eRight = cx * Math.Cos(psi) - cz * Math.Sin(psi);
            double headErr = psiP - psi;
            while (headErr > Math.PI) headErr -= 2 * Math.PI;
            while (headErr < -Math.PI) headErr += 2 * Math.PI;
            double v = Math.Abs(s.Tractor.SpeedForward);
            double delta = headErr + Math.Atan2(_k * eRight, v + 1.0);
            double steer = MathUtil.Clamp(delta / s.Tractor.Steering.MaxAngle, -1, 1);

            bool atEnd = best >= n - 2 && bestU > 0.95;
            double vt = _p[best][2];
            for (int j = best; j < Math.Min(n, best + 4); j++) vt = Math.Min(vt, _p[j][2]);
            _sc.TargetMs = atEnd ? 0 : vt / 3.6;
            _sc.Update(v, dt, out double th, out double br);
            if (atEnd) { th = 0; br = 0.5; }
            return new DriverInput { Throttle = th, Brake = br, Steer = steer, Selector = GearSelector.Drive };
        }
    }
}
