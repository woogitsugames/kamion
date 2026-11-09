using System.Globalization;
using Game.Core;
using Game.Platform;
using Game.Rendering;
using Game.Telemetry;
using Game.UI;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Composition root of the Boot scene: creates platform services, applies quality tier and
    /// frame-rate target (launch args → saved prefs → defaults), starts diagnostics sampling and
    /// the overlay. Launch args: Android intent extras (adb shell am start ... -e tier Low -e fps 60)
    /// or desktop "-tier Low -fps 60".
    /// </summary>
    [DefaultExecutionOrder(-1000)]
    public sealed class GameBootstrap : MonoBehaviour
    {
        [SerializeField] int defaultTargetFps = 30;
        [SerializeField] bool showOverlay = true;

        public IPlatformServices Platform { get; private set; }

        void Awake()
        {
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            Platform = PlatformServices.Create();

            string tierArg = Platform.GetLaunchArgument("tier");
            if (!QualityTiers.Apply(tierArg)) QualityTiers.Apply(QualityTiers.SavedTier);

            int fps = defaultTargetFps;
            if (int.TryParse(Platform.GetLaunchArgument("fps"), NumberStyles.Integer, CultureInfo.InvariantCulture, out int argFps) && argFps > 0)
                fps = argFps;
            else if (QualityTiers.SavedFrameRate > 0)
                fps = QualityTiers.SavedFrameRate;
            QualityTiers.SetTargetFrameRate(fps);

            var build = BuildInfo.Current;
            Debug.Log($"[BOOT] Kamion {build.ShortLabel} unity={build.unityVersion} platform={Platform.Name} " +
                      $"device='{SystemInfo.deviceModel}' gpu='{SystemInfo.graphicsDeviceName}' api='{SystemInfo.graphicsDeviceVersion}' " +
                      $"ram={SystemInfo.systemMemorySize}MB screen={Screen.width}x{Screen.height} tier={QualityTiers.Current} targetFps={fps}");

            var sampler = gameObject.AddComponent<DiagnosticsSampler>();
            sampler.Initialize(Platform);
            Debug.Log($"[BOOT] diagnostics output: {sampler.OutputDirectory}");

            if (showOverlay)
            {
                var cam = Camera.main;
                var overlay = DiagnosticsOverlay.Create(cam, Platform, sampler);
                overlay.transform.SetParent(transform, false);
            }
        }
    }
}
