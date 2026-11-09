using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Steering: command -> rate-limited virtual road-wheel angle -> per-wheel Ackermann angles.
    /// Positive angle = wheel turned to the right (+X), giving a positive yaw rate (right turn).
    /// </summary>
    public sealed class Steering
    {
        public readonly SteeringDefinition Def;
        readonly double _maxAngle, _maxRate;
        /// <summary>Virtual (bicycle-model) road-wheel angle [rad].</summary>
        public double Angle;

        public Steering(SteeringDefinition def)
        {
            Def = def;
            _maxAngle = def.maxRoadWheelAngleDeg * MathUtil.Deg2Rad;
            _maxRate = def.maxSteerRateDegS * MathUtil.Deg2Rad;
        }

        public double MaxAngle => _maxAngle;

        /// <summary>Handwheel angle [deg] derived from the road-wheel angle and overall ratio.</summary>
        public double HandwheelDeg => Angle * MathUtil.Rad2Deg * Def.steeringRatio;

        public void Update(double command, double dt)
        {
            double target = MathUtil.Clamp(command, -1, 1) * _maxAngle;
            Angle = MathUtil.MoveTowards(Angle, target, _maxRate * dt);
        }

        /// <summary>
        /// Road-wheel angle for a steered wheel at lateral offset x [m], whose axle is `wheelbase` metres
        /// ahead of the reference (non-steered) axle line.
        /// </summary>
        public double WheelAngle(double x, double wheelbase)
        {
            double d = Angle;
            if (Math.Abs(d) < 1e-6 || wheelbase <= 0) return d;
            double radius = wheelbase / Math.Tan(d); // signed: >0 centre on the right
            double ack = Math.Atan(wheelbase / (radius - x));
            // atan wraps when the wheel is beyond the turn centre; keep the sign of the command.
            if (Math.Sign(ack) != Math.Sign(d)) ack = d;
            return d + Def.ackermannFactor * (ack - d);
        }
    }
}
