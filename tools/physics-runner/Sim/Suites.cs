using System;
using System.Collections.Generic;
using System.Linq;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    /// <summary>Multi-run validations shared by the console runner and the xUnit tests.</summary>
    public static class Suites
    {
        public static Scenario Find(string id)
        {
            foreach (var s in Scenario.LoadAll(RepoPaths.ScenariosDir)) if (s.id == id) return s;
            throw new ArgumentException($"Scenario '{id}' not found");
        }

        public sealed class SpreadResult
        {
            public string Label = "";
            public double[] Values = Array.Empty<double>();
            public double Mean => Values.Average();
            /// <summary>Max deviation from the mean, relative [-].</summary>
            public double MaxRelDev => Values.Max(v => Math.Abs(v - Mean)) / Mean;
            public override string ToString() => $"{Label}: [{string.Join(", ", Values.Select(v => v.ToString("F3")))}] mean {Mean:F3}, max dev {MaxRelDev * 100:F2}%";
        }

        /// <summary>
        /// Repeatability of 0-60 / 0-80: three runs with different headings (world-frame orientation,
        /// i.e. different floating-point paths) — docs/04 section 6 item 3.
        /// </summary>
        public static SpreadResult[] Repeatability(string scenarioId, double[] headings, Func<int, string> csvPath = null)
        {
            var sc = Find(scenarioId);
            var t60 = new double[headings.Length];
            var t80 = new double[headings.Length];
            for (int i = 0; i < headings.Length; i++)
            {
                var r = ScenarioRunner.Run(sc, new RunOptions { HeadingDeg = headings[i], CsvPath = csvPath?.Invoke(i) });
                t60[i] = r.Metric("time_to_kmh", 60);
                t80[i] = r.Metric("time_to_kmh", 80);
            }
            return new[]
            {
                new SpreadResult { Label = "0-60 km/h [s]", Values = t60 },
                new SpreadResult { Label = "0-80 km/h [s]", Values = t80 },
            };
        }

        /// <summary>Same scenario at several fixed steps (substeps scaled to keep ~2.5 ms inner step) — item 12.</summary>
        public static SpreadResult DtSweep(string scenarioId, string metric, double arg, double[] dts)
        {
            var sc = Find(scenarioId);
            var vals = new double[dts.Length];
            for (int i = 0; i < dts.Length; i++)
            {
                int sub = Math.Max(1, (int)Math.Round(dts[i] / 0.0025));
                var r = ScenarioRunner.Run(sc, new RunOptions { Dt = dts[i], Substeps = sub });
                vals[i] = r.Metric(metric, arg);
            }
            return new SpreadResult { Label = $"{scenarioId}:{metric}({arg}) @dt {string.Join("/", dts.Select(d => (1 / d).ToString("F0") + "Hz"))}", Values = vals };
        }

        /// <summary>Same scenario at a fixed dt with different substep counts — item 12 (substep consistency).</summary>
        public sealed class BitCompareResult
        {
            public string Label = "";
            public bool Identical;
            public int SampleMismatches;
            public int CheckMismatches;
            public string FirstMismatch = "";
            public override string ToString() =>
                $"{Label}: {(Identical ? "BIT-IDENTICAL" : $"DIFFERS ({SampleMismatches} sample bits, {CheckMismatches} check values) first: {FirstMismatch}")}";
        }

        /// <summary>
        /// docs/04 s6.12/s6.14 determinism: the same scenario run twice must produce bit-identical results
        /// (every sample field compared as raw IEEE-754 bits, plus all check values). Timing (MeanStepMicros) is
        /// excluded - it is wall-clock, not simulation state.
        /// </summary>
        public static BitCompareResult BitIdentical(string scenarioId, RunOptions opt = null)
        {
            var sc = Find(scenarioId);
            opt ??= new RunOptions();
            var a = ScenarioRunner.Run(sc, opt);
            var b = ScenarioRunner.Run(sc, opt);
            var r = new BitCompareResult { Label = $"{sc.id} x2" };
            if (a.Samples.Count != b.Samples.Count)
            {
                r.FirstMismatch = $"sample count {a.Samples.Count} vs {b.Samples.Count}";
                return r;
            }
            var sb = new System.Text.StringBuilder(4096);
            for (int i = 0; i < a.Samples.Count; i++)
            {
                sb.Clear();
                AccumulateBits(a.Samples[i], sb);
                string ba = sb.ToString();
                sb.Clear();
                AccumulateBits(b.Samples[i], sb);
                if (ba != sb.ToString())
                {
                    r.SampleMismatches++;
                    if (r.FirstMismatch.Length == 0) r.FirstMismatch = $"sample {i} (t={a.Samples[i].T})";
                }
            }
            for (int i = 0; i < Math.Min(a.Checks.Count, b.Checks.Count); i++)
                if (BitConverter.DoubleToInt64Bits(a.Checks[i].Value) != BitConverter.DoubleToInt64Bits(b.Checks[i].Value))
                {
                    r.CheckMismatches++;
                    if (r.FirstMismatch.Length == 0) r.FirstMismatch = $"check {a.Checks[i].Spec.metric}";
                }
            r.Identical = r.SampleMismatches == 0 && r.CheckMismatches == 0 && a.Checks.Count == b.Checks.Count;
            return r;
        }

        static void AccumulateBits(Sample s, System.Text.StringBuilder sb)
        {
            void D(double v) => sb.Append(BitConverter.DoubleToInt64Bits(v).ToString("X16"));
            void V(Vec3 v) { D(v.x); D(v.y); D(v.z); }
            D(s.T); V(s.Pos); V(s.ComPos); V(s.Vel); V(s.Fwd); V(s.Right);
            D(s.SpeedFwd); D(s.YawRate); D(s.Rpm); D(s.SteerAngle); D(s.Pitch); D(s.Roll); D(s.LatAccel); D(s.LongAccel);
            sb.Append(s.Gear); D(s.ThrottleIn); D(s.BrakeIn); sb.Append(s.Stalled ? 1 : 0);
            D(s.MaxFzRatio); D(s.SumFz); D(s.MinFz); sb.Append(s.WheelsOffGround); sb.Append(s.OffMask.ToString("X16")); sb.Append(s.TractorWheelCount);
            D(s.KineticEnergy); D(s.PotentialEnergy); D(s.MaxFrictionRatio);
            sb.Append(s.HasTrailer ? 1 : 0); sb.Append(s.Coupled ? 1 : 0);
            V(s.TrailerPos); V(s.TrailerComPos); V(s.TrailerVel); V(s.TrailerAxlePos);
            D(s.Articulation); D(s.KingpinFz); D(s.KingpinFx); D(s.KingpinFy); D(s.FifthWheelError);
            D(s.TrailerYawRate); D(s.TrailerLatAccel); D(s.TrailerRoll);
            D(s.AirFront); D(s.AirRear); D(s.AirPark); D(s.AirTrailer); D(s.AirSupply);
            sb.Append(s.LowAirWarning ? 1 : 0); sb.Append(s.TrailerEmergency ? 1 : 0);
            D(s.ChamberFront); D(s.ChamberRear); D(s.ChamberTrailer); D(s.RearSlip); D(s.TrailerSlip);
            D(s.RetarderTorque); D(s.EngineBrakeTorque); D(s.BrakeDemand); D(s.ClutchTemp);
            sb.Append(s.AmtState); D(s.ClutchCmd); D(s.CabPitch); D(s.CabRoll); D(s.CabHeave);
            D(s.LandingGearLoad); D(s.ParkingState); sb.Append(s.ParkWarning ? 1 : 0); D(s.WheelBrakeTorque);
        }

        public static SpreadResult SubstepSweep(string scenarioId, string metric, double arg, int[] substeps)
        {
            var sc = Find(scenarioId);
            var vals = new double[substeps.Length];
            for (int i = 0; i < substeps.Length; i++)
            {
                var r = ScenarioRunner.Run(sc, new RunOptions { Substeps = substeps[i] });
                vals[i] = r.Metric(metric, arg);
            }
            return new SpreadResult { Label = $"{scenarioId}:{metric}({arg}) @substeps {string.Join("/", substeps)}", Values = vals };
        }
    }
}
