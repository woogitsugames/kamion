namespace Game.Core
{
    /// <summary>Vehicle sound cues requested by UI / gameplay that have no physics source yet (ADR 0142).</summary>
    public enum AudioCue { None = 0, HornTap = 1, DoorOpen = 2, DoorClose = 3 }

    /// <summary>
    /// One-slot mailbox from the UI (Game.UI, e.g. the settings preview row) to the vehicle audio (Game.Gameplay), which
    /// does not reference each other. The audio controller polls <see cref="TryTake"/> every frame (no allocation); the
    /// horn hold state is a plain flag set by an input source (keyboard H in the lab).
    /// </summary>
    public static class AudioCues
    {
        static AudioCue s_Pending;

        /// <summary>Horn button held (any input source). Read by the vehicle audio every frame.</summary>
        public static bool HornHeld;

        public static void Request(AudioCue cue) => s_Pending = cue;

        public static bool TryTake(out AudioCue cue)
        {
            cue = s_Pending;
            s_Pending = AudioCue.None;
            return cue != AudioCue.None;
        }
    }
}
