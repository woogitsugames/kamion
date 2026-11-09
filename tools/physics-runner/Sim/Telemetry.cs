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
        public Vec3 Pos, ComPos, Vel, Fwd, Right;
        public double SpeedFwd, YawRate, Rpm, SteerAngle, Pitch, Roll, LatAccel, LongAccel;
        public int Gear;
        public double ThrottleIn, BrakeIn;
        public bool Stalled;
        public double MaxFzRatio;
        public double SumFz;
        public double MinFz;
        public int WheelsOffGround;
        /// <summary>Bit i set = wheel i unloaded (no contact or Fz &lt; 500 N); tractor wheels first, then trailer.</summary>
        public ulong OffMask;
        public int TractorWheelCount;
        public double KineticEnergy;
        // combination
        public bool HasTrailer, Coupled;
        public Vec3 TrailerPos, TrailerComPos, TrailerVel, TrailerAxlePos;
        public double Articulation, KingpinFz, KingpinFx, KingpinFy, FifthWheelError;
        public double TrailerYawRate, TrailerLatAccel, TrailerRoll;
        // brakes / air / endurance
        public double AirFront, AirRear, AirPark, AirTrailer, AirSupply;
        public bool LowAirWarning, TrailerEmergency;
        public double ChamberFront, ChamberRear, ChamberTrailer;
        public double RearSlip;              // most negative kinematic slip on the tractor drive axle
        public double TrailerSlip;           // most negative kinematic slip on the trailer
        public double RetarderTorque, EngineBrakeTorque, BrakeDemand;
        public double ClutchTemp;
        public int AmtState;
        public double CabPitch, CabRoll, CabHeave;
        public double LandingGearLoad;
        public double ParkingState;
    }

    /// <summary>CSV telemetry writer (docs/04 section 4).</summary>
    public sealed class CsvTelemetry : IDisposable
    {
        readonly StreamWriter _w;
        readonly StringBuilder _sb = new StringBuilder(8192);
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
        readonly string _configId, _commit;

        public CsvTelemetry(string path, SimContext s, string configId, string commit)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            _w = new StreamWriter(path, false, new UTF8Encoding(false));
            _configId = configId; _commit = commit;
            _sb.Append("t,x,y,z,speed_kmh,v_fwd,a_long,a_lat,yaw_rate_dps,heading_deg,pitch_deg,roll_deg,");
            _sb.Append("throttle_in,brake_in,steer_in,parking_in,retarder_lever,throttle_eff,brake_demand,parking_state,hill_hold,");
            _sb.Append("rpm,gear,amt_state,clutch_cmd,engine_torque,clutch_torque,boost,asr_factor,clutch_temp_c,");
            _sb.Append("engine_brake_cmd,engine_brake_torque,retarder_cmd,retarder_torque,retarder_power_kw,");
            _sb.Append("air_supply_bar,air_front_bar,air_rear_bar,air_park_bar,air_red_bar,air_yellow_bar,air_trailer_res_bar,low_air_warning,compressor_on,trailer_emergency,");
            _sb.Append("steer_angle_deg,handwheel_deg,aligning_torque,cab_pitch_deg,cab_roll_deg,cab_heave_mm,");
            _sb.Append("articulation_deg,kingpin_fz,kingpin_fx,kingpin_fy,fifth_wheel_err_mm,coupled,trailer_yaw_rate_dps,trailer_a_lat,trailer_roll_deg,trailer_x,trailer_z,landing_gear_load,");
            foreach (var wh in s.AllWheels)
            {
                string n = wh.Name;
                _sb.Append($"{n}_fz,{n}_fx,{n}_fy,{n}_slip,{n}_alpha_deg,{n}_comp,{n}_omega,{n}_brake_t,{n}_abs,{n}_drive_t,{n}_tire_defl,{n}_contact,{n}_p_bar,");
            }
            _sb.Append("axle0_load,axle1_load,trailer_axles_load,step_us,config_id,commit");
            _w.WriteLine(_sb.ToString());
        }

        void F(double v) { _sb.Append(v.ToString("G6", Inv)); _sb.Append(','); }

        public void Write(SimContext s, in DriverInput inp, double stepMicros)
        {
            var m = s.Tractor; var b = s.Body; var tr = s.Trailer; var fw = s.Combo.FifthWheel;
            _sb.Clear();
            Vec3 fwd = b.Rotation * Vec3.Forward;
            Vec3 right = b.Rotation * Vec3.Right;
            double heading = Math.Atan2(fwd.x, fwd.z) * MathUtil.Rad2Deg;
            double pitch = Math.Asin(MathUtil.Clamp(fwd.y, -1, 1)) * MathUtil.Rad2Deg;
            double roll = Math.Asin(MathUtil.Clamp(right.y, -1, 1)) * MathUtil.Rad2Deg;
            F(m.Time); F(b.Position.x); F(b.Position.y); F(b.Position.z);
            F(b.Velocity.Magnitude * 3.6); F(m.SpeedForward); F(m.LocalAcceleration.z); F(m.LocalAcceleration.x + m.SpeedForward * m.YawRate);
            F(m.YawRate * MathUtil.Rad2Deg); F(heading); F(pitch); F(roll);
            F(inp.Throttle); F(inp.Brake); F(inp.Steer); F(inp.ParkingBrake ? 1 : 0); F(inp.RetarderLever); F(m.ThrottleDemand); F(m.BrakeDemand); F(m.ParkingBrakeState); F(m.HillHoldActive ? 1 : 0);
            F(m.Engine.Rpm); F(m.Amt.Gear); F((int)m.Amt.State); F(m.Amt.ClutchCommand); F(m.EngineTorque); F(m.ClutchTorque); F(m.Engine.Boost); F(m.AsrFactor); F(m.Amt.ClutchTempC);
            F(m.EngineBrakeCommand); F(m.Engine.EngineBrakeTorque); F(m.RetarderCommand); F(m.Retarder.Torque); F(m.Retarder.Power / 1000);
            var a = m.Air;
            F(a.Supply); F(a.Front); F(a.Rear); F(a.ParkTrailer); F(a.TrailerSupplyLine); F(a.TrailerControlLine); F(tr != null ? tr.Brakes.Reservoir : 0);
            F(a.LowPressureWarning ? 1 : 0); F(a.CompressorLoaded ? 1 : 0); F(tr != null && tr.Brakes.Emergency ? 1 : 0);
            F(m.Steering.Angle * MathUtil.Rad2Deg); F(m.Steering.HandwheelDeg); F(m.AligningTorqueTotal); F(m.Cab.Pitch * MathUtil.Rad2Deg); F(m.Cab.Roll * MathUtil.Rad2Deg); F(m.Cab.Heave * 1000);
            if (tr != null)
            {
                var tb = s.TrailerBody;
                Vec3 tright = tb.Rotation * Vec3.Right;
                F(fw.Articulation * MathUtil.Rad2Deg); F(fw.KingpinLoadLocal.y); F(fw.KingpinLoadLocal.z); F(fw.KingpinLoadLocal.x); F(fw.PositionError * 1000); F(fw.Coupled ? 1 : 0);
                F(tr.YawRate * MathUtil.Rad2Deg); F(tr.SpeedForward * tr.YawRate); F(Math.Asin(MathUtil.Clamp(tright.y, -1, 1)) * MathUtil.Rad2Deg); F(tb.Position.x); F(tb.Position.z); F(tr.LandingGearLoad);
            }
            else for (int i = 0; i < 12; i++) F(0);
            double a0 = 0, a1 = 0, at = 0;
            foreach (var w in m.Wheels) { WriteWheel(w); if (w.AxleIndex == 0) a0 += w.Fz; else a1 += w.Fz; }
            if (tr != null) foreach (var w in tr.Wheels) { WriteWheel(w); at += w.Fz; }
            F(a0); F(a1); F(at); F(stepMicros);
            _sb.Append(_configId); _sb.Append(','); _sb.Append(_commit);
            _w.WriteLine(_sb.ToString());
        }

        void WriteWheel(WheelState w)
        {
            F(w.Fz); F(w.Fx); F(w.Fy); F(w.SlipRatio); F(w.SlipAngle * MathUtil.Rad2Deg); F(w.Compression); F(w.Omega); F(w.BrakeTorque); F(w.AbsActive ? 1 : 0); F(w.DriveTorque); F(w.TireDeflection); F(w.Contact ? 1 : 0); F(w.ChamberPressure);
        }

        public void Dispose() => _w.Dispose();
    }
}
