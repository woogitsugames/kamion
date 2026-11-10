using System;

namespace Game.Vehicle.Physics
{
    public enum AmtState { Idle = 0, Launch = 1, Drive = 2, ShiftTorqueRamp = 3, ShiftNeutral = 4, ShiftSync = 5, ShiftEngage = 6 }

    /// <summary>
    /// Automated manual transmission (12-speed) logic. Runs once per fixed step and commands the driveline solver.
    ///
    /// Auto mode: launch gear and launch speed from mass and grade; up-shifts only when the truck can still
    /// accelerate in the new gear (tractive force vs. grade + rolling + aero resistance); skip shifts when light;
    /// a grade bonus keeps the engine in its torque plateau on climbs; engine-brake mode holds the engine in the
    /// braking band; an over-rev guard bypasses the anti-hunting hold-off. Every shift interrupts torque
    /// (ramp-down, neutral, synchronisation by rev matching, clutch close).
    /// Manual mode: the driver picks the gear (ShiftUp/ShiftDown edges); the AMT rejects shifts that would over-rev
    /// or lug the engine, protects against stalling and still operates the clutch.
    /// Clutch thermal model: energy from slip, temperature with a first-order cooling.
    /// </summary>
    public sealed class AmtController
    {
        public readonly GearboxDefinition Def;
        readonly double _finalDrive;

        /// <summary>Engaged gear: 0 = neutral, 1..N forward, -1 reverse.</summary>
        public int Gear { get; private set; }
        public AmtState State { get; private set; }
        /// <summary>Clutch engagement command 0..1 (fraction of capacity).</summary>
        public double ClutchCommand { get; private set; }
        /// <summary>Multiplier applied to the accelerator demand (torque interruption during shifts).</summary>
        public double TorqueScale { get; private set; } = 1;
        /// <summary>Engine speed target for rev matching (rad/s), 0 = none.</summary>
        public double EngineTargetOmega { get; private set; }
        public int TargetGear { get; private set; }
        public int ShiftCount { get; private set; }
        public int RejectedShiftCount { get; private set; }
        public bool Manual { get; private set; }
        /// <summary>Set by the vehicle each step: ABS is currently modulating a wheel.</summary>
        public bool AbsActive;
        /// <summary>Set by the vehicle each step: the driver requests endurance braking (engine brake).</summary>
        public bool EngineBrakeRequest;

        public double ClutchTempC { get; private set; } = 25;
        public double ClutchEnergyJ { get; private set; }
        public bool ClutchOverheat => ClutchTempC > Def.clutchWarnTempC;

        double _timer, _sinceUpshift = 100, _sinceShift = 100;
        double _rpmRate, _prevRpm;
        bool _rpmRateValid; // false until the first Update after construction / ForceState (no 0 -> rpm spike)
        bool _prevUp, _prevDown;
        int _manualGear;
        GearSelector _lastSelector = GearSelector.Neutral;

        public AmtController(GearboxDefinition def, double finalDrive)
        {
            def.Validate();
            Def = def;
            _finalDrive = finalDrive;
        }

        public double GearRatio(int gear)
        {
            if (gear == 0) return 0;
            if (gear < 0) return -Def.reverseRatio;
            return Def.forwardRatios[Math.Min(gear, Def.ForwardGearCount) - 1];
        }

        /// <summary>Total ratio engine -> wheel (signed), 0 in neutral.</summary>
        public double TotalRatio => GearRatio(Gear) * _finalDrive;
        public double Efficiency => Def.efficiency;

        public void ForceState(int gear, bool clutchClosed)
        {
            _lastSelector = gear > 0 ? GearSelector.Drive : (gear < 0 ? GearSelector.Reverse : GearSelector.Neutral);
            Gear = gear;
            TargetGear = gear;
            _manualGear = Math.Max(1, gear);
            State = clutchClosed && gear != 0 ? AmtState.Drive : AmtState.Idle;
            ClutchCommand = clutchClosed ? 1 : 0;
            TorqueScale = 1;
            EngineTargetOmega = 0;
            _sinceUpshift = _sinceShift = Def.shiftCooldown;
            _rpmRateValid = false;
        }

        /// <summary>Chooses the highest launch gear able to deliver the resistance force with margin.</summary>
        public int ChooseLaunchGear(double massKg, double gradeSin, double wheelRadius, double fullLoadTorqueAtLaunch)
        {
            double need = massKg * 9.81 * (Math.Max(gradeSin, 0) + 0.012) * 2.5; // 2.5x margin (WORKING_VALUE)
            int best = 1;
            for (int g = 1; g <= Math.Min(Def.maxLaunchGear, Def.ForwardGearCount); g++)
            {
                double f = fullLoadTorqueAtLaunch * 0.6 * GearRatio(g) * _finalDrive * Def.efficiency / wheelRadius;
                if (f >= need) best = g;
            }
            return best;
        }

        /// <summary>Tractive force at the wheels in a gear at an engine speed and load fraction [N].</summary>
        double Tractive(Engine engine, int gear, double omega, double load, double wheelRadius, double fdEff) =>
            engine.FullLoadTorque(omega) * load * Math.Abs(GearRatio(gear)) * _finalDrive * Def.efficiency * fdEff / wheelRadius;

        /// <summary>
        /// Update once per fixed step.
        /// drivelineOmega: mean driven-wheel speed (rad/s). resistanceForce: grade + rolling + aero resistance [N]
        /// (positive opposes forward motion), used by the mass/grade-aware shift strategy.
        /// </summary>
        public void Update(double dt, in DriverInput input, double vehicleSpeed, double drivelineOmega, Engine engine,
            double massKg, double gradeSin, double wheelRadius, double resistanceForce = 0, double finalDriveEfficiency = 0.97)
        {
            double throttle = MathUtil.Clamp01(input.Throttle);
            double engOmega = engine.Omega;
            double rpm = engOmega * MathUtil.RadSToRpm;
            double idle = engine.IdleOmega;
            _sinceUpshift += dt; _sinceShift += dt;
            if (!_rpmRateValid) { _prevRpm = rpm; _rpmRate = 0; _rpmRateValid = true; }
            double rr = (rpm - _prevRpm) / dt;
            _rpmRate += (rr - _rpmRate) * Math.Min(1.0, dt / 0.15);
            _prevRpm = rpm;

            // --- mode & manual requests (edge-triggered) ---
            if (input.ManualMode != Manual)
            {
                Manual = input.ManualMode;
                _manualGear = Gear > 0 ? Gear : Math.Max(1, _manualGear);
            }
            bool upEdge = input.ShiftUp && !_prevUp, downEdge = input.ShiftDown && !_prevDown;
            _prevUp = input.ShiftUp; _prevDown = input.ShiftDown;

            // --- selector handling ---
            if (input.Selector != _lastSelector)
            {
                bool slow = Math.Abs(vehicleSpeed) < 1.0;
                if (input.Selector == GearSelector.Neutral || slow)
                {
                    Gear = 0; State = AmtState.Idle; ClutchCommand = 0; _lastSelector = input.Selector;
                }
            }

            if (_lastSelector == GearSelector.Neutral)
            {
                Gear = 0; ClutchCommand = 0; TorqueScale = 1; EngineTargetOmega = 0; State = AmtState.Idle;
                return;
            }

            bool reverse = _lastSelector == GearSelector.Reverse;
            bool ebMode = EngineBrakeRequest && throttle < 0.02 && !reverse;

            switch (State)
            {
                case AmtState.Idle:
                {
                    TorqueScale = 1; EngineTargetOmega = 0;
                    ClutchCommand = MathUtil.MoveTowards(ClutchCommand, 0, dt * 6);
                    int launch;
                    if (reverse) launch = -1;
                    else if (Manual)
                    {
                        if (upEdge) _manualGear = Math.Min(_manualGear + 1, Def.maxLaunchGear);
                        if (downEdge) _manualGear = Math.Max(_manualGear - 1, 1);
                        launch = _manualGear;
                    }
                    else launch = ChooseLaunchGear(massKg, gradeSin, wheelRadius, engine.FullLoadTorque(Def.launchRpmFull * MathUtil.RpmToRadS));
                    if (Math.Abs(vehicleSpeed) < 2.0 || Gear == 0) Gear = launch;
                    if (throttle > 0.02 && !engine.Stalled) State = AmtState.Launch;
                    else if (!reverse && Gear > 0 && Math.Abs(vehicleSpeed) >= 2.0 && input.Brake < 0.05 && !AbsActive)
                    {
                        // Rolling in D without throttle: pick the matching gear and close the clutch (coasting / engine braking).
                        double minRpm = ebMode ? Def.engineBrakeDownshiftRpm : Def.downshiftRpmLight + 150;
                        int g = BestGearForSpeed(drivelineOmega, minRpm, ebMode ? Def.engineBrakeUpshiftRpm : Def.upshiftRpmFull);
                        if (g > 0) { Gear = g; _manualGear = g; State = AmtState.Launch; }
                    }
                    break;
                }
                case AmtState.Launch:
                {
                    TorqueScale = 1; EngineTargetOmega = 0;
                    if (AbsActive) { State = AmtState.Idle; break; }
                    // Launch speed rises with the force the start needs (heavy / uphill).
                    double needF = massKg * 9.81 * (Math.Max(gradeSin, 0) + 0.008);
                    double haveF = Tractive(engine, Math.Max(1, Math.Abs(Gear)), Def.launchRpmFull * MathUtil.RpmToRadS, 1.0, wheelRadius, finalDriveEfficiency);
                    double loadFrac = haveF > 0 ? MathUtil.Clamp01(needF / haveF) : 0;
                    double launchOmega = (MathUtil.Lerp(Def.launchRpmLight, Def.launchRpmFull, throttle) + Def.launchRpmLoadBonus * loadFrac * throttle) * MathUtil.RpmToRadS;
                    double slip = engOmega - Math.Abs(TotalRatio) * Math.Abs(drivelineOmega);
                    if (throttle < 0.02 && Math.Abs(vehicleSpeed) < 2.0)
                    {
                        State = AmtState.Idle;
                        break;
                    }
                    double ff = engine.FullLoadTorque(engOmega) * throttle / Def.clutchMaxTorque;
                    double cmd = ff + 0.01 * (engOmega - launchOmega);
                    if (throttle < 0.02) cmd = 1; // rolling engagement (coast / engine brake)
                    // Creep function: with a small pedal the clutch transmits a fixed creep torque at idle
                    // (manoeuvring, coupling); the idle governor supplies it.
                    else if (throttle < Def.creepPedal) cmd = Math.Max(cmd, Def.creepTorqueNm / Def.clutchMaxTorque);
                    if (engOmega < idle * 0.95) cmd = Math.Min(cmd, ClutchCommand - dt * 2); // anti-stall
                    cmd = MathUtil.Clamp01(cmd);
                    ClutchCommand = MathUtil.MoveTowards(ClutchCommand, cmd, dt * 4.0);
                    // Close only when the clutch is synchronous AND the drive wheels are not spinning (the
                    // engine-to-road slip, referenced to vehicle speed, is small): a launch with wheelspin keeps slipping the clutch.
                    double roadSlip = engOmega - Math.Abs(TotalRatio) * Math.Abs(vehicleSpeed) / wheelRadius;
                    if (Math.Abs(slip) < 4.0 && Math.Abs(drivelineOmega) > 0.5 && roadSlip < 0.15 * engOmega + 8.0)
                    {
                        State = AmtState.Drive;
                        _sinceShift = 0;
                    }
                    break;
                }
                case AmtState.Drive:
                {
                    TorqueScale = 1; EngineTargetOmega = 0;
                    ClutchCommand = MathUtil.MoveTowards(ClutchCommand, 1, dt * 3);
                    // Anti-stall: open the clutch when the engine is dragged down to idle without throttle,
                    // and whenever ABS is regulating (wheel lock must not drag the engine down).
                    if ((engOmega < idle * 1.05 && throttle < 0.05) || AbsActive)
                    {
                        State = AmtState.Idle;
                        break;
                    }
                    if (engOmega < idle * 0.9 && (Gear == -1 || Gear <= Def.maxLaunchGear))
                    {
                        State = AmtState.Launch;
                        break;
                    }
                    if (reverse) break;
                    if (Manual) ManualDrive(rpm, upEdge, downEdge, engine);
                    else AutoDrive(rpm, throttle, ebMode, engine, massKg, gradeSin, wheelRadius, resistanceForce, finalDriveEfficiency, vehicleSpeed);
                    break;
                }
                case AmtState.ShiftTorqueRamp:
                    _timer += dt;
                    TorqueScale = 1 - MathUtil.Clamp01(_timer / Def.shiftTorqueRampTime);
                    if (_timer >= Def.shiftTorqueRampTime) { State = AmtState.ShiftNeutral; _timer = 0; }
                    break;
                case AmtState.ShiftNeutral:
                    _timer += dt;
                    TorqueScale = 0;
                    ClutchCommand = MathUtil.MoveTowards(ClutchCommand, 0, dt / Math.Max(0.02, Def.shiftNeutralTime * 0.5));
                    if (_timer >= Def.shiftNeutralTime) { Gear = 0; State = AmtState.ShiftSync; _timer = 0; }
                    break;
                case AmtState.ShiftSync:
                    _timer += dt;
                    ClutchCommand = 0;
                    TorqueScale = 0;
                    EngineTargetOmega = Math.Max(idle, Math.Abs(GearRatio(TargetGear) * _finalDrive * drivelineOmega));
                    if (_timer >= Def.shiftSyncTime) { Gear = TargetGear; State = AmtState.ShiftEngage; _timer = 0; }
                    break;
                case AmtState.ShiftEngage:
                    _timer += dt;
                    EngineTargetOmega = 0;
                    double f = MathUtil.Clamp01(_timer / Def.shiftClutchCloseTime);
                    ClutchCommand = f;
                    TorqueScale = f;
                    if (_timer >= Def.shiftClutchCloseTime)
                    {
                        State = AmtState.Drive; TorqueScale = 1; ClutchCommand = 1;
                    }
                    break;
            }
        }

        void AutoDrive(double rpm, double throttle, bool ebMode, Engine engine, double massKg, double gradeSin,
            double wheelRadius, double resistance, double fdEff, double speed)
        {
            double govRpm = engine.Def.governorStartRpm;
            bool overRev = !ebMode && rpm > govRpm - 50 && throttle > 0.05;
            bool ebOverRev = ebMode && rpm > Def.engineBrakeUpshiftRpm;
            if (!overRev && !ebOverRev && _sinceShift < Def.sameDirectionCooldown) return;

            // ---------- up-shift ----------
            double upRpm = ebMode ? Def.engineBrakeUpshiftRpm : MathUtil.Lerp(Def.upshiftRpmLight, Def.upshiftRpmFull, throttle);
            // Predict where the engine will be when the torque comes back (shift duration x rpm rate).
            double shiftDur = Def.shiftTorqueRampTime + Def.shiftNeutralTime;
            double rpmPred = rpm + Math.Max(0, _rpmRate) * shiftDur;
            // Effective down-shift line (incl. grade bonus): an up-shift must land clearly above it, or it hunts.
            double downLine = MathUtil.Lerp(Def.downshiftRpmLight, Def.downshiftRpmFull, throttle);
            if (gradeSin > Def.gradeDownshiftThreshold && throttle > 0.5) downLine += Def.gradeDownshiftBonusRpm;
            // Speed lost during the torque interruption (resistance only, no drive) -> rpm after the shift is lower.
            double totalShift = Def.shiftTorqueRampTime + Def.shiftNeutralTime + Def.shiftSyncTime + Def.shiftClutchCloseTime * 0.5;
            double dv = Math.Max(0, resistance) / Math.Max(massKg, 1) * totalShift;
            double speedFactor = speed > 0.5 ? Math.Max(0.5, 1 - dv / speed) : 1;
            if (Gear < Def.ForwardGearCount && (rpmPred > upRpm || overRev || ebOverRev))
            {
                double minAfter = ebMode ? Def.engineBrakeDownshiftRpm + 100 : Math.Max(MathUtil.Lerp(Def.minRpmAfterUpshiftLight, Def.minRpmAfterUpshiftFull, throttle), downLine + 100);
                int best = 0;
                for (int k = 1; k <= Def.maxSkip && Gear + k <= Def.ForwardGearCount; k++)
                {
                    double after = rpm * GearRatio(Gear + k) / GearRatio(Gear) * (ebMode ? 1 : speedFactor);
                    if (after < minAfter && !(k == 1 && (overRev || ebOverRev))) continue;
                    if (!ebMode && throttle > 0.3)
                    {
                        // Mass/grade awareness: the truck must still accelerate in the new gear.
                        double fAfter = Tractive(engine, Gear + k, after * MathUtil.RpmToRadS, throttle, wheelRadius, fdEff);
                        double accel = (fAfter - resistance) / Math.Max(massKg, 1);
                        // At the governor the next gear is taken even with little reserve, but only if it can at
                        // least hold the speed: on a steep climb the engine stays on the governor instead of
                        // up-shifting into a gear that drops back down (4-5-4 hunting at 12 %, ADR 0024).
                        if (accel < Def.minAccelAfterUpshift * throttle && !(k == 1 && overRev && accel >= 0)) continue;
                    }
                    best = Gear + k;
                }
                if (best > 0) { BeginShift(best); return; }
            }

            // ---------- down-shift ----------
            if (Gear <= 1) return;
            double downRpm;
            if (ebMode)
            {
                if (speed < 15 / 3.6) return; // no engine-brake downshifts at walking pace
                downRpm = Def.engineBrakeDownshiftRpm;
            }
            else
            {
                downRpm = MathUtil.Lerp(Def.downshiftRpmLight, Def.downshiftRpmFull, throttle);
                if (gradeSin > Def.gradeDownshiftThreshold && throttle > 0.5) downRpm += Def.gradeDownshiftBonusRpm;
            }
            // Down-shift hold while pulling (ADR 0024). The up-shift only picks a gear in which the truck still
            // accelerates by at least minAccelAfterUpshift x throttle; the down-shift is the exact mirror: while the
            // same force balance (full-load torque x throttle in the current gear minus grade + rolling + aero) still
            // gives that acceleration, the engine is pulling, not lugging, and a shift would only cost a torque
            // interruption on the grade and bring the up-shift straight back (3-2-3 after an ASR-limited hill start,
            // 5-4-5 on 12 %). Model-based on purpose: the measured rpm trend is distorted for ~0.5 s after every clutch
            // close. If the model is optimistic (ASR, wrong mass) the engine keeps falling and the lugging guard below
            // fires; it judges the engine speed one shift duration ahead (mirror of the up-shift rpm prediction), so a
            // fast-rising engine just after the launch clutch closes is not "lugging", a falling one downshifts at once.
            // Not in engine-brake mode: there a rising rpm means the truck runs away downhill and wants the lower gear.
            bool pulling = !ebMode && throttle > 0.3 &&
                (Tractive(engine, Gear, rpm * MathUtil.RpmToRadS, throttle, wheelRadius, fdEff) - resistance) / Math.Max(massKg, 1)
                >= Def.minAccelAfterUpshift * throttle;
            double rpmDown = ebMode ? rpm : rpm + Math.Max(0, _rpmRate) * totalShift;
            bool lugging = rpmDown < downRpm - 150;
            if (rpm < downRpm && (lugging || (!pulling && _sinceUpshift > Def.shiftCooldown)))
            {
                double ceiling = ebMode ? Def.engineBrakeUpshiftRpm - 100 : MathUtil.Lerp(Def.upshiftRpmLight, Def.upshiftRpmFull, throttle) - 100;
                int target = Gear - 1;
                for (int k = 1; k <= Def.maxSkip && Gear - k >= 1; k++)
                {
                    double after = rpm * GearRatio(Gear - k) / GearRatio(Gear);
                    if (after > ceiling && k > 1) break;
                    target = Gear - k;
                    if (after >= downRpm + 150) break;
                }
                BeginShift(target);
            }
        }

        void ManualDrive(double rpm, bool upEdge, bool downEdge, Engine engine)
        {
            double maxRpm = engine.Def.maxRpm;
            if (upEdge && Gear < Def.ForwardGearCount)
            {
                double after = rpm * GearRatio(Gear + 1) / GearRatio(Gear);
                if (after >= Def.manualMinRpmAfterShift) { BeginShift(Gear + 1); _manualGear = Gear + 1; return; }
                RejectedShiftCount++;
            }
            if (downEdge && Gear > 1)
            {
                double after = rpm * GearRatio(Gear - 1) / GearRatio(Gear);
                if (after <= maxRpm) { BeginShift(Gear - 1); _manualGear = Gear - 1; return; }
                RejectedShiftCount++;
            }
            // Protection: a manual box would stall here; the AMT downshifts on its own.
            if (rpm < Def.manualProtectDownshiftRpm && Gear > 1 && _sinceShift > Def.sameDirectionCooldown)
            {
                BeginShift(Gear - 1);
                _manualGear = Gear - 1;
            }
        }

        /// <summary>Clutch heating from the slip power of the last step [W].</summary>
        public void UpdateClutchThermal(double slipPowerW, double dt, double ambientC = 25)
        {
            ClutchEnergyJ += slipPowerW * dt;
            ClutchTempC += (slipPowerW / Def.clutchHeatCapacity - (ClutchTempC - ambientC) / Def.clutchCoolingTimeConstant) * dt;
        }

        public int BestGearForSpeed(double drivelineOmega, double minRpm) => BestGearForSpeed(drivelineOmega, minRpm, Def.upshiftRpmFull);

        public int BestGearForSpeed(double drivelineOmega, double minRpm, double maxRpm)
        {
            int best = 0;
            for (int g = 1; g <= Def.ForwardGearCount; g++)
            {
                double rpm = Math.Abs(GearRatio(g) * _finalDrive * drivelineOmega) * MathUtil.RadSToRpm;
                if (rpm >= minRpm && rpm < maxRpm) best = g;
            }
            return best;
        }

        void BeginShift(int target)
        {
            if (target > Gear) _sinceUpshift = 0;
            _sinceShift = 0;
            TargetGear = target;
            State = AmtState.ShiftTorqueRamp;
            _timer = 0;
            ShiftCount++;
        }
    }
}
