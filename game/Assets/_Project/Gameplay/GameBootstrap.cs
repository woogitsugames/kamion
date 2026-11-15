using System.Globalization;
using Game.Controls;
using Game.Core;
using Game.Platform;
using Game.Rendering;
using Game.Telemetry;
using Game.UI;
using Game.World;
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

        /// <summary>Desktop frame-rate cap when neither a launch argument nor a saved choice exists (ADR 0261). WORKING_VALUE
        /// until the owner names the reference PC (ADR 0260); "-fps N" overrides it (e.g. -fps 1000 for an uncapped measurement).</summary>
        public const int DesktopTargetFps = 60;

        public static bool IsDesktopPlayer(RuntimePlatform p) =>
            p == RuntimePlatform.WindowsPlayer || p == RuntimePlatform.OSXPlayer || p == RuntimePlatform.LinuxPlayer;

        /// <summary>First-launch tier of a desktop player ("High"); null on phones and in the editor (device rules / saved tier).</summary>
        public static string DesktopDefaultTier(RuntimePlatform p) => IsDesktopPlayer(p) ? "High" : null;

        public static int DesktopDefaultFps(RuntimePlatform p, int mobileDefault) => IsDesktopPlayer(p) ? DesktopTargetFps : mobileDefault;
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
            string desktopTier = DesktopDefaultTier(Application.platform);
            if (QualityTiers.Apply(tierArg) || QualityTiers.Apply(QualityTiers.SavedTier)) { }
            else if (desktopTier != null)
            {
                // Desktop player (ADR 0261): the device rules are a phone GPU list; PC starts at High (not saved).
                QualityTiers.Apply(desktopTier);
                Debug.Log($"[BOOT] desktop default tier {desktopTier}");
            }
            else
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

            // ADR 0152 diagnostics: per-frame camera pose CSV (camlog=1) and the old head-spring integration for A/B (cam_legacy=1).
            Game.Cameras.CameraRig.LegacyHeadIntegration = Platform.GetLaunchArgument("cam_legacy") == "1";
            if (Platform.GetLaunchArgument("camlog") == "1")
            {
                string dir = System.IO.Path.Combine(Application.persistentDataPath, "diag");
                System.IO.Directory.CreateDirectory(dir);
                Game.Cameras.CameraRig.PoseLogPath = System.IO.Path.Combine(dir, "campose.csv");
                Debug.Log($"[CAM] pose log {Game.Cameras.CameraRig.PoseLogPath} legacyHead={Game.Cameras.CameraRig.LegacyHeadIntegration}");
            }

            string rq = RenderOverrides.Parse(Platform.GetLaunchArgument);
            if (rq != null) Debug.Log("[BOOT] render overrides (profiling): " + rq);

            int fps = DesktopDefaultFps(Application.platform, defaultTargetFps);
            if (int.TryParse(Platform.GetLaunchArgument("fps"), NumberStyles.Integer, CultureInfo.InvariantCulture, out int argFps) && argFps > 0)
                fps = argFps;
            else if (QualityTiers.SavedFrameRate > 0)
                fps = QualityTiers.SavedFrameRate;
            QualityTiers.SetTargetFrameRate(fps);
            AdaptiveFrameDriver.ThermalStatusProvider = Platform.GetThermalStatus;   // ADR 0046 thermal fallback

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
            var options = StartMenuOptions.Load();
            var entries = new System.Collections.Generic.List<(string, System.Action)>
            {
                ("DrivingLab — plac testowy", () => SceneManager.LoadScene(DrivingLabLayout.SceneName)),
            };
            if (Application.CanStreamedLevelBeLoaded(WorldCSceneName))
            {
                // Same values as the launch arguments route_s / route_end (consumed by DrivingLabBootstrap in WorldC).
                // Labels name streets and generic places only, never a company or a commercial site (CLAUDE.md rule 8,
                // BRAND-SWEEP-S20 #3: the depot start used to carry the name of the logistics park).
                entries.Add(("Trasa G3-A — baza, brama, Bieżeństwa", () =>
                {
                    StartRequest.Set("G3-A", StartRequest.G3AStartS, StartRequest.G3AEndS, options.LightingId);
                    SceneManager.LoadScene(WorldCSceneForTier());
                }));
                entries.Add(("Trasa G3-B — Andersa, Rondo Putry", () =>
                {
                    StartRequest.Set("G3-B", StartRequest.G3BStartS, StartRequest.G3BEndS, options.LightingId);
                    SceneManager.LoadScene(WorldCSceneForTier());
                }));
            }
            // Region starts (ADR 0229): every catalog region; the ones whose scene is not in this APK are greyed out.
            m_Catalog = RegionCatalog.Load();
            var regions = BuildRegionChoices(m_Catalog, options);
            ControlSettings.Load().Log("boot");
            m_Menu = BootMenu.Create(Camera.main, options, entries, OpenControlSettings, OpenAbout, regions);
            m_Menu.transform.SetParent(transform, false);
            Debug.Log("[CONTROLS] menu shown light=" + options.LightingId + " tier=" + options.Tier + " fps=" + options.Fps);

            // Launch argument "scene" (adb: -e scene DrivingLab) jumps straight into a scene; the remaining
            // arguments (autopilot, speed) are read by that scene's bootstrap.
            DesktopAutoShot.StartFromArguments(Platform.GetLaunchArgument);   // shot=<png> shot_t=<s> quit_t=<s> (ADR 0261 evidence run)
            string scene = Platform.GetLaunchArgument("scene");
            if (!string.IsNullOrEmpty(scene)) m_PendingScene = scene == WorldCSceneName ? WorldCSceneForTier() : LaunchSceneFor(scene);
        }

        RegionCatalog m_Catalog;

        /// <summary>Launch argument scene=&lt;region id or alias&gt; (adb -e scene knyszyn) loads that region's scene for the
        /// active tier; any other value is a scene name as before.</summary>
        string LaunchSceneFor(string scene)
        {
            string id = m_Catalog?.ResolveId(scene);
            return id != null ? RegionSceneForTier(id) : scene;
        }

        /// <summary>The scene of a region matching the active quality tier: High content when shipped (ADR 0012), else Low.</summary>
        public static string RegionSceneForTier(string region)
        {
            string high = RegionScenes.SceneNameFor(region, RegionScenes.HighTier);
            return RegionScenes.UsesHighContent(QualityTiers.Current) && Application.CanStreamedLevelBeLoaded(high)
                ? high : RegionScenes.SceneNameFor(region);
        }

        static System.Collections.Generic.List<BootRegionChoice> BuildRegionChoices(RegionCatalog catalog, StartMenuOptions options)
        {
            var list = new System.Collections.Generic.List<BootRegionChoice>();
            if (catalog == null) return list;
            var ci = CultureInfo.InvariantCulture;
            foreach (var r in catalog.regions)
            {
                string id = r.id, label = r.label;
                bool inBuild = Application.CanStreamedLevelBeLoaded(RegionScenes.SceneNameFor(id));
                float s = RegionStart.ClampStartS(r.startS, r.routeLengthM);
                string km = (r.routeLengthM / 1000f).ToString("0.0", ci).Replace('.', ',');
                string detail = inBuild ? $"{r.group} · trasa {km} km · start na początku trasy" : $"{r.group} · brak w tym APK";
                list.Add(new BootRegionChoice(id, label, detail, inBuild, () =>
                {
                    StartRequest.SetRegion("region " + id, id, s, options.LightingId);
                    SceneManager.LoadScene(RegionSceneForTier(id));
                }));
            }
            return list;
        }

        ControlSettingsPanel m_Settings;
        AboutPanel m_About;
        BootMenu m_Menu;

        public BootMenu Menu => m_Menu;

        void OpenControlSettings()
        {
            if (m_Settings != null) return;
            m_Settings = ControlSettingsPanel.Create(null, ControlSettings.Load(), null, null);
            m_Settings.transform.SetParent(transform, false);
        }

        /// <summary>"Informacje": attributions and licence texts (Resources/About/attributions.txt; LICENSES-AUDIT-S20 R-P0-1).</summary>
        void OpenAbout()
        {
            if (m_About != null) return;
            m_About = AboutPanel.Create(null, null);
            m_About.transform.SetParent(transform, false);
        }
    }
}
