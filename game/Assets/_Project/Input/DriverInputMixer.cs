using System.Collections.Generic;

namespace Game.Controls
{
    /// <summary>
    /// Combines several <see cref="IDriverInput"/> sources:
    /// - steering: the first source (in priority order) that reports <see cref="DriverIntent.SteerActive"/>;
    ///   if none, the last active source's value is held by the sources themselves (each keeps its own state);
    /// - throttle / brake: maximum over sources (pedal on any device wins);
    /// - one-shot commands: merged (last non-None selector wins, shift deltas summed, toggles OR-ed).
    /// Allocation-free per frame.
    /// </summary>
    public sealed class DriverInputMixer
    {
        readonly List<IDriverInput> m_Sources = new List<IDriverInput>(8);
        DriverIntent[] m_Scratch = new DriverIntent[8];

        /// <summary>Name of the source that steered in the last <see cref="Sample"/> (for the HUD).</summary>
        public string SteeringSource { get; private set; } = "-";

        /// <summary>Adds a source; earlier sources have higher steering priority.</summary>
        public void Add(IDriverInput source)
        {
            m_Sources.Add(source);
            if (m_Scratch.Length < m_Sources.Count) m_Scratch = new DriverIntent[m_Sources.Count * 2];
        }

        public IReadOnlyList<IDriverInput> Sources => m_Sources;

        public DriverIntent Sample(float dt, in VehicleFeedback fb)
        {
            var result = new DriverIntent();
            bool steered = false;
            for (int i = 0; i < m_Sources.Count; i++)
            {
                var s = m_Sources[i];
                ref var it = ref m_Scratch[i];
                it.ClearCommands();
                if (!s.Enabled) { it.SteerActive = false; it.Throttle = 0; it.Brake = 0; continue; }
                s.Sample(dt, fb, ref it);
                if (!steered && it.SteerActive)
                {
                    result.Steer = it.Steer;
                    result.SteerActive = true;
                    steered = true;
                    SteeringSource = s.Name;
                }
                if (it.Throttle > result.Throttle) result.Throttle = it.Throttle;
                if (it.Brake > result.Brake) result.Brake = it.Brake;
                if (it.Selector != SelectorRequest.None) result.Selector = it.Selector;
                result.ShiftDelta += it.ShiftDelta;
                result.ToggleParkingBrake |= it.ToggleParkingBrake;
                result.ToggleManual |= it.ToggleManual;
                result.RetarderDelta += it.RetarderDelta;
                result.ToggleCoupling |= it.ToggleCoupling;
                result.ToggleLandingGear |= it.ToggleLandingGear;
                result.ToggleBrakeCruise |= it.ToggleBrakeCruise;
                result.ToggleReverseCamera |= it.ToggleReverseCamera;
            }
            if (!steered) SteeringSource = "-";
            return result;
        }
    }
}
