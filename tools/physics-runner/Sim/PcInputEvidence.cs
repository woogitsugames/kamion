using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using Game.Controls;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    /// <summary>
    /// drive-feel-s24 (D93 pkt 3): PC keyboard / gamepad steering in the loop — the game's own chain
    /// (<see cref="KeyboardAxisRamp"/> / <see cref="PadSteerFilter"/> with <c>pad_keyboard_feel.json</c> -> <see cref="SteeringColumn"/>
    /// with <c>steering_feel.json</c> -> <c>DriverInput.Steer</c>, as <c>DrivingLabBootstrap.FixedUpdate</c>) driving the physics
    /// core. Cases: full key / full stick held at speed (what a player does on a roundabout or in a panic), a single key tap
    /// (smallest correction), and a lane change by a human model (keyboard: bang-bang with hysteresis on the previewed
    /// lateral error; pad: proportional stick). Speed held by the PI controller. Not a scenario-file suite: it measures the
    /// input tuning, not the physics; the physics checks stay in tests/physics/scenarios.
    /// </summary>
    public static class PcInputEvidence
    {
        public static string PadFeelPath => Path.Combine(RepoPaths.Root, "game", "Assets", "_Project", "Input", "Resources", "Controls", "pad_keyboard_feel.json");

        public enum Mode { KeyHold, PadHold, KeyTap, KeyLaneChange, PadLaneChange }

        public sealed class Case
        {
            public string Name, Combination = "laden40";
            public Mode Mode;
            public double Kmh;
            /// <summary>Cargo CoG height [m] (0 = scenario default); 2.6 = rollover_r50_cog_high.</summary>
            public double CogHeight;
            public double HoldStart = 1.0, HoldLen = 6.0, Duration = 14.0;
            public double TapLen = 0.1;
            /// <summary>Lane change: offset [m, left +], manoeuvre length [m] from v x 4 s.</summary>
            public double Offset = 3.5;
            /// <summary>Human model: perception delay [s], preview [s] (TouchEvidence 0.25 / 1.5, WORKING_VALUE).</summary>
            public double DelayS = 0.25, PreviewS = 1.5;
            /// <summary>Keyboard driver band [m]: press when |previewed error| exceeds it, release below 0.3 x it (WORKING_VALUE).</summary>
            public double KeyBandM = 0.3;
            /// <summary>Pad driver stick per metre of previewed error, thumb lag [s] (WORKING_VALUE).</summary>
            public double PadGainPerM = 0.25, PadTauS = 0.1;
        }

        public sealed class Trace
        {
            public List<double> T = new(), Kmh = new(), Cmd = new(), ColumnDeg = new(), RoadWheelDeg = new(), Lat = new(), Target = new(),
                YawRateDps = new(), LatAccel = new(), TrailerLatAccel = new(), Artic = new();
            public List<int> Key = new();
            public int WheelLiftSamples;
            public double ManoeuvreEndT = double.NaN;
        }

        public sealed class Result
        {
            public string Name, Mode, Combination;
            public double Kmh, Cog;
            public double PeakRoadWheelDeg, SteadyRoadWheelDeg, PeakLatAccel, PeakTrailerLatAccel, PeakYawRate, PeakArtic;
            public double T90, ReturnS, LatAfterTapM, OvershootM, SettleS, Pio, KeyPresses;
            public int WheelLift;
        }

        public static PadKeyboardFeel LoadFeel(string path)
        {
            var f = PadKeyboardFeel.Defaults();
            if (path != null && File.Exists(path)) UnityEngine.JsonUtility.FromJsonOverwrite(File.ReadAllText(path), f);
            f.Sanitize();
            return f;
        }

        static double Offset(Case c, double x, double s0, double len)
        {
            if (x < s0) return 0;
            if (x < s0 + len) return 0.5 * c.Offset * (1 - Math.Cos(Math.PI * (x - s0) / len));
            return c.Offset;
        }

        public static Trace Run(Case c, PadKeyboardFeel feel)
        {
            double dt = 0.01, v0 = c.Kmh / 3.6;
            var sc = new Scenario
            {
                id = "pc_" + c.Name, combination = c.Combination, duration = c.Duration, dt = dt, substeps = 4,
                initial = new InitialSpec { speedKmh = c.Kmh },
                driver = new DriverSpec { type = "pc_input", targetKmh = c.Kmh },
            };
            if (c.CogHeight > 0) sc.cargo = new CargoSpec { cogHeight = c.CogHeight };
            sc.baseId = sc.id; sc.variant = sc.combination;
            var s = ScenarioRunner.Setup(sc, new RunOptions());

            var steerFeel = SteeringFeel.FromJson(File.Exists(TouchDriver.FeelPath) ? File.ReadAllText(TouchDriver.FeelPath) : null);
            var st = s.Tractor.Steering;
            var column = new SteeringColumn(steerFeel, (float)(st.MaxAngle * MathUtil.Rad2Deg * st.Def.steeringRatio));
            var tuning = PadUserTuning.From(feel);
            var ramp = default(KeyboardAxisRamp);
            var pad = default(PadSteerFilter);
            var speed = new SpeedController(v0);

            var tr = new Trace();
            Vec3 p0 = s.Body.Position;
            Vec3 f0 = s.Body.Rotation * Vec3.Forward; f0 = new Vec3(f0.x, 0, f0.z).Normalized;
            var l0 = new Vec3(-f0.z, 0, f0.x);
            double s0 = v0 * 4.0, len = Math.Max(20, v0 * 4.0);
            var delay = new double[Math.Max(1, (int)Math.Round(c.DelayS / dt)) + 1];
            int head = 0, keyDir = 0;
            double stick = 0, prevH = 0, hRate = 0, t = 0;
            int steps = (int)Math.Round(c.Duration / dt);
            for (int i = 0; i < steps; i++)
            {
                var m = s.Tractor;
                double v = m.SpeedForward;
                speed.Update(Math.Abs(v), dt, out double th, out double br);
                Vec3 rel = s.Body.Position - p0;
                double x = Vec3.Dot(rel, f0), lat = Vec3.Dot(rel, l0);
                Vec3 fw = s.Body.Rotation * Vec3.Forward;
                double h = Math.Atan2(Vec3.Dot(fw, l0), Vec3.Dot(fw, f0));
                if (i > 0) hRate += ((h - prevH) / dt - hRate) * (1 - Math.Exp(-dt / 0.05));
                prevH = h;
                double target = 0;

                // ---- the player
                int dir = 0; double raw = 0;
                bool inHold = t >= c.HoldStart && t < c.HoldStart + c.HoldLen;
                switch (c.Mode)
                {
                    case Mode.KeyHold: dir = inHold ? 1 : 0; break;
                    case Mode.PadHold: raw = inHold ? 1 : 0; break;
                    case Mode.KeyTap: dir = t >= c.HoldStart && t < c.HoldStart + c.TapLen ? 1 : 0; break;
                    default:
                    {
                        double ahead = Math.Max(1.0, Math.Abs(v)) * c.PreviewS;
                        target = Offset(c, x + ahead, s0, len);
                        double predicted = lat + ahead * Math.Sin(h) + 0.5 * ahead * c.PreviewS * hRate;
                        delay[head] = target - predicted; head = (head + 1) % delay.Length;
                        double e = delay[head]; // left +, humanDelay ago
                        if (c.Mode == Mode.KeyLaneChange)
                        {
                            if (keyDir == 0 && Math.Abs(e) > c.KeyBandM) keyDir = e > 0 ? -1 : 1;   // target left -> left key
                            else if (keyDir != 0 && (Math.Abs(e) < 0.3 * c.KeyBandM || Math.Sign(e) == keyDir)) keyDir = 0;
                            dir = keyDir;
                        }
                        else
                        {
                            double cmd = Math.Max(-1, Math.Min(1, -c.PadGainPerM * e));
                            stick += (cmd - stick) * (1 - Math.Exp(-dt / c.PadTauS));
                            raw = stick;
                        }
                        break;
                    }
                }

                // ---- the game's input chain (as PcInputBridge + DrivingLabBootstrap.FixedUpdate)
                var fb = new VehicleFeedback
                {
                    ForwardSpeed = (float)v, AligningTorque = (float)m.AligningTorqueTotal,
                    RoadWheelAngleNormalized = (float)(m.Steering.Angle / Math.Max(1e-6, m.Steering.MaxAngle)), HandwheelLockDeg = column.LockDeg,
                };
                float steer; bool active, handsOn;
                bool isKey = c.Mode == Mode.KeyHold || c.Mode == Mode.KeyTap || c.Mode == Mode.KeyLaneChange;
                if (isKey)
                {
                    ramp.Step(feel, tuning, dir, false, false, (float)v, (float)dt);
                    steer = ramp.Steer; active = dir != 0 || Math.Abs(ramp.Steer) > 1e-3f; handsOn = active;
                }
                else
                {
                    pad.Step(feel, tuning, (float)raw, (float)v, fb.RoadWheelAngleNormalized, (float)dt);
                    steer = pad.Steer; active = pad.Active; handsOn = pad.Active;
                }
                column.Step((float)dt, (active ? steer : 0f) * column.LockDeg, active && handsOn, (float)(v * 3.6), (float)m.AligningTorqueTotal);
                var inp = new DriverInput { Throttle = th, Brake = br, Steer = column.Normalized, Selector = GearSelector.Drive };

                var ts = s.Body.State;
                var trs = s.TrailerBody != null ? s.TrailerBody.State : default;
                s.Combo.Step(dt, ts, trs, inp, s.Ground);
                ScenarioRunner.StepBodies(s, dt);
                t += dt;
                var smp = ScenarioRunner.MakeSample(t, s, inp);
                if (double.IsNaN(tr.ManoeuvreEndT) && x >= s0 + len) tr.ManoeuvreEndT = t;
                if (smp.WheelsOffGround > 0) tr.WheelLiftSamples++;
                if (i % 2 != 0) continue; // 50 Hz trace
                tr.T.Add(t); tr.Kmh.Add(smp.SpeedFwd * 3.6); tr.Cmd.Add(isKey ? dir : raw); tr.Key.Add(dir);
                tr.ColumnDeg.Add(column.AngleDeg); tr.RoadWheelDeg.Add(smp.SteerAngle * MathUtil.Rad2Deg);
                tr.Lat.Add(lat); tr.Target.Add(target); tr.YawRateDps.Add(smp.YawRate * MathUtil.Rad2Deg);
                tr.LatAccel.Add(smp.LatAccel); tr.TrailerLatAccel.Add(smp.TrailerLatAccel); tr.Artic.Add(smp.Articulation * MathUtil.Rad2Deg);
            }
            return tr;
        }

        public static Result Measure(Case c, Trace tr)
        {
            var r = new Result { Name = c.Name, Mode = c.Mode.ToString(), Combination = c.Combination, Kmh = c.Kmh, Cog = c.CogHeight, WheelLift = tr.WheelLiftSamples };
            int n = tr.T.Count;
            double tHoldEnd = c.HoldStart + (c.Mode == Mode.KeyTap ? c.TapLen : c.HoldLen);
            double steadySum = 0; int steadyN = 0;
            for (int i = 0; i < n; i++)
            {
                r.PeakRoadWheelDeg = Math.Max(r.PeakRoadWheelDeg, Math.Abs(tr.RoadWheelDeg[i]));
                r.PeakLatAccel = Math.Max(r.PeakLatAccel, Math.Abs(tr.LatAccel[i]));
                r.PeakTrailerLatAccel = Math.Max(r.PeakTrailerLatAccel, Math.Abs(tr.TrailerLatAccel[i]));
                r.PeakYawRate = Math.Max(r.PeakYawRate, Math.Abs(tr.YawRateDps[i]));
                r.PeakArtic = Math.Max(r.PeakArtic, Math.Abs(tr.Artic[i]));
                if (tr.T[i] > tHoldEnd - 1.0 && tr.T[i] <= tHoldEnd) { steadySum += tr.RoadWheelDeg[i]; steadyN++; }
                if (i > 0 && tr.Key[i] != 0 && tr.Key[i - 1] != tr.Key[i]) r.KeyPresses++;
            }
            r.SteadyRoadWheelDeg = steadyN > 0 ? steadySum / steadyN : double.NaN;
            r.T90 = r.ReturnS = r.LatAfterTapM = r.OvershootM = r.SettleS = r.Pio = double.NaN;
            if (c.Mode == Mode.KeyHold || c.Mode == Mode.PadHold)
            {
                double peakIn = 0;
                for (int i = 0; i < n; i++) if (tr.T[i] <= tHoldEnd) peakIn = Math.Max(peakIn, Math.Abs(tr.YawRateDps[i]));
                for (int i = 0; i < n; i++) if (tr.T[i] >= c.HoldStart && Math.Abs(tr.YawRateDps[i]) >= 0.9 * peakIn) { r.T90 = tr.T[i] - c.HoldStart; break; }
                for (int i = 0; i < n; i++) if (tr.T[i] > tHoldEnd && Math.Abs(tr.YawRateDps[i]) < 0.1 * peakIn) { r.ReturnS = tr.T[i] - tHoldEnd; break; }
            }
            else if (c.Mode == Mode.KeyTap)
            {
                for (int i = 0; i < n; i++) if (tr.T[i] >= c.HoldStart + 4.0) { r.LatAfterTapM = tr.Lat[i]; break; }
            }
            else
            {
                double A = c.Offset, tEnd = tr.ManoeuvreEndT;
                r.Pio = TouchEvidence.OscillationIndex(new TouchEvidence.Trace { T = tr.T, YawRateDps = tr.YawRateDps, Artic = tr.Artic, WheelLiftSamples = tr.WheelLiftSamples });
                if (!double.IsNaN(tEnd))
                {
                    double over = 0, lastOut = tEnd, tLast = tr.T[n - 1];
                    for (int i = 0; i < n; i++)
                    {
                        if (tr.T[i] < tEnd - 1.0) continue;
                        over = Math.Max(over, tr.Lat[i] - A);
                        if (tr.T[i] >= tEnd && Math.Abs(tr.Lat[i] - A) > 0.25) lastOut = tr.T[i];
                    }
                    r.OvershootM = over;
                    r.SettleS = lastOut >= tLast - 0.05 ? double.NaN : lastOut - tEnd;
                }
            }
            return r;
        }

        public static void WriteCsv(string path, Trace tr)
        {
            var sb = new StringBuilder("t,kmh,cmd,column_deg,roadwheel_deg,lat_m,target_m,yaw_rate_dps,lat_accel_ms2,trailer_lat_accel_ms2,articulation_deg\n");
            var ci = CultureInfo.InvariantCulture;
            for (int i = 0; i < tr.T.Count; i++)
                sb.Append(string.Format(ci, "{0:F2},{1:F2},{2:F3},{3:F2},{4:F3},{5:F4},{6:F4},{7:F3},{8:F3},{9:F3},{10:F3}\n",
                    tr.T[i], tr.Kmh[i], tr.Cmd[i], tr.ColumnDeg[i], tr.RoadWheelDeg[i], tr.Lat[i], tr.Target[i], tr.YawRateDps[i],
                    tr.LatAccel[i], tr.TrailerLatAccel[i], tr.Artic[i]));
            File.WriteAllText(path, sb.ToString());
        }

        public static IEnumerable<Case> Cases()
        {
            foreach (double kmh in new[] { 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0 })
            {
                yield return new Case { Name = $"keyhold{kmh:F0}_high", Mode = Mode.KeyHold, Kmh = kmh, CogHeight = 2.6 };
                yield return new Case { Name = $"padhold{kmh:F0}_high", Mode = Mode.PadHold, Kmh = kmh, CogHeight = 2.6 };
                yield return new Case { Name = $"keyhold{kmh:F0}_empty", Mode = Mode.KeyHold, Kmh = kmh, Combination = "empty" };
            }
            foreach (double kmh in new[] { 30.0, 50.0, 80.0 })
                yield return new Case { Name = $"keytap{kmh:F0}", Mode = Mode.KeyTap, Kmh = kmh, Duration = 8 };
            foreach (double kmh in new[] { 30.0, 50.0, 70.0, 80.0 })
            {
                yield return new Case { Name = $"keylc{kmh:F0}", Mode = Mode.KeyLaneChange, Kmh = kmh, Duration = 30 };
                yield return new Case { Name = $"padlc{kmh:F0}", Mode = Mode.PadLaneChange, Kmh = kmh, Duration = 30 };
                foreach (double g in new[] { 0.5, 1.0 })
                    yield return new Case { Name = string.Format(CultureInfo.InvariantCulture, "padlc{0:F0}_g{1:F1}", kmh, g), Mode = Mode.PadLaneChange, Kmh = kmh, Duration = 30, PadGainPerM = g };
            }
        }

        /// <summary>--input-feel &lt;outDir&gt; [--feel &lt;json&gt;]: every case, CSV per case + summary.csv.</summary>
        public static int WriteAll(string outDir, string feelPath)
        {
            Directory.CreateDirectory(outDir);
            var feel = LoadFeel(feelPath ?? PadFeelPath);
            var ci = CultureInfo.InvariantCulture;
            var sum = new StringBuilder("case,mode,combination,kmh,cog_m,peak_roadwheel_deg,steady_roadwheel_deg,peak_lat_accel_ms2,peak_trailer_lat_accel_ms2,peak_yaw_rate_dps,peak_artic_deg,t90_s,return_s,lat_4s_after_tap_m,overshoot_m,settle_s,pio_index_dps,key_presses,wheel_lift_samples\n");
            foreach (var c in Cases())
            {
                var tr = Run(c, feel);
                var r = Measure(c, tr);
                WriteCsv(Path.Combine(outDir, c.Name + ".csv"), tr);
                sum.Append(string.Format(ci, "{0},{1},{2},{3:F0},{4:F1},{5:F2},{6:F2},{7:F2},{8:F2},{9:F2},{10:F2},{11:F2},{12:F2},{13:F3},{14:F3},{15:F2},{16:F3},{17:F0},{18}\n",
                    r.Name, r.Mode, r.Combination, r.Kmh, r.Cog, r.PeakRoadWheelDeg, r.SteadyRoadWheelDeg, r.PeakLatAccel, r.PeakTrailerLatAccel,
                    r.PeakYawRate, r.PeakArtic, r.T90, r.ReturnS, r.LatAfterTapM, r.OvershootM, r.SettleS, r.Pio, r.KeyPresses, r.WheelLift));
            }
            File.WriteAllText(Path.Combine(outDir, "summary.csv"), sum.ToString());
            Console.WriteLine(sum.ToString());
            return 0;
        }
    }
}
