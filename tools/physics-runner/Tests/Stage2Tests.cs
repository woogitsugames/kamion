using System;
using System.Collections.Generic;
using System.Linq;
using Game.Vehicle.Physics;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>Stage 2: combination, air brakes, endurance brakes, golden telemetry.</summary>
    public class Stage2Tests
    {
        readonly ITestOutputHelper _out;
        public Stage2Tests(ITestOutputHelper output) { _out = output; }

        public static IEnumerable<object[]> GoldenIds() => Golden.Ids.Select(i => new object[] { i });

        /// <summary>Regression against tests/golden (10 Hz subsets, per-column tolerances).</summary>
        [Theory]
        [MemberData(nameof(GoldenIds))]
        public void GoldenTelemetry_Matches(string id)
        {
            string csv = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "physics-golden-" + id.Replace('@', '_') + ".csv");
            ScenarioRunner.Run(Suites.Find(id), new RunOptions { CsvPath = csv });
            var res = Golden.Compare(id, csv);
            foreach (var c in res) _out.WriteLine(c.ToString());
            Assert.NotEmpty(res);
            Assert.All(res, c => Assert.True(c.Passed, c.ToString()));
        }

        /// <summary>40 t preset: total mass and static axle loads (axle limits as commonly quoted from Directive 96/53/EC, UNVERIFIED).</summary>
        [Fact]
        public void Laden40_StaticLoads_AreConsistentAndPlausible()
        {
            var s = ScenarioRunner.Setup(Suites.Find("park_flat_5min_comb@laden40"), new RunOptions());
            double total = s.Tractor.MassProps.Mass + s.Trailer.Mass;
            double front = 0, drive = 0, tridem = 0;
            foreach (var w in s.Tractor.Wheels) if (w.AxleIndex == 0) front += w.StaticLoad; else drive += w.StaticLoad;
            foreach (var w in s.Trailer.Wheels) tridem += w.StaticLoad;
            _out.WriteLine($"GCW {total:F0} kg, front {front / 9.81:F0}, drive {drive / 9.81:F0}, tridem {tridem / 9.81:F0} kg, kingpin {s.Combo.StaticKingpinLoad / 9.81:F0} kg");
            Assert.InRange(total, 39990, 40010);
            Assert.InRange((front + drive + tridem) / 9.81, total - 1, total + 1);
            Assert.True(front / 9.81 <= 7500, "steer axle");
            Assert.True(drive / 9.81 <= 11500, "drive axle 11.5 t");
            Assert.True(tridem / 9.81 <= 24000, "tridem 24 t");
        }

        /// <summary>Kingpin load in a parked combination equals the static nose load (constraint transmits gravity correctly).</summary>
        [Theory]
        [InlineData("park_flat_5min_comb@empty")]
        [InlineData("park_flat_5min_comb@laden40")]
        public void KingpinLoad_EqualsStaticNoseLoad(string id)
        {
            var r = ScenarioRunner.Run(Suites.Find(id), new RunOptions { Duration = 20 });
            double ratio = r.Metric("kingpin_load_vs_static", 0, 10);
            _out.WriteLine($"{id}: kingpin / static = {ratio:F4}");
            Assert.InRange(ratio, 0.97, 1.03);
        }

        /// <summary>docs/04 s6.7: the rollover threshold depends on the cargo CoG height.</summary>
        [Fact]
        public void Rollover_HigherCog_LiftsEarlier()
        {
            double low = ScenarioRunner.Run(Suites.Find("rollover_r50_cog_low@laden40")).Metric("lat_accel_at_first_lift");
            double high = ScenarioRunner.Run(Suites.Find("rollover_r50_cog_high@laden40")).Metric("lat_accel_at_first_lift");
            _out.WriteLine($"first wheel lift: CoG 1.9 m at {low:F3} g, CoG 2.6 m at {high:F3} g");
            Assert.True(low > high + 0.05, $"low {low} high {high}");
        }

        /// <summary>Endurance brake ratings vs the class-reference sources (S1 VEB+ 375 kW at 2300 rpm, S2 Intarder 4000 Nm / 600 kW).</summary>
        [Fact]
        public void EnduranceBrakes_MatchClassReference()
        {
            var m = ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            double w2300 = 2300 * MathUtil.RpmToRadS;
            double pEb = m.Engine.EngineBrakeTotal(w2300) * w2300 / 1000;
            _out.WriteLine($"engine brake at 2300 rpm: {pEb:F1} kW");
            Assert.InRange(pEb, 370, 380);
            double maxT = 0, maxP = 0;
            for (double rpm = 50; rpm <= 3000; rpm += 25)
            {
                double w = rpm * MathUtil.RpmToRadS;
                double t = m.Retarder.Available(w);
                maxT = Math.Max(maxT, t); maxP = Math.Max(maxP, t * w / 1000);
            }
            _out.WriteLine($"retarder max torque {maxT:F0} Nm, max power {maxP:F0} kW");
            Assert.True(maxT <= 4000.001 && maxT > 3900);
            Assert.True(maxP <= 600.001 && maxP > 590);
        }

        /// <summary>docs/04 s6.12 for the combination: dt and substeps do not change the outcome qualitatively.</summary>
        [Theory]
        [InlineData("brake_80_0_dry_abs_comb@laden40", "stop_distance_m", 0)]
        [InlineData("brake_80_0_wet_abs_comb@laden40", "stop_distance_m", 0)]
        [InlineData("lane_change_80@laden40", "max_articulation_deg", 0)]
        [InlineData("launch_flat_comb@laden40", "time_to_kmh", 60)]
        public void Combination_DtVariation_IsConsistent(string id, string metric, double arg)
        {
            var s = Suites.DtSweep(id, metric, arg, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 });
            var sub = Suites.SubstepSweep(id, metric, arg, new[] { 2, 4, 8 });
            _out.WriteLine(s.ToString()); _out.WriteLine(sub.ToString());
            Assert.True(s.MaxRelDev <= 0.05, s.ToString());
            Assert.True(sub.MaxRelDev <= 0.05, sub.ToString());
        }

        // ------------------------------------------------------------------ R5: coupling throat

        static RunResult RunCouple(string id, double offset, double articulationDeg = 0, double duration = 40)
        {
            var sc = Suites.Find(id);
            sc.overrides.trailerOffset = offset;
            sc.overrides.articulationDeg = articulationDeg;
            return ScenarioRunner.Run(sc, new RunOptions { Duration = duration });
        }

        /// <summary>R5: the throat ramps guide a kingpin up to +/- 0.18 m off the centre line into the jaw (hand reversing).</summary>
        [Theory]
        [InlineData(-0.18, 0)]
        [InlineData(-0.12, 5)]
        [InlineData(0.0, 0)]
        [InlineData(0.10, -5)]
        [InlineData(0.15, 4)]
        [InlineData(0.17, 0)]
        public void CouplingThroat_GuidesKingpinIntoJaw(double offset, double articulationDeg)
        {
            var r = RunCouple("couple_standstill_locked@laden40", offset, articulationDeg);
            _out.WriteLine($"offset {offset:F2} m, yaw {articulationDeg} deg: couplings {r.CouplingEvents}, bump {r.Metric("max_kingpin_long_kn"):F0} kN, dv {r.Metric("max_dv_step_ms"):F3} m/s");
            Assert.Equal(1, r.CouplingEvents);
            Assert.True(r.Metric("max_kingpin_long_kn") < 150);
            Assert.True(r.Metric("max_dv_step_ms") < 0.35);
        }

        /// <summary>R5: wider than the mouth, or far off, there is no (false) coupling.</summary>
        [Theory]
        [InlineData(0.21)]
        [InlineData(-0.21)]
        [InlineData(0.30)]
        [InlineData(-0.45)]
        public void CouplingThroat_FarOff_DoesNotCouple(double offset)
        {
            var r = RunCouple("couple_standstill_locked@empty", offset, 0, 12);
            _out.WriteLine($"offset {offset:F2} m: couplings {r.CouplingEvents}");
            Assert.Equal(0, r.CouplingEvents);
            Assert.Equal(0, r.Metric("coupled_final"));
        }

        /// <summary>R5: the throat does nothing while the jaw is not armed.</summary>
        [Fact]
        public void CouplingThroat_NotArmed_NoCouplingNoGuide()
        {
            var sc = Suites.Find("couple_standstill_locked@empty");
            sc.overrides.trailerOffset = 0.12;
            sc.events = new EventSpec[0];
            var r = ScenarioRunner.Run(sc, new RunOptions { Duration = 8 });
            Assert.Equal(0, r.CouplingEvents);
        }

        // ------------------------------------------------------------------ R6: kingpin load at standstill

        /// <summary>R6: legs up on locked brakes, no rolling: the kingpin carries the static nose load (was 0.67-0.9x).</summary>
        [Theory]
        [InlineData("couple_standstill_locked@empty")]
        [InlineData("couple_standstill_locked@laden40")]
        public void KingpinLoad_LegsUpOnLockedBrakes_IsStatic(string id)
        {
            var r = ScenarioRunner.Run(Suites.Find(id), new RunOptions());
            double ratio = r.Metric("kingpin_load_vs_static", 0, 50, 80);
            _out.WriteLine($"{id}: kingpin / static = {ratio:F4}");
            Assert.InRange(ratio, 0.97, 1.03);
            Assert.True(r.Metric("max_speed_after_ms", 0, 60) < 0.005);
        }

        // ------------------------------------------------------------------ R7: trailer / cargo swap in place

        static void Settle(SimContext s, IDriver driver, double seconds, double dt = 0.01)
        {
            var tractorState = default(ChassisState); var trailerState = default(ChassisState);
            double t = 0;
            int n = (int)Math.Round(seconds / dt);
            for (int i = 0; i < n; i++)
            {
                var inp = driver.Update(t, dt, s);
                tractorState = s.Body.State;
                if (s.TrailerBody != null) trailerState = s.TrailerBody.State;
                s.Combo.Step(dt, tractorState, trailerState, inp, s.Ground);
                s.Body.Integrate(dt, s.Combo.TractorForce, s.Combo.TractorTorque);
                s.TrailerBody?.Integrate(dt, s.Combo.TrailerForce, s.Combo.TrailerTorque);
                t += dt;
            }
        }

        /// <summary>The host's side of a load change: new rigid body mass properties on the same pose.</summary>
        static void ReplaceTrailerBody(SimContext s)
        {
            var old = s.TrailerBody;
            var nb = new RigidBody6Dof(s.Combo.Trailer.MassProps) { Position = old.Position, Rotation = old.Rotation, Velocity = Vec3.Zero };
            s.TrailerBody = nb;
        }

        /// <summary>R7: cargo change in place keeps the tractor model, the trailer model and the wheel states; the new load settles to its static kingpin load.</summary>
        [Fact]
        public void SetCargo_InPlace_SettlesToNewStaticLoad()
        {
            var sc = Suites.Find("park_flat_5min_comb@empty");
            var s = ScenarioRunner.Setup(sc, new RunOptions());
            var driver = ScenarioRunner.CreateDriver(sc, s, out _);
            Settle(s, driver, 3);
            var tractor = s.Combo.Tractor; var trailer = s.Combo.Trailer; var wheels = trailer.Wheels;
            double emptyMass = trailer.Mass;
            s.Combo.SetCargo(new CargoDefinition { massKg = 22000 });
            ReplaceTrailerBody(s);
            Assert.Same(tractor, s.Combo.Tractor);
            Assert.Same(trailer, s.Combo.Trailer);
            Assert.Same(wheels, trailer.Wheels);
            Assert.InRange(trailer.Mass, emptyMass + 21999, emptyMass + 22001);
            Settle(s, driver, 40);
            var fw = s.Combo.FifthWheel;
            double ratio = fw.KingpinLoadLocal.y / s.Combo.StaticKingpinLoad;
            _out.WriteLine($"22 t cargo in place: kingpin / static = {ratio:F4}, error {fw.PositionError * 1000:F2} mm, kingpin {s.Combo.StaticKingpinLoad / 9.81:F0} kg");
            Assert.InRange(ratio, 0.97, 1.03);
            Assert.True(fw.PositionError < 0.005);
            Assert.True(s.Body.Velocity.Magnitude < 0.01 && s.TrailerBody.Velocity.Magnitude < 0.01);
            // Back to empty: the static load returns to the empty value.
            s.Combo.SetCargo(new CargoDefinition());
            ReplaceTrailerBody(s);
            Settle(s, driver, 40);
            ratio = fw.KingpinLoadLocal.y / s.Combo.StaticKingpinLoad;
            _out.WriteLine($"back to empty: kingpin / static = {ratio:F4}");
            Assert.InRange(ratio, 0.97, 1.03);
        }

        /// <summary>R7: SetTrailer swaps a coupled trailer (different load) and removes / re-adds one, without a new combination or tractor model.</summary>
        [Fact]
        public void SetTrailer_SwapsWithoutRebuildingTheCombination()
        {
            var sc = Suites.Find("park_flat_5min_comb@empty");
            var s = ScenarioRunner.Setup(sc, new RunOptions());
            var driver = ScenarioRunner.CreateDriver(sc, s, out _);
            Settle(s, driver, 3);
            var combo = s.Combo; var tractor = combo.Tractor;
            var settings = new SolverSettings { substeps = sc.substeps };
            var heavy = ScenarioRunner.Defs.CreateTrailer(sc.trailer, new CargoDefinition { massKg = 18000 }, settings);
            combo.SetTrailer(heavy, true);
            // The host re-places the new trailer on the same pose.
            var old = s.TrailerBody;
            s.TrailerBody = new RigidBody6Dof(heavy.MassProps) { Position = old.Position, Rotation = old.Rotation };
            Assert.Same(tractor, combo.Tractor);
            Assert.Same(heavy, combo.Trailer);
            Assert.True(combo.Coupled);
            Settle(s, driver, 40);
            double ratio = combo.FifthWheel.KingpinLoadLocal.y / combo.StaticKingpinLoad;
            _out.WriteLine($"swapped to 18 t cargo: kingpin / static = {ratio:F4}");
            Assert.InRange(ratio, 0.97, 1.03);
            Assert.True(combo.FifthWheel.PositionError < 0.005);
            Assert.Equal(0, combo.FifthWheel.UncouplingEvents);

            // Remove the trailer: solo tractor.
            combo.SetTrailer(null, false);
            s.TrailerBody = null;
            Assert.False(combo.HasTrailer);
            Assert.False(combo.Coupled);
            Assert.False(tractor.TrailerConnected);
            Assert.Equal(0, tractor.TowedMass);
            Settle(s, driver, 20);
            Assert.True(s.Body.Velocity.Magnitude < 0.01);
            Assert.Equal(0, combo.TrailerForce.Magnitude);
        }

        /// <summary>R7: the combination step stays allocation-free after a cargo change.</summary>
        [Fact]
        public void Step_DoesNotAllocate_AfterSetCargo()
        {
            var sc = Suites.Find("park_flat_5min_comb@empty");
            var s = ScenarioRunner.Setup(sc, new RunOptions());
            var driver = ScenarioRunner.CreateDriver(sc, s, out _);
            Settle(s, driver, 2);
            s.Combo.SetCargo(new CargoDefinition { massKg = 15000 });
            ReplaceTrailerBody(s);
            Settle(s, driver, 2);
            long before = GC.GetAllocatedBytesForCurrentThread();
            var inp = default(DriverInput);
            for (int i = 0; i < 500; i++)
            {
                s.Combo.Step(0.01, s.Body.State, s.TrailerBody.State, inp, s.Ground);
                s.Body.Integrate(0.01, s.Combo.TractorForce, s.Combo.TractorTorque);
                s.TrailerBody.Integrate(0.01, s.Combo.TrailerForce, s.Combo.TrailerTorque);
            }
            long bytes = GC.GetAllocatedBytesForCurrentThread() - before;
            _out.WriteLine($"allocated in 500 steps: {bytes} B");
            Assert.Equal(0, bytes);
        }

        /// <summary>Air supply: an empty system charges, releases the spring brakes, and the governor cuts out.</summary>
        [Fact]
        public void AirSystem_ChargesFromEmpty()
        {
            var m = ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            m.Air.Charge(0);
            m.InitParking(true);
            double t = 0, tRelease = double.NaN, tCutOut = double.NaN;
            for (int i = 0; i < 60000 && double.IsNaN(tCutOut); i++)
            {
                m.Air.Update(0.01, 1200, true, 0, false, false, m.Group);
                m.Air.BeginSubsteps();
                m.Air.UpdateChambers(0.01, m.Group);
                t += 0.01;
                if (double.IsNaN(tRelease) && m.Wheels[2].SpringChamberPressure >= m.Def.air.springReleaseFullBar) tRelease = t;
                if (!m.Air.CompressorLoaded && t > 1) tCutOut = t;
            }
            _out.WriteLine($"1200 rpm, empty system: spring brakes released after {tRelease:F0} s, governor cut-out after {tCutOut:F0} s");
            Assert.False(double.IsNaN(tRelease));
            Assert.False(double.IsNaN(tCutOut));
            Assert.True(tRelease < tCutOut);
            Assert.InRange(tCutOut, 30, 600);
        }
    }
}
