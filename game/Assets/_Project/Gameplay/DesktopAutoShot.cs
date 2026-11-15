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
    /// </summary>
    public sealed class DesktopAutoShot : MonoBehaviour
    {
        string m_Path;
        float m_ShotAt = -1f, m_QuitAt = -1f;
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
            Debug.Log($"[AUTOSHOT] shot='{path}' shot_t={a.m_ShotAt.ToString("F1", CultureInfo.InvariantCulture)} quit_t={a.m_QuitAt.ToString("F1", CultureInfo.InvariantCulture)}");
            return a;
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
            if (m_QuitAt >= 0f && t >= m_QuitAt)
            {
                m_QuitAt = -1f;
                Debug.Log("[AUTOSHOT] quit");
                Application.Quit(0);
            }
        }
    }
}
