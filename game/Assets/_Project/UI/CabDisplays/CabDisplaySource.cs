using System;
using Game.Controls;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using UnityEngine;

namespace Game.UI.CabDisplays
{
    /// <summary>
    /// Reads the cab-screen state from the solver (<see cref="VehicleModel"/>: speed, engine, AMT, air circuits, retarder,
    /// ABS, parking brake), the lamp state (<see cref="TruckLights"/>) and the sun, and runs a small trip computer
    /// (odometer, trip, fuel and AdBlue use, range, tachograph driving time). Read-only towards the physics: nothing here
    /// feeds back into the vehicle. Zero allocations per <see cref="Sample"/>.
    /// </summary>
    public sealed class CabDisplaySource
    {
        // ---- trip computer constants (no fuel model in the solver; display-side estimate) ----
        // Fuel flow: FuelFlowModel (BSFC map over load, idle floor); coolant: CoolantModel (first-order warm-up); clock: GameClock.
        // All WORKING_VALUE, documented in Game.Controls.CabInstrumentModels.
        /// <summary>AdBlue dosing as a share of fuel volume. WORKING_VALUE (SCR Euro VI, typical 3-6 %).</summary>
        public const double AdBlueShare = 0.045;
        /// <summary>Tank sizes of the fictional TRAKT [l]. WORKING_VALUE (not modelled in the art yet).</summary>
        public const float FuelTankLitres = 600f, AdBlueTankLitres = 85f;
        /// <summary>Consumption used for the range until the trip average is meaningful [l/100 km]. WORKING_VALUE.</summary>
        public const float ReferenceConsumption = 30f;
        /// <summary>Trip distance after which the average is shown [km].</summary>
        public const double AverageMinKm = 0.5;

        /// <summary>Outside temperature [deg C] (no weather model yet: scene value). WORKING_VALUE.</summary>
        public float OutsideTempC = 7f;
        /// <summary>Optional clock override (minutes of the day); otherwise the clock follows the scene sun (<see cref="SolarClock"/>).</summary>
        public Func<int> ClockOverride;
        /// <summary>Turn-signal lever fallback (0 off, -1 left, +1 right, 2 hazard) when no <see cref="TruckLights"/> carries the live state.</summary>
        public int Indicators;
        /// <summary>Start coolant temperature [deg C] of a new session (parked after a short stop). WORKING_VALUE.</summary>
        public double CoolantC = 55.0;
        /// <summary>Game clock (anchored to the scene sun, then follows the simulation time).</summary>
        public readonly GameClock Clock = new GameClock();

        public double OdometerKm = 184327.0;   // WORKING_VALUE: start reading of the fictional truck (no save game yet)
        public double TripKm;
        public double FuelLitres = 0.62 * FuelTankLitres;
        public double AdBlueLitres = 0.80 * AdBlueTankLitres;
        public double TripFuelLitres;
        public double DrivingSeconds;

        double m_LastTime = double.NaN;

        /// <summary>Fills <paramref name="s"/>. <paramref name="model"/> may be null (no solver: parked, engine off).</summary>
        public void Sample(VehicleModel model, TrailerModel trailer, bool coupled, TruckLights lights, Transform truck,
            Transform regionFrame, double time, ref CabDisplayState s)
        {
            if (model != null)
            {
                var amt = model.Amt;
                var e = model.Engine;
                s.SpeedKmh = (float)(model.SpeedForward * 3.6);
                s.EngineRunning = !e.Stalled;
                s.EngineRpm = s.EngineRunning ? (float)e.Rpm : 0f;
                s.IdleRpm = (float)e.Def.idleRpm;
                s.MaxRpm = (float)e.Def.maxRpm;
                s.EcoLowRpm = (float)amt.Def.upshiftRpmLight;
                s.EcoHighRpm = (float)amt.Def.upshiftRpmFull;
                s.Gear = amt.Gear;
                bool shifting = amt.State >= AmtState.ShiftTorqueRamp && amt.State <= AmtState.ShiftEngage;
                s.ShiftTarget = shifting ? amt.TargetGear : 0;
                s.ManualMode = amt.Manual;
                s.HillHold = model.HillHoldActive;

                var air = model.Air;
                // Circuit I = front axle, II = rear axle (multi-circuit protection valve order in AirBrakeSystem).
                s.AirCircuit1Bar = (float)air.Front;
                s.AirCircuit2Bar = (float)air.Rear;
                s.AirWarnBar = (float)model.Def.air.lowPressureWarningBar;
                s.AirLowWarning = air.LowPressureWarning;
                s.AbsFault = model.Def.brakes.absEnabled && !air.AbsEnabled;
                s.AbsActive = air.AbsAnyActive;
                s.ParkingBrake = model.ParkingBrakeState > 0.5;
                s.ParkingBrakeWarning = model.ParkingBrakeWarning;
                s.RetarderStages = model.Retarder.Def.present ? model.Retarder.Def.stages : 0;
                s.RetarderFill = (float)model.Retarder.Fill;
                s.TrailerConnected = trailer != null && coupled;
                s.TrailerAbsFault = s.TrailerConnected && trailer.Def.brakes.absEnabled && !trailer.Brakes.AbsEnabled;
            }
            else
            {
                s.SpeedKmh = 0f; s.EngineRunning = false; s.EngineRpm = 0f; s.Gear = 0; s.ShiftTarget = 0;
                s.IdleRpm = 600f; s.MaxRpm = 2100f; s.EcoLowRpm = 1250f; s.EcoHighRpm = 1750f;
                s.ParkingBrake = true; s.ParkingBrakeWarning = false; s.AirWarnBar = 5.5f;
            }

            // ---- trip computer (integrates on the solver clock, so pauses and tests are deterministic) ----
            double dt = double.IsNaN(m_LastTime) ? 0 : Math.Max(0, Math.Min(1.0, time - m_LastTime));
            m_LastTime = time;
            if (model != null && dt > 0)
            {
                double dKm = Math.Abs(model.SpeedForward) * dt / 1000.0;
                OdometerKm += dKm; TripKm += dKm;
                double litres = 0;
                double load = 0;
                if (!model.Engine.Stalled)
                {
                    double powerKw = Math.Max(0, model.EngineTorque * model.Engine.Omega) / 1000.0;
                    load = model.EngineTorque / Math.Max(1.0, PeakTorque(model.Engine.Def));
                    litres = FuelFlowModel.LitresPerHour(powerKw, load) * dt / 3600.0;
                }
                CoolantC = CoolantModel.Step(CoolantC, dt, !model.Engine.Stalled, load, OutsideTempC);
                FuelLitres = Math.Max(0, FuelLitres - litres);
                AdBlueLitres = Math.Max(0, AdBlueLitres - litres * AdBlueShare);
                TripFuelLitres += litres;
                if (Math.Abs(model.SpeedForward) > 0.5) DrivingSeconds += dt;
            }
            s.OdometerKm = OdometerKm;
            s.TripKm = TripKm;
            s.CoolantC = (float)CoolantC;
            s.FuelCapacityLitres = FuelTankLitres;
            s.FuelLitres = (float)FuelLitres;
            s.AdBlueFraction = (float)(AdBlueLitres / AdBlueTankLitres);
            s.AvgConsumption = TripKm >= AverageMinKm ? (float)(TripFuelLitres / TripKm * 100.0) : float.NaN;
            float cons = float.IsNaN(s.AvgConsumption) ? ReferenceConsumption : Mathf.Clamp(s.AvgConsumption, 15f, 80f);
            s.RangeKm = s.FuelLitres / cons * 100f;
            s.DrivingMinutes = (int)(DrivingSeconds / 60.0);

            // ---- driver controls, lamps ----
            bool live = lights != null && lights.indicatorLever != 0;
            s.Indicators = live ? lights.indicatorLever : Indicators;
            // Live: the flasher phase of the stalk (TurnSignal, 1.5 Hz); fallback without a stalk source: same rate on the sim clock.
            s.FlasherOn = s.Indicators != 0 && (live ? lights.flasherLit : (time % 0.667) < 0.333);
            s.ParkingBrakeFlashOn = s.ParkingBrakeWarning && (time % 0.8) < 0.4;
            s.LowBeam = lights != null && lights.LowBeamOn;
            s.HighBeam = lights != null && lights.highBeam;
            // Night mode by the light sensor: sun below the automatic dipped-beam threshold (TruckLights, 6°). The sun
            // light itself may be disabled (overcast preset: no direct light) - its direction still gives the elevation.
            var sun = RenderSettings.sun;
            float threshold = lights != null ? lights.autoLowBeamSunDeg : 6f;
            s.Night = sun != null ? SunElevation(sun) < threshold : s.LowBeam;

            // ---- environment ----
            s.OutsideTempC = OutsideTempC;
            s.ClockMinutes = ClockOverride != null ? ClockOverride() : Clock.Advance(dt, SunClock());

            // ---- position for the navigation ----
            s.HasPosition = truck != null;
            if (truck != null)
            {
                Vector3 p = regionFrame != null ? regionFrame.InverseTransformPoint(truck.position) : truck.position;
                Vector3 f = regionFrame != null ? regionFrame.InverseTransformDirection(truck.forward) : truck.forward;
                s.PosE = p.x; s.PosN = p.z;
                s.HeadingDeg = Mathf.Atan2(f.x, f.z) * Mathf.Rad2Deg;
            }
        }

        /// <summary>Copies the driver's stalk / brake cruise settings (they live in the solver input, not the model).</summary>
        public static void SampleInput(in DriverInput input, ref CabDisplayState s)
        {
            s.RetarderLever = input.RetarderLever;
            s.BrakeCruiseKmh = (float)input.BrakeCruiseKmh;
            s.Selector = input.Selector == GearSelector.Reverse ? 'R' : input.Selector == GearSelector.Neutral ? 'N' : 'D';
            s.ManualMode |= input.ManualMode;
        }

        static double s_PeakDef; static EngineDefinition s_PeakFor;
        static double PeakTorque(EngineDefinition def)
        {
            if (!ReferenceEquals(def, s_PeakFor))
            {
                s_PeakFor = def; s_PeakDef = 1;
                for (int i = 0; i < def.torqueCurveNm.Length; i++) s_PeakDef = Math.Max(s_PeakDef, def.torqueCurveNm[i]);
            }
            return s_PeakDef;
        }

        static float SunElevation(Light sun) => Mathf.Asin(Mathf.Clamp(-sun.transform.forward.y, -1f, 1f)) * Mathf.Rad2Deg;

        static int SunClock()
        {
            var sun = RenderSettings.sun;
            if (sun == null) return (int)(DateTime.Now.TimeOfDay.TotalMinutes);
            Vector3 toSun = -sun.transform.forward;
            float elev = Mathf.Asin(Mathf.Clamp(toSun.y, -1f, 1f)) * Mathf.Rad2Deg;
            float az = Mathf.Atan2(toSun.x, toSun.z) * Mathf.Rad2Deg;
            return SolarClock.LocalMinutes(elev, az);
        }
    }
}
