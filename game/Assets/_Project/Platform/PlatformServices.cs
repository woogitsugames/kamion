using System;

namespace Game.Platform
{
    public static class PlatformServices
    {
        public static IPlatformServices Create()
        {
#if UNITY_ANDROID && !UNITY_EDITOR
            try
            {
                return new AndroidPlatformServices();
            }
            catch (Exception e)
            {
                UnityEngine.Debug.LogWarning($"[Platform] Android services unavailable, using defaults: {e.Message}");
            }
#endif
            return new DefaultPlatformServices();
        }
    }

    /// <summary>Editor/desktop fallback: no sensors, launch args from the command line.</summary>
    public sealed class DefaultPlatformServices : IPlatformServices
    {
        public string Name => "default";
        public float? GetBatteryTemperatureC() => null;
        public int? GetThermalStatus() => null;
        public float? GetThermalHeadroom() => null;
        public long? GetProcessPssKb() => null;

        public string GetLaunchArgument(string key)
        {
            var args = Environment.GetCommandLineArgs();
            string flag = "-" + key;
            for (int i = 0; i < args.Length - 1; i++)
                if (string.Equals(args[i], flag, StringComparison.OrdinalIgnoreCase))
                    return args[i + 1];
            return null;
        }
    }
}
