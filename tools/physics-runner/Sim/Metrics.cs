using System;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    /// <summary>Scalar metrics over a recorded run. Names are referenced from scenario JSON checks.</summary>
    public static class Metrics
    {
        public static double Compute(RunResult r, string name, double arg, double from)
        {
            var s = r.Samples;
            if (s.Count == 0) return double.NaN;
            int i0 = IndexAt(r, from);
            switch (name)
            {
                case "drift_m":
                    return (s[s.Count - 1].Pos - s[i0].Pos).Magnitude;
                case "max_speed_after_ms":
                {
                    double m = 0;
                    for (int i = i0; i < s.Count; i++) m = Math.Max(m, s[i].Vel.Magnitude);
                    return m;
                }
                case "rollback_m":
                {
                    // Largest displacement opposite to the net travel direction (start -> end) after 'from'.
                    Vec3 p0 = s[i0].Pos;
                    Vec3 dir = (s[s.Count - 1].Pos - p0).Normalized;
                    if (dir.SqrMagnitude < 0.5) return 0;
                    double worst = 0;
                    for (int i = i0; i < s.Count; i++) worst = Math.Max(worst, -Vec3.Dot(s[i].Pos - p0, dir));
                    return worst;
                }
                case "time_to_kmh":
                {
                    double tStart = double.NaN;
                    for (int i = 0; i < s.Count; i++) if (s[i].ThrottleIn > 0.01) { tStart = s[i].T - r.Dt; break; }
                    if (double.IsNaN(tStart)) return double.NaN;
                    for (int i = 1; i < s.Count; i++)
                    {
                        double v1 = Math.Abs(s[i].SpeedFwd) * 3.6;
                        if (v1 >= arg)
                        {
                            double v0 = Math.Abs(s[i - 1].SpeedFwd) * 3.6;
                            double f = v1 > v0 ? (arg - v0) / (v1 - v0) : 0;
                            return s[i - 1].T + f * (s[i].T - s[i - 1].T) - tStart;
                        }
                    }
                    return double.NaN;
                }
                case "max_speed_kmh":
                {
                    double m = 0;
                    for (int i = i0; i < s.Count; i++) m = Math.Max(m, s[i].SpeedFwd * 3.6);
                    return m;
                }
                case "mean_speed_kmh":
                {
                    double sum = 0; int n = 0;
                    for (int i = i0; i < s.Count; i++) { sum += s[i].SpeedFwd * 3.6; n++; }
                    return n > 0 ? sum / n : double.NaN;
                }
                case "stop_distance_m":
                {
                    int ib = FirstBrake(s);
                    if (ib < 0) return double.NaN;
                    Vec3 pb = ib > 0 ? s[ib - 1].Pos : s[ib].Pos;
                    for (int i = ib; i < s.Count; i++)
                        if (Math.Abs(s[i].SpeedFwd) < 0.05) return (s[i].Pos - pb).Magnitude;
                    return double.NaN;
                }
                case "mfdd_ms2":
                {
                    // Mean fully developed deceleration, UN R13 Annex 4 definition: between 0.8 v0 and 0.1 v0.
                    int ib = FirstBrake(s);
                    if (ib < 0) return double.NaN;
                    double v0 = Math.Abs(s[Math.Max(ib - 1, 0)].SpeedFwd);
                    double vb = 0.8 * v0, ve = 0.1 * v0;
                    int ia = -1, ie = -1;
                    for (int i = ib; i < s.Count; i++)
                    {
                        double v = Math.Abs(s[i].SpeedFwd);
                        if (ia < 0 && v <= vb) ia = i;
                        if (ie < 0 && v <= ve) { ie = i; break; }
                    }
                    if (ia < 0 || ie < 0) return double.NaN;
                    double sd = (s[ie].Pos - s[ia].Pos).Magnitude;
                    double va = Math.Abs(s[ia].SpeedFwd), vE = Math.Abs(s[ie].SpeedFwd);
                    return (va * va - vE * vE) / (2 * sd);
                }
                case "max_lateral_deviation_m":
                {
                    int ib = FirstBrake(s);
                    if (ib < 0) ib = 0;
                    Vec3 p0 = s[ib].Pos;
                    Vec3 dir = s[ib].Vel.Normalized;
                    double m = 0;
                    for (int i = ib; i < s.Count; i++)
                    {
                        Vec3 d = s[i].Pos - p0;
                        Vec3 lat = d - dir * Vec3.Dot(d, dir);
                        m = Math.Max(m, new Vec3(lat.x, 0, lat.z).Magnitude);
                    }
                    return m;
                }
                case "radius_mean_m":
                {
                    double sum = 0; int n = 0;
                    for (int i = i0; i < s.Count; i++) { sum += HorizDist(s[i].Pos, r.CircleCenter); n++; }
                    return sum / n;
                }
                case "radius_error_m":
                {
                    double m = 0;
                    for (int i = i0; i < s.Count; i++) m = Math.Max(m, Math.Abs(HorizDist(s[i].Pos, r.CircleCenter) - r.CircleRadius));
                    return m;
                }
                case "steer_angle_deg":
                {
                    double sum = 0; int n = 0;
                    for (int i = i0; i < s.Count; i++) { sum += s[i].SteerAngle; n++; }
                    return sum / n * MathUtil.Rad2Deg;
                }
                case "steer_vs_ackermann":
                {
                    // Ratio of mean steer angle to kinematic angle atan(L/R) (understeer > 1).
                    double sum = 0; int n = 0;
                    for (int i = i0; i < s.Count; i++) { sum += s[i].SteerAngle; n++; }
                    double kin = Math.Atan(arg / r.CircleRadius);
                    return Math.Abs(sum / n) / kin;
                }
                case "lat_accel_ms2":
                {
                    double sum = 0; int n = 0;
                    for (int i = i0; i < s.Count; i++) { sum += s[i].LatAccel; n++; }
                    return Math.Abs(sum / n);
                }
                case "yaw_rate_mean_dps":
                {
                    double sum = 0; int n = 0;
                    for (int i = i0; i < s.Count; i++) { sum += s[i].YawRate; n++; }
                    return sum / n * MathUtil.Rad2Deg;
                }
                case "lateral_displacement_m":
                    return s[s.Count - 1].Pos.x - s[i0].Pos.x;
                case "max_dv_step_ms":
                {
                    double m = 0;
                    for (int i = Math.Max(i0, 1); i < s.Count; i++) m = Math.Max(m, (s[i].Vel - s[i - 1].Vel).Magnitude);
                    return m;
                }
                case "max_pos_jump_m":
                {
                    // Position change not explained by velocity (teleport detector).
                    double m = 0;
                    for (int i = Math.Max(i0, 1); i < s.Count; i++)
                        m = Math.Max(m, ((s[i].ComPos - s[i - 1].ComPos) - s[i].Vel * r.Dt).Magnitude);
                    return m;
                }
                case "max_fz_ratio":
                {
                    double m = 0;
                    for (int i = i0; i < s.Count; i++) m = Math.Max(m, s[i].MaxFzRatio);
                    return m;
                }
                case "min_rpm":
                {
                    double m = double.MaxValue;
                    for (int i = i0; i < s.Count; i++) m = Math.Min(m, s[i].Rpm);
                    return m;
                }
                case "stalled":
                {
                    for (int i = i0; i < s.Count; i++) if (s[i].Stalled) return 1;
                    return 0;
                }
                case "max_abs_roll_deg":
                {
                    double m = 0;
                    for (int i = i0; i < s.Count; i++) m = Math.Max(m, Math.Abs(s[i].Roll));
                    return m * MathUtil.Rad2Deg;
                }
                case "final_z_m":
                    return s[s.Count - 1].Pos.z;
                case "final_gear":
                    return s[s.Count - 1].Gear;
                case "max_yaw_rate_dps":
                {
                    double m = 0;
                    for (int i = i0; i < s.Count; i++) m = Math.Max(m, Math.Abs(s[i].YawRate));
                    return m * MathUtil.Rad2Deg;
                }
                default:
                    throw new ArgumentException($"Unknown metric '{name}'");
            }
        }

        static double HorizDist(Vec3 a, Vec3 b)
        {
            double dx = a.x - b.x, dz = a.z - b.z;
            return Math.Sqrt(dx * dx + dz * dz);
        }

        static int FirstBrake(System.Collections.Generic.List<Sample> s)
        {
            for (int i = 0; i < s.Count; i++) if (s[i].BrakeIn > 0.05) return i;
            return -1;
        }

        static int IndexAt(RunResult r, double t)
        {
            var s = r.Samples;
            for (int i = 0; i < s.Count; i++) if (s[i].T >= t - 1e-9) return i;
            return s.Count - 1;
        }
    }
}
