using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Game.Core;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.SceneManagement;

namespace Game.World.Packs
{
    /// <summary>
    /// Runtime side of region packs (ADR 0234): installed set on <c>persistentDataPath/regionpacks</c>, install from
    /// <c>incoming/</c> (adb push), optional download from a configured URL (UnityWebRequest, default none), SHA-256 +
    /// version check before loading, AssetBundle load/unload around region scenes.
    /// One instance (<see cref="Instance"/>, DontDestroyOnLoad). All work happens in the start menu or on the loading step
    /// before a region scene; the driving loop never calls into this class (no per-frame allocations: no Update method).
    /// </summary>
    public sealed class RegionPackService : MonoBehaviour, IRegionPackProvider
    {
        /// <summary>PlayerPrefs key of the download base URL (folder holding regionpacks.json + bundles). Empty = no download.</summary>
        public const string PrefBaseUrl = "regionpacks.url";
        const int DownloadTimeoutS = 0;      // 0 = no overall timeout (large packs on slow links); aborts come from the user
        const int ManifestTimeoutS = 20;     // WORKING_VALUE

        static RegionPackService s_Instance;

        public static RegionPackService Instance
        {
            get
            {
                if (s_Instance != null) return s_Instance;
                var go = new GameObject("RegionPackService");
                DontDestroyOnLoad(go);
                s_Instance = go.AddComponent<RegionPackService>();
                return s_Instance;
            }
        }

        public event Action Changed;

        RegionPackPaths m_Paths;
        RegionPackManifest m_Installed;
        RegionPackManifest m_Remote;
        string m_RemoteJson;
        string m_RemoteError;
        readonly List<AssetBundle> m_Loaded = new List<AssetBundle>();
        readonly List<string> m_LoadedScenePaths = new List<string>();
        string m_LoadedKey;              // "<region>|<tier>" of the loaded bundles
        string m_DownloadingKey;
        float m_DownloadProgress;
        long m_DownloadBytes;

        public RegionPackPaths Paths => m_Paths;
        public RegionPackManifest InstalledSet => m_Installed;
        public RegionPackManifest RemoteSet => m_Remote;
        public string RemoteError => m_RemoteError;

        public static RegionPackAppIdentity CurrentApp => new RegionPackAppIdentity(
            BuildInfo.Current.versionCode, Application.unityVersion,
            Application.platform == RuntimePlatform.Android ? "Android" : Application.platform.ToString());

        public string BaseUrl
        {
            get => PlayerPrefs.GetString(PrefBaseUrl, "");
            set { PlayerPrefs.SetString(PrefBaseUrl, value ?? ""); PlayerPrefs.Save(); m_Remote = null; m_RemoteJson = null; m_RemoteError = null; }
        }

        public bool DownloadEnabled => !string.IsNullOrWhiteSpace(BaseUrl);

        void Awake()
        {
            if (s_Instance != null && s_Instance != this) { Destroy(gameObject); return; }
            s_Instance = this;
            m_Paths = new RegionPackPaths(Application.persistentDataPath);
            SceneManager.activeSceneChanged += OnActiveSceneChanged;
            InstallIncoming();
        }

        void OnDestroy()
        {
            SceneManager.activeSceneChanged -= OnActiveSceneChanged;
            if (s_Instance == this) s_Instance = null;
        }

        // ------------------------------------------------------------------ installed set

        /// <summary>Installs adb-pushed / downloaded files from incoming/ and reloads the installed manifest.
        /// Synchronous: hashes every new bundle (menu only; ~1 s per 100 MB on a phone, ESTIMATED).</summary>
        public RegionPackInstallResult InstallIncoming()
        {
            RegionPackInstallResult r;
            try { r = RegionPackInstaller.InstallIncoming(m_Paths, CurrentApp, RegionPackDiskFiles.Instance); }
            catch (Exception e)
            {
                r = new RegionPackInstallResult { Attempted = true, Error = e.GetType().Name + ": " + e.Message };
            }
            if (r.Attempted) Debug.Log("[PACKS] install " + r);
            ReloadInstalled();
            return r;
        }

        void ReloadInstalled()
        {
            m_Installed = null;
            if (File.Exists(m_Paths.InstalledManifest))
            {
                if (RegionPackManifest.TryParse(File.ReadAllText(m_Paths.InstalledManifest), out var m, out string err)) m_Installed = m;
                else Debug.LogWarning("[PACKS] installed manifest invalid: " + err);
            }
            string compat = m_Installed != null ? RegionPackResolver.CompatibilityProblem(m_Installed, CurrentApp) : null;
            Debug.Log("[PACKS] set=" + (m_Installed?.packSetVersion ?? "none") + " packs=" + (m_Installed?.packs.Length ?? 0) +
                      (compat != null ? " INCOMPATIBLE: " + compat : "") + " root=" + m_Paths.Root);
            Changed?.Invoke();
        }

        public RegionPackInfo GetInfo(string region, string tier, bool sceneInBuild)
        {
            if (sceneInBuild) return new RegionPackInfo(RegionPackState.InBase, "", 0);
            string key = region + "|" + tier;
            if (key == m_LoadedKey && m_Loaded.Count > 0) return new RegionPackInfo(RegionPackState.Loaded, "", 0);
            if (key == m_DownloadingKey) return new RegionPackInfo(RegionPackState.Downloading, "", m_DownloadBytes, m_DownloadProgress);
            var info = RegionPackResolver.Resolve(m_Installed, region, tier, CurrentApp, m_Paths, RegionPackDiskFiles.Instance, false);
            // Not installed / incompatible locally but offered by the download folder: show the download size of the remote set.
            if (m_Remote != null && (info.State == RegionPackState.NotInstalled || info.State == RegionPackState.Incompatible))
            {
                var e = m_Remote.FindRegion(region, tier);
                if (e != null)
                    return new RegionPackInfo(RegionPackState.NotInstalled, "offered by " + m_Remote.packSetVersion,
                                              RegionPackResolver.MissingBytes(m_Remote, e, m_Paths, RegionPackDiskFiles.Instance));
            }
            return info;
        }

        // ------------------------------------------------------------------ load / unload

        public IEnumerator Prepare(string region, string tier, Action<RegionPackLoadResult> done)
        {
            string key = region + "|" + tier;
            if (key == m_LoadedKey && m_Loaded.Count > 0 && m_LoadedScenePaths.Count > 0)
            {
                done?.Invoke(new RegionPackLoadResult(Path.GetFileNameWithoutExtension(m_LoadedScenePaths[0]), null));
                yield break;
            }
            UnloadAll(true);

            // Deep check (SHA-256 of the pack and its dependencies) on a worker thread, once per start from the menu.
            var installed = m_Installed;
            var app = CurrentApp;
            var paths = m_Paths;
            var task = Task.Run(() => RegionPackResolver.Resolve(installed, region, tier, app, paths, RegionPackDiskFiles.Instance, true));
            while (!task.IsCompleted) yield return null;
            if (task.IsFaulted) { Fail(done, "verify failed: " + task.Exception?.GetBaseException().Message); yield break; }
            var info = task.Result;
            if (info.State != RegionPackState.Installed) { Fail(done, region + "/" + tier + ": " + info); yield break; }

            var entry = installed.FindRegion(region, tier);
            var order = new List<RegionPackEntry>();
            foreach (var d in entry.dependencies) order.Add(installed.Find(d));
            order.Add(entry);
            foreach (var e in order)
            {
                var req = AssetBundle.LoadFromFileAsync(paths.Installed(e.file));
                yield return req;
                if (req.assetBundle == null)
                {
                    UnloadAll(true);
                    Fail(done, "AssetBundle.LoadFromFileAsync failed: " + e.file);
                    yield break;
                }
                m_Loaded.Add(req.assetBundle);
                if (req.assetBundle.isStreamedSceneAssetBundle) m_LoadedScenePaths.AddRange(req.assetBundle.GetAllScenePaths());
            }
            if (m_LoadedScenePaths.Count == 0) { UnloadAll(true); Fail(done, entry.file + " has no scene"); yield break; }
            m_LoadedKey = key;
            string scene = Path.GetFileNameWithoutExtension(m_LoadedScenePaths[0]);
            Debug.Log("[PACKS] loaded " + entry.id + " set=" + installed.packSetVersion + " scene=" + scene + " bundles=" + m_Loaded.Count);
            Changed?.Invoke();
            done?.Invoke(new RegionPackLoadResult(scene, null));
        }

        static void Fail(Action<RegionPackLoadResult> done, string error)
        {
            Debug.LogWarning("[PACKS] " + error);
            done?.Invoke(new RegionPackLoadResult(null, error));
        }

        /// <summary>Unloads every loaded pack bundle. <paramref name="unloadAllObjects"/> true also destroys their assets
        /// (only when no scene of them is open).</summary>
        public void UnloadAll(bool unloadAllObjects)
        {
            if (m_Loaded.Count == 0) return;
            for (int i = m_Loaded.Count - 1; i >= 0; i--)
                if (m_Loaded[i] != null) m_Loaded[i].Unload(unloadAllObjects);
            m_Loaded.Clear();
            m_LoadedScenePaths.Clear();
            m_LoadedKey = null;
            Debug.Log("[PACKS] unloaded (objects=" + unloadAllObjects + ")");
        }

        // Leaving a pack region (menu, DrivingLab, a region in the APK): free the bundles and their meshes/textures.
        void OnActiveSceneChanged(Scene from, Scene to)
        {
            if (m_Loaded.Count == 0) return;
            if (m_LoadedScenePaths.Contains(to.path)) return;
            UnloadAll(true);
            Changed?.Invoke();
        }

        // ------------------------------------------------------------------ download (optional, URL configured)

        /// <summary>Fetches regionpacks.json from <see cref="BaseUrl"/> (menu, on demand). done(null) = ok.</summary>
        public IEnumerator RefreshRemote(Action<string> done)
        {
            string url = RegionPackPaths.Url(BaseUrl, RegionPackManifest.FileName);
            if (url == null) { done?.Invoke("no download URL configured"); yield break; }
            using (var req = UnityWebRequest.Get(url))
            {
                req.timeout = ManifestTimeoutS;
                yield return req.SendWebRequest();
                if (req.result != UnityWebRequest.Result.Success) { RemoteFail(done, url + ": " + req.error); yield break; }
                if (!RegionPackManifest.TryParse(req.downloadHandler.text, out var m, out string err)) { RemoteFail(done, err); yield break; }
                string compat = RegionPackResolver.CompatibilityProblem(m, CurrentApp);
                if (compat != null) { RemoteFail(done, "remote set " + m.packSetVersion + ": " + compat); yield break; }
                m_Remote = m;
                m_RemoteJson = req.downloadHandler.text;
                m_RemoteError = null;
                Debug.Log("[PACKS] remote set=" + m.packSetVersion + " packs=" + m.packs.Length);
                Changed?.Invoke();
                done?.Invoke(null);
            }
        }

        void RemoteFail(Action<string> done, string error)
        {
            m_Remote = null;
            m_RemoteJson = null;
            m_RemoteError = error;
            Debug.LogWarning("[PACKS] remote: " + error);
            Changed?.Invoke();
            done?.Invoke(error);
        }

        public IEnumerator Download(string region, string tier, Action<string> done)
        {
            if (m_DownloadingKey != null) { done?.Invoke("another download is running"); yield break; }
            if (m_Remote == null)
            {
                string err = null;
                yield return RefreshRemote(e => err = e);
                if (err != null) { done?.Invoke(err); yield break; }
            }
            var set = m_Remote;
            string setJson = m_RemoteJson;
            var entry = set.FindRegion(region, tier);
            if (entry == null) { done?.Invoke(region + "/" + tier + " not in remote set " + set.packSetVersion); yield break; }

            // The dependency first, then the region; files already intact in the installed set are skipped.
            var todo = new List<RegionPackEntry>();
            foreach (var d in entry.dependencies)
            {
                var dep = set.Find(d);
                if (RegionPackResolver.CheckFile(dep, m_Paths, RegionPackDiskFiles.Instance, false) != RegionPackState.Installed) todo.Add(dep);
            }
            if (RegionPackResolver.CheckFile(entry, m_Paths, RegionPackDiskFiles.Instance, false) != RegionPackState.Installed) todo.Add(entry);

            m_DownloadingKey = region + "|" + tier;
            m_DownloadBytes = 0;
            foreach (var e in todo) m_DownloadBytes += e.sizeBytes;
            m_DownloadProgress = 0f;
            Changed?.Invoke();
            Directory.CreateDirectory(m_Paths.Incoming);
            long doneBytes = 0;
            string error = null;
            foreach (var e in todo)
            {
                string part = m_Paths.IncomingPart(e.file);
                var handler = new DownloadHandlerFile(part) { removeFileOnAbort = true };
                using (var req = new UnityWebRequest(RegionPackPaths.Url(BaseUrl, e.file), UnityWebRequest.kHttpVerbGET, handler, null))
                {
                    req.timeout = DownloadTimeoutS;
                    var op = req.SendWebRequest();
                    float lastNotified = -1f;
                    while (!op.isDone)
                    {
                        m_DownloadProgress = m_DownloadBytes > 0 ? (doneBytes + e.sizeBytes * req.downloadProgress) / m_DownloadBytes : 0f;
                        if (m_DownloadProgress - lastNotified >= 0.01f) { lastNotified = m_DownloadProgress; Changed?.Invoke(); }
                        yield return null;
                    }
                    if (req.result != UnityWebRequest.Result.Success) { error = e.file + ": " + req.error; break; }
                }
                // Verify before it may replace anything (the installer checks again; this catches a bad download early).
                var verify = Task.Run(() => RegionPackDiskFiles.Instance.Size(part) == e.sizeBytes && RegionPackHash.Sha256File(part) == e.sha256);
                while (!verify.IsCompleted) yield return null;
                if (verify.IsFaulted || !verify.Result)
                {
                    TryDelete(part);
                    error = e.file + ": downloaded file does not match the manifest (size/sha256)";
                    break;
                }
                string final = m_Paths.IncomingFile(e.file);
                TryDelete(final);
                File.Move(part, final);
                doneBytes += e.sizeBytes;
            }
            m_DownloadingKey = null;
            if (error == null)
            {
                // A new remote set replaces the installed one (same rules as an adb push).
                File.WriteAllText(m_Paths.IncomingManifest, setJson);
                var r = InstallIncoming();
                if (!r.Ok) error = r.Error ?? "install failed";
                else if (r.Rejected.Count > 0) error = "rejected: " + string.Join(",", r.Rejected);
                else
                {
                    // A same-size file of an older set may have been skipped above and removed by the installer.
                    var after = RegionPackResolver.Resolve(m_Installed, region, tier, CurrentApp, m_Paths, RegionPackDiskFiles.Instance, false);
                    if (after.State != RegionPackState.Installed) error = "after install: " + after + " (download again)";
                }
            }
            if (error != null) Debug.LogWarning("[PACKS] download " + region + "/" + tier + ": " + error);
            Changed?.Invoke();
            done?.Invoke(error);
        }

        static void TryDelete(string path)
        {
            try { if (path != null && File.Exists(path)) File.Delete(path); }
            catch (IOException) { }
        }
    }
}
