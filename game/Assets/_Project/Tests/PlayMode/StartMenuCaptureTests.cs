using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using Game.Controls;
using Game.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>Renders the start menu and the settings panel to PNG (artifacts/visual-qa/menu, 1024 px wide) for review.</summary>
    public class StartMenuCaptureTests
    {
        static void Shot(Camera cam, string name)
        {
            const int w = 1024, h = 576;
            var rt = new RenderTexture(w, h, 24);
            cam.targetTexture = rt;
            cam.Render();
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(w, h, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, w, h), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            cam.targetTexture = null;
            string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "artifacts", "visual-qa", "menu"));
            Directory.CreateDirectory(dir);
            File.WriteAllBytes(Path.Combine(dir, name + ".png"), tex.EncodeToPNG());
            UnityEngine.Object.Destroy(tex); rt.Release(); UnityEngine.Object.Destroy(rt);
        }

        [UnityTest]
        public IEnumerator Capture_StartMenuAndSettings()
        {
            PlayerPrefs.DeleteKey(ControlSettings.PrefKey);
            var camGo = new GameObject("CaptureCam");
            var cam = camGo.AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.11f, 0.12f, 0.13f);
            cam.nearClipPlane = 0.05f; cam.farClipPlane = 10f;
            var starts = new List<(string, Action)>
            {
                ("DrivingLab — plac testowy", () => { }),
                ("Trasa G3-A — Kwadrat Park, brama, Bieżeństwa", () => { }),
                ("Trasa G3-B — Andersa, Rondo Putry", () => { }),
            };
            var menu = BootMenu.Create(cam, StartMenuOptions.Load(), starts, null);
            yield return null;
            Canvas.ForceUpdateCanvases();
            yield return null;
            Shot(cam, "start-menu");
            UnityEngine.Object.Destroy(menu.gameObject);

            var panel = ControlSettingsPanel.Create(cam, ControlSettings.Load(), null, null);
            yield return null;
            Canvas.ForceUpdateCanvases();
            yield return null;
            Shot(cam, "settings");
            UnityEngine.Object.Destroy(panel.gameObject);
            UnityEngine.Object.Destroy(camGo);
            PlayerPrefs.DeleteKey(ControlSettings.PrefKey);
        }
    }
}
