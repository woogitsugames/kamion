using System;
using System.Collections.Generic;
using System.Linq;
using Game.Vehicle.Physics;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    // ---------------------------------------------------------------------------
    // Unit tests for the shared physics core modules (game/Assets/_Project/Vehicle/Physics,
    // compiled into PhysicsRunner.Sim): engine, AMT + clutch, pneumatic brakes, retarder,
    // tire model, fifth-wheel (trailer joint), math helpers.
    // Property / edge-case focus: monotonicity, limits, symmetry, dt extremes, NaN/Inf,
    // determinism. No production behaviour is changed; a failing property is a bug report.
    // ---------------------------------------------------------------------------

    public class EngineTests
    {
        readonly ITestOutputHelper _out;
        public EngineTests(ITestOutputHelper output) { _out = output; }

        Engine NewEngine() => ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings()).Engine;

        [Fact]
        public void FullLoadTorque_NonNegativeFinite_AcrossWholeRange()
        {
            var e = NewEngine();
            for (double rpm = 0; rpm <= 3000; rpm += 10)
            {
                double t = e.FullLoadTorque(rpm * MathUtil.RpmToRadS);
                Assert.False(double.IsNaN(t) || double.IsInfinity(t), $"rpm {rpm}");
                Assert.True(t >= 0, $"rpm {rpm}: {t}");
            }
        }

        /// <summary>Torque rises to the plateau (500-1270 rpm) and then fades monotonically to the cut-off at maxRpm.</summary>
        [Fact]
        public void FullLoadTorque_PlateauThenMonotoneFadeToZeroAtMaxRpm()
        {
            var e = NewEngine();
            double prev = double.NegativeInfinity;
            for (double rpm = 500; rpm <= 1270; rpm += 10)
            {
                double t = e.FullLoadTorque(rpm * MathUtil.RpmToRadS);
                Assert.True(t >= prev - 1e-9, $"not non-decreasing at {rpm} rpm: {prev} -> {t}");
                prev = t;
            }
            prev = double.PositiveInfinity;
            for (double rpm = 1270; rpm <= e.Def.maxRpm * 1.5; rpm += 10)
            {
                double t = e.FullLoadTorque(rpm * MathUtil.RpmToRadS);
                Assert.True(t <= prev + 1e-9, $"not non-increasing at {rpm} rpm: {prev} -> {t}");
                prev = t;
            }
            Assert.Equal(0, e.FullLoadTorque(e.MaxOmega));
            Assert.Equal(0, e.FullLoadTorque(e.MaxOmega * 1.1));
        }

        [Fact]
        public void DragTorque_PositiveAndNonDecreasing()
        {
            var e = NewEngine();
            double prev = 0;
            for (double rpm = 0; rpm <= 3000; rpm += 25)
            {
                double d = e.DragTorque(rpm * MathUtil.RpmToRadS);
                Assert.True(d >= prev - 1e-9 && d > 0, $"rpm {rpm}: {prev} -> {d}");
                prev = d;
            }
        }

        [Fact]
        public void EngineBrakeTotal_AtLeastDrag_MonotoneInBrakingBand()
        {
            var e = NewEngine();
            Assert.True(e.HasEngineBrake);
            for (double rpm = 0; rpm <= 3000; rpm += 25)
            {
                double w = rpm * MathUtil.RpmToRadS;
                double eb = e.EngineBrakeTotal(w);
                Assert.False(double.IsNaN(eb));
                Assert.True(eb >= e.DragTorque(w) - 1e-9, $"rpm {rpm}: eb {eb} < drag {e.DragTorque(w)}");
            }
            // No engine braking at standstill: only the motoring drag remains.
            Assert.Equal(e.DragTorque(0), e.EngineBrakeTotal(0));
            double prev = 0;
            for (double rpm = 1000; rpm <= 2400; rpm += 25)
            {
                double eb = e.EngineBrakeTotal(rpm * MathUtil.RpmToRadS);
                Assert.True(eb >= prev - 1e-9, $"not non-decreasing at {rpm} rpm");
                prev = eb;
            }
        }

        /// <summary>Rev limiter: free-revving at full throttle the engine stays below the cut-off and never stalls.</summary>
        [Fact]
        public void FullThrottleFreeRev_StaysBelowMaxRpm_NoStall_NoNaN()
        {
            var e = NewEngine();
            double dt = 0.01;
            for (int i = 0; i < 6000; i++)
            {
                double te = e.ComputeTorque(1.0, 0, dt);
                Assert.False(double.IsNaN(te) || double.IsNaN(e.Boost));
                e.Omega += dt * te / e.Inertia;
                e.CheckStall();
            }
            _out.WriteLine($"free-rev after 60 s: {e.Rpm:F1} rpm, stalled {e.Stalled}");
            Assert.False(e.Stalled);
            Assert.True(e.Omega <= e.MaxOmega + 15, $"omega {e.Omega} rad/s vs max {e.MaxOmega}");
            Assert.True(e.Omega >= e.IdleOmega * 0.9, $"omega {e.Omega}");
        }

        /// <summary>Idle governor: from high rpm at zero throttle the engine settles at idle without stalling.</summary>
        [Fact]
        public void ZeroThrottle_IdleGovernorHoldsIdle_NoStall()
        {
            var e = NewEngine();
            e.Omega = 2000 * MathUtil.RpmToRadS;
            double dt = 0.01;
            for (int i = 0; i < 6000; i++)
            {
                e.Omega += dt * e.ComputeTorque(0, 0, dt) / e.Inertia;
                e.CheckStall();
            }
            _out.WriteLine($"zero throttle after 60 s: {e.Rpm:F1} rpm, stalled {e.Stalled}");
            Assert.False(e.Stalled);
            Assert.InRange(e.Omega, e.IdleOmega * 0.95, e.IdleOmega * 1.05);
        }

        [Fact]
        public void Stall_And_Restart()
        {
            var e = NewEngine();
            e.Omega = (e.Def.stallRpm - 50) * MathUtil.RpmToRadS;
            e.CheckStall();
            Assert.True(e.Stalled);
            double t = e.ComputeTorque(1.0, 0, 0.01);
            Assert.Equal(-e.DragTorque(e.Omega), t); // stalled: only drag
            Assert.True(t < 0, "stalled engine must be dragged, not driven");
            e.Restart();
            Assert.False(e.Stalled);
            Assert.Equal(e.IdleOmega, e.Omega);
        }

        /// <summary>Extreme demands / targets / dt: no NaN/Inf, boost stays in [0,1].</summary>
        [Theory]
        [InlineData(-5, 0, 0.01)]
        [InlineData(7, 0, 0.01)]
        [InlineData(1, -1, 0.01)]
        [InlineData(1, 1e9, 0.01)]
        [InlineData(1, 0, 1e-9)]
        [InlineData(1, 0, 100.0)]
        public void ComputeTorque_ExtremeInputs_NoNaN(double demand, double targetOmega, double dt)
        {
            var e = NewEngine();
            double t = e.ComputeTorque(demand, targetOmega, dt);
            Assert.False(double.IsNaN(t) || double.IsInfinity(t));
            Assert.False(double.IsNaN(e.Boost) || double.IsInfinity(e.Boost));
            Assert.InRange(e.Boost, 0, 1);
        }

        [Fact]
        public void Deterministic_SameInputsSameState()
        {
            var e1 = NewEngine(); var e2 = NewEngine();
            double dt = 0.01;
            for (int i = 0; i < 1000; i++)
            {
                double demand = (i % 7) / 7.0;
                double t1 = e1.ComputeTorque(demand, 0, dt);
                double t2 = e2.ComputeTorque(demand, 0, dt);
                Assert.Equal(t1, t2);
                e1.Omega += dt * t1 / e1.Inertia; e2.Omega += dt * t2 / e2.Inertia;
                e1.CheckStall(); e2.CheckStall();
            }
            Assert.Equal(e1.Omega, e2.Omega);
            Assert.Equal(e1.Boost, e2.Boost);
        }
    }

    public class AmtClutchTests
    {
        readonly ITestOutputHelper _out;
        public AmtClutchTests(ITestOutputHelper output) { _out = output; }

        static VehicleModel NewModel() => ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings());

        [Fact]
        public void GearRatios_NeutralZero_ReverseNegative_ForwardDecreasing()
        {
            var m = NewModel();
            var amt = m.Amt;
            Assert.Equal(0, amt.GearRatio(0));
            Assert.True(amt.GearRatio(-1) < 0);
            double prev = double.PositiveInfinity;
            for (int g = 1; g <= amt.Def.ForwardGearCount; g++)
            {
                Assert.True(amt.GearRatio(g) > 0 && amt.GearRatio(g) < prev, $"gear {g}");
                prev = amt.GearRatio(g);
            }
        }

        /// <summary>Neutral selector: throttle does not engage a gear or the clutch, no shift.</summary>
        [Fact]
        public void NeutralSelector_NoGearNoClutch_NoShift()
        {
            var m = NewModel(); var amt = m.Amt; var e = m.Engine;
            amt.ForceState(0, false);
            var inp = new DriverInput { Throttle = 1, Selector = GearSelector.Neutral };
            for (int i = 0; i < 200; i++)
                amt.Update(0.01, inp, 0, 0, e, 8000, 0, m.WheelRadiusRef, 0, 0.97);
            Assert.Equal(0, amt.Gear);
            Assert.Equal(0, amt.ClutchCommand);
            Assert.Equal(AmtState.Idle, amt.State);
            Assert.Equal(0, amt.ShiftCount);
        }

        /// <summary>Clutch open at standstill (no throttle): the pre-selected launch gear never shifts and the clutch stays open.</summary>
        [Fact]
        public void NoShiftWhileClutchOpen_AtStandstill()
        {
            var m = NewModel(); var amt = m.Amt; var e = m.Engine;
            amt.ForceState(0, false);
            var inp = new DriverInput { Throttle = 0, Selector = GearSelector.Drive };
            int firstGear = -1;
            for (int i = 0; i < 200; i++)
            {
                amt.Update(0.01, inp, 0, 0, e, 8000, 0, m.WheelRadiusRef, 0, 0.97);
                if (i == 10) firstGear = amt.Gear;
                Assert.Equal(0, amt.ClutchCommand);
                Assert.Equal(0, amt.ShiftCount);
            }
            Assert.Equal(AmtState.Idle, amt.State);
            Assert.InRange(amt.Gear, 1, amt.Def.maxLaunchGear); // launch gear pre-selected, constant
            Assert.Equal(firstGear, amt.Gear);
        }

        /// <summary>Drive-away interlock: parking brake applied at standstill -> clutch stays open, torque cut, no shift.</summary>
        [Fact]
        public void ParkingInterlock_KeepsClutchOpen_NoGearChange()
        {
            var m = NewModel(); var amt = m.Amt; var e = m.Engine;
            amt.ForceState(0, false);
            amt.ParkingBrakeApplied = true;
            var inp = new DriverInput { Throttle = 1, Selector = GearSelector.Drive };
            for (int i = 0; i < 100; i++)
                amt.Update(0.01, inp, 0, 0, e, 40000, 0, m.WheelRadiusRef, 2200, 0.97);
            Assert.True(amt.ParkingInterlockActive);
            Assert.Equal(AmtState.Idle, amt.State);
            Assert.Equal(0, amt.ClutchCommand);
            Assert.Equal(0, amt.TorqueScale);
            Assert.Equal(0, amt.ShiftCount);
        }

        /// <summary>Over-rev guard: at 2090 rpm in 3rd at full throttle the AMT upshifts immediately (bypasses the hold-off).</summary>
        [Fact]
        public void OverRev_BypassesCooldown_TriggersUpshift()
        {
            var m = NewModel(); var amt = m.Amt; var e = m.Engine;
            amt.ForceState(3, true);
            e.Omega = 2090 * MathUtil.RpmToRadS;
            var inp = new DriverInput { Throttle = 1, Selector = GearSelector.Drive };
            double drivelineOmega = e.Omega / Math.Abs(amt.TotalRatio);
            amt.Update(0.01, inp, 30, drivelineOmega, e, 40000, 0, m.WheelRadiusRef, 0, 0.97);
            Assert.Equal(AmtState.ShiftTorqueRamp, amt.State);
            Assert.Equal(4, amt.TargetGear);
            Assert.Equal(1, amt.ShiftCount);
        }

        /// <summary>Anti-hunting on a steady 5% climb at constant full throttle (40 t): after settling, at most a couple
        /// of gear changes and no downshift within the 1 s up-shift hold-off (ADR 0024).</summary>
        [Fact]
        public void SteadyGrade_ConstantThrottle_NoHunting()
        {
            var r = ScenarioRunner.Run(Suites.Find("grade_5pct_steady@laden40"));
            var samples = r.Samples.Where(s => s.T >= 150).ToList();
            Assert.True(samples.Count > 100);
            var events = new List<KeyValuePair<double, int>>(); // t, +1 up / -1 down
            int lastGear = 0;
            foreach (var s in samples)
            {
                if (s.Gear > 0)
                {
                    if (lastGear > 0 && s.Gear != lastGear)
                        events.Add(new KeyValuePair<double, int>(s.T, Math.Sign(s.Gear - lastGear)));
                    lastGear = s.Gear;
                }
            }
            _out.WriteLine($"gear events after 150 s: {string.Join(", ", events.Select(e => $"{e.Value:+0;-0}@{e.Key:F1}s"))}");
            Assert.True(events.Count <= 3, $"too many gear changes in the steady window: {events.Count}");
            for (int i = 1; i < events.Count; i++)
                if (events[i].Value < 0 && events[i - 1].Value > 0)
                    Assert.True(events[i].Key - events[i - 1].Key >= 0.9,
                        $"hunting: downshift {events[i].Key - events[i - 1].Key:F2} s after an upshift");
        }

        [Fact]
        public void Deterministic_SameScriptSameState()
        {
            var m1 = NewModel(); var m2 = NewModel();
            var a1 = m1.Amt; var a2 = m2.Amt; var e1 = m1.Engine; var e2 = m2.Engine;
            a1.ForceState(0, false); a2.ForceState(0, false);
            var inp = new DriverInput { Selector = GearSelector.Drive, Throttle = 0.8 };
            double dt = 0.01, v = 0;
            for (int i = 0; i < 3000; i++)
            {
                double d1 = a1.Gear != 0 ? e1.Omega / Math.Abs(a1.TotalRatio) : 0;
                double d2 = a2.Gear != 0 ? e2.Omega / Math.Abs(a2.TotalRatio) : 0;
                a1.Update(dt, inp, v, d1, e1, 40000, 0, 0.51, 2200, 0.97);
                a2.Update(dt, inp, v, d2, e2, 40000, 0, 0.51, 2200, 0.97);
                double t1 = e1.ComputeTorque(inp.Throttle * a1.TorqueScale, a1.EngineTargetOmega, dt);
                double t2 = e2.ComputeTorque(inp.Throttle * a2.TorqueScale, a2.EngineTargetOmega, dt);
                e1.Omega += dt * t1 / e1.Inertia; e2.Omega += dt * t2 / e2.Inertia;
                e1.CheckStall(); e2.CheckStall();
                v = a1.Gear != 0 ? e1.Omega / Math.Abs(a1.TotalRatio) * 0.51 : 0;
            }
            Assert.Equal(a1.Gear, a2.Gear);
            Assert.Equal(a1.State, a2.State);
            Assert.Equal(a1.ClutchCommand, a2.ClutchCommand);
            Assert.Equal(a1.TorqueScale, a2.TorqueScale);
            Assert.Equal(a1.ShiftCount, a2.ShiftCount);
            Assert.Equal(e1.Omega, e2.Omega);
            Assert.Equal(a1.ClutchTempC, a2.ClutchTempC);
        }

        [Fact]
        public void ClutchThermal_HeatsUnderSlipPower_CoolsToAmbient()
        {
            var m = NewModel(); var amt = m.Amt;
            double ambient = 25;
            double prev = amt.ClutchTempC;
            for (int i = 0; i < 2000; i++) // 20 s at 50 kW slip
            {
                amt.UpdateClutchThermal(50000, 0.01, ambient);
                Assert.True(amt.ClutchTempC >= prev - 1e-9, "heating must be monotone");
                prev = amt.ClutchTempC;
            }
            Assert.True(amt.ClutchTempC > amt.Def.clutchWarnTempC, $"temp {amt.ClutchTempC}");
            Assert.True(amt.ClutchOverheat);
            prev = amt.ClutchTempC;
            for (int i = 0; i < 200000; i++) // 2000 s at rest: cools toward ambient
            {
                amt.UpdateClutchThermal(0, 0.01, ambient);
                Assert.True(amt.ClutchTempC <= prev + 1e-9, "cooling must be monotone");
                prev = amt.ClutchTempC;
            }
            Assert.InRange(amt.ClutchTempC, ambient, ambient + 1.0);
            Assert.False(amt.ClutchOverheat);
        }

        [Theory]
        [InlineData(1e-9)]
        [InlineData(1.0)]
        public void ExtremeDt_ClutchCommandBounded_NoNaN(double dt)
        {
            var m = NewModel(); var amt = m.Amt; var e = m.Engine;
            amt.ForceState(2, true);
            e.Omega = 1400 * MathUtil.RpmToRadS;
            var inp = new DriverInput { Throttle = 0.6, Selector = GearSelector.Drive };
            for (int i = 0; i < 50; i++)
            {
                amt.Update(dt, inp, 10, e.Omega / Math.Abs(amt.TotalRatio), e, 40000, 0, 0.51, 2200, 0.97);
                Assert.False(double.IsNaN(amt.ClutchCommand));
                Assert.InRange(amt.ClutchCommand, 0, 1);
                Assert.InRange(amt.TorqueScale, 0, 1);
            }
        }
    }

    public class PneumaticBrakeTests
    {
        readonly ITestOutputHelper _out;
        public PneumaticBrakeTests(ITestOutputHelper output) { _out = output; }

        [Fact]
        public void DeltaP_AirFor_AreInverse()
        {
            Assert.Equal(5.0, Pneumatics.AirFor(Pneumatics.DeltaP(5.0, 30.0), 30.0), 9);
            Assert.Equal(0.0, Pneumatics.DeltaP(0.0, 20.0), 12);
        }

        [Fact]
        public void Flow_NoBackflow_NeverOvershootsEqualisation()
        {
            Assert.Equal(0, Pneumatics.Flow(5, 30, 10, 20, 20, 0.01)); // no backflow
            Assert.Equal(0, Pneumatics.Flow(8, 30, 8, 20, 20, 0.01));  // equal: no flow
            double q = Pneumatics.Flow(10, 30, 5, 20, 20, 0.01);
            double qEq = (10 - 5) / (Pneumatics.Atm / 30 + Pneumatics.Atm / 20);
            Assert.True(q > 0 && q <= qEq + 1e-12, $"q {q}, qEq {qEq}");
            double pFrom = 10 - Pneumatics.DeltaP(q, 30), pTo = 5 + Pneumatics.DeltaP(q, 20);
            Assert.True(pFrom >= pTo - 1e-9, "overshoot past equalisation");
            // Huge dt: flow clamps to exactly the equalisation amount.
            double qBig = Pneumatics.Flow(10, 30, 5, 20, 20, 1000.0);
            Assert.Equal(qEq, qBig, 9);
            double pF = 10 - Pneumatics.DeltaP(qBig, 30), pT = 5 + Pneumatics.DeltaP(qBig, 20);
            Assert.Equal(pF, pT, 9);
        }

        [Fact]
        public void UpdateChamber_ConvergesToTarget_Monotone_RespectsSupplyLimit()
        {
            var w = new WheelState { ChamberPressure = 0 };
            double prev = 0;
            for (int i = 0; i < 2000; i++)
            {
                double nl = Pneumatics.UpdateChamber(w, 6.0, 8.5, 0.8, 0.20, 0, 0.30, 0.045, 3.0, 0.01);
                Assert.True(nl >= 0);
                Assert.True(w.ChamberPressure >= prev - 1e-12, "apply must be monotone");
                prev = w.ChamberPressure;
            }
            Assert.Equal(6.0, w.ChamberPressure, 3);
            // Target above the supply: clamped to supply - 0.1, never above.
            var w2 = new WheelState { ChamberPressure = 0 };
            for (int i = 0; i < 2000; i++)
            {
                Pneumatics.UpdateChamber(w2, 12.0, 8.5, 0.8, 0.20, 0, 0.30, 0.045, 3.0, 0.01);
                Assert.True(w2.ChamberPressure <= 8.4 + 1e-9, $"over supply limit: {w2.ChamberPressure}");
            }
            Assert.Equal(8.4, w2.ChamberPressure, 3);
            // Release: target 0 -> monotone down to 0.
            prev = w.ChamberPressure;
            for (int i = 0; i < 2000; i++)
            {
                Pneumatics.UpdateChamber(w, 0, 8.5, 0.8, 0.20, 0, 0.30, 0.045, 3.0, 0.01);
                Assert.True(w.ChamberPressure <= prev + 1e-12, "release must be monotone");
                prev = w.ChamberPressure;
            }
            Assert.Equal(0.0, w.ChamberPressure, 6);
        }

        [Fact]
        public void UpdateChamber_DumpMode_DrivesToZero()
        {
            var w = new WheelState { ChamberPressure = 8.0, AbsMode = 2 };
            for (int i = 0; i < 500; i++)
                Pneumatics.UpdateChamber(w, 8.0, 8.5, 0.8, 0.20, 0, 0.30, 0.045, 3.0, 0.01);
            Assert.True(w.ChamberPressure < 0.01, $"dump did not exhaust: {w.ChamberPressure}");
            Assert.True(w.ChamberPressure >= -1e-12);
        }

        [Theory]
        [InlineData(1e-9)]
        [InlineData(1.0)]
        public void UpdateChamber_ExtremeDt_NoNaN_Bounded(double dt)
        {
            var w = new WheelState { ChamberPressure = 0 };
            for (int i = 0; i < 100; i++)
            {
                Pneumatics.UpdateChamber(w, 8.0, 8.5, 0.8, 0.20, 0, 0.30, 0.045, 3.0, dt);
                Assert.False(double.IsNaN(w.ChamberPressure) || double.IsNaN(w.LinePressure));
                Assert.InRange(w.ChamberPressure, -1e-9, 8.4 + 1e-9);
            }
        }

        [Fact]
        public void BrakeTorque_ServiceRampAndCap_SpringBrake_AntiCompounding()
        {
            var ax = new AxleDefinition { serviceBrakeTorque = 18000, parkingBrakeTorque = 12000 };
            var w = new WheelState { Axle = ax };
            const double pThr = 0.4, pMax = 8.5, sStart = 3.0, sFull = 5.5;
            // Below threshold and spring released: nothing.
            w.ChamberPressure = 0.4; w.SpringChamberPressure = 8.5;
            Assert.Equal(0, Pneumatics.BrakeTorque(w, pThr, pMax, sStart, sFull));
            // Full service, spring released: service cap.
            w.ChamberPressure = pMax;
            Assert.Equal(18000, Pneumatics.BrakeTorque(w, pThr, pMax, sStart, sFull));
            // Service monotone non-decreasing in chamber pressure, capped.
            double prev = 0;
            for (double p = 0; p <= pMax; p += 0.1)
            {
                w.ChamberPressure = p; w.SpringChamberPressure = 8.5;
                double tq = Pneumatics.BrakeTorque(w, pThr, pMax, sStart, sFull);
                Assert.True(tq >= prev - 1e-9 && tq <= 18000 + 1e-9, $"p {p}: {tq}");
                prev = tq;
            }
            // Spring brake: full at 0 bar, monotone decreasing to 0 at springReleaseFullBar.
            w.ChamberPressure = 0;
            prev = double.PositiveInfinity;
            for (double p = 0; p <= sFull; p += 0.1)
            {
                w.SpringChamberPressure = p;
                double tq = Pneumatics.BrakeTorque(w, pThr, pMax, sStart, sFull);
                Assert.True(tq <= prev + 1e-9 && tq >= 0, $"spring {p}: {tq}");
                prev = tq;
            }
            Assert.Equal(12000, Pneumatics.BrakeTorque(new WheelState { Axle = ax, SpringChamberPressure = 0 }, pThr, pMax, sStart, sFull));
            // Anti-compounding: max(service, spring), never the sum.
            w.ChamberPressure = pMax; w.SpringChamberPressure = 0;
            Assert.Equal(18000, Pneumatics.BrakeTorque(w, pThr, pMax, sStart, sFull));
        }

        [Fact]
        public void AbsStep_DumpsOnHighSlip_DisablesAtLowSpeed()
        {
            var w = new WheelState { Contact = true, Vx = 10, KinematicSlip = -0.5, TreadAccel = 0, AbsMode = 0 };
            Pneumatics.AbsStep(w, true, 0.16, 0.06, 12.0, 4.0, 1.5, 8.0);
            Assert.Equal(2, w.AbsMode);
            Assert.True(w.AbsActive);
            // Low speed: modulator disabled.
            var w2 = new WheelState { Contact = true, Vx = 0.5, KinematicSlip = -0.9, AbsMode = 2, AbsActive = true };
            Pneumatics.AbsStep(w2, true, 0.16, 0.06, 12.0, 4.0, 1.5, 8.0);
            Assert.Equal(0, w2.AbsMode);
            Assert.False(w2.AbsActive);
            // Small slip: stays in apply.
            var w3 = new WheelState { Contact = true, Vx = 10, KinematicSlip = -0.02, AbsMode = 0 };
            Pneumatics.AbsStep(w3, true, 0.16, 0.06, 12.0, 4.0, 1.5, 8.0);
            Assert.Equal(0, w3.AbsMode);
            Assert.False(w3.AbsActive);
        }

        /// <summary>Whole air system from empty: pressures bounded, governor caps the supply, no NaN even with
        /// out-of-range service demand.</summary>
        [Fact]
        public void AirSystem_ChargesFromEmpty_PressuresBounded_NoNaN()
        {
            var m = ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            var air = m.Air;
            air.Charge(0);
            m.InitParking(true);
            Assert.True(air.LowPressureWarning);
            bool sawCutOut = false;
            for (int i = 0; i < 60000; i++) // 600 s
            {
                double demand = (i / 1000) % 5 == 4 ? 2.0 : 0.5; // includes out-of-range demand
                air.Update(0.01, 1200, true, demand, false, false, m.Group);
                air.BeginSubsteps();
                air.UpdateChambers(0.01, m.Group);
                if (i % 10 == 0)
                    foreach (var w in m.Wheels)
                    {
                        // Out-of-range demand may push the chamber above pMax (bounded by the supply);
                        // the torque itself stays capped by Clamp01 in BrakeTorque.
                        Assert.InRange(w.ChamberPressure, -1e-9, 12.55);
                        Assert.InRange(w.SpringChamberPressure, -1e-9, 9.0);
                        Assert.InRange(w.BrakeTorque, 0, 40000);
                        Assert.False(double.IsNaN(w.BrakeTorque));
                    }
                if (i % 100 == 0)
                {
                    Assert.InRange(air.Supply, 0, 12.55);
                    Assert.InRange(air.Front, 0, 12.55);
                    Assert.InRange(air.Rear, 0, 12.55);
                    Assert.InRange(air.ParkTrailer, 0, 12.55);
                }
                if (i % 100 == 0 && !air.CompressorLoaded && air.Supply > 12.4) sawCutOut = true;
            }
            _out.WriteLine($"after 600 s: supply {air.Supply:F2}, front {air.Front:F2}, rear {air.Rear:F2}, park {air.ParkTrailer:F2} bar");
            Assert.True(sawCutOut, "governor cut-out never reached");
            Assert.True(air.Supply <= 12.5 + 0.05);
        }

        [Fact]
        public void AirSystem_LeakWithoutCompressor_DrainsSupplyToZero()
        {
            var m = ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            var air = m.Air;
            air.Charge(8.0);
            air.LeakLpm[0] = 600; // 10 NL/s on the supply reservoir
            double prev = air.Supply;
            for (int i = 0; i < 6000; i++) // 60 s, engine off
            {
                air.Update(0.01, 1200, false, 0, false, false, m.Group);
                Assert.True(air.Supply <= prev + 1e-12, "supply must drain monotonically");
                Assert.True(air.Supply >= 0);
                prev = air.Supply;
            }
            Assert.True(air.Supply < 0.5, $"supply {air.Supply} after 60 s of leak");
        }

        [Fact]
        public void AirSystem_Deterministic_SameStepsSamePressures()
        {
            var m1 = ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            var m2 = ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            m1.Air.Charge(0); m2.Air.Charge(0);
            m1.InitParking(true); m2.InitParking(true);
            for (int i = 0; i < 3000; i++)
            {
                double demand = (i % 500) / 500.0;
                m1.Air.Update(0.01, 1200, true, demand, false, false, m1.Group);
                m2.Air.Update(0.01, 1200, true, demand, false, false, m2.Group);
                m1.Air.BeginSubsteps(); m2.Air.BeginSubsteps();
                m1.Air.UpdateChambers(0.01, m1.Group);
                m2.Air.UpdateChambers(0.01, m2.Group);
            }
            Assert.Equal(m1.Air.Supply, m2.Air.Supply);
            Assert.Equal(m1.Air.Front, m2.Air.Front);
            Assert.Equal(m1.Air.Rear, m2.Air.Rear);
            Assert.Equal(m1.Air.ParkTrailer, m2.Air.ParkTrailer);
            for (int i = 0; i < m1.Wheels.Length; i++)
                Assert.Equal(m1.Wheels[i].ChamberPressure, m2.Wheels[i].ChamberPressure);
        }
    }

    public class RetarderTests
    {
        readonly ITestOutputHelper _out;
        public RetarderTests(ITestOutputHelper output) { _out = output; }

        Retarder NewRetarder() => ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings()).Retarder;

        [Fact]
        public void Available_ZeroAtStandstill_MonotoneToFullTorque()
        {
            var r = NewRetarder();
            var d = r.Def;
            Assert.True(d.present);
            Assert.Equal(0, r.Available(0));
            double wFull = d.fullTorqueShaftRpm * MathUtil.RpmToRadS;
            double prev = 0;
            for (double rpm = 0; rpm <= d.fullTorqueShaftRpm; rpm += 10)
            {
                double t = r.Available(rpm * MathUtil.RpmToRadS);
                Assert.False(double.IsNaN(t));
                Assert.True(t >= prev - 1e-9, $"not non-decreasing at {rpm} rpm: {prev} -> {t}");
                prev = t;
            }
            Assert.Equal(d.maxTorqueNm, r.Available(wFull), 6);
            // Full torque plateau up to where the power cap binds.
            Assert.Equal(d.maxTorqueNm, r.Available(1400 * MathUtil.RpmToRadS), 1);
        }

        [Fact]
        public void Available_PowerCapAtHighSpeed_NoNaN()
        {
            var r = NewRetarder();
            double maxP = r.Def.maxPowerKW * 1000.0;
            for (double rpm = 1; rpm <= 100000; rpm *= 1.5)
            {
                double w = rpm * MathUtil.RpmToRadS;
                double t = r.Available(w);
                Assert.False(double.IsNaN(t) || double.IsInfinity(t));
                Assert.True(t * w <= maxP + 1e-6, $"power cap violated at {rpm} rpm: {t * w} W");
            }
            double tHuge = r.Available(1e10);
            Assert.False(double.IsNaN(tHuge));
            Assert.True(tHuge >= 0 && tHuge < 1.0);
            // Negative shaft speed: same magnitude (Abs).
            Assert.Equal(r.Available(500 * MathUtil.RpmToRadS), r.Available(-500 * MathUtil.RpmToRadS), 12);
        }

        [Fact]
        public void Update_FillBounded_TorqueFollowsAvailable_PowerCapped()
        {
            var r = NewRetarder();
            double w = 1200 * MathUtil.RpmToRadS;
            double prev = 0;
            for (int i = 0; i < 200; i++)
            {
                r.Update(0.01, 1.0, w);
                Assert.InRange(r.Fill, 0, 1);
                Assert.True(r.Fill >= prev - 1e-12, "fill must be monotone toward command 1");
                prev = r.Fill;
                Assert.Equal(r.Fill * r.Available(w), r.Torque, 9);
                Assert.True(r.Power <= r.Def.maxPowerKW * 1000.0 + 1e-6, $"power {r.Power}");
                Assert.False(double.IsNaN(r.Torque) || double.IsNaN(r.Power));
            }
            Assert.True(r.Fill > 0.99);
            // Drain back to 0.
            prev = r.Fill;
            for (int i = 0; i < 200; i++)
            {
                r.Update(0.01, 0, w);
                Assert.True(r.Fill <= prev + 1e-12);
                prev = r.Fill;
            }
            Assert.True(r.Fill < 0.01);
            Assert.True(r.Torque < r.Def.maxTorqueNm * 0.01, $"drained torque {r.Torque}");
        }

        [Theory]
        [InlineData(1e-9)]
        [InlineData(10.0)]
        public void Update_ExtremeDt_FillBounded_NoNaN(double dt)
        {
            var r = NewRetarder();
            for (int i = 0; i < 100; i++)
            {
                r.Update(dt, 1.0, 800 * MathUtil.RpmToRadS);
                Assert.False(double.IsNaN(r.Fill) || double.IsNaN(r.Torque));
                Assert.InRange(r.Fill, 0, 1);
            }
        }

        [Fact]
        public void NotPresent_AlwaysZero()
        {
            var r = new Retarder(new RetarderDefinition { present = false });
            Assert.Equal(0, r.Available(1000 * MathUtil.RpmToRadS));
            for (int i = 0; i < 100; i++) r.Update(0.01, 1.0, 1000 * MathUtil.RpmToRadS);
            Assert.Equal(0, r.Torque);
            Assert.Equal(0, r.Power);
        }

        [Fact]
        public void Deterministic_SameInputsSameTorque()
        {
            var r1 = NewRetarder(); var r2 = NewRetarder();
            for (int i = 0; i < 500; i++)
            {
                double cmd = (i % 11) / 10.0;
                double w = 500 + (i % 37) * 40;
                r1.Update(0.01, cmd, w * MathUtil.RpmToRadS);
                r2.Update(0.01, cmd, w * MathUtil.RpmToRadS);
                Assert.Equal(r1.Torque, r2.Torque);
                Assert.Equal(r1.Fill, r2.Fill);
            }
        }
    }

    public class TireModelTests
    {
        readonly ITestOutputHelper _out;
        public TireModelTests(ITestOutputHelper output) { _out = output; }

        TireModel NewTire() => new TireModel(ScenarioRunner.Defs.Tires["tire_315_80_r22_5"]);

        [Fact]
        public void PeakMu_DecreasesWithLoad_AndHasFloor()
        {
            var tm = NewTire();
            double n = tm.Def.nominalLoadN;
            Assert.True(tm.PeakMu(2 * n, 1.0) < tm.PeakMu(n, 1.0), "load sensitivity must lower mu");
            Assert.Equal(tm.Def.peakMu, tm.PeakMu(n, 1.0), 12);
            Assert.Equal(0.1 * tm.Def.peakMu, tm.PeakMu(1e8, 1.0), 12); // floor
            Assert.Equal(tm.PeakMu(n, 1.0) * 0.5, tm.PeakMu(n, 0.5), 12); // surface scale
        }

        /// <summary>Left/right symmetry: mirrored slips give exactly mirrored forces, same mu.</summary>
        [Fact]
        public void CombinedForces_SymmetricUnderSignFlip()
        {
            var tm = NewTire();
            double fz = 50000;
            tm.CombinedForces(fz, 2, 1.0, 0.10, 0.20, out double fx1, out double fy1, out double mu1);
            tm.CombinedForces(fz, 2, 1.0, -0.10, -0.20, out double fx2, out double fy2, out double mu2);
            Assert.Equal(fx1, -fx2, 9);
            Assert.Equal(fy1, -fy2, 9);
            Assert.Equal(mu1, mu2);
            // Pure lateral: left vs right.
            tm.CombinedForces(fz, 2, 1.0, 0, 0.3, out _, out double fyL, out _);
            tm.CombinedForces(fz, 2, 1.0, 0, -0.3, out _, out double fyR, out _);
            Assert.Equal(fyL, -fyR, 9);
            Assert.True(fyL > 0 && fyR < 0);
        }

        /// <summary>Pure longitudinal: force rises monotonically to the peak slip, then saturates below mu*Fz.</summary>
        [Fact]
        public void CombinedForces_Longitudinal_MonotoneToPeak_ThenSaturates()
        {
            var tm = NewTire();
            double fz = 60000; int count = 2;
            double fzt = fz / count;
            double mu = tm.PeakMu(fzt, 1.0);
            double kpk = tm.PeakKappa(mu, fzt);
            double prev = 0;
            for (int i = 0; i <= 50; i++)
            {
                double k = kpk * i / 50.0;
                tm.CombinedForces(fz, count, 1.0, k, 0, out double fx, out _, out _);
                Assert.True(fx >= prev - 1e-6, $"not non-decreasing at k={k:F4}: {prev} -> {fx}");
                prev = fx;
            }
            tm.CombinedForces(fz, count, 1.0, kpk, 0, out double fxPeak, out _, out _);
            Assert.InRange(fxPeak, 0.999 * mu * fz, 1.0001 * mu * fz);
            tm.CombinedForces(fz, count, 1.0, 3 * kpk, 0, out double fxSat, out _, out _);
            Assert.True(fxSat < fxPeak, $"saturation: {fxSat} vs peak {fxPeak}");
            // Global friction bound over a wide slip range.
            for (double k = -5; k <= 5; k += 0.05)
            {
                tm.CombinedForces(fz, count, 1.0, k, 0, out double fx, out _, out _);
                Assert.True(Math.Abs(fx) <= mu * fz * 1.0001, $"k {k}: {fx}");
                Assert.False(double.IsNaN(fx));
            }
        }

        [Fact]
        public void CombinedForces_FrictionCircle_UnderCombinedSlip()
        {
            var tm = NewTire();
            double fz = 60000;
            double mu = tm.PeakMu(fz / 2, 1.0);
            for (double k = -1.5; k <= 1.5; k += 0.25)
                for (double a = -1.5; a <= 1.5; a += 0.25)
                {
                    tm.CombinedForces(fz, 2, 1.0, k, a, out double fx, out double fy, out _);
                    Assert.False(double.IsNaN(fx) || double.IsNaN(fy));
                    Assert.True(Math.Sqrt(fx * fx + fy * fy) <= mu * fz * 1.0001, $"k {k} a {a}");
                }
        }

        [Fact]
        public void CombinedForces_ExtremeInputs_NoNaN_ZeroLoadGivesZero()
        {
            var tm = NewTire();
            tm.CombinedForces(0, 2, 1.0, 0.5, 0.5, out double fx0, out double fy0, out _);
            Assert.Equal(0, fx0); Assert.Equal(0, fy0);
            tm.CombinedForces(-1000, 2, 1.0, 0.5, 0.5, out double fxN, out double fyN, out _);
            Assert.Equal(0, fxN); Assert.Equal(0, fyN);
            tm.CombinedForces(1e12, 2, 1.0, 1e9, -1e9, out double fx, out double fy, out double mu);
            Assert.False(double.IsNaN(fx) || double.IsNaN(fy) || double.IsNaN(mu));
            double bound = mu * 1e12 * 1.001;
            Assert.True(Math.Sqrt(fx * fx + fy * fy) <= bound, $"{fx} {fy} vs bound {bound}");
        }

        [Fact]
        public void SmallSlip_LateralLinearity()
        {
            var tm = NewTire();
            double fz = 60000, count = 2;
            double fzt = fz / count;
            tm.CombinedForces(fz, count, 1.0, 0, 1e-6, out double fx, out double fy, out _);
            Assert.InRange(fy / 1e-6, 0.99 * tm.KyPerLoad(fzt) * fz, 1.01 * tm.KyPerLoad(fzt) * fz);
            Assert.True(Math.Abs(fx) < 1e-6);
        }

        [Fact]
        public void Deterministic_SameInputsSameForces()
        {
            var t1 = NewTire(); var t2 = NewTire();
            for (int i = 0; i < 200; i++)
            {
                double k = -2 + i * 0.02, a = 1 - i * 0.01;
                t1.CombinedForces(40000, 2, 1.0, k, a, out double fx1, out double fy1, out double mu1);
                t2.CombinedForces(40000, 2, 1.0, k, a, out double fx2, out double fy2, out double mu2);
                Assert.Equal(fx1, fx2);
                Assert.Equal(fy1, fy2);
                Assert.Equal(mu1, mu2);
            }
        }
    }

    public class FifthWheelTests
    {
        readonly ITestOutputHelper _out;
        public FifthWheelTests(ITestOutputHelper output) { _out = output; }

        static FifthWheelDefinition Def => ScenarioRunner.Defs.Vehicles["tractor_4x2_generic"].fifthWheel;

        static ChassisState StateAt(Vec3 pos, Quat rot) => new ChassisState
        {
            Position = pos,
            Rotation = rot,
            CenterOfMassWorld = pos,
            LinearVelocity = Vec3.Zero,
            AngularVelocity = Vec3.Zero,
        };

        static MassProperties HeavyProps(double mass) =>
            new MassProperties { Mass = mass, CenterOfMass = Vec3.Zero, Inertia = Mat3.Diagonal(mass * 100, mass * 100, mass * 100) };

        [Fact]
        public void TryCapture_InsideWindowCouples_OutsideOrTooFastDoesNot()
        {
            var def = Def;
            var fw = new FifthWheel(def);
            var a = StateAt(Vec3.Zero, Quat.Identity);
            Vec3 anchorA = def.position;
            var b = StateAt(anchorA, Quat.Identity);
            Assert.True(fw.TryCapture(a, anchorA, b, Vec3.Zero));
            Assert.True(fw.Coupled);
            Assert.Equal(1, fw.CouplingEvents);

            var fw2 = new FifthWheel(def);
            var far = StateAt(anchorA + new Vec3(0.20, 0, 0), Quat.Identity);
            Assert.False(fw2.TryCapture(a, anchorA, far, Vec3.Zero));
            var high = StateAt(anchorA + new Vec3(0, 0.20, 0), Quat.Identity);
            Assert.False(fw2.TryCapture(a, anchorA, high, Vec3.Zero));
            var fast = StateAt(anchorA, Quat.Identity);
            fast.LinearVelocity = new Vec3(2.0, 0, 0); // > captureMaxSpeed 1.5
            Assert.False(fw2.TryCapture(a, anchorA, fast, Vec3.Zero));
            Assert.Equal(0, fw2.CouplingEvents);
        }

        /// <summary>Coupled at rest with the tractor held: the kingpin carries the trailer's weight.</summary>
        [Fact]
        public void Solve_StaticVerticalLoad_TransferredToTractor()
        {
            var def = Def;
            double mB = 8000;
            var ma = HeavyProps(1e9);
            var mb = HeavyProps(mB);
            var a = StateAt(Vec3.Zero, Quat.Identity);
            var b = StateAt(Vec3.Zero, Quat.Identity);
            var fw = new FifthWheel(def) { Coupled = true };
            Vec3 holdA = new Vec3(0, ma.Mass * 9.81, 0);
            Vec3 gravity = new Vec3(0, -9.81, 0);
            fw.Solve(0.01, a, ma, Vec3.Zero, holdA, Vec3.Zero, b, mb, Vec3.Zero, Vec3.Zero, Vec3.Zero, gravity);
            double expected = mB * 9.81;
            _out.WriteLine($"kingpin vertical {fw.KingpinLoadLocal.y:F0} N, expected {expected:F0} N, err {fw.PositionError * 1000:F4} mm");
            Assert.InRange(fw.KingpinLoadLocal.y, expected * 0.99, expected * 1.01);
            Assert.True(Math.Abs(fw.KingpinLoadLocal.x) < 1.0 && Math.Abs(fw.KingpinLoadLocal.z) < 1.0);
            Assert.True(fw.PositionError < 1e-9);
            Assert.True(fw.TorqueOnTrailer.Magnitude < 1.0);
            Assert.False(double.IsNaN(fw.ForceOnTrailer.x) || double.IsNaN(fw.ForceOnTrailer.y));
        }

        [Theory]
        [InlineData(1e-6)]
        [InlineData(0.5)]
        public void Solve_ExtremeDt_StaticLoadStillHeld_NoNaN(double dt)
        {
            double mB = 8000;
            var ma = HeavyProps(1e9);
            var mb = HeavyProps(mB);
            var a = StateAt(Vec3.Zero, Quat.Identity);
            var b = StateAt(Vec3.Zero, Quat.Identity);
            var fw = new FifthWheel(Def) { Coupled = true };
            fw.Solve(dt, a, ma, Vec3.Zero, new Vec3(0, ma.Mass * 9.81, 0), Vec3.Zero,
                b, mb, Vec3.Zero, Vec3.Zero, Vec3.Zero, new Vec3(0, -9.81, 0));
            Assert.False(double.IsNaN(fw.ForceOnTrailer.Magnitude));
            Assert.InRange(fw.KingpinLoadLocal.y, mB * 9.81 * 0.98, mB * 9.81 * 1.02);
        }

        /// <summary>Articulation beyond the yaw stop: the stop pushes back; mirrored angles give mirrored torques.</summary>
        [Fact]
        public void Solve_YawStop_SymmetricAndFinite()
        {
            double ang = 100 * MathUtil.Deg2Rad;
            var ma = HeavyProps(1e9);
            var mb = HeavyProps(8000);
            var a = StateAt(Vec3.Zero, Quat.Identity);
            Vec3 gravity = new Vec3(0, -9.81, 0);

            var fw1 = new FifthWheel(Def) { Coupled = true };
            var b1 = StateAt(Vec3.Zero, Quat.AngleAxis(ang, Vec3.Up));
            fw1.Solve(0.01, a, ma, Vec3.Zero, Vec3.Zero, Vec3.Zero, b1, mb, Vec3.Zero, Vec3.Zero, Vec3.Zero, gravity);

            var fw2 = new FifthWheel(Def) { Coupled = true };
            var b2 = StateAt(Vec3.Zero, Quat.AngleAxis(-ang, Vec3.Up));
            fw2.Solve(0.01, a, ma, Vec3.Zero, Vec3.Zero, Vec3.Zero, b2, mb, Vec3.Zero, Vec3.Zero, Vec3.Zero, gravity);

            _out.WriteLine($"articulation {fw1.Articulation * MathUtil.Rad2Deg:F2} deg, torque y {fw1.TorqueOnTrailer.y:F0} / {fw2.TorqueOnTrailer.y:F0} N m");
            Assert.Equal(100.0, Math.Abs(fw1.Articulation) * MathUtil.Rad2Deg, 6);
            Assert.True(Math.Abs(fw1.Articulation) > Def.yawLimitDeg * MathUtil.Deg2Rad);
            Assert.True(Math.Abs(fw1.TorqueOnTrailer.y) > 1e4, "yaw stop did not push");
            Assert.True(Math.Abs(fw1.TorqueOnTrailer.y + fw2.TorqueOnTrailer.y) <= 1e-6 * Math.Abs(fw1.TorqueOnTrailer.y) + 1e-6,
                $"asymmetric yaw stop: {fw1.TorqueOnTrailer.y} vs {fw2.TorqueOnTrailer.y}");
            Assert.False(double.IsNaN(fw1.TorqueOnTrailer.Magnitude) || double.IsNaN(fw2.TorqueOnTrailer.Magnitude));
        }

        /// <summary>Coupling throat ramps: mirrored kingpin offsets give mirrored guide forces.</summary>
        [Fact]
        public void ThroatGuide_SymmetricLeftRight()
        {
            var def = Def;
            var a = StateAt(Vec3.Zero, Quat.Identity);
            Vec3 anchorA = def.position;
            var fw1 = new FifthWheel(def);
            var b1 = StateAt(anchorA + new Vec3(0.15, 0, -0.2), Quat.Identity);
            Assert.True(fw1.ComputeThroatGuide(a, anchorA, b1, Vec3.Zero, out Vec3 f1));
            var fw2 = new FifthWheel(def);
            var b2 = StateAt(anchorA + new Vec3(-0.15, 0, -0.2), Quat.Identity);
            Assert.True(fw2.ComputeThroatGuide(a, anchorA, b2, Vec3.Zero, out Vec3 f2));
            _out.WriteLine($"guide forces {f1} vs {f2}");
            Assert.Equal(f1.x, -f2.x, 6);
            Assert.Equal(f1.y, f2.y, 9);
            Assert.Equal(f1.z, f2.z, 6);
            Assert.Equal(fw1.GuideForce, fw2.GuideForce, 6);
            Assert.True(fw1.GuideForce > 0 && fw1.GuideForce <= def.captureGuideMaxForce + 1e-9);
            // Wider than the mouth: no guide force.
            var fw3 = new FifthWheel(def);
            var b3 = StateAt(anchorA + new Vec3(0.30, 0, -0.2), Quat.Identity);
            Assert.False(fw3.ComputeThroatGuide(a, anchorA, b3, Vec3.Zero, out Vec3 f3));
            Assert.Equal(Vec3.Zero.x, f3.x);
            Assert.Equal(0, fw3.GuideForce);
        }

        [Fact]
        public void Solve_Deterministic_SameInputsSameForces()
        {
            double mB = 8000;
            var ma = HeavyProps(1e9);
            var mb = HeavyProps(mB);
            var a = StateAt(Vec3.Zero, Quat.Identity);
            var b = StateAt(new Vec3(0.001, 0, 0), Quat.AngleAxis(5 * MathUtil.Deg2Rad, Vec3.Up));
            Vec3 gravity = new Vec3(0, -9.81, 0);
            var fw1 = new FifthWheel(Def) { Coupled = true };
            var fw2 = new FifthWheel(Def) { Coupled = true };
            fw1.Solve(0.01, a, ma, Vec3.Zero, new Vec3(0, ma.Mass * 9.81, 0), Vec3.Zero, b, mb, Vec3.Zero, Vec3.Zero, Vec3.Zero, gravity);
            fw2.Solve(0.01, a, ma, Vec3.Zero, new Vec3(0, ma.Mass * 9.81, 0), Vec3.Zero, b, mb, Vec3.Zero, Vec3.Zero, Vec3.Zero, gravity);
            Assert.Equal(fw1.ForceOnTrailer.x, fw2.ForceOnTrailer.x);
            Assert.Equal(fw1.ForceOnTrailer.y, fw2.ForceOnTrailer.y);
            Assert.Equal(fw1.ForceOnTrailer.z, fw2.ForceOnTrailer.z);
            Assert.Equal(fw1.TorqueOnTrailer.y, fw2.TorqueOnTrailer.y);
        }
    }

    public class MathUtilTests
    {
        [Fact]
        public void Lut_ClampsAtEnds_ExactAtNodes_LinearBetween()
        {
            double[] xs = { 0, 10, 20 }, ys = { 5, 15, 25 };
            Assert.Equal(5, MathUtil.Lut(xs, ys, -5));
            Assert.Equal(25, MathUtil.Lut(xs, ys, 25));
            Assert.Equal(15, MathUtil.Lut(xs, ys, 10));
            Assert.Equal(10, MathUtil.Lut(xs, ys, 5));
        }

        [Fact]
        public void FirstOrder_StableForAnyDt()
        {
            Assert.Equal(1.0, MathUtil.FirstOrder(0, 1, 0.5, 1000.0), 9);  // huge dt -> target
            Assert.Equal(0.0, MathUtil.FirstOrder(1, 0, 0.0, 0.01), 12);    // tau 0 -> target
            Assert.True(Math.Abs(MathUtil.FirstOrder(0, 1, 0.5, 1e-12)) < 1e-9); // tiny dt -> ~unchanged
            Assert.Equal(1.0, MathUtil.FirstOrder(0, 1, 1e-10, 0.01), 12); // tau ~ 0 -> target
        }

        [Fact]
        public void Clamp_MoveTowards_Basics()
        {
            Assert.Equal(0, MathUtil.Clamp01(-3));
            Assert.Equal(1, MathUtil.Clamp01(3));
            Assert.Equal(5, MathUtil.MoveTowards(0, 5, 2));
            Assert.Equal(-5, MathUtil.MoveTowards(0, -5, 2));
            Assert.Equal(3, MathUtil.MoveTowards(2.9, 3, 2));
        }
    }
}
