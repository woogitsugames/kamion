using System;
using System.Runtime.InteropServices;
using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// ADR 0333: the Windows player opts its process out of Windows power throttling (EcoQoS: lower CPU clocks and
    /// ignored timer-resolution requests for processes whose window is in the background / occluded). Measured s24
    /// (build #5, dw671-tykocin-06, windowed 1600x900 behind another window, other agents' Unity + worldgen at ~25 % CPU):
    /// see ADR 0333 for the A/B numbers. Launch argument <c>-power_throttling default</c> leaves the Windows default
    /// (A/B). No effect in the editor or on other platforms. Logs one <c>[PACING]</c> line.
    /// </summary>
    public static class WindowsPowerThrottling
    {
        const int ProcessPowerThrottling = 4;                 // PROCESS_INFORMATION_CLASS
        const uint ExecutionSpeed = 0x1;                      // PROCESS_POWER_THROTTLING_EXECUTION_SPEED
        const uint IgnoreTimerResolution = 0x4;               // PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION

        [StructLayout(LayoutKind.Sequential)]
        struct PowerThrottlingState { public uint Version; public uint ControlMask; public uint StateMask; }

        /// <summary>Result of the last apply: null = not attempted, true/false = SetProcessInformation result.</summary>
        public static bool? Applied { get; private set; }

        /// <summary>Pure: should the opt-out run for these launch arguments?</summary>
        public static bool WantedByArguments(string[] args)
        {
            if (args == null) return true;
            for (int i = 0; i < args.Length - 1; i++)
                if (string.Equals(args[i], "-power_throttling", StringComparison.OrdinalIgnoreCase)
                    && string.Equals(args[i + 1], "default", StringComparison.OrdinalIgnoreCase)) return false;
            return true;
        }

#if UNITY_STANDALONE_WIN && !UNITY_EDITOR
        [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool SetProcessInformation(IntPtr process, int infoClass, ref PowerThrottlingState info, int size);

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSplashScreen)]
        static void Apply()
        {
            if (!WantedByArguments(Environment.GetCommandLineArgs()))
            {
                Debug.Log("[PACING] power throttling: Windows default (-power_throttling default)");
                return;
            }
            try
            {
                var s = new PowerThrottlingState { Version = 1, ControlMask = ExecutionSpeed | IgnoreTimerResolution, StateMask = 0 };
                bool ok = SetProcessInformation(GetCurrentProcess(), ProcessPowerThrottling, ref s, Marshal.SizeOf<PowerThrottlingState>());
                Applied = ok;
                Debug.Log(ok ? "[PACING] power throttling: off (execution speed + timer resolution, ADR 0333)"
                             : "[PACING] power throttling: SetProcessInformation failed, error " + Marshal.GetLastWin32Error());
            }
            catch (Exception e)   // EntryPointNotFound on Windows < 8 / unexpected marshalling: never block the boot
            {
                Applied = false;
                Debug.LogWarning("[PACING] power throttling: " + e.GetType().Name);
            }
        }
#endif
    }
}
