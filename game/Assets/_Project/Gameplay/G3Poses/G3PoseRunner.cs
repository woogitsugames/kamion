using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using Game.Core;
using Game.Platform;
using Game.Rendering;
using Game.World;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Game.Gameplay
{
    /// <summary>
    /// Photo-pair capture on the phone (ADR 0246, BACKLOG B-111). Development builds only, launch argument g3pose=1
    /// (<see cref="G3PoseArgs"/>). Hooked from code (<see cref="RuntimeInitializeOnLoadMethodAttribute"/>), no scene or prefab
    /// change: when a scene with a <see cref="WorldRegionRoot"/> loads, it waits for the warm-up, then for every pose of
    /// Resources/g3_poses.json places an off-screen camera at the pose (same pose function as the editor pairs), renders it
    /// into a render texture at the tier render scale and MSAA until streaming has settled (<see cref="G3PoseSettle"/>),
    /// downsamples to the editor pair size (1280 x photo aspect) and writes a PNG to
    /// persistentDataPath/g3poses/&lt;run&gt;/. Every step is logged with <c>[G3POSE]</c>; the run always ends with a DONE line.
    /// The player's view, HUD and vehicle are left as they are (the capture camera never draws to the screen).
    /// </summary>
    public sealed class G3PoseRunner : MonoBehaviour
    {
        /// <summary>Far clip the gate cameras are created with (Gate3Cameras.CreateAll); the tier far clip caps it, as in
        /// VisualQaRunner (min(authored, tier)).</summary>
        public const float AuthoredFarClip = 1400f;

        static G3PoseArgs s_Args;
        static bool s_Started;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Init()
        {
            s_Started = false;
            IPlatformServices platform;
            try { platform = PlatformServices.Create(); }
            catch (Exception e) { Debug.LogWarning($"{G3PoseCapture.Tag} platform services unavailable: {e.Message}"); return; }
            var warnings = new List<string>();
            s_Args = G3PoseArgs.Parse(platform.GetLaunchArgument, warnings);
            if (!s_Args.Enabled) return;   // the normal case: silent, no hook
            foreach (var w in warnings) Debug.LogWarning($"{G3PoseCapture.Tag} arg: {w}");
            if (!G3PoseArgs.ShouldRun(s_Args, Debug.isDebugBuild, out string reason))
            {
                Debug.LogWarning($"{G3PoseCapture.Tag} {reason}");
                Debug.Log(G3PoseCapture.DoneLine(s_Args.RunId, 0, 0, 0, "-"));
                return;
            }
            Debug.Log($"{G3PoseCapture.Tag} armed: {s_Args} (waiting for a world scene, e.g. -e scene WorldC)");
            SceneManager.sceneLoaded -= OnSceneLoaded;
            SceneManager.sceneLoaded += OnSceneLoaded;
            OnSceneLoaded(SceneManager.GetActiveScene(), LoadSceneMode.Single);
        }

        static void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            if (s_Started || s_Args == null) return;
            var root = FindAnyObjectByType<WorldRegionRoot>();
            if (root == null) return;   // Boot menu: the scene launch argument loads the world next
            s_Started = true;
            SceneManager.sceneLoaded -= OnSceneLoaded;
            var go = new GameObject("G3PoseRunner");
            var runner = go.AddComponent<G3PoseRunner>();
            runner.m_Args = s_Args;
            runner.m_Root = root;
            runner.m_Scene = scene.name;
        }

        G3PoseArgs m_Args;
        WorldRegionRoot m_Root;
        string m_Scene;
        Camera m_Cam;
        RenderTexture m_Src, m_Dst;
        Texture2D m_Tex;

        [Serializable] class ShotRow
        {
            public int index; public string id; public string segment; public string file; public string status; public string reason;
            public int width; public int height; public int render_width; public int render_height; public int msaa;
            public int frames; public float wait_s; public long tex_pending; public bool timeout;
            public float[] unity_pos; public float[] unity_forward; public float fov_deg;
            public string reference_photo; public string comparison_photo;
        }

        [Serializable] class Manifest
        {
            public string schema = "kamion/g3-poses-capture/1";
            public string run; public string scene; public string region; public string build; public string device; public string gpu;
            public string tier; public float render_scale; public int msaa; public string lighting; public int width;
            public string args; public string started_utc; public string finished_utc;
            public int selected; public int total; public int captured; public int failed; public int timeout;
            public string[] errors;
            public ShotRow[] shots;
        }

        void Start() => StartCoroutine(Run());

        IEnumerator Run()
        {
            var a = m_Args;
            string dir = G3PoseCapture.OutputDir(Application.persistentDataPath, a.RunId);
            var man = new Manifest
            {
                run = a.RunId, scene = m_Scene, build = BuildInfo.Current != null ? BuildInfo.Current.ShortLabel : "?",
                device = SystemInfo.deviceModel, gpu = SystemInfo.graphicsDeviceName, lighting = a.Lighting, width = a.Width,
                args = a.ToString(), started_utc = DateTime.UtcNow.ToString("o"),
            };
            var rows = new List<ShotRow>();
            var errors = new List<string>();
            int captured = 0, failed = 0, timedOut = 0;

            Debug.Log($"{G3PoseCapture.Tag} scene {m_Scene}: warm-up {a.WarmupSeconds:0.#} s");
            yield return new WaitForSecondsRealtime(a.WarmupSeconds);

            var text = Resources.Load<TextAsset>(G3PoseSet.ResourceName);
            var file = G3PoseSet.Parse(text != null ? text.text : null, errors);
            foreach (var e in errors) Debug.LogWarning($"{G3PoseCapture.Tag} pose file: {e}");
            List<G3Pose> poses = G3PoseSet.Select(file, a.Filter);
            man.region = file?.region; man.total = file?.poses?.Length ?? 0; man.selected = poses.Count;

            QualityProfile.Tier tier = default;
            bool hasTier = QualityProfileApplier.HasCurrent;
            if (hasTier) tier = QualityProfileApplier.Current;
            else
            {
                var qp = QualityProfile.Load();
                hasTier = qp != null && qp.TryGet(QualityTiers.Current, out tier);
            }
            float scale = hasTier ? tier.renderScale : 1f;
            int msaa = hasTier ? Mathf.Max(1, tier.msaa) : 1;
            man.tier = hasTier ? tier.name : QualityTiers.Current; man.render_scale = scale; man.msaa = msaa;

            if (file == null) errors.Add("pose file missing or invalid (Resources/" + G3PoseSet.ResourceName + ".json)");
            else if (poses.Count == 0) errors.Add($"filter '{a.Filter}' matched no pose");
            if (errors.Count == 0)
            {
                try { Directory.CreateDirectory(dir); }
                catch (Exception e) { errors.Add("cannot create " + dir + ": " + e.Message); }
            }

            if (errors.Count == 0 || (file != null && poses.Count > 0 && Directory.Exists(dir)))
            {
                Debug.Log(G3PoseCapture.BeginLine(a.RunId, poses.Count, man.total, man.tier, a.Lighting, a.Width, dir));
                Debug.Log($"{G3PoseCapture.Tag} build={man.build} device='{man.device}' gpu='{man.gpu}' renderScale={scale} msaa={msaa} screen={Screen.width}x{Screen.height}");
                CreateCamera(hasTier, tier);
                var settle = new G3PoseSettle(a);
                for (int i = 0; i < poses.Count; i++)
                {
                    var p = poses[i];
                    var row = new ShotRow
                    {
                        index = p.index, id = p.id, segment = p.segment, fov_deg = p.fov_deg, msaa = msaa,
                        reference_photo = p.reference?.photo, comparison_photo = p.reference?.comparison_photo,
                    };
                    rows.Add(row);
                    string fail = Place(p, a.Width, scale, msaa, row);
                    if (fail != null)
                    {
                        row.status = "FAIL"; row.reason = fail; failed++;
                        Debug.LogWarning(G3PoseCapture.FailLine(i + 1, poses.Count, p.id, fail));
                        continue;
                    }
                    m_Cam.enabled = true;
                    settle.Reset();
                    var state = G3PoseSettle.State.Waiting;
                    while (state == G3PoseSettle.State.Waiting)
                    {
                        yield return null;
                        state = settle.Step(Time.unscaledDeltaTime, PendingTextureLoads());
                    }
                    yield return new WaitForEndOfFrame();   // the capture camera has rendered this frame into m_Src
                    row.frames = settle.Frames; row.wait_s = settle.Elapsed; row.tex_pending = settle.LastPending; row.timeout = settle.TimedOut;
                    string name = G3PoseCapture.FileName(p, a.Lighting);
                    fail = Save(Path.Combine(dir, name), row.width, row.height, msaa);
                    m_Cam.enabled = false;
                    if (fail != null)
                    {
                        row.status = "FAIL"; row.reason = fail; failed++;
                        Debug.LogWarning(G3PoseCapture.FailLine(i + 1, poses.Count, p.id, fail));
                        continue;
                    }
                    row.file = name; row.status = settle.TimedOut ? "TIMEOUT" : "OK";
                    captured++;
                    if (settle.TimedOut) timedOut++;
                    Debug.Log(G3PoseCapture.ShotLine(i + 1, poses.Count, p, name, row.width, row.height, row.render_width, row.render_height, msaa, settle));
                }
            }
            foreach (var e in errors) Debug.LogWarning(G3PoseCapture.FailLine(0, poses.Count, "-", e));

            man.captured = captured; man.failed = failed + errors.Count; man.timeout = timedOut;
            man.errors = errors.ToArray(); man.shots = rows.ToArray(); man.finished_utc = DateTime.UtcNow.ToString("o");
            try
            {
                if (Directory.Exists(dir)) File.WriteAllText(Path.Combine(dir, G3PoseCapture.ManifestName), JsonUtility.ToJson(man, true));
            }
            catch (Exception e) { Debug.LogWarning($"{G3PoseCapture.Tag} manifest not written: {e.Message}"); }
            Cleanup();
            Debug.Log(G3PoseCapture.DoneLine(a.RunId, captured, man.failed, timedOut, Directory.Exists(dir) ? dir : "-"));
        }

        void CreateCamera(bool hasTier, QualityProfile.Tier tier)
        {
            var go = new GameObject("G3PoseCamera");
            go.transform.SetParent(transform, false);
            m_Cam = go.AddComponent<Camera>();
            m_Cam.enabled = false;
            m_Cam.nearClipPlane = 0.1f;
            m_Cam.farClipPlane = AuthoredFarClip;
            if (hasTier)
            {
                // Camera-level tier settings only (far clip, MSAA/HDR flags, post); the volume and textures stay as the
                // scene's QualityProfileApplier set them.
                CaptureCameraTier.Apply(tier, m_Cam);
                m_Cam.farClipPlane = Mathf.Min(AuthoredFarClip, tier.cameraFarClip);
            }
        }

        /// <summary>Moves the capture camera to the pose and sizes the targets. Null on success, else the reason.</summary>
        string Place(G3Pose p, int width, float scale, int msaa, ShotRow row)
        {
            if (!G3PoseCapture.TryOutputSize(p, width, out int w, out int h)) return "no output size";
            G3PoseCapture.RenderSize(w, h, scale, out int rw, out int rh);
            row.width = w; row.height = h; row.render_width = rw; row.render_height = rh;
            var e = ToEntry(p);
            Vector3 pos = m_Root.LocalToUnity(p.pos[0], p.pos[1], p.pos[2]);
            Vector3 look = m_Root.LocalToUnity(p.look_at[0], p.look_at[1], p.look_at[2]);
            Gate3Cameras.ComputePose(e, pos, look, (x, z, fromY) => (Gate3Cameras.TryGroundY(x, z, fromY, null, out float gy), gy), out pos, out look);
            var dirv = look - pos;
            if (dirv.sqrMagnitude < 1e-6f) return "look_at == pos after seating";
            m_Cam.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(dirv, Vector3.up));
            m_Cam.fieldOfView = p.fov_deg;
            row.unity_pos = new[] { pos.x, pos.y, pos.z };
            var f = m_Cam.transform.forward;
            row.unity_forward = new[] { f.x, f.y, f.z };

            if (m_Src == null || m_Src.width != rw || m_Src.height != rh || m_Src.antiAliasing != msaa)
            {
                m_Cam.targetTexture = null;
                Release(ref m_Src);
                m_Src = new RenderTexture(rw, rh, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB) { antiAliasing = msaa, filterMode = FilterMode.Bilinear, name = "G3PoseSrc" };
                if (!m_Src.Create()) { Release(ref m_Src); return $"render texture {rw}x{rh} msaa {msaa} not created"; }
            }
            m_Cam.targetTexture = m_Src;
            return null;
        }

        /// <summary>Like VisualQaRunner.RenderToPixels: bilinear resolve/downsample to the output size, read back, PNG.</summary>
        string Save(string path, int w, int h, int msaa)
        {
            try
            {
                RenderTexture read = m_Src;
                if (m_Src.width != w || m_Src.height != h || msaa > 1)
                {
                    if (m_Dst == null || m_Dst.width != w || m_Dst.height != h)
                    {
                        Release(ref m_Dst);
                        m_Dst = new RenderTexture(w, h, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB) { antiAliasing = 1, filterMode = FilterMode.Bilinear, name = "G3PoseDst" };
                    }
                    Graphics.Blit(m_Src, m_Dst);
                    read = m_Dst;
                }
                if (m_Tex == null || m_Tex.width != w || m_Tex.height != h)
                {
                    if (m_Tex != null) Destroy(m_Tex);
                    m_Tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
                }
                var prev = RenderTexture.active;
                RenderTexture.active = read;
                m_Tex.ReadPixels(new Rect(0, 0, w, h), 0, 0);
                m_Tex.Apply(false);
                RenderTexture.active = prev;
                File.WriteAllBytes(path, m_Tex.EncodeToPNG());
                return null;
            }
            catch (Exception e) { return e.GetType().Name + ": " + e.Message; }
        }

        /// <summary>The pose as a gate camera entry, so the phone goes through the same pose function as the editor pairs
        /// (<see cref="Gate3Cameras.ComputePose"/>; scripts/sbs-gate3.ps1 renders sbs_cameras.json via visual-qa -Gate3).</summary>
        public static Gate3Cameras.Entry ToEntry(G3Pose p) => p == null ? null : new Gate3Cameras.Entry
        {
            id = p.id, kind = p.kind, pos = p.pos, look_at = p.look_at, fov_deg = p.fov_deg, seat = p.seat,
            note = p.source != null ? p.source.note : null,
        };

        static long PendingTextureLoads()
        {
            if (!QualitySettings.streamingMipmapsActive) return 0;
            return (long)Texture.streamingTextureLoadingCount + (long)Texture.streamingTexturePendingLoadCount;
        }

        void Cleanup()
        {
            if (m_Cam != null) { m_Cam.enabled = false; m_Cam.targetTexture = null; Destroy(m_Cam.gameObject); m_Cam = null; }
            Release(ref m_Src);
            Release(ref m_Dst);
            if (m_Tex != null) { Destroy(m_Tex); m_Tex = null; }
        }

        static void Release(ref RenderTexture rt)
        {
            if (rt == null) return;
            rt.Release();
            Destroy(rt);
            rt = null;
        }

        void OnDestroy() => Cleanup();
    }
}
