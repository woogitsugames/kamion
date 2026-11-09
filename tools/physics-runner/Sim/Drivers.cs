using System;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    public interface IDriver
    {
        DriverInput Update(double t, double dt, VehicleModel model, RigidBody6Dof body);
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

    /// <summary>Open-loop timeline; throttle/brake/steer linearly interpolated, booleans/selector stepwise.</summary>
    public sealed class TimelineDriver : IDriver
    {
        readonly KeySpec[] _keys;
        public TimelineDriver(KeySpec[] keys)
        {
            if (keys.Length == 0) throw new ArgumentException("timeline needs keys");
            _keys = keys;
        }

        public DriverInput Update(double t, double dt, VehicleModel model, RigidBody6Dof body)
        {
            int i = 0;
            while (i + 1 < _keys.Length && _keys[i + 1].t <= t) i++;
            var a = _keys[i];
            var inp = new DriverInput
            {
                Throttle = a.throttle, Brake = a.brake, Steer = a.steer,
                ParkingBrake = a.parkingBrake, Selector = Selectors.Parse(a.selector),
            };
            return inp;
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
            if (brake > 0) throttle = 0;
        }
    }

    /// <summary>Straight-line speed hold with constant steer command.</summary>
    public sealed class SpeedHoldDriver : IDriver
    {
        readonly SpeedController _sc;
        readonly double _steer;
        readonly GearSelector _sel;
        public SpeedHoldDriver(double targetKmh, double steer, string selector)
        {
            _sc = new SpeedController(targetKmh / 3.6);
            _steer = steer;
            _sel = Selectors.Parse(selector);
        }

        public DriverInput Update(double t, double dt, VehicleModel model, RigidBody6Dof body)
        {
            _sc.Update(Math.Abs(model.SpeedForward), dt, out double th, out double br);
            return new DriverInput { Throttle = th, Brake = br, Steer = _steer, Selector = _sel };
        }
    }

    /// <summary>
    /// Constant-radius circle: pure-pursuit path following of the rear-axle ground point + PI speed hold.
    /// Circle centre is at (start.x + dir*R, start.z) for a vehicle starting at heading 0.
    /// </summary>
    public sealed class CircleDriver : IDriver
    {
        readonly SpeedController _sc;
        readonly double _r;
        readonly int _dir;
        public readonly Vec3 Center;
        readonly double _wheelbase;

        public CircleDriver(double targetKmh, double radius, int direction, Vec3 center, double wheelbase)
        {
            _sc = new SpeedController(targetKmh / 3.6);
            _r = radius; _dir = direction >= 0 ? 1 : -1; Center = center; _wheelbase = wheelbase;
        }

        public DriverInput Update(double t, double dt, VehicleModel model, RigidBody6Dof body)
        {
            _sc.Update(Math.Abs(model.SpeedForward), dt, out double th, out double br);
            Vec3 p = body.Position;
            double phi = Math.Atan2(p.x - Center.x, p.z - Center.z);
            double ld = Math.Max(6.0, 0.9 * Math.Abs(model.SpeedForward));
            double phiT = phi + _dir * ld / _r;
            Vec3 target = Center + new Vec3(_r * Math.Sin(phiT), 0, _r * Math.Cos(phiT));
            Vec3 local = body.Rotation.InverseRotate(target - p);
            double alpha = Math.Atan2(local.x, local.z);
            double delta = Math.Atan(2 * _wheelbase * Math.Sin(alpha) / ld);
            double steer = delta / model.Steering.MaxAngle;
            return new DriverInput { Throttle = th, Brake = br, Steer = MathUtil.Clamp(steer, -1, 1), Selector = GearSelector.Drive };
        }
    }
}
