using System.Globalization;
using Game.Core;
using Game.Platform;
using Game.Rendering;
using Game.Telemetry;
using Game.UI;
using UnityEngine;
using UnityEngine.SceneManagement;

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
        public const string WorldCSceneName = "WorldC";
        /// <summary>High-content variant (full chunks, LOD0 buildings, 1 m terrain band; ADR 0012). Only in builds made
        /// with -WorldHigh; Low/Medium always use <see cref="WorldCSceneName"/>.</summary>
        public const string WorldCHighSceneName = "WorldC_High";

        /// <summary>The WorldC scene matching the active quality tier (content tier, ADR 0012).</summary>
        public static string WorldCSceneForTier()
        {
            string t = QualityTiers.Current;
            bool high = t == "High" || t == "Ultra";
            return high && Application.CanStreamedLevelBeLoaded(WorldCHighSceneName) ? WorldCHighSceneName : WorldCSceneName;
        }
        [SerializeField] int defaultTargetFps = 30;
        [SerializeField] bool showOverlay = true;

        public IPlatformServices Platform { get; private set; }
        string m_PendingScene;

        void Start()
        {
            if (string.IsNullOrEmpty(m_PendingScene)) return;
            Debug.Log($"[BOOT] launch argument scene={m_PendingScene}");
            SceneManager.LoadScene(m_PendingScene);
        }

        void Awake()
        {
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            Platform = PlatformServices.Create();

            string tierArg = Platform.GetLaunchArgument("tier");
            if (!QualityTiers.Apply(tierArg) && !QualityTiers.Apply(QualityTiers.SavedTier))
            {
                // First launch: tier by device class (data in QualityProfile.deviceRules; not saved, so a rule update
                // reaches players who never chose a tier themselves).
                var qp = QualityProfile.Load();
                if (qp != null)
                {
                    string auto = qp.TierForDevice(SystemInfo.graphicsDeviceName, SystemInfo.deviceModel, SystemInfo.systemMemorySize, out string why);
                    QualityTiers.Apply(auto);
                    Debug.Log($"[BOOT] auto tier {auto}: {why}");
                }
            }

            string rq = RenderOverrides.Parse(Platform.GetLaunchArgument);
            if (rq != null) Debug.Log("[BOOT] render overrides (profiling): " + rq);

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

            // The imported world (WorldC) is in the build only when it was generated (scripts/import-region.ps1).
            var entries = new System.Collections.Generic.List<(string, System.Action)>
            {
                ("Plac testowy — jazda", () => SceneManager.LoadScene(DrivingLabLayout.SceneName)),
            };
            if (Application.CanStreamedLevelBeLoaded(WorldCSceneName))
                entries.Add(("Białystok — Kwadrat Park", () => SceneManager.LoadScene(WorldCSceneForTier())));
            BootMenu.Create(Camera.main, entries.ToArray()).transform.SetParent(transform, false);

            // Launch argument "scene" (adb: -e scene DrivingLab) jumps straight into a scene; the remaining
            // arguments (autopilot, speed) are read by that scene's bootstrap.
            string scene = Platform.GetLaunchArgument("scene");
            if (!string.IsNullOrEmpty(scene)) m_PendingScene = scene == WorldCSceneName ? WorldCSceneForTier() : scene;
        }
    }
}
