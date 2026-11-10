using System;

namespace Game.Controls
{
    /// <summary>
    /// Pure models behind the cluster instruments: fuel flow, coolant temperature, game clock. They live in Game.Controls
    /// only so the EditMode test assembly can reach them (Game.UI is not referenced there); the cab screens
    /// (<c>CabDisplaySource</c>) call them. No Unity types, no allocations. Every constant is WORKING_VALUE (typical Euro VI
    /// 13 l class engine) until measured data replaces it.
    /// </summary>
    public static class FuelFlowModel
    {
        /// <summary>Best-island brake specific fuel consumption [g/kWh]. WORKING_VALUE (typical 190-200).</summary>
        public const double BestBsfcGPerKWh = 198;
        /// <summary>Part-load penalty: bsfc = best * (1 + k (1 - load)^2). k = 0.45 gives ~ +36 % at 10 % load (maps show 250-280 g/kWh there). WORKING_VALUE.</summary>
        public const double PartLoadPenalty = 0.45;
        /// <summary>Idle fuel flow [l/h] (13 l class engine at 600 rpm, typical 2-3). WORKING_VALUE.</summary>
        public const double IdleLitresPerHour = 2.4;
        /// <summary>Diesel density [kg/l] (EN 590: 0.820-0.845).</summary>
        public const double DieselDensity = 0.835;

        /// <summary>BSFC [g/kWh] at a load fraction (torque / full-load torque at that speed, clamped 0.05..1).</summary>
        public static double Bsfc(double load)
        {
            double l = Math.Max(0.05, Math.Min(1.0, load));
            double d = 1.0 - l;
            return BestBsfcGPerKWh * (1.0 + PartLoadPenalty * d * d);
        }

        /// <summary>Fuel flow [l/h] for an engine delivering <paramref name="powerKw"/> at <paramref name="load"/>; never below idle.</summary>
        public static double LitresPerHour(double powerKw, double load)
        {
            if (powerKw <= 0) return IdleLitresPerHour;
            return Math.Max(IdleLitresPerHour, powerKw * Bsfc(load) / 1000.0 / DieselDensity);
        }
    }

    /// <summary>
    /// Coolant temperature, first-order lag towards a target (heat in from the engine load, heat out through the thermostat):
    /// - thermostat closed (below <see cref="ThermostatC"/>): target <see cref="UnregulatedC"/>, time constant
    ///   <see cref="WarmupTauS"/> / (1 + 2 load): about 15 min from 20 C at idle, 6 min under full load;
    /// - thermostat open: regulated target <see cref="RegulatedIdleC"/> + 8 load, time constant <see cref="RegulatedTauS"/>;
    /// - engine off: cools towards the ambient temperature with <see cref="CoolTauS"/>.
    /// All WORKING_VALUE (typical 82-90 C operating band of a heavy diesel; no measurement yet).
    /// </summary>
    public static class CoolantModel
    {
        public const double ThermostatC = 82, UnregulatedC = 96, RegulatedIdleC = 86, RegulatedSpanC = 8;
        public const double WarmupTauS = 540, RegulatedTauS = 45, CoolTauS = 3600;
        /// <summary>Overheat telltale threshold [C] (red thermometer). WORKING_VALUE.</summary>
        public const double WarnC = 105;
        /// <summary>Gauge range [C].</summary>
        public const double GaugeMinC = 40, GaugeMaxC = 120;

        public static double Step(double tempC, double dt, bool running, double load, double ambientC)
        {
            if (dt <= 0) return tempC;
            double l = Math.Max(0, Math.Min(1, load));
            double target, tau;
            if (!running) { target = ambientC; tau = CoolTauS; }
            else if (tempC < ThermostatC) { target = UnregulatedC; tau = WarmupTauS / (1.0 + 2.0 * l); }
            else { target = RegulatedIdleC + RegulatedSpanC * l; tau = RegulatedTauS; }
            return tempC + (target - tempC) * (1.0 - Math.Exp(-dt / tau));
        }
    }

    /// <summary>
    /// Cab clock: minutes of the day advancing with the (simulation) game time at 1:1. It is anchored to the scene sun
    /// (solar clock of the lighting preset) and re-anchored only when the sun-derived time jumps, so a static sun gives a
    /// clock that ticks on in game time, and a future day cycle still drives it.
    /// </summary>
    public sealed class GameClock
    {
        const double ReanchorMinutes = 2.0;
        double m_Minutes;
        int m_LastSun = int.MinValue;
        /// <summary>Game speed relative to real time (1 = real time).</summary>
        public double TimeScale = 1.0;

        /// <summary>Minutes of the day, 0..1440.</summary>
        public double Minutes => m_Minutes;

        /// <summary>Advances by <paramref name="dtSeconds"/> of game time; <paramref name="sunMinutes"/> = clock derived from the sun.</summary>
        public int Advance(double dtSeconds, int sunMinutes)
        {
            if (m_LastSun == int.MinValue || CircularDiff(sunMinutes, m_LastSun) >= ReanchorMinutes)
            {
                m_Minutes = sunMinutes;
                m_LastSun = sunMinutes;
            }
            else m_Minutes += Math.Max(0, dtSeconds) * TimeScale / 60.0;
            m_Minutes %= 1440.0;
            return (int)m_Minutes;
        }

        static double CircularDiff(int a, int b)
        {
            double d = Math.Abs(a - b) % 1440.0;
            return Math.Min(d, 1440.0 - d);
        }
    }
}
