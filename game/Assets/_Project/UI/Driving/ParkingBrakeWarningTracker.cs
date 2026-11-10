namespace Game.UI.Driving
{
    /// <summary>
    /// Polling logic for the parking-brake drive-away warning (ADR 0004 addendum): turns the physics flag
    /// (<c>VehicleModel.ParkingBrakeWarning</c>) and the chime event counter (<c>ParkingBrakeWarningCount</c>) into a HUD alpha
    /// (full while the flag is on, linear fade over <see cref="FadeSeconds"/> after it clears) and a one-shot chime request
    /// (once per counter increment, however many increments happened between two polls). No allocations.
    /// The first poll only synchronises (a respawn or a new model with a lower counter re-synchronises silently).
    /// </summary>
    public struct ParkingBrakeWarningTracker
    {
        public const float FadeSeconds = 1f;

        bool m_Init, m_Active;
        int m_LastCount;
        float m_ClearedAt;
        float m_Alpha;

        /// <summary>HUD text opacity 0..1 after the last <see cref="Poll"/>.</summary>
        public float Alpha => m_Alpha;

        /// <summary>Polls the model; returns true when the cluster chime should sound now (once per count increment).</summary>
        public bool Poll(bool warning, int count, float now)
        {
            bool chime = false;
            if (!m_Init) { m_Init = true; m_LastCount = count; }
            else if (count > m_LastCount) { chime = true; m_LastCount = count; }
            else if (count < m_LastCount) m_LastCount = count;

            if (warning) { m_Active = true; m_Alpha = 1f; }
            else
            {
                if (m_Active) { m_Active = false; m_ClearedAt = now; }
                m_Alpha = m_Alpha > 0f ? UnityEngine.Mathf.Clamp01(1f - (now - m_ClearedAt) / FadeSeconds) : 0f;
            }
            return chime;
        }

        public void Reset() { m_Init = false; m_Active = false; m_Alpha = 0f; }
    }
}
