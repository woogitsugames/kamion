using System;
using System.Globalization;
using System.IO;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Evidence run of a desktop player without a person at the keyboard (ADR 0261): launch arguments
    /// <c>-shot &lt;file.png&gt; [-shot_t 20] [-quit_t 30]</c> save one screenshot of the back buffer (HUD included) shot_t
    /// seconds after start and quit the player after quit_t seconds (quit_t alone = timed run for the [DIAG] frame
    /// statistics). Survives scene loads; does nothing without the arguments. Unscaled time, no per-frame allocation.
    /// ADR 0302: <c>-shot_every &lt;s&gt;</c> also saves <c>&lt;file&gt;_t&lt;seconds&gt;.png</c> every s seconds after shot_t
    /// (evidence of the GPS before / after a seam; allocates only when it shoots).
    /// </summary>
    public sealed class DesktopAutoShot : MonoBehaviour
    {
        string m_Path;
        float m_ShotAt = -1f, m_QuitAt = -1f, m_Every = -1f, m_NextEvery = -1f;
        bool m_Shot;

        /// <summary>Parses "12.5" style seconds; negative / missing / not a number = <paramref name="fallback"/>.</summary>
        public static float ParseSeconds(string text, float fallback)
        {
            return float.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out float v) && v >= 0f ? v : fallback;
        }

        /// <summary>Creates the runner when shot= or quit_t= is given. Returns null otherwise.</summary>
        public static DesktopAutoShot StartFromArguments(Func<string, string> arg)
        {
            string path = arg("shot");
            float quit = ParseSeconds(arg("quit_t"), -1f);
            if (string.IsNullOrEmpty(path) && quit < 0f) return null;
            var go = new GameObject("DesktopAutoShot");
            DontDestroyOnLoad(go);
            var a = go.AddComponent<DesktopAutoShot>();
            a.m_Path = path;
            a.m_ShotAt = string.IsNullOrEmpty(path) ? -1f : ParseSeconds(arg("shot_t"), 20f);
            a.m_QuitAt = quit;
            a.m_Every = string.IsNullOrEmpty(path) ? -1f : ParseSeconds(arg("shot_every"), -1f);
            if (a.m_Every > 0f) a.m_NextEvery = a.m_ShotAt + a.m_Every;
            // An unattended periodic evidence run must keep driving when another window takes focus (as G3PoseRunner).
            if (a.m_Every > 0f) Application.runInBackground = true;
            Debug.Log($"[AUTOSHOT] shot='{path}' shot_t={a.m_ShotAt.ToString("F1", CultureInfo.InvariantCulture)} quit_t={a.m_QuitAt.ToString("F1", CultureInfo.InvariantCulture)}");
            return a;
        }

        /// <summary>Take at most one periodic screenshot after a stall/pause; missed captures cannot be recovered.</summary>
        public static bool TryTakePeriodicShot(float now, float every, float quitAt, ref float nextAt)
        {
            if (every <= 0f || now < nextAt || (quitAt >= 0f && now >= quitAt - 1f)) return false;
            nextAt = now + every;
            return true;
        }

        void Update()
        {
            float t = Time.realtimeSinceStartup;
            if (!m_Shot && m_ShotAt >= 0f && t >= m_ShotAt)
            {
                m_Shot = true;
                try
                {
                    string dir = Path.GetDirectoryName(Path.GetFullPath(m_Path));
                    if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
                    ScreenCapture.CaptureScreenshot(m_Path);
                    Debug.Log($"[AUTOSHOT] screenshot {m_Path} {Screen.width}x{Screen.height} scene={UnityEngine.SceneManagement.SceneManager.GetActiveScene().name}");
                }
                catch (Exception e) { Debug.LogWarning("[AUTOSHOT] screenshot failed: " + e.Message); }
            }
            if (TryTakePeriodicShot(t, m_Every, m_QuitAt, ref m_NextEvery))
            {
                string p = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(m_Path)) ?? "",
                    Path.GetFileNameWithoutExtension(m_Path) + "_t" + Mathf.RoundToInt(t).ToString("D4", CultureInfo.InvariantCulture) + ".png");
                ScreenCapture.CaptureScreenshot(p);
                Debug.Log($"[AUTOSHOT] screenshot {p}");
            }
            if (m_QuitAt >= 0f && t >= m_QuitAt)
            {
                m_QuitAt = -1f;
                Debug.Log("[AUTOSHOT] quit");
                Application.Quit(0);
            }
        }
    }
}
