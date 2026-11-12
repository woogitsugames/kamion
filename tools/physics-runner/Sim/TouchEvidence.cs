using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    /// <summary>
    /// ADR 0149: finger-in-the-loop evidence — the game's touch chain (drag gesture -> column) driving the physics core.
    /// Before = ADR 0135 gain curve (dragLatAccelMatchKmh 0), after = shipped steering_feel.json.
    /// </summary>
    public static class TouchEvidence
    {
        public sealed class Trace
        {
            public List<double> T = new(), Kmh = new(), Finger = new(), ScreenDeg = new(), ColumnDeg = new(), RoadWheelDeg = new(),
                Lat = new(), Target = new(), HeadingDeg = new(), YawRateDps = new(), LatAccel = new(), Artic = new();
            public int WheelLiftSamples;
            public double ManoeuvreEndT = double.NaN;
        }

        public sealed class Result
        {
            public string Case;
            public double Kmh, FingerGain, MatchKmh;
            public double PeakRoadWheelDeg, PeakLatAccel, PeakYawRate, PeakArtic;
            public double OvershootM, SettleS, ResidualRmsM, LatAt5s, HeadingAt5s;
            public int WheelLift;
            public bool Stable => WheelLift == 0 && !double.IsNaN(SettleS) && SettleS < 6.0 && OvershootM < 0.7;
        }

        /// <summary>Driver preview time [s] for the lane-change human model (driver-model literature uses ~1-2 s; WORKING_VALUE).</summary>
        public static double PreviewS = double.TryParse(Environment.GetEnvironmentVariable("TOUCH_PREVIEW"), NumberStyles.Float, CultureInfo.InvariantCulture, out var p) ? p : 1.5;

        /// <summary>Override of dragLatAccelCapAboveMatch for the scenarios built next (-1 shipped, 0 off = ADR 0149 r2, 1 on).</summary>
        public static int CapAbove = -1;

        public static Scenario LaneChange(double kmh, double fingerGain, double matchKmh, string combination = "laden40", double delayS = 0.25)
        {
            double v = kmh / 3.6;
            return new Scenario
            {
                id = $"touch_lc_{kmh:F0}", combination = combination, duration = 4.0 + 4.0 + 12.0, dt = 0.01, substeps = 4,
                initial = new InitialSpec { speedKmh = kmh },
                driver = new DriverSpec
                {
                    type = "touch", touchMode = "human", targetKmh = kmh, startDistance = v * 4.0, length = Math.Max(20, v * 4.0),
                    offset = 3.5, doubleChange = false, humanDelayS = delayS, neuroTauS = 0.1, previewS = PreviewS,
                    fingerGainMmPerM = fingerGain, touchLatAccelMatchKmh = matchKmh, touchCapAbove = CapAbove,
                },
            };
        }

        /// <summary>Replay of the owner's thumb, video 2026-11-12 17.57-18.23 s: 4.4 mm to the left in 0.66 s, then released.</summary>
        public static Scenario Replay(double kmh, double matchKmh, string combination = "laden40")
        {
            return new Scenario
            {
                id = $"touch_replay_{kmh:F0}", combination = combination, duration = 8.0, dt = 0.01, substeps = 4,
                initial = new InitialSpec { speedKmh = kmh },
                driver = new DriverSpec
                {
                    type = "touch", touchMode = "replay", targetKmh = kmh, touchLatAccelMatchKmh = matchKmh, touchCapAbove = CapAbove,
                    fingerKeys = new[] { new[] { 0.0, 0, 0 }, new[] { 1.0, 0, 1 }, new[] { 1.66, -4.4, 1 }, new[] { 1.67, -4.4, 0 } },
                },
            };
        }

        /// <summary>Cab-wheel degrees per millimetre of thumb at a speed (the shipped chain, steady state, sensitivity 1).</summary>
        public static double CabDegPerMm(double kmh, double matchKmh, SimContext ctx)
        {
            var feel = Game.Controls.SteeringFeel.FromJson(File.ReadAllText(TouchDriver.FeelPath));
            if (matchKmh >= 0) feel.dragLatAccelMatchKmh = (float)matchKmh;
            if (CapAbove >= 0) feel.dragLatAccelCapAboveMatch = CapAbove > 0;
            var st = ctx.Tractor.Steering;
            float lockDeg = (float)(st.MaxAngle * MathUtil.Rad2Deg * st.Def.steeringRatio);
            var w = new Game.Controls.TouchSteeringWheel { Feel = feel, Grab = Game.Controls.WheelGrab.Drag, HalfRangeDeg = 270f, DeadZone = 0f };
            w.PointerDown(new UnityEngine.Vector2(0, 200), new UnityEngine.Vector2(0, 0));
            w.PointerDrag(new UnityEngine.Vector2(0, 200), new UnityEngine.Vector2(1, 0));
            var intent = default(Game.Controls.DriverIntent);
            w.Sample(0.01f, new Game.Controls.VehicleFeedback { ForwardSpeed = (float)(kmh / 3.6), HandwheelLockDeg = lockDeg }, ref intent);
            return intent.Steer * lockDeg;
        }

        public static Trace Run(Scenario sc, Action<SimContext> tweak = null)
        {
            sc.baseId = sc.id; sc.variant = sc.combination;
            var s = ScenarioRunner.Setup(sc, new RunOptions());
            tweak?.Invoke(s);
            var d = new TouchDriver(sc.driver, s, sc.dt);
            var tr = new Trace();
            double dt = sc.dt, t = 0;
            int steps = (int)Math.Round(sc.duration / dt);
            double xEnd = sc.driver.startDistance + sc.driver.length;
            Vec3 p0 = s.Body.Position;
            Vec3 f0 = s.Body.Rotation * Vec3.Forward; f0 = new Vec3(f0.x, 0, f0.z).Normalized;
            for (int i = 0; i < steps; i++)
            {
                var inp = d.Update(t, dt, s);
                var ts = s.Body.State;
                var trs = s.TrailerBody != null ? s.TrailerBody.State : default;
                s.Combo.Step(dt, ts, trs, inp, s.Ground);
                ScenarioRunner.StepBodies(s, dt);
                t += dt;
                var smp = ScenarioRunner.MakeSample(t, s, inp);
                if (double.IsNaN(tr.ManoeuvreEndT) && Vec3.Dot(s.Body.Position - p0, f0) >= xEnd) tr.ManoeuvreEndT = t;
                if (i % 2 != 0) continue; // 50 Hz trace
                tr.T.Add(t); tr.Kmh.Add(smp.SpeedFwd * 3.6); tr.Finger.Add(d.FingerMm); tr.ScreenDeg.Add(d.Wheel.WheelDeg);
                tr.ColumnDeg.Add(d.Column.AngleDeg); tr.RoadWheelDeg.Add(smp.SteerAngle * MathUtil.Rad2Deg);
                tr.Lat.Add(d.LateralM); tr.Target.Add(d.TargetM); tr.HeadingDeg.Add(d.HeadingRad * MathUtil.Rad2Deg);
                tr.YawRateDps.Add(smp.YawRate * MathUtil.Rad2Deg); tr.LatAccel.Add(smp.LatAccel); tr.Artic.Add(smp.Articulation * MathUtil.Rad2Deg);
                if (smp.WheelsOffGround > 0) tr.WheelLiftSamples++;
            }
            return tr;
        }

        public static Result Measure(string name, Scenario sc, Trace tr)
        {
            var r = new Result { Case = name, Kmh = sc.initial.speedKmh, FingerGain = sc.driver.fingerGainMmPerM, MatchKmh = sc.driver.touchLatAccelMatchKmh, WheelLift = tr.WheelLiftSamples };
            for (int i = 0; i < tr.T.Count; i++)
            {
                r.PeakRoadWheelDeg = Math.Max(r.PeakRoadWheelDeg, Math.Abs(tr.RoadWheelDeg[i]));
                r.PeakLatAccel = Math.Max(r.PeakLatAccel, Math.Abs(tr.LatAccel[i]));
                r.PeakYawRate = Math.Max(r.PeakYawRate, Math.Abs(tr.YawRateDps[i]));
                r.PeakArtic = Math.Max(r.PeakArtic, Math.Abs(tr.Artic[i]));
            }
            int i5 = Math.Min(tr.T.Count - 1, (int)Math.Round(5.0 / (tr.T[1] - tr.T[0])) - 1);
            r.LatAt5s = tr.Lat[i5]; r.HeadingAt5s = tr.HeadingDeg[i5];
            if (sc.driver.touchMode == "human")
            {
                double A = sc.driver.offset, tEnd = tr.ManoeuvreEndT;
                if (double.IsNaN(tEnd)) { r.SettleS = double.NaN; r.OvershootM = double.NaN; return r; }
                double over = 0, lastOut = tEnd, sq = 0; int n = 0;
                double tLast = tr.T[tr.T.Count - 1];
                for (int i = 0; i < tr.T.Count; i++)
                {
                    if (tr.T[i] < tEnd - 1.0) continue;
                    over = Math.Max(over, tr.Lat[i] - A);
                    if (tr.T[i] >= tEnd && Math.Abs(tr.Lat[i] - A) > 0.25) lastOut = tr.T[i];
                    if (tr.T[i] >= tLast - 4.0) { sq += (tr.Lat[i] - A) * (tr.Lat[i] - A); n++; }
                }
                r.OvershootM = over;
                r.SettleS = lastOut >= tLast - 0.05 ? double.NaN : lastOut - tEnd;
                r.ResidualRmsM = n > 0 ? Math.Sqrt(sq / n) : double.NaN;
            }
            return r;
        }

        /// <summary>
        /// Pilot-induced oscillation index [deg/s]: RMS of the yaw rate in the last 8 s after removing its 3-s centred moving
        /// average (leaves the &gt; ~0.3 Hz weave a thumb-in-the-loop instability produces; a slow, lightly damped return to
        /// the lane is not counted). Wheel lift or articulation &gt; 20 deg = loss of control (+inf).
        /// </summary>
        public static double OscillationIndex(Trace tr)
        {
            if (tr.WheelLiftSamples > 0) return double.PositiveInfinity;
            foreach (var a in tr.Artic) if (Math.Abs(a) > 20) return double.PositiveInfinity;
            int n = tr.T.Count;
            double dt = tr.T[1] - tr.T[0];
            int half = (int)Math.Round(1.5 / dt), from = n - (int)Math.Round(8.0 / dt);
            double sq = 0; int cnt = 0;
            for (int i = Math.Max(half, from); i < n - half; i++)
            {
                double m = 0;
                for (int j = i - half; j <= i + half; j++) m += tr.YawRateDps[j];
                m /= 2 * half + 1;
                double e = tr.YawRateDps[i] - m;
                sq += e * e; cnt++;
            }
            return cnt > 0 ? Math.Sqrt(sq / cnt) : double.NaN;
        }

        /// <summary>Thumb gains [mm per m of previewed lateral error] swept for the PIO onset.</summary>
        public static readonly double[] GainGrid = { 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 16 };
        /// <summary>Oscillation index above which the loop counts as weaving [deg/s] (WORKING_VALUE).</summary>
        public const double PioThresholdDps = 0.75;

        /// <summary>Smallest thumb gain of <see cref="GainGrid"/> at which the loop weaves (PIO onset); +inf = none in the grid.</summary>
        public static double PioOnsetGain(double kmh, double matchKmh, string combination = "laden40")
        {
            foreach (double g in GainGrid)
            {
                var sc = LaneChange(kmh, g, matchKmh, combination);
                sc.duration = 30;
                if (!(OscillationIndex(Run(sc)) <= PioThresholdDps)) return g;
            }
            return double.PositiveInfinity;
        }
        public static void WriteCsv(string path, Trace tr)
        {
            var sb = new StringBuilder("t,kmh,finger_mm,screen_deg,column_deg,roadwheel_deg,lat_m,target_m,heading_deg,yaw_rate_dps,lat_accel_ms2,articulation_deg\n");
            var c = CultureInfo.InvariantCulture;
            for (int i = 0; i < tr.T.Count; i++)
                sb.Append(string.Format(c, "{0:F2},{1:F2},{2:F3},{3:F2},{4:F2},{5:F3},{6:F4},{7:F4},{8:F3},{9:F3},{10:F3},{11:F3}\n",
                    tr.T[i], tr.Kmh[i], tr.Finger[i], tr.ScreenDeg[i], tr.ColumnDeg[i], tr.RoadWheelDeg[i], tr.Lat[i], tr.Target[i],
                    tr.HeadingDeg[i], tr.YawRateDps[i], tr.LatAccel[i], tr.Artic[i]));
            File.WriteAllText(path, sb.ToString());
        }

        /// <summary>Full evidence set: replay 35 km/h, lane change at 20/35/45/60/80 km/h, thumb-gain sweep; before/after.</summary>
        public static int WriteAll(string outDir)
        {
            Directory.CreateDirectory(outDir);
            var c = CultureInfo.InvariantCulture;
            var sum = new StringBuilder("case,phase,kmh,finger_gain_mm_per_m,match_kmh,peak_roadwheel_deg,peak_lat_accel_ms2,peak_yaw_rate_dps,peak_artic_deg,overshoot_m,settle_s,residual_rms_m,lat_at_5s_m,heading_at_5s_deg,wheel_lift,stable,pio_index_dps\n");
            void Add(string name, string phase, Scenario sc, bool csv)
            {
                var tr = Run(sc);
                var r = Measure(name, sc, tr);
                if (csv) WriteCsv(Path.Combine(outDir, $"{name}_{phase}.csv"), tr);
                else { Directory.CreateDirectory(Path.Combine(outDir, "sweep")); WriteCsv(Path.Combine(outDir, "sweep", string.Format(c, "{0}_g{1:F1}_{2}.csv", name, sc.driver.fingerGainMmPerM, phase)), tr); }
                sum.Append(string.Format(c, "{0},{1},{2:F0},{3:F2},{4:F0},{5:F2},{6:F2},{7:F2},{8:F2},{9:F3},{10:F2},{11:F3},{12:F3},{13:F2},{14},{15},{16:F3}\n",
                    name, phase, r.Kmh, r.FingerGain, r.MatchKmh, r.PeakRoadWheelDeg, r.PeakLatAccel, r.PeakYawRate, r.PeakArtic, r.OvershootM,
                    r.SettleS, r.ResidualRmsM, r.LatAt5s, r.HeadingAt5s, r.WheelLift, r.Stable ? 1 : 0, OscillationIndex(tr)));
            }
            // Phases: before = ADR 0135 curve, r2 = ADR 0149 (cap 24-60 km/h only), after = shipped (ADR 0151: cap also above 60).
            var phases = new[] { ("before", 0.0, -1), ("r2", -1.0, 0), ("after", -1.0, -1) };
            foreach (var (phase, match, capAbove) in phases)
            {
                CapAbove = capAbove;
                Add("replay35", phase, Replay(35, match), true);
                foreach (double kmh in new[] { 20.0, 35.0, 45.0, 60.0, 70.0, 80.0, 90.0 })
                {
                    { var lc = LaneChange(kmh, 4.0, match); lc.duration = 30; Add($"lc{kmh:F0}", phase, lc, true); }
                    foreach (double g in GainGrid)
                        { var sw = LaneChange(kmh, g, match); sw.duration = 30; Add($"sweep{kmh:F0}", phase, sw, false); }
                }
            }
            CapAbove = -1;
            File.WriteAllText(Path.Combine(outDir, "summary.csv"), sum.ToString());
            Console.WriteLine(sum.ToString());

            // Gain margin of the thumb loop per speed: the smallest thumb gain at which the driver-vehicle loop weaves (PIO).
            var crit = new StringBuilder("kmh,cab_deg_per_mm_before,cab_deg_per_mm_r2,cab_deg_per_mm_after,lat_accel_per_mm_before,lat_accel_per_mm_r2,lat_accel_per_mm_after,pio_onset_gain_before_mm_per_m,pio_onset_gain_r2_mm_per_m,pio_onset_gain_after_mm_per_m\n");
            var probe = Replay(35, 0); probe.baseId = probe.id; probe.variant = probe.combination;
            var ctx = ScenarioRunner.Setup(probe, new RunOptions());
            var st = ctx.Tractor.Steering;
            double ratio = st.Def.steeringRatio;
            double wb = ctx.Tractor.Def.axles[0].positionZ - ctx.Tractor.Def.axles[1].positionZ;
            foreach (double kmh in new[] { 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 70.0, 80.0, 90.0 })
            {
                double v = kmh / 3.6, k = v * v / wb * MathUtil.Deg2Rad / ratio;
                var cab = new double[3]; var pio = new double[3];
                for (int p = 0; p < 3; p++)
                {
                    CapAbove = phases[p].Item3;
                    cab[p] = CabDegPerMm(kmh, phases[p].Item2, ctx);
                    pio[p] = PioOnsetGain(kmh, phases[p].Item2);
                }
                CapAbove = -1;
                crit.Append(string.Format(c, "{0:F0},{1:F2},{2:F2},{3:F2},{4:F3},{5:F3},{6:F3},{7:F2},{8:F2},{9:F2}\n",
                    kmh, cab[0], cab[1], cab[2], cab[0] * k, cab[1] * k, cab[2] * k, pio[0], pio[1], pio[2]));
            }
            File.WriteAllText(Path.Combine(outDir, "gain_margin.csv"), crit.ToString());
            Console.WriteLine(crit.ToString());
            return 0;
        }
    }
}
