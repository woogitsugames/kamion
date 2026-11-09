using System;

namespace Game.Vehicle.Physics
{
    public enum AmtState { Idle = 0, Launch = 1, Drive = 2, ShiftTorqueRamp = 3, ShiftNeutral = 4, ShiftSync = 5, ShiftEngage = 6 }

    /// <summary>
    /// Automated manual transmission (12-speed) logic: launch-gear choice by mass and grade, clutch
    /// launch control holding a target engine speed, up/down shifts with skip shifts, torque interruption
    /// and rev matching. Runs once per fixed step. Outputs are commands for the driveline solver.
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
        /// <summary>Set by the vehicle each step: ABS is currently modulating a wheel.</summary>
        public bool AbsActive;

        double _timer, _cooldown;
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
            return Def.forwardRatios[gear - 1];
        }

        /// <summary>Total ratio engine -> wheel (signed), 0 in neutral.</summary>
        public double TotalRatio => GearRatio(Gear) * _finalDrive;
        public double Efficiency => Def.efficiency;

        public void ForceState(int gear, bool clutchClosed)
        {
            _lastSelector = gear > 0 ? GearSelector.Drive : (gear < 0 ? GearSelector.Reverse : GearSelector.Neutral);
            Gear = gear;
            TargetGear = gear;
            State = clutchClosed && gear != 0 ? AmtState.Drive : AmtState.Idle;
            ClutchCommand = clutchClosed ? 1 : 0;
            TorqueScale = 1;
            EngineTargetOmega = 0;
            _cooldown = Def.shiftCooldown;
        }

        /// <summary>
        /// Chooses the highest launch gear able to deliver the resistance force with margin.
        /// </summary>
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

        /// <summary>
        /// Update once per fixed step.
        /// drivelineOmega: gearbox-output-referred speed expressed at the wheels (avg driven wheel omega, rad/s).
        /// </summary>
        public void Update(double dt, in DriverInput input, double vehicleSpeed, double drivelineOmega, Engine engine,
            double massKg, double gradeSin, double wheelRadius)
        {
            double throttle = MathUtil.Clamp01(input.Throttle);
            double engOmega = engine.Omega;
            double idle = engine.IdleOmega;
            _cooldown -= dt;

            // --- selector handling ---
            if (input.Selector != _lastSelector)
            {
                bool slow = Math.Abs(vehicleSpeed) < 1.0;
                if (input.Selector == GearSelector.Neutral)
                {
                    Gear = 0; State = AmtState.Idle; ClutchCommand = 0; _lastSelector = input.Selector;
                }
                else if (slow)
                {
                    Gear = 0; State = AmtState.Idle; ClutchCommand = 0; _lastSelector = input.Selector;
                }
                // else: ignore the request until slow enough (keeps current gear).
            }

            if (_lastSelector == GearSelector.Neutral)
            {
                Gear = 0; ClutchCommand = 0; TorqueScale = 1; EngineTargetOmega = 0; State = AmtState.Idle;
                return;
            }

            bool reverse = _lastSelector == GearSelector.Reverse;

            switch (State)
            {
                case AmtState.Idle:
                {
                    TorqueScale = 1; EngineTargetOmega = 0;
                    ClutchCommand = MathUtil.MoveTowards(ClutchCommand, 0, dt * 6);
                    // Pre-select launch gear while standing.
                    int launch = reverse ? -1 : ChooseLaunchGear(massKg, gradeSin, wheelRadius, engine.FullLoadTorque(Def.launchRpmFull * MathUtil.RpmToRadS));
                    if (Math.Abs(vehicleSpeed) < 2.0 || Gear == 0) Gear = launch;
                    if (throttle > 0.02 && engine.Stalled == false) State = AmtState.Launch;
                    else if (!reverse && Gear > 0 && Math.Abs(vehicleSpeed) >= 2.0 && input.Brake < 0.05 && !AbsActive)
                    {
                        // Rolling in D without throttle (e.g. coasting after stop request): pick matching gear and close clutch
                        int g = BestGearForSpeed(drivelineOmega, Def.downshiftRpmLight + 150);
                        if (g > 0) { Gear = g; State = AmtState.Launch; }
                    }
                    break;
                }
                case AmtState.Launch:
                {
                    TorqueScale = 1; EngineTargetOmega = 0;
                    if (AbsActive) { State = AmtState.Idle; break; }
                    double launchOmega = MathUtil.Lerp(Def.launchRpmLight, Def.launchRpmFull, throttle) * MathUtil.RpmToRadS;
                    double slip = engOmega - Math.Abs(TotalRatio) * Math.Abs(drivelineOmega);
                    if (throttle < 0.02 && Math.Abs(vehicleSpeed) < 2.0)
                    {
                        State = AmtState.Idle;
                        break;
                    }
                    // Feed-forward from engine torque + P on engine speed above launch target.
                    double ff = engine.FullLoadTorque(engOmega) * throttle / Def.clutchMaxTorque;
                    double cmd = ff + 0.01 * (engOmega - launchOmega);
                    if (engOmega < idle * 0.95) cmd = Math.Min(cmd, ClutchCommand - dt * 2); // anti-stall
                    cmd = MathUtil.Clamp01(cmd);
                    ClutchCommand = cmd > ClutchCommand ? MathUtil.MoveTowards(ClutchCommand, cmd, dt * 4.0) : MathUtil.MoveTowards(ClutchCommand, cmd, dt * 4);
                    if (Math.Abs(slip) < 4.0 && Math.Abs(drivelineOmega) > 0.5)
                    {
                        State = AmtState.Drive;
                        _cooldown = Def.shiftCooldown;
                    }
                    break;
                }
                case AmtState.Drive:
                {
                    TorqueScale = 1; EngineTargetOmega = 0;
                    ClutchCommand = MathUtil.MoveTowards(ClutchCommand, 1, dt * 3);
                    // Anti-stall: open clutch when the engine is dragged down to idle without throttle,
                    // and whenever ABS is regulating (wheel-lock must not drag the engine down).
                    if ((engOmega < idle * 1.05 && throttle < 0.05) || AbsActive)
                    {
                        State = AmtState.Idle;
                        break;
                    }
                    if (engOmega < idle * 0.9 && (Gear == -1 || Gear <= Def.maxLaunchGear))
                    {
                        State = AmtState.Launch; // slip clutch to recover
                        break;
                    }
                    if (reverse || _cooldown > 0) break;

                    double upRpm = MathUtil.Lerp(Def.upshiftRpmLight, Def.upshiftRpmFull, throttle);
                    double downRpm = MathUtil.Lerp(Def.downshiftRpmLight, Def.downshiftRpmFull, throttle);
                    double rpm = engOmega * MathUtil.RadSToRpm;
                    if (rpm > upRpm && Gear < Def.ForwardGearCount)
                    {
                        double minAfter = MathUtil.Lerp(Def.minRpmAfterUpshiftLight, Def.minRpmAfterUpshiftFull, throttle);
                        int best = 0;
                        for (int k = 1; k <= Def.maxSkip && Gear + k <= Def.ForwardGearCount; k++)
                        {
                            double after = rpm * GearRatio(Gear + k) / GearRatio(Gear);
                            if (after >= minAfter) best = Gear + k;
                        }
                        if (best > 0) BeginShift(best);
                    }
                    else if (rpm < downRpm && Gear > 1)
                    {
                        int target = Gear - 1;
                        for (int k = 1; k <= Def.maxSkip && Gear - k >= 1; k++)
                        {
                            target = Gear - k;
                            double after = rpm * GearRatio(Gear - k) / GearRatio(Gear);
                            if (after >= downRpm + 150) break;
                        }
                        BeginShift(target);
                    }
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
                        State = AmtState.Drive; TorqueScale = 1; ClutchCommand = 1; _cooldown = Def.shiftCooldown;
                    }
                    break;
            }
        }

        public int BestGearForSpeed(double drivelineOmega, double minRpm)
        {
            int best = 0;
            for (int g = 1; g <= Def.ForwardGearCount; g++)
            {
                double rpm = Math.Abs(GearRatio(g) * _finalDrive * drivelineOmega) * MathUtil.RadSToRpm;
                if (rpm >= minRpm && rpm < Def.upshiftRpmFull) best = g;
            }
            return best;
        }

        void BeginShift(int target)
        {
            TargetGear = target;
            State = AmtState.ShiftTorqueRamp;
            _timer = 0;
            ShiftCount++;
        }
    }
}
