using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Diesel engine: full-load torque LUT, motoring drag LUT, simple boost lag, idle governor,
    /// high-speed governor (torque fade), engine brake (compression release / exhaust pressure governor)
    /// and a speed-target mode used by the AMT for rev matching.
    /// </summary>
    public sealed class Engine
    {
        public readonly EngineDefinition Def;
        public double Omega;          // rad/s
        public double Boost;          // 0..1 boost state (turbo lag)
        public double LastTorque;     // net indicated torque applied this substep [N m]
        public double LastLoad;       // effective fuel demand 0..1
        public bool Stalled;
        /// <summary>Engine brake activation state 0..1 and the retarding torque it adds beyond the motoring drag [N m].</summary>
        public double EngineBrakeState;
        public double EngineBrakeTorque;

        readonly double _idleOmega, _govStart, _maxOmega, _stallOmega;

        public Engine(EngineDefinition def)
        {
            def.Validate();
            Def = def;
            _idleOmega = def.idleRpm * MathUtil.RpmToRadS;
            _govStart = def.governorStartRpm * MathUtil.RpmToRadS;
            _maxOmega = def.maxRpm * MathUtil.RpmToRadS;
            _stallOmega = def.stallRpm * MathUtil.RpmToRadS;
            Omega = _idleOmega;
        }

        public double Rpm => Omega * MathUtil.RadSToRpm;
        public double IdleOmega => _idleOmega;
        public double MaxOmega => _maxOmega;
        public double Inertia => Def.inertia;
        public bool HasEngineBrake => Def.engineBrakeCurveRpm.Length >= 2;

        public double FullLoadTorque(double omega)
        {
            double rpm = omega * MathUtil.RadSToRpm;
            double t = MathUtil.Lut(Def.torqueCurveRpm, Def.torqueCurveNm, rpm);
            if (omega > _govStart)
                t *= MathUtil.Clamp01((_maxOmega - omega) / (_maxOmega - _govStart));
            return t;
        }

        public double DragTorque(double omega) => MathUtil.Lut(Def.dragCurveRpm, Def.dragCurveNm, omega * MathUtil.RadSToRpm);

        /// <summary>Total retarding torque (drag included) at full engine-brake command [N m].</summary>
        public double EngineBrakeTotal(double omega)
        {
            double drag = DragTorque(omega);
            if (!HasEngineBrake) return drag;
            double eb = MathUtil.Lut(Def.engineBrakeCurveRpm, Def.engineBrakeCurveNm, omega * MathUtil.RadSToRpm);
            // Below ~idle the valve actuation fades out (no braking at standstill engine).
            eb *= MathUtil.Clamp01((omega - 0.9 * _idleOmega) / (0.5 * _idleOmega));
            return Math.Max(drag, eb);
        }

        /// <summary>Set by the vehicle each step from AmtController.SyncBrakeRequest: an up-shift is being synchronised with the
        /// engine brake, so the brake may act although a rev-matching target is set (ADR 0134; explicit signal, review P2).</summary>
        public bool SyncBrakeActive;

        /// <summary>Releases the engine brake at once (AMT up-shift sync finished, clutch about to close; ADR 0134).</summary>
        public void CutEngineBrake() => EngineBrakeState = 0;

        /// <summary>Updates the engine-brake actuator (once per fixed step). Command 0..1.</summary>
        public void UpdateEngineBrake(double command, double dt)
        {
            if (!HasEngineBrake || Stalled) command = 0;
            EngineBrakeState = MathUtil.FirstOrder(EngineBrakeState, MathUtil.Clamp01(command), Def.engineBrakeTimeConstant, dt);
            if (EngineBrakeState < 1e-4) EngineBrakeState = 0;
        }

        /// <summary>
        /// Computes the net engine torque for this substep.
        /// demand: accelerator 0..1 (already limited by speed limiter / AMT torque ramp).
        /// targetOmega: when > 0 the engine controller tracks this speed (rev matching during shifts) instead of the pedal.
        /// </summary>
        public double ComputeTorque(double demand, double targetOmega, double dt)
        {
            EngineBrakeTorque = 0;
            if (Stalled)
            {
                LastLoad = 0;
                LastTorque = Omega > 0 ? -DragTorque(Omega) : 0;
                return LastTorque;
            }
            double full = FullLoadTorque(Omega);
            double drag = DragTorque(Omega);
            double load = MathUtil.Clamp01(demand);

            if (targetOmega > 0)
            {
                double err = targetOmega - Omega;
                load = MathUtil.Clamp01(err * 0.05 + drag / Math.Max(full, 1.0));
            }

            double idleErr = _idleOmega - Omega;
            if (idleErr > 0)
            {
                double idleLoad = MathUtil.Clamp01(idleErr * 0.08 + drag / Math.Max(full, 1.0));
                if (idleLoad > load) load = idleLoad;
            }

            Boost = MathUtil.FirstOrder(Boost, load, Def.boostTimeConstant, dt);
            double available = Def.naturallyAspiratedFraction + (1.0 - Def.naturallyAspiratedFraction) * Boost;
            double effLoad = Math.Min(load, available);
            if (Omega >= _maxOmega) effLoad = 0;

            double retard = drag;
            if (EngineBrakeState > 0 && effLoad < 0.02 && (targetOmega <= 0 || SyncBrakeActive))
            {
                // Fuel cut while the engine brake is active (also above a rev-matching target: AMT up-shift sync, ADR 0134).
                double total = EngineBrakeTotal(Omega);
                retard = drag + EngineBrakeState * (total - drag);
                EngineBrakeTorque = retard - drag;
                effLoad = 0;
            }

            LastLoad = effLoad;
            LastTorque = full * effLoad - retard;
            return LastTorque;
        }

        public void CheckStall()
        {
            if (!Stalled && Omega < _stallOmega) Stalled = true;
            if (Omega < 0) Omega = 0;
        }

        /// <summary>Starter: restart a stalled engine (instant for Stage 1/2).</summary>
        public void Restart()
        {
            Stalled = false;
            if (Omega < _idleOmega) Omega = _idleOmega;
        }
    }
}
