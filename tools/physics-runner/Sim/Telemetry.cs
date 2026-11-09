using System;
using System.Globalization;
using System.IO;
using System.Text;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    /// <summary>Compact per-step record used for metrics.</summary>
    public struct Sample
    {
        public double T;
        public Vec3 Pos, ComPos, Vel;
        public double SpeedFwd, YawRate, Rpm, SteerAngle, Pitch, Roll, LatAccel, LongAccel;
        public int Gear;
        public double ThrottleIn, BrakeIn;
        public bool Stalled;
        public double MaxFzRatio;
        public double SumFz;
    }

    /// <summary>CSV telemetry writer (docs/04 section 4 subset for a solo tractor).</summary>
    public sealed class CsvTelemetry : IDisposable
    {
        readonly StreamWriter _w;
        readonly StringBuilder _sb = new StringBuilder(4096);
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
        readonly string _configId, _commit;

        public CsvTelemetry(string path, VehicleModel m, string configId, string commit)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            _w = new StreamWriter(path, false, new UTF8Encoding(false));
            _configId = configId; _commit = commit;
            _sb.Append("t,x,y,z,speed_kmh,v_fwd,a_long,a_lat,yaw_rate_dps,heading_deg,pitch_deg,roll_deg,");
            _sb.Append("throttle_in,brake_in,steer_in,parking_in,throttle_eff,brake_demand,parking_state,hill_hold,");
            _sb.Append("rpm,gear,amt_state,clutch_cmd,engine_torque,clutch_torque,boost,asr_factor,");
            _sb.Append("steer_angle_deg,handwheel_deg,aligning_torque,cab_pitch_deg,cab_roll_deg,");
            foreach (var wh in m.Wheels)
            {
                string n = wh.Name;
                _sb.Append($"{n}_fz,{n}_fx,{n}_fy,{n}_slip,{n}_alpha_deg,{n}_comp,{n}_omega,{n}_brake_t,{n}_abs,{n}_drive_t,{n}_tire_defl,{n}_contact,");
            }
            _sb.Append("axle0_load,axle1_load,step_us,config_id,commit");
            _w.WriteLine(_sb.ToString());
        }

        void F(double v) { _sb.Append(v.ToString("G6", Inv)); _sb.Append(','); }

        public void Write(VehicleModel m, RigidBody6Dof b, in DriverInput inp, double stepMicros)
        {
            _sb.Clear();
            Vec3 fwd = b.Rotation * Vec3.Forward;
            Vec3 right = b.Rotation * Vec3.Right;
            double heading = Math.Atan2(fwd.x, fwd.z) * MathUtil.Rad2Deg;
            double pitch = Math.Asin(MathUtil.Clamp(fwd.y, -1, 1)) * MathUtil.Rad2Deg;
            double roll = Math.Asin(MathUtil.Clamp(right.y, -1, 1)) * MathUtil.Rad2Deg;
            F(m.Time); F(b.Position.x); F(b.Position.y); F(b.Position.z);
            F(b.Velocity.Magnitude * 3.6); F(m.SpeedForward); F(m.LocalAcceleration.z); F(m.LocalAcceleration.x);
            F(m.YawRate * MathUtil.Rad2Deg); F(heading); F(pitch); F(roll);
            F(inp.Throttle); F(inp.Brake); F(inp.Steer); F(inp.ParkingBrake ? 1 : 0); F(m.ThrottleDemand); F(m.BrakeDemand); F(m.ParkingBrakeState); F(m.HillHoldActive ? 1 : 0);
            F(m.Engine.Rpm); F(m.Amt.Gear); F((int)m.Amt.State); F(m.Amt.ClutchCommand); F(m.EngineTorque); F(m.ClutchTorque); F(m.Engine.Boost); F(m.AsrFactor);
            F(m.Steering.Angle * MathUtil.Rad2Deg); F(m.Steering.HandwheelDeg); F(m.AligningTorqueTotal); F(m.Cab.Pitch * MathUtil.Rad2Deg); F(m.Cab.Roll * MathUtil.Rad2Deg);
            double a0 = 0, a1 = 0;
            foreach (var w in m.Wheels)
            {
                F(w.Fz); F(w.Fx); F(w.Fy); F(w.SlipRatio); F(w.SlipAngle * MathUtil.Rad2Deg); F(w.Compression); F(w.Omega); F(w.BrakeTorque); F(w.AbsFactor); F(w.DriveTorque); F(w.TireDeflection); F(w.Contact ? 1 : 0);
                if (w.AxleIndex == 0) a0 += w.Fz; else a1 += w.Fz;
            }
            F(a0); F(a1); F(stepMicros);
            _sb.Append(_configId); _sb.Append(','); _sb.Append(_commit);
            _w.WriteLine(_sb.ToString());
        }

        public void Dispose() => _w.Dispose();
    }
}
