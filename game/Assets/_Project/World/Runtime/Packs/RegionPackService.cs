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
    /// version check before loading, AssetBundle load/unload around region scenes with reference counting (ADR 0273:
    /// the menu start and the additive streamer hold regions at the same time, see <see cref="RegionPackLeases"/>).
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

        /// <summary>The service if something already created it (the start menu), else null. Never creates it: creation
        /// installs incoming/ and hashes new bundles synchronously, which must not happen mid-drive (ADR 0273 §3).</summary>
        public static RegionPackService Existing => s_Instance;

        public event Action Changed;

        RegionPackPaths m_Paths;
        RegionPackManifest m_Installed;
        RegionPackManifest m_Remote;
        string m_RemoteJson;
        string m_RemoteError;
        readonly RegionPackLeases m_Leases = new RegionPackLeases();
        readonly Dictionary<string, AssetBundle> m_Bundles = new Dictionary<string, AssetBundle>(StringComparer.Ordinal);   // pack id -> bundle
        string m_DownloadingKey;
        float m_DownloadProgress;
        long m_DownloadBytes;

        public RegionPackPaths Paths => m_Paths;
        public RegionPackManifest InstalledSet => m_Installed;
        public RegionPackManifest RemoteSet => m_Remote;
        public string RemoteError => m_RemoteError;

        public static RegionPackAppIdentity CurrentApp => new RegionPackAppIdentity(
            BuildInfo.Current.versionCode, Application.unityVersion, RegionPackManifest.TargetFor(Application.platform));

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
            string key = RegionPackLeases.Key(region, tier);
            if (m_Leases.IsHeld(key)) return new RegionPackInfo(RegionPackState.Loaded, "", 0);
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

        // ------------------------------------------------------------------ load / unload (reference counted, ADR 0273)

        /// <summary>Leases of the menu start (<see cref="Prepare"/>): released when the active scene leaves that region.</summary>
        string m_MenuKey;
        bool m_Busy;   // one Acquire at a time: overlapping loads of a shared bundle (common) must not race

        public RegionPackLeases Leases => m_Leases;

        /// <summary>Menu start (ADR 0234 §4): <see cref="Acquire"/> with the menu's own lease; a previous menu lease is
        /// given back first. Regions held by the streamer stay loaded (no global unload, review s22 #112 P1-2).</summary>
        public IEnumerator Prepare(string region, string tier, Action<RegionPackLoadResult> done)
        {
            string key = RegionPackLeases.Key(region, tier);
            if (m_MenuKey == key && m_Leases.IsHeld(key))
            {
                done?.Invoke(new RegionPackLoadResult(SceneOf(key, false), null));
                yield break;
            }
            RegionPackLoadResult result = default;
            yield return Acquire(region, tier, r => result = r);
            if (result.Ok)
            {
                if (m_MenuKey != null && m_MenuKey != key) ReleaseKey(m_MenuKey);
                m_MenuKey = key;
            }
            done?.Invoke(result);
        }

        public IEnumerator Acquire(string region, string tier, Action<RegionPackLoadResult> done)
        {
            while (m_Busy) yield return null;
            m_Busy = true;
            try
            {
                string key = RegionPackLeases.Key(region, tier);
                if (m_Leases.IsHeld(key))
                {
                    m_Leases.Acquire(key, null);
                    done?.Invoke(new RegionPackLoadResult(SceneOf(key, false), null, SceneOf(key, true)));
                    yield break;
                }

                // Deep check (SHA-256) of the bundles this key still has to load, on a worker thread. Bundles already
                // loaded for another region (common) were verified when they were loaded.
                var installed = m_Installed;
                var app = CurrentApp;
                var paths = m_Paths;
                var task = Task.Run(() => RegionPackResolver.Resolve(installed, region, tier, app, paths, RegionPackDiskFiles.Instance, true));
                while (!task.IsCompleted) yield return null;
                if (task.IsFaulted) { Fail(done, "verify failed: " + task.Exception?.GetBaseException().Message); yield break; }
                var info = task.Result;
                if (info.State != RegionPackState.Installed) { Fail(done, region + "/" + tier + ": " + info); yield break; }

                var entry = installed.FindRegion(region, tier);
                var order = installed.LoadOrder(entry);
                order.Add(entry);
                var ids = new List<string>(order.Count);
                foreach (var e in order) ids.Add(e.id);
                var toLoad = m_Leases.Acquire(key, ids);
                foreach (var id in toLoad)
                {
                    var e = installed.Find(id);
                    var req = e != null ? AssetBundle.LoadFromFileAsync(paths.Installed(e.file)) : null;
                    if (req != null) yield return req;
                    if (req == null || req.assetBundle == null)
                    {
                        ReleaseKey(key);   // unloads what this key loaded so far; bundles of other keys keep their count
                        Fail(done, "AssetBundle.LoadFromFileAsync failed: " + (e?.file ?? id));
                        yield break;
                    }
                    m_Bundles[id] = req.assetBundle;
                }
                string full = SceneOf(key, false);
                if (string.IsNullOrEmpty(full)) { ReleaseKey(key); Fail(done, entry.file + " has no region scene"); yield break; }
                Debug.Log("[PACKS] acquire " + entry.id + " set=" + installed.packSetVersion + " scene=" + full + " tile=" + (SceneOf(key, true) ?? "-") +
                          " loaded " + toLoad.Count + " bundle(s), held regions " + m_Leases.HeldKeyCount + ", bundles " + m_Leases.LoadedBundleCount);
                Changed?.Invoke();
                done?.Invoke(new RegionPackLoadResult(full, null, SceneOf(key, true)));
            }
            finally { m_Busy = false; }
        }

        public void Release(string region, string tier) => ReleaseKey(RegionPackLeases.Key(region, tier));

        void ReleaseKey(string key)
        {
            if (key == m_MenuKey && m_Leases.LeaseCount(key) <= 1) m_MenuKey = null;
            var toUnload = m_Leases.Release(key);
            foreach (var id in toUnload)
            {
                // true: the region's meshes/textures go with it. Callers release only after the scene is unloaded.
                if (m_Bundles.TryGetValue(id, out var ab) && ab != null) ab.Unload(true);
                m_Bundles.Remove(id);
            }
            if (toUnload.Count > 0)
            {
                Debug.Log("[PACKS] release " + key + ": unloaded [" + string.Join(",", toUnload) + "], held regions " + m_Leases.HeldKeyCount);
                Changed?.Invoke();
            }
        }

        /// <summary>Scene name of a held key from its loaded scene bundle: the full region scene, or the tile scene.</summary>
        string SceneOf(string key, bool tile)
        {
            var bundles = m_Leases.BundlesOf(key);
            if (bundles.Count == 0) return null;
            if (!m_Bundles.TryGetValue(bundles[bundles.Count - 1], out var ab) || ab == null || !ab.isStreamedSceneAssetBundle) return null;
            foreach (var path in ab.GetAllScenePaths())
            {
                string name = Path.GetFileNameWithoutExtension(path);
                if (RegionPackLoadResult.IsTileScene(name) == tile) return name;
            }
            return null;
        }

        static void Fail(Action<RegionPackLoadResult> done, string error)
        {
            Debug.LogWarning("[PACKS] " + error);
            done?.Invoke(new RegionPackLoadResult(null, error));
        }

        /// <summary>Unloads every loaded pack bundle and drops every lease (tests, shutdown). <paramref name="unloadAllObjects"/>
        /// true also destroys their assets - only when no scene of them is open.</summary>
        public void UnloadAll(bool unloadAllObjects)
        {
            var all = m_Leases.Clear();
            m_MenuKey = null;
            if (all.Count == 0) return;
            foreach (var id in all)
                if (m_Bundles.TryGetValue(id, out var ab) && ab != null) ab.Unload(unloadAllObjects);
            m_Bundles.Clear();
            Debug.Log("[PACKS] unloaded all (objects=" + unloadAllObjects + ")");
        }

        // Leaving the menu-started pack region (menu, DrivingLab, a region in the build): give back the menu lease only.
        // Leases of the streamer are released by the streamer when it unloads its tile scenes (or is destroyed).
        void OnActiveSceneChanged(Scene from, Scene to)
        {
            if (m_MenuKey == null) return;
            if (to.name == SceneOf(m_MenuKey, false)) return;
            ReleaseKey(m_MenuKey);
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
            foreach (var dep in set.LoadOrder(entry))
                if (RegionPackResolver.CheckFile(dep, m_Paths, RegionPackDiskFiles.Instance, false) != RegionPackState.Installed) todo.Add(dep);
            if (RegionPackResolver.CheckFile(entry, m_Paths, RegionPackDiskFiles.Instance, false) != RegionPackState.Installed) todo.Add(entry);

            m_DownloadingKey = RegionPackLeases.Key(region, tier);
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
