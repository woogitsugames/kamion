namespace Game.Platform
{
    /// <summary>
    /// Platform-specific device queries. Game logic talks only to this interface;
    /// Android/iOS calls live in the implementations. Every query may return null
    /// when the platform cannot provide the value. Calls may be slow (JNI) — poll at ~0.5 Hz.
    /// </summary>
    public interface IPlatformServices
    {
        string Name { get; }

        /// <summary>Battery temperature in degrees Celsius.</summary>
        float? GetBatteryTemperatureC();

        /// <summary>OS thermal status (Android PowerManager THERMAL_STATUS_*: 0 none … 6 shutdown).</summary>
        int? GetThermalStatus();

        /// <summary>Thermal headroom forecast (Android 11+): 1.0 ≈ throttling threshold.</summary>
        float? GetThermalHeadroom();

        /// <summary>Proportional set size of the app process in KiB.</summary>
        long? GetProcessPssKb();

        /// <summary>Launch argument (Android intent string extra, desktop "-key value").</summary>
        string GetLaunchArgument(string key);
    }

    public static class ThermalStatusNames
    {
        static readonly string[] k_Names = { "none", "light", "moderate", "severe", "critical", "emergency", "shutdown" };

        public static string Get(int? status)
        {
            if (!status.HasValue) return "n/a";
            int s = status.Value;
            return s >= 0 && s < k_Names.Length ? k_Names[s] : s.ToString();
        }
    }
}
