using System;
using System.Globalization;
using System.IO;

namespace Game.Gameplay
{
    /// <summary>
    /// Pure helpers of the photo-pair capture (ADR 0246): file names, output and render sizes, the settle rule and the
    /// <c>[G3POSE]</c> logcat lines that scripts/g3-poses.ps1 parses. No scene access (EditMode tests).
    /// </summary>
    public static class G3PoseCapture
    {
        public const string Tag = "[G3POSE]";
        public const string DirName = "g3poses";
        public const string ManifestName = "manifest.json";

        /// <summary>"07_sbs-g3-a-1406533339711789_overcast.png": index first so the files sort in route order.</summary>
        public static string FileName(G3Pose p, string lighting)
        {
            string id = G3PoseArgs.SanitizeToken(p?.id ?? "pose", 96);
            if (id.Length == 0) id = "pose";
            string l = G3PoseArgs.SanitizeToken(lighting ?? "", 32);
            int index = p != null ? p.index : 0;
            return index.ToString("D2", CultureInfo.InvariantCulture) + "_" + id + (l.Length > 0 ? "_" + l : "") + ".png";
        }

        /// <summary>&lt;persistentDataPath&gt;/g3poses/&lt;run&gt; (adb: /sdcard/Android/data/&lt;package&gt;/files/g3poses/&lt;run&gt;).</summary>
        public static string OutputDir(string persistentDataPath, string runId)
        {
            string run = G3PoseArgs.SanitizeToken(runId ?? "", 64);
            return Path.Combine(persistentDataPath ?? "", DirName, run.Length > 0 ? run : "run");
        }

        /// <summary>The folder a run writes to: <paramref name="overrideDir"/> (launch argument g3pose_dir, desktop players:
        /// scripts/g3-poses.ps1 -Exe points it into artifacts/) unless empty or on a mobile platform, else
        /// <see cref="OutputDir"/>.</summary>
        public static string ResolveOutputDir(string persistentDataPath, string runId, string overrideDir, bool isMobile)
        {
            if (!isMobile && !string.IsNullOrWhiteSpace(overrideDir)) return overrideDir.Trim();
            return OutputDir(persistentDataPath, runId);
        }

        /// <summary>
        /// Output size at <paramref name="width"/>: the file's out_width/out_height when the width matches (the editor pair
        /// size), otherwise the height from the reference photo aspect, rounded like PowerShell [int] (half to even).
        /// </summary>
        public static bool TryOutputSize(G3Pose p, int width, out int w, out int h)
        {
            w = 0; h = 0;
            if (p == null || width <= 0) return false;
            if (p.out_width == width && p.out_height > 0) { w = width; h = p.out_height; return true; }
            double rw, rh;
            if (p.reference != null && p.reference.width > 0 && p.reference.height > 0) { rw = p.reference.width; rh = p.reference.height; }
            else if (p.out_width > 0 && p.out_height > 0) { rw = p.out_width; rh = p.out_height; }
            else return false;
            w = width;
            h = (int)Math.Round(width * rh / rw, MidpointRounding.ToEven);
            return h > 0;
        }

        /// <summary>Render-target size at the tier render scale, as VisualQaRunner.RenderToPixels (min 16 px, Unity rounding).</summary>
        public static void RenderSize(int w, int h, float scale, out int rw, out int rh)
        {
            if (!(scale > 0f) || float.IsInfinity(scale)) scale = 1f;
            rw = Math.Max(16, (int)Math.Round(w * (double)scale, MidpointRounding.ToEven));
            rh = Math.Max(16, (int)Math.Round(h * (double)scale, MidpointRounding.ToEven));
        }

        static string F(float v) => v.ToString("0.###", CultureInfo.InvariantCulture);

        public static string BeginLine(string run, int selected, int total, string tier, string lighting, int width, string dir) =>
            $"{Tag} BEGIN run={run} poses={selected} total={total} tier={tier} lighting={(string.IsNullOrEmpty(lighting) ? "default" : lighting)} width={width} dir={dir}";

        public static string ShotLine(int i, int n, G3Pose p, string file, int w, int h, int rw, int rh, int msaa, G3PoseSettle s) =>
            $"{Tag} SHOT {i}/{n} id={p.id} file={file} size={w}x{h} render={rw}x{rh} msaa={msaa} frames={s.Frames} wait_s={F(s.Elapsed)} tex_pending={s.LastPending} settled={(s.TimedOut ? "timeout" : "yes")}";

        public static string FailLine(int i, int n, string id, string reason) =>
            $"{Tag} FAIL {i}/{n} id={id} reason={Oneline(reason)}";

        /// <summary>The end marker the script waits for. Always logged, also after errors (captured may be 0).</summary>
        public static string DoneLine(string run, int captured, int failed, int timedOut, string dir) =>
            $"{Tag} DONE run={run} captured={captured} failed={failed} timeout={timedOut} dir={dir}";

        public static string Oneline(string s) => (s ?? "").Replace('\r', ' ').Replace('\n', ' ');
    }

    /// <summary>
    /// "Streaming has settled" at a pose (ADR 0246): at least <see cref="MinFrames"/> rendered frames and
    /// <see cref="MinSeconds"/> at the pose, and no texture mip loads pending for <see cref="StableFrames"/> frames in a row;
    /// after <see cref="MaxSeconds"/> the capture happens anyway and is flagged. WorldC is one scene with no chunk
    /// streaming in the game code (ADR 0246), so mip streaming is the only asynchronous load counted.
    /// </summary>
    public sealed class G3PoseSettle
    {
        public enum State { Waiting, Settled, TimedOut }

        public int MinFrames = G3PoseArgs.DefaultSettleFrames;
        public float MinSeconds = G3PoseArgs.DefaultSettleSeconds;
        public float MaxSeconds = G3PoseArgs.DefaultMaxWaitSeconds;
        public int StableFrames = 5;   // WORKING_VALUE

        public int Frames { get; private set; }
        public float Elapsed { get; private set; }
        public long LastPending { get; private set; }
        public bool TimedOut { get; private set; }
        int m_Quiet;

        public G3PoseSettle() { }

        public G3PoseSettle(G3PoseArgs a)
        {
            if (a == null) return;
            MinFrames = a.SettleFrames; MinSeconds = a.SettleSeconds; MaxSeconds = a.MaxWaitSeconds;
        }

        public void Reset() { Frames = 0; Elapsed = 0f; LastPending = 0; TimedOut = false; m_Quiet = 0; }

        /// <summary>One rendered frame at the pose: <paramref name="dt"/> unscaled seconds, <paramref name="pendingLoads"/>
        /// texture mip loads in flight or queued (negative = unknown, treated as 0).</summary>
        public State Step(float dt, long pendingLoads)
        {
            Frames++;
            if (dt > 0f && !float.IsInfinity(dt)) Elapsed += dt;
            LastPending = Math.Max(0, pendingLoads);
            m_Quiet = LastPending == 0 ? m_Quiet + 1 : 0;
            if (Frames >= MinFrames && Elapsed >= MinSeconds && m_Quiet >= StableFrames) return State.Settled;
            if (Elapsed >= MaxSeconds) { TimedOut = true; return State.TimedOut; }
            return State.Waiting;
        }
    }
}
