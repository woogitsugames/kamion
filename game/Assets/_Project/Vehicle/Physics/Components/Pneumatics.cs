using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Shared pieces of the compressed-air brake model: air bookkeeping and chamber pressure dynamics with the
    /// ABS modulator. Air quantities are in normal litres (free air at 1.013 bar abs); pressures in bar gauge.
    /// </summary>
    public static class Pneumatics
    {
        public const double Atm = 1.013;

        /// <summary>Pressure change of a reservoir of volume V [L] when nl normal litres are added (negative = drawn).</summary>
        public static double DeltaP(double nl, double volumeL) => nl * Atm / volumeL;

        /// <summary>Normal litres needed to raise a volume V by dp.</summary>
        public static double AirFor(double dp, double volumeL) => dp * volumeL / Atm;

        /// <summary>Isothermal flow between two volumes through a conductance [NL/s per bar], explicit but bounded (never overshoots equalisation).</summary>
        public static double Flow(double pFrom, double vFrom, double pTo, double vTo, double conductance, double dt)
        {
            if (pFrom <= pTo) return 0;
            double q = conductance * (pFrom - pTo) * dt;
            // Equalisation limit: after transfer both pressures equal.
            double qEq = (pFrom - pTo) / (Atm / vFrom + Atm / vTo);
            return Math.Min(q, qEq);
        }

        /// <summary>
        /// ABS modulator state machine for one sensed wheel (wheel-speed + wheel-deceleration thresholds, like a
        /// production 4S/4M or 2S/2M system). Modes: 0 apply, 1 hold, 2 dump, 3 slow re-apply.
        /// </summary>
        public static void AbsStep(WheelState w, bool enabled, double slipRelease, double slipReapply,
            double decelThreshold, double reaccelThreshold, double minSpeed, double target)
        {
            if (!enabled || !w.Contact || Math.Abs(w.Vx) < minSpeed || target < 0.3)
            {
                w.AbsMode = 0; w.AbsActive = false;
                return;
            }
            double dir = Math.Sign(w.Vx);
            double slip = -w.KinematicSlip * dir;      // > 0 while braking
            double a = w.TreadAccel * dir;             // < 0 while the wheel decelerates
            // At low speed the relative slip thresholds are paired with an absolute slip-speed floor
            // (otherwise the modulator dumps on tiny speed differences and the last metres lose braking).
            double slipSpeed = slip * Math.Abs(w.Vx);
            if (slipSpeed < 0.6 && slip < 0.5) slip = Math.Min(slip, slipRelease * 0.9);
            switch (w.AbsMode)
            {
                case 0:
                case 3:
                    if (slip > slipRelease) { w.AbsMode = 2; w.AbsActive = true; }
                    else if (a < -decelThreshold && slip > slipReapply) { w.AbsMode = 1; w.AbsActive = true; }
                    else if (w.AbsMode == 3 && w.ChamberPressure >= target - 0.05) { w.AbsMode = 0; w.AbsActive = false; }
                    break;
                case 1:
                    if (slip > slipRelease) w.AbsMode = 2;
                    else if (a > -0.5 * decelThreshold && slip < slipRelease * 0.75) w.AbsMode = 3;
                    break;
                case 2:
                    if (a > reaccelThreshold || slip < slipReapply) w.AbsMode = 1;
                    break;
            }
        }

        /// <summary>
        /// Advances one service chamber. target = requested chamber pressure [bar] (already load-sensed),
        /// supply = pressure of the feeding reservoir. Returns the free air drawn from the supply [NL].
        /// </summary>
        public static double UpdateChamber(WheelState w, double target, double supply, double chamberVolumeL,
            double tauApply, double tauApply2, double tauRelease, double dumpTau, double slowFactor, double dt)
        {
            double limit = Math.Max(0, supply - 0.1);
            if (target > limit) target = limit;
            double p0 = w.ChamberPressure;

            // First stage (line / relay pilot) for cascaded lags.
            double stageTarget = target;
            if (tauApply2 > 0)
            {
                double tl = target > w.LinePressure ? tauApply : tauRelease;
                w.LinePressure = MathUtil.FirstOrder(w.LinePressure, target, tl, dt);
                stageTarget = w.LinePressure;
                tauApply = tauApply2;
            }
            else w.LinePressure = target;

            double p = p0;
            switch (w.AbsMode)
            {
                case 2: p = MathUtil.FirstOrder(p0, 0, dumpTau, dt); break;
                case 1: if (stageTarget < p0) p = MathUtil.FirstOrder(p0, stageTarget, tauRelease, dt); break;
                case 3:
                    p = MathUtil.FirstOrder(p0, stageTarget, stageTarget > p0 ? tauApply * slowFactor : tauRelease, dt);
                    break;
                default:
                    p = MathUtil.FirstOrder(p0, stageTarget, stageTarget > p0 ? tauApply : tauRelease, dt);
                    break;
            }
            if (p > limit && p > p0) p = Math.Max(p0, limit);
            w.ChamberPressure = p;
            return p > p0 ? AirFor(p - p0, chamberVolumeL) : 0;
        }

        /// <summary>Service torque from chamber pressure, spring brake torque from spring chamber pressure; anti-compounding (max).</summary>
        public static double BrakeTorque(WheelState w, double pThreshold, double pMax, double springStart, double springFull)
        {
            double service = w.Axle.serviceBrakeTorque * MathUtil.Clamp01((w.ChamberPressure - pThreshold) / (pMax - pThreshold));
            double spring = 0;
            if (w.Axle.parkingBrakeTorque > 0)
                spring = w.Axle.parkingBrakeTorque * MathUtil.Clamp01((springFull - w.SpringChamberPressure) / (springFull - springStart));
            return Math.Max(service, spring);
        }
    }

    /// <summary>
    /// Tractor air system: compressor + governor, supply reservoir, multi-circuit protection valve, service
    /// circuits 1 (front) and 2 (rear), circuit 3 (spring brakes + trailer supply), trailer control valve,
    /// per-wheel service chambers with EBS load sensing and a 4S/4M ABS, spring-brake chambers, warnings.
    /// </summary>
    public sealed class AirBrakeSystem
    {
        readonly AirSystemDefinition _a;
        readonly BrakeSystemDefinition _b;

        public double Supply, Front, Rear, ParkTrailer;   // bar gauge
        public bool CompressorLoaded;
        public double TrailerSupplyLine, TrailerControlLine; // red / yellow [bar]
        public bool LowPressureWarning;
        /// <summary>Fault injection: leak rates [NL/min] per reservoir (0 supply, 1 front, 2 rear, 3 park/trailer).</summary>
        public readonly double[] LeakLpm = new double[4];
        public double CompressorDeliveredNL, ConsumedNL;
        public bool AbsAnyActive, AbsDriveAxleActive;
        public bool AbsEnabled;
        /// <summary>EBS load sensing active (false = EBS fault, pneumatic back-up without load-dependent pressure).</summary>
        public bool LoadSensingEnabled = true;

        public AirBrakeSystem(AirSystemDefinition air, BrakeSystemDefinition brakes)
        {
            _a = air; _b = brakes;
            AbsEnabled = brakes.absEnabled;
            Charge(air.cutOutBar);
        }

        /// <summary>Sets all tractor reservoirs to a pressure (e.g. charged vehicle at scenario start, or 0 = empty).</summary>
        public void Charge(double bar)
        {
            Supply = Math.Min(bar, _a.cutOutBar);
            Front = Rear = Math.Min(Supply, _a.cutOutBar);
            ParkTrailer = Math.Min(Supply, _a.cutOutBar);
            CompressorLoaded = Supply < _a.cutInBar;
        }

        public double MaxChamberPressure => _b.maxChamberPressureBar;

        /// <summary>
        /// Advances the tractor air system by one fixed step and sets every wheel's brake torque capacity.
        /// serviceDemand: 0..1 service brake demand (after blending / hill hold).
        /// </summary>
        public void Update(double dt, double engineRpm, bool engineRunning, double serviceDemand, bool parkingApplied,
            bool trailerConnected, WheelGroup wheels)
        {
            // --- compressor & governor ---
            double lowest = Math.Min(Supply, Math.Min(Front, Rear));
            if (Supply >= _a.cutOutBar) CompressorLoaded = false;
            else if (lowest < _a.cutInBar || Supply < _a.cutInBar) CompressorLoaded = true;
            if (CompressorLoaded && engineRunning)
            {
                double q = _a.compressorFlowLpm / 60.0 * Math.Max(0, engineRpm) / _a.compressorRatedRpm
                           * Math.Max(0.2, 1 - _a.compressorPressureLossPerBar * Supply) * dt;
                Supply += Pneumatics.DeltaP(q, _a.supplyVolumeL);
                CompressorDeliveredNL += q;
            }

            // --- multi-circuit protection valve ---
            if (Supply >= _a.protectionOpeningBar)
            {
                double q1 = Pneumatics.Flow(Supply, _a.supplyVolumeL, Front, _a.frontVolumeL, _a.circuitConductance, dt);
                Supply -= Pneumatics.DeltaP(q1, _a.supplyVolumeL); Front += Pneumatics.DeltaP(q1, _a.frontVolumeL);
                double q2 = Pneumatics.Flow(Supply, _a.supplyVolumeL, Rear, _a.rearVolumeL, _a.circuitConductance, dt);
                Supply -= Pneumatics.DeltaP(q2, _a.supplyVolumeL); Rear += Pneumatics.DeltaP(q2, _a.rearVolumeL);
                double q3 = Pneumatics.Flow(Supply, _a.supplyVolumeL, ParkTrailer, _a.parkTrailerVolumeL, _a.circuitConductance, dt);
                Supply -= Pneumatics.DeltaP(q3, _a.supplyVolumeL); ParkTrailer += Pneumatics.DeltaP(q3, _a.parkTrailerVolumeL);
            }

            // --- leaks & background consumption ---
            Supply -= Pneumatics.DeltaP((LeakLpm[0] + _a.baselineConsumptionLpm) / 60.0 * dt, _a.supplyVolumeL);
            Front -= Pneumatics.DeltaP(LeakLpm[1] / 60.0 * dt, _a.frontVolumeL);
            Rear -= Pneumatics.DeltaP(LeakLpm[2] / 60.0 * dt, _a.rearVolumeL);
            ParkTrailer -= Pneumatics.DeltaP(LeakLpm[3] / 60.0 * dt, _a.parkTrailerVolumeL);
            ConsumedNL += (LeakLpm[0] + LeakLpm[1] + LeakLpm[2] + LeakLpm[3] + _a.baselineConsumptionLpm) / 60.0 * dt;
            Supply = Math.Max(0, Supply); Front = Math.Max(0, Front); Rear = Math.Max(0, Rear); ParkTrailer = Math.Max(0, ParkTrailer);

            LowPressureWarning = Front < _a.lowPressureWarningBar || Rear < _a.lowPressureWarningBar || ParkTrailer < _a.lowPressureWarningBar;

            // --- trailer lines ---
            TrailerSupplyLine = trailerConnected ? Math.Min(ParkTrailer, _a.trailerSupplyLimitBar) : 0;
            double controlTarget = trailerConnected ? Math.Min(serviceDemand * _a.trailerControlMaxBar, Math.Max(Front, Rear)) : 0;
            TrailerControlLine = MathUtil.FirstOrder(TrailerControlLine, controlTarget, controlTarget > TrailerControlLine ? 0.06 : 0.10, dt);

            // --- spring brake chambers (fed from circuit 3 through the pressure limiter) ---
            _serviceDemand = serviceDemand;
            // (ABS flags keep the previous step until BeginSubsteps: the AMT and the endurance-brake cut-off read them.)
            var ws = wheels.Wheels;
            for (int i = 0; i < ws.Length; i++)
            {
                var w = ws[i];
                var ax = w.Axle;
                if (ax.parkingBrakeTorque <= 0) continue;
                double sTarget = parkingApplied ? 0 : Math.Min(ParkTrailer, _a.trailerSupplyLimitBar);
                double p0 = w.SpringChamberPressure;
                double p = MathUtil.FirstOrder(p0, sTarget, _b.parkingTimeConstant, dt);
                if (p > ParkTrailer && p > p0) p = Math.Max(p0, ParkTrailer);
                w.SpringChamberPressure = p;
                if (p > p0) { double q = Pneumatics.AirFor(p - p0, ax.brakeChamberVolumeL); ParkTrailer -= Pneumatics.DeltaP(q, _a.parkTrailerVolumeL); ConsumedNL += q; }
            }
        }

        double _serviceDemand;

        /// <summary>Resets the per-step ABS activity flags (call before the first substep).</summary>
        public void BeginSubsteps() { AbsAnyActive = false; AbsDriveAxleActive = false; }

        /// <summary>
        /// Service chambers, EBS load sensing and the 4S/4M ABS modulators for one wheel substep h (the ABS loop
        /// runs at the substep rate, ~2.5 ms, so braking does not depend on the fixed step). Sets each wheel's
        /// brake torque capacity (service vs spring brake, anti-compounding).
        /// </summary>
        public void UpdateChambers(double h, WheelGroup wheels)
        {
            double pMax = _b.maxChamberPressureBar;
            var ws = wheels.Wheels;
            for (int i = 0; i < ws.Length; i++)
            {
                var w = ws[i];
                var ax = w.Axle;
                double lsf = 1;
                if (ax.ladenAxleLoadN > 0 && LoadSensingEnabled)
                    lsf = MathUtil.Clamp(wheels.AxleLoadSignal(w.AxleIndex) / ax.ladenAxleLoadN, ax.minLoadSensingFactor, 1.0);
                w.LoadSensingFactor = lsf;
                double target = _serviceDemand * pMax * lsf;
                Pneumatics.AbsStep(w, AbsEnabled, _b.absSlipRelease, _b.absSlipReapply, _b.absDecelThreshold, _b.absReaccelThreshold, _b.absMinSpeedMs, w.ChamberPressure > target ? w.ChamberPressure : target);
                bool rear = ax.brakeCircuit == 2;
                double supply = rear ? Rear : Front;
                double nl = Pneumatics.UpdateChamber(w, target, supply, ax.brakeChamberVolumeL, ax.brakeApplyTimeConstant,
                    ax.brakeApplySecondTimeConstant, ax.brakeReleaseTimeConstant, _b.absDumpTimeConstant, _b.absSlowApplyFactor, h);
                if (rear) Rear -= Pneumatics.DeltaP(nl, _a.rearVolumeL); else Front -= Pneumatics.DeltaP(nl, _a.frontVolumeL);
                ConsumedNL += nl;
                w.BrakePressure = w.ChamberPressure / pMax;
                w.AbsFactor = w.AbsActive ? MathUtil.Clamp01(w.ChamberPressure / Math.Max(target, 1e-6)) : 1;
                w.BrakeTorque = Pneumatics.BrakeTorque(w, _b.thresholdPressureBar, pMax, _a.springReleaseStartBar, _a.springReleaseFullBar);
                if (w.AbsActive) { AbsAnyActive = true; if (w.Driven) AbsDriveAxleActive = true; }
            }
        }

        /// <summary>Spring chambers start released at the given pressure (vehicle parked with brake released and charged).</summary>
        public void InitSpringChambers(WheelGroup wheels, bool applied)
        {
            foreach (var w in wheels.Wheels)
                w.SpringChamberPressure = applied || w.Axle.parkingBrakeTorque <= 0 ? 0 : Math.Min(ParkTrailer, _a.trailerSupplyLimitBar);
        }

        /// <summary>Charges a trailer reservoir through the red line; returns nothing, updates both sides.</summary>
        public void ChargeTrailer(ref double trailerReservoir, double trailerVolumeL, double dt)
        {
            if (TrailerSupplyLine <= 0) return;
            double q = Pneumatics.Flow(TrailerSupplyLine, _a.parkTrailerVolumeL, trailerReservoir, trailerVolumeL, _a.redLineConductance, dt);
            if (q <= 0) return;
            ParkTrailer -= Pneumatics.DeltaP(q, _a.parkTrailerVolumeL);
            trailerReservoir += Pneumatics.DeltaP(q, trailerVolumeL);
        }
    }

    /// <summary>
    /// Trailer brake system: reservoir charged via the red line, relay emergency valve (red-line loss applies the
    /// brakes from the reservoir), control (yellow) line -> relay -> chambers with a longer cascaded lag, EBS load
    /// sensing from the bellows force, 2S/2M ABS (one modulator per side), spring brakes with a trailer park valve.
    /// </summary>
    public sealed class TrailerBrakeSystem
    {
        readonly TrailerBrakeDefinition _d;
        public double Reservoir;
        public bool Emergency;
        public bool ParkValveApplied;
        public double ConsumedNL;
        public bool AbsAnyActive;
        public bool AbsEnabled;
        public bool LoadSensingEnabled = true;
        public double LeakLpm;

        public TrailerBrakeSystem(TrailerBrakeDefinition d)
        {
            _d = d;
            AbsEnabled = d.absEnabled;
            Reservoir = 8.5;
        }

        public double VolumeL => _d.reservoirVolumeL;

        public void Update(double dt, double redLine, double controlLine, WheelGroup wheels)
        {
            if (redLine < _d.emergencyApplyBar) Emergency = true;
            else if (redLine > _d.emergencyReleaseBar) Emergency = false;

            Reservoir -= Pneumatics.DeltaP(LeakLpm / 60.0 * dt, _d.reservoirVolumeL);
            ConsumedNL += LeakLpm / 60.0 * dt;
            if (Reservoir < 0) Reservoir = 0;

            _demandP = Emergency ? _d.maxChamberPressureBar : Math.Min(controlLine * _d.relayGain, _d.maxChamberPressureBar);
            // (ABS flag keeps the previous step until BeginSubsteps.)
            var ws = wheels.Wheels;
            for (int i = 0; i < ws.Length; i++)
            {
                var w = ws[i];
                var ax = w.Axle;
                if (ax.parkingBrakeTorque <= 0) continue;
                double sTarget = ParkValveApplied ? 0 : Math.Min(Reservoir, 8.5);
                double p0 = w.SpringChamberPressure;
                double p = MathUtil.FirstOrder(p0, sTarget, _d.parkingTimeConstant, dt);
                if (p > Reservoir && p > p0) p = Math.Max(p0, Reservoir);
                w.SpringChamberPressure = p;
                if (p > p0) { double q = Pneumatics.AirFor(p - p0, ax.brakeChamberVolumeL); Reservoir -= Pneumatics.DeltaP(q, _d.reservoirVolumeL); ConsumedNL += q; }
            }
        }

        double _demandP;

        /// <summary>Resets the per-step ABS activity flag (call before the first substep).</summary>
        public void BeginSubsteps() { AbsAnyActive = false; }

        /// <summary>Relay output to the chambers, EBS load sensing and ABS for one wheel substep h.</summary>
        public void UpdateChambers(double h, WheelGroup wheels)
        {
            double pMax = _d.maxChamberPressureBar;
            double demandP = _demandP;
            var ws = wheels.Wheels;
            // ABS decisions. Per side (2 modulators): every wheel of the side is sensed and the side's modulator
            // follows the most critical wheel (select-low), so no axle of a tridem can lock unnoticed.
            if (_d.absPerSide)
            {
                for (int side = -1; side <= 1; side += 2)
                {
                    int mode = 0; bool active = false;
                    for (int i = 0; i < ws.Length; i++)
                    {
                        var s = ws[i];
                        if (s.Side != side) continue;
                        double t = demandP * LoadFactor(wheels, s.AxleIndex);
                        Pneumatics.AbsStep(s, AbsEnabled && !Emergency, 0.16, 0.06, 12.0, 4.0, 1.5, s.ChamberPressure > t ? s.ChamberPressure : t);
                        mode = Math.Max(mode, Severity(s.AbsMode));
                        active |= s.AbsActive;
                    }
                    int m = mode == 3 ? 2 : mode == 2 ? 1 : mode == 1 ? 3 : 0;
                    for (int i = 0; i < ws.Length; i++)
                        if (ws[i].Side == side) { ws[i].AbsMode = m; ws[i].AbsActive = active; }
                }
            }
            for (int i = 0; i < ws.Length; i++)
            {
                var w = ws[i];
                var ax = w.Axle;
                double lsf = LoadFactor(wheels, w.AxleIndex);
                w.LoadSensingFactor = lsf;
                double target = demandP * lsf;
                if (!_d.absPerSide)
                    Pneumatics.AbsStep(w, AbsEnabled && !Emergency, 0.16, 0.06, 12.0, 4.0, 1.5, w.ChamberPressure > target ? w.ChamberPressure : target);
                double nl = Pneumatics.UpdateChamber(w, target, Reservoir, ax.brakeChamberVolumeL, ax.brakeApplyTimeConstant,
                    ax.brakeApplySecondTimeConstant, ax.brakeReleaseTimeConstant, 0.045, 3.0, h);
                Reservoir -= Pneumatics.DeltaP(nl, _d.reservoirVolumeL);
                ConsumedNL += nl;
                w.BrakePressure = w.ChamberPressure / pMax;
                w.AbsFactor = w.AbsActive ? MathUtil.Clamp01(w.ChamberPressure / Math.Max(target, 1e-6)) : 1;
                w.BrakeTorque = Pneumatics.BrakeTorque(w, _d.thresholdPressureBar, pMax, _d.springReleaseStartBar, _d.springReleaseFullBar);
                if (w.AbsActive) AbsAnyActive = true;
            }
        }

        /// <summary>Ranks ABS modes: dump (3) > hold (2) > slow re-apply (1) > apply (0).</summary>
        static int Severity(int mode) => mode == 2 ? 3 : mode == 1 ? 2 : mode == 3 ? 1 : 0;

        double LoadFactor(WheelGroup wheels, int axle)
        {
            var ax = wheels.Axles[axle];
            if (ax.ladenAxleLoadN <= 0 || !LoadSensingEnabled) return 1;
            return MathUtil.Clamp(wheels.AxleLoadSignal(axle) / ax.ladenAxleLoadN, ax.minLoadSensingFactor, 1.0);
        }

        public void InitSpringChambers(WheelGroup wheels)
        {
            foreach (var w in wheels.Wheels)
                w.SpringChamberPressure = ParkValveApplied || w.Axle.parkingBrakeTorque <= 0 ? 0 : Math.Min(Reservoir, 8.5);
        }
    }

    /// <summary>Secondary hydrodynamic retarder on the gearbox output.</summary>
    public sealed class Retarder
    {
        public readonly RetarderDefinition Def;
        /// <summary>Fill state 0..1 and braking torque at the gearbox output [N m, positive = braking].</summary>
        public double Fill, Torque, Power;

        public Retarder(RetarderDefinition def) { Def = def; }

        /// <summary>Available torque at shaft speed omega [rad/s] (hydrodynamic n^2 below full-torque speed, power cap above).</summary>
        public double Available(double shaftOmega)
        {
            if (!Def.present) return 0;
            double w = Math.Abs(shaftOmega);
            double wFull = Def.fullTorqueShaftRpm * MathUtil.RpmToRadS;
            double t = Def.maxTorqueNm * Math.Min(1.0, (w / wFull) * (w / wFull));
            if (w > 1e-3) t = Math.Min(t, Def.maxPowerKW * 1000.0 / w);
            return t;
        }

        public void Update(double dt, double command, double shaftOmega)
        {
            command = MathUtil.Clamp01(command);
            Fill = MathUtil.FirstOrder(Fill, command, command > Fill ? Def.fillTimeConstant : Def.drainTimeConstant, dt);
            Torque = Def.present ? Fill * Available(shaftOmega) : 0;
            Power = Torque * Math.Abs(shaftOmega);
        }
    }
}
