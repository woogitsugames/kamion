using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Diesel engine: full-load torque LUT, motoring drag LUT, simple boost lag, idle governor,
    /// high-speed governor (torque fade) and a speed-target mode used by the AMT for rev matching.
    /// </summary>
    public sealed class Engine
    {
        public readonly EngineDefinition Def;
        public double Omega;          // rad/s
        public double Boost;          // 0..1 boost state (turbo lag)
        public double LastTorque;     // net indicated torque applied this substep [N m]
        public double LastLoad;       // effective fuel demand 0..1
        public bool Stalled;

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
        public double Inertia => Def.inertia;

        public double FullLoadTorque(double omega)
        {
            double rpm = omega * MathUtil.RadSToRpm;
            double t = MathUtil.Lut(Def.torqueCurveRpm, Def.torqueCurveNm, rpm);
            if (omega > _govStart)
                t *= MathUtil.Clamp01((_maxOmega - omega) / (_maxOmega - _govStart));
            return t;
        }

        public double DragTorque(double omega) => MathUtil.Lut(Def.dragCurveRpm, Def.dragCurveNm, omega * MathUtil.RadSToRpm);

        /// <summary>
        /// Computes the net engine torque for this substep.
        /// demand: accelerator 0..1 (already limited by speed limiter / AMT torque ramp).
        /// targetOmega: when > 0 the engine controller tracks this speed (rev matching during shifts) instead of the pedal.
        /// </summary>
        public double ComputeTorque(double demand, double targetOmega, double dt)
        {
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
                // P controller on speed, expressed as load fraction.
                double err = targetOmega - Omega;
                load = MathUtil.Clamp01(err * 0.05 + drag / Math.Max(full, 1.0));
            }

            // Idle governor: never let fuelling drop below what keeps idle speed.
            double idleErr = _idleOmega - Omega;
            if (idleErr > 0)
            {
                double idleLoad = MathUtil.Clamp01(idleErr * 0.08 + drag / Math.Max(full, 1.0));
                if (idleLoad > load) load = idleLoad;
            }

            // Turbo lag: boost follows load with a first-order lag; available torque fraction
            // = NA fraction + (1 - NA) * boost.
            Boost = MathUtil.FirstOrder(Boost, load, Def.boostTimeConstant, dt);
            double available = Def.naturallyAspiratedFraction + (1.0 - Def.naturallyAspiratedFraction) * Boost;
            double effLoad = Math.Min(load, available);
            if (Omega >= _maxOmega) effLoad = 0;

            LastLoad = effLoad;
            LastTorque = full * effLoad - drag;
            return LastTorque;
        }

        public void CheckStall()
        {
            if (!Stalled && Omega < _stallOmega) Stalled = true;
            if (Omega < 0) Omega = 0;
        }

        /// <summary>Starter: restart a stalled engine (instant for Stage 1).</summary>
        public void Restart()
        {
            Stalled = false;
            if (Omega < _idleOmega) Omega = _idleOmega;
        }
    }
}
