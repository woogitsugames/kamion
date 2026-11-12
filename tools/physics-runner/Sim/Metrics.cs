using System;
using System.Collections.Generic;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    /// <summary>Scalar metrics over a recorded run. Names are referenced from scenario JSON checks.</summary>
    public static class Metrics
    {
        public static double Compute(RunResult r, string name, double arg, double from, double to = 0)
        {
            var s = r.Samples;
            if (s.Count == 0) return double.NaN;
            int i0 = IndexAt(r, from);
            int i1 = to > 0 ? IndexAt(r, to) : s.Count - 1;
            switch (name)
            {
                case "drift_m":
                    return (s[i1].Pos - s[i0].Pos).Magnitude;
                case "creep_m":
                {
                    // Displacement in the ground plane (vehicle forward / right at 'from'): creep, without the
                    // vertical settling of the levelled air suspension.
                    Vec3 d = s[i1].Pos - s[i0].Pos;
                    double a = Vec3.Dot(d, s[i0].Fwd), b = Vec3.Dot(d, s[i0].Right);
                    return Math.Sqrt(a * a + b * b);
                }
                case "trailer_creep_m":
                {
                    Vec3 d = s[i1].TrailerPos - s[i0].TrailerPos;
                    double a = Vec3.Dot(d, s[i0].Fwd), b = Vec3.Dot(d, s[i0].Right);
                    return Math.Sqrt(a * a + b * b);
                }
                case "trailer_drift_m":
                    return (s[i1].TrailerPos - s[i0].TrailerPos).Magnitude;
                case "max_speed_after_ms":
                {
                    double m = 0;
                    for (int i = i0; i <= i1; i++) m = Math.Max(m, Math.Max(s[i].Vel.Magnitude, s[i].TrailerVel.Magnitude));
                    return m;
                }
                case "rollback_m":
                {
                    Vec3 p0 = s[i0].Pos;
                    Vec3 dir = (s[i1].Pos - p0).Normalized;
                    if (dir.SqrMagnitude < 0.5) return 0;
                    double worst = 0;
                    for (int i = i0; i <= i1; i++) worst = Math.Max(worst, -Vec3.Dot(s[i].Pos - p0, dir));
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
                case "max_speed_kmh": return Max(s, i0, i1, x => x.SpeedFwd * 3.6);
                case "min_speed_kmh": return Min(s, i0, i1, x => x.SpeedFwd * 3.6);
                case "mean_speed_kmh": return Mean(s, i0, i1, x => x.SpeedFwd * 3.6);
                case "speed_range_kmh": return Max(s, i0, i1, x => x.SpeedFwd * 3.6) - Min(s, i0, i1, x => x.SpeedFwd * 3.6);
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
                    if (ib < 0) ib = i0;
                    Vec3 p0 = s[ib].Pos;
                    Vec3 dir = s[ib].Vel.Normalized;
                    double m = 0;
                    for (int i = ib; i <= i1; i++)
                    {
                        Vec3 d = s[i].Pos - p0;
                        Vec3 lat = d - dir * Vec3.Dot(d, dir);
                        m = Math.Max(m, new Vec3(lat.x, 0, lat.z).Magnitude);
                    }
                    return m;
                }
                case "radius_mean_m": return Mean(s, i0, i1, x => HorizDist(x.Pos, r.CircleCenter));
                case "radius_error_m": return Max(s, i0, i1, x => Math.Abs(HorizDist(x.Pos, r.CircleCenter) - r.CircleRadius));
                case "trailer_offtracking_m":
                    // Rear-axle-group path radius of the trailer minus the tractor rear-axle radius (positive = inside).
                    return Mean(s, i0, i1, x => HorizDist(x.Pos, r.CircleCenter)) - Mean(s, i0, i1, x => HorizDist(x.TrailerAxlePos, r.CircleCenter));
                case "steer_angle_deg": return Mean(s, i0, i1, x => x.SteerAngle) * MathUtil.Rad2Deg;
                case "steer_vs_ackermann":
                {
                    double mean = Mean(s, i0, i1, x => x.SteerAngle);
                    double kin = Math.Atan(arg / r.CircleRadius);
                    return Math.Abs(mean) / kin;
                }
                case "lat_accel_ms2": return Math.Abs(Mean(s, i0, i1, x => x.LatAccel));
                case "max_lat_accel_ms2": return Max(s, i0, i1, x => Math.Abs(x.LatAccel));
                case "yaw_rate_mean_dps": return Mean(s, i0, i1, x => x.YawRate) * MathUtil.Rad2Deg;
                case "lateral_displacement_m": return s[i1].Pos.x - s[i0].Pos.x;
                case "max_dv_step_ms":
                {
                    double m = 0;
                    for (int i = Math.Max(i0, 1); i <= i1; i++)
                    {
                        m = Math.Max(m, (s[i].Vel - s[i - 1].Vel).Magnitude);
                        if (s[i].HasTrailer) m = Math.Max(m, (s[i].TrailerVel - s[i - 1].TrailerVel).Magnitude);
                    }
                    return m;
                }
                case "max_pos_jump_m":
                {
                    double m = 0;
                    for (int i = Math.Max(i0, 1); i <= i1; i++)
                    {
                        m = Math.Max(m, ((s[i].ComPos - s[i - 1].ComPos) - s[i].Vel * r.SampleDt).Magnitude);
                        if (s[i].HasTrailer) m = Math.Max(m, ((s[i].TrailerComPos - s[i - 1].TrailerComPos) - s[i].TrailerVel * r.SampleDt).Magnitude);
                    }
                    return m;
                }
                case "max_fz_ratio": return Max(s, i0, i1, x => x.MaxFzRatio);
                case "min_rpm": return Min(s, i0, i1, x => x.Rpm);
                case "max_rpm": return Max(s, i0, i1, x => x.Rpm);
                case "max_rpm_in_gear":
                {
                    // Highest engine speed while driving (clutch closed, Drive state) in gears <= arg.
                    double m = 0;
                    for (int i = i0; i <= i1; i++) if (s[i].AmtState == (int)AmtState.Drive && s[i].Gear > 0 && s[i].Gear <= arg) m = Math.Max(m, s[i].Rpm);
                    return m;
                }
                case "stalled":
                {
                    for (int i = i0; i <= i1; i++) if (s[i].Stalled) return 1;
                    return 0;
                }
                case "max_abs_roll_deg": return Max(s, i0, i1, x => Math.Abs(x.Roll)) * MathUtil.Rad2Deg;
                case "max_trailer_roll_deg": return Max(s, i0, i1, x => Math.Abs(x.TrailerRoll)) * MathUtil.Rad2Deg;
                case "final_z_m": return s[i1].Pos.z;
                case "final_gear": return s[i1].Gear;
                case "max_gear": return Max(s, i0, i1, x => x.Gear);
                case "shift_count": return r.ShiftCount;
                case "downshift_count":
                {
                    // Engaged forward gear lower than the previous engaged forward gear (neutral during a shift skipped).
                    int n = 0, last = 0;
                    for (int i = i0; i <= i1; i++)
                    {
                        int g = s[i].Gear;
                        if (g <= 0) continue;
                        if (last > 0 && g < last) n++;
                        last = g;
                    }
                    return n;
                }
                case "rejected_shifts": return r.RejectedShifts;
                case "max_yaw_rate_dps": return Max(s, i0, i1, x => Math.Abs(x.YawRate)) * MathUtil.Rad2Deg;
                // ---------------- combination ----------------
                case "max_articulation_deg": return Max(s, i0, i1, x => Math.Abs(x.Articulation)) * MathUtil.Rad2Deg;
                case "final_articulation_deg": return Math.Abs(s[i1].Articulation) * MathUtil.Rad2Deg;
                case "kingpin_load_kn": return Mean(s, i0, i1, x => x.KingpinFz) / 1000;
                case "kingpin_load_vs_static": return r.StaticKingpinLoad > 0 ? Mean(s, i0, i1, x => x.KingpinFz) / r.StaticKingpinLoad : double.NaN;
                case "max_kingpin_long_kn": return Max(s, i0, i1, x => Math.Abs(x.KingpinFx)) / 1000;
                case "max_fifth_wheel_error_mm": return Max(s, i0, i1, x => x.FifthWheelError) * 1000;
                case "max_trailer_yaw_rate_dps": return Max(s, i0, i1, x => Math.Abs(x.TrailerYawRate)) * MathUtil.Rad2Deg;
                case "rearward_amplification":
                {
                    double tr = Max(s, i0, i1, x => Math.Abs(x.TrailerLatAccel));
                    double tk = Max(s, i0, i1, x => Math.Abs(x.LatAccel));
                    return tk > 1e-6 ? tr / tk : double.NaN;
                }
                case "articulation_settle_deg":
                    // Largest articulation in the window (use after the manoeuvre: residual oscillation).
                    return Max(s, i0, i1, x => Math.Abs(x.Articulation)) * MathUtil.Rad2Deg;
                case "lat_accel_at_first_lift":
                {
                    for (int i = i0; i <= i1; i++) if (s[i].WheelsOffGround > 0) return Math.Abs(s[i].LatAccel) / 9.81;
                    return double.NaN;
                }
                case "wheel_off_ground_time_s":
                {
                    // total time with any wheel (tractor or trailer) unloaded; samples are equally spaced
                    if (i1 <= i0) return 0;
                    double dtS = (s[i1].T - s[i0].T) / (i1 - i0), tOff = 0;
                    for (int i = i0; i <= i1; i++) if (s[i].WheelsOffGround > 0) tOff += dtS;
                    return tOff;
                }
                case "max_wheel_airtime_s":
                {
                    // longest continuous interval in which one single wheel is unloaded ("axle flight");
                    // arg 1 = tractor wheels only, otherwise every wheel of the combination
                    if (i1 <= i0) return 0;
                    double dtS = (s[i1].T - s[i0].T) / (i1 - i0), best = 0;
                    var run = new int[64];
                    for (int i = i0; i <= i1; i++)
                    {
                        ulong mask = s[i].OffMask;
                        int n = arg == 1 ? s[i].TractorWheelCount : 64;
                        for (int b = 0; b < n; b++)
                        {
                            run[b] = (mask & (1UL << b)) != 0 ? run[b] + 1 : 0;
                            best = Math.Max(best, run[b] * dtS);
                        }
                    }
                    return best;
                }
                case "wheel_lift": return Max(s, i0, i1, x => x.WheelsOffGround) > 0 ? 1 : 0;
                case "coupled_final": return s[i1].Coupled ? 1 : 0;
                case "coupling_events": return r.CouplingEvents;
                case "uncoupling_events": return r.UncouplingEvents;
                case "tractor_trailer_distance_m": return HorizDist(s[i1].Pos, s[i1].TrailerPos);
                case "landing_gear_load_kn": return Mean(s, i0, i1, x => x.LandingGearLoad) / 1000;
                // ---------------- air / brakes ----------------
                case "min_air_service_bar": return Min(s, i0, i1, x => Math.Min(x.AirFront, x.AirRear));
                case "min_air_trailer_bar": return Min(s, i0, i1, x => x.AirTrailer);
                case "min_air_park_bar": return Min(s, i0, i1, x => x.AirPark);
                case "final_air_service_bar": return Math.Min(s[i1].AirFront, s[i1].AirRear);
                case "low_air_warning": { for (int i = i0; i <= i1; i++) if (s[i].LowAirWarning) return 1; return 0; }
                case "time_low_air_warning":
                {
                    for (int i = i0; i <= i1; i++) if (s[i].LowAirWarning) return s[i].T;
                    return double.NaN;
                }
                case "trailer_emergency": { for (int i = i0; i <= i1; i++) if (s[i].TrailerEmergency) return 1; return 0; }
                case "brake_response_s":
                {
                    // Time from pedal application to 75 % of the final chamber pressure: arg 0 front, 1 rear, 2 trailer.
                    int ib = FirstBrake(s);
                    if (ib < 0) return double.NaN;
                    Func<Sample, double> p = arg < 0.5 ? (Func<Sample, double>)(x => x.ChamberFront) : arg < 1.5 ? x => x.ChamberRear : x => x.ChamberTrailer;
                    double final = 0;
                    for (int i = ib; i < Math.Min(s.Count, ib + (int)(2.0 / r.SampleDt)); i++) final = Math.Max(final, p(s[i]));
                    if (final <= 0.1) return double.NaN;
                    for (int i = ib; i < s.Count; i++) if (p(s[i]) >= 0.75 * final) return s[i].T - s[ib].T + r.SampleDt;
                    return double.NaN;
                }
                case "rear_lock_time_s":
                {
                    // Total time a tractor drive wheel is (nearly) locked: kinematic slip < -arg (default 0.5) while moving.
                    double thr = arg > 0 ? arg : 0.5, tot = 0;
                    for (int i = i0; i <= i1; i++) if (s[i].RearSlip < -thr) tot += r.SampleDt;
                    return tot;
                }
                case "trailer_lock_time_s":
                {
                    double thr = arg > 0 ? arg : 0.5, tot = 0;
                    for (int i = i0; i <= i1; i++) if (s[i].TrailerSlip < -thr) tot += r.SampleDt;
                    return tot;
                }
                case "max_retarder_torque_nm": return Max(s, i0, i1, x => x.RetarderTorque);
                case "max_engine_brake_torque_nm": return Max(s, i0, i1, x => x.EngineBrakeTorque);
                case "max_service_demand": return Max(s, i0, i1, x => x.BrakeDemand);
                case "max_clutch_temp_c": return Max(s, i0, i1, x => x.ClutchTemp);
                case "max_cab_pitch_deg": return Max(s, i0, i1, x => Math.Abs(x.CabPitch)) * MathUtil.Rad2Deg;
                case "max_cab_heave_mm": return Max(s, i0, i1, x => Math.Abs(x.CabHeave)) * 1000;
                case "parking_state_min": return Min(s, i0, i1, x => x.ParkingState);
                case "park_warning": { for (int i = i0; i <= i1; i++) if (s[i].ParkWarning) return 1; return 0; }
                // ---------------- shift interruption (ADR 0004 addendum 2026-11-10) ----------------
                case "max_shift_retard_torque_nm":
                {
                    // Wheel brakes (service + spring, all axles) + retarder + engine brake while an up-/down-shift
                    // is in progress: must be 0 unless the driver commands braking.
                    double m = 0;
                    for (int i = i0; i <= i1; i++)
                        if (s[i].AmtState >= (int)AmtState.ShiftTorqueRamp)
                            // The engine brake counts only while the clutch transmits: with the clutch open it only pulls the
                            // engine down to the new gear's speed (AMT up-shift sync, ADR 0134) and cannot brake the vehicle.
                            m = Math.Max(m, s[i].WheelBrakeTorque + s[i].RetarderTorque + (s[i].ClutchCmd > 0.01 ? s[i].EngineBrakeTorque : 0));
                    return m;
                }
                case "max_shift_eye_pitch_swing_deg":
                {
                    // ADR 0134 (owner feel test 2026-11-12, "buja jak sportowe auto"): peak-to-peak pitch of the driver's eye
                    // in the world (chassis pitch, nose up +, minus cab pitch relative to the frame, nose down +) within
                    // arg seconds (default 1.5) after the start of each shift; worst shift. The cab-view camera rides on
                    // the cab pivot, so this is the nod the player sees on every gear change.
                    double win = arg > 0 ? arg : 1.5, m = 0;
                    for (int i = Math.Max(i0, 1); i <= i1; i++)
                    {
                        if (!(s[i].AmtState == (int)AmtState.ShiftTorqueRamp && s[i - 1].AmtState != (int)AmtState.ShiftTorqueRamp)) continue;
                        double lo = double.MaxValue, hi = double.MinValue;
                        for (int j = i; j <= i1 && s[j].T <= s[i].T + win; j++)
                        {
                            double e = s[j].Pitch - s[j].CabPitch;
                            lo = Math.Min(lo, e); hi = Math.Max(hi, e);
                        }
                        m = Math.Max(m, (hi - lo) * MathUtil.Rad2Deg);
                    }
                    return m;
                }
                case "min_accel_shift_gap_ms2":
                {
                    // Mean longitudinal acceleration (forward speed change / time) of each clutch-open gap (neutral +
                    // synchronisation), worst gap: only rolling resistance + aero (+ grade) may act. Per-gap mean, not
                    // the instantaneous value: the fifth-wheel surge when the driveline unloads swings the tractor
                    // a_long by +/-0.5-1 m/s2 for ~0.2 s with zero net impulse (real cab/trailer jolt, not braking).
                    double m = double.MaxValue; int g0 = -1;
                    for (int i = i0; i <= i1 + 1; i++)
                    {
                        bool gap = i <= i1 && (s[i].AmtState == (int)AmtState.ShiftNeutral || s[i].AmtState == (int)AmtState.ShiftSync);
                        if (gap) { if (g0 < 0) g0 = i; continue; }
                        if (g0 >= 0 && i - 1 > g0)
                            m = Math.Min(m, (s[i - 1].SpeedFwd - s[g0].SpeedFwd) / (s[i - 1].T - s[g0].T));
                        g0 = -1;
                    }
                    return m == double.MaxValue ? 0 : m;
                }
                // ---------------- soak ----------------
                case "max_kinetic_energy_j": return Max(s, i0, i1, x => x.KineticEnergy);
                case "max_roll_rate_proxy_deg":
                    // Peak-to-peak body roll in the window (oscillation growth detector).
                    return (Max(s, i0, i1, x => x.Roll) - Min(s, i0, i1, x => x.Roll)) * MathUtil.Rad2Deg;
                default:
                    throw new ArgumentException($"Unknown metric '{name}'");
            }
        }

        static double Max(List<Sample> s, int a, int b, Func<Sample, double> f)
        {
            double m = double.MinValue;
            for (int i = a; i <= b; i++) m = Math.Max(m, f(s[i]));
            return m;
        }

        static double Min(List<Sample> s, int a, int b, Func<Sample, double> f)
        {
            double m = double.MaxValue;
            for (int i = a; i <= b; i++) m = Math.Min(m, f(s[i]));
            return m;
        }

        static double Mean(List<Sample> s, int a, int b, Func<Sample, double> f)
        {
            double sum = 0; int n = 0;
            for (int i = a; i <= b; i++) { sum += f(s[i]); n++; }
            return n > 0 ? sum / n : double.NaN;
        }

        static double HorizDist(Vec3 a, Vec3 b)
        {
            double dx = a.x - b.x, dz = a.z - b.z;
            return Math.Sqrt(dx * dx + dz * dz);
        }

        static int FirstBrake(List<Sample> s)
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
