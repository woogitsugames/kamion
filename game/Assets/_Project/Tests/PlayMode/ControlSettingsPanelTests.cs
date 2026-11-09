using System.Collections;
using System.IO;
using System.Text.RegularExpressions;
using Game.Controls;
using Game.Gameplay;
using Game.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace Game.Tests
{
    public class ControlSettingsPanelTests
    {
        [SetUp] public void SetUp() { PlayerPrefs.DeleteKey(ControlSettings.PrefKey); }
        [TearDown] public void TearDown() { PlayerPrefs.DeleteKey(ControlSettings.PrefKey); }

        static void Click(GameObject root, string buttonName)
        {
            foreach (var b in root.GetComponentsInChildren<Button>(true))
                if (b.name == buttonName) { b.onClick.Invoke(); return; }
            Assert.Fail("button not found: " + buttonName);
        }

        [UnityTest]
        public IEnumerator Panel_ButtonsEditSaveAndLog()
        {
            var s = ControlSettings.Load();
            int changed = 0;
            LogAssert.ignoreFailingMessages = false;
            var p = ControlSettingsPanel.Create(null, s, () => changed++, null);
            yield return null;
            LogAssert.Expect(LogType.Log, new Regex(@"\[CONTROLS\] changed"));
            Click(p.gameObject, "+");   // first stepper: wheel range 270 -> 360
            Assert.AreEqual(360f, s.wheelRangeDeg);
            Assert.AreEqual(1, changed);
            LogAssert.Expect(LogType.Log, new Regex(@"\[CONTROLS\] changed .*steer=gyro"));
            Click(p.gameObject, "gyro");
            Assert.IsTrue(s.gyroEnabled);
            LogAssert.Expect(LogType.Log, new Regex(@"\[CONTROLS\] changed .*gyroInvert=on"));
            Click(p.gameObject, "odwrócony");
            Assert.IsTrue(s.gyroInvert);
            LogAssert.Expect(LogType.Log, new Regex(@"\[CONTROLS\] changed .*throttle=linear"));
            Click(p.gameObject, "liniowa");   // first matching button: throttle curve
            Assert.IsFalse(s.throttleProgressive);
            Assert.AreEqual(s.ToJson(), ControlSettings.Load().ToJson(), "every click is saved");
            LogAssert.Expect(LogType.Log, new Regex(@"\[CONTROLS\] reset"));
            Click(p.gameObject, "Przywróć domyślne");
            Assert.AreEqual(ControlSettings.Defaults().ToJson(), s.ToJson());
            Assert.AreEqual(ControlSettings.Defaults().ToJson(), ControlSettings.Load().ToJson());
            Object.Destroy(p.gameObject);
        }

        [Test]
        public void Step_StaysOnGridAndClamps()
        {
            Assert.AreEqual(360f, ControlSettingsPanel.Step(270f, +1, 90f, 180f, 900f));
            Assert.AreEqual(180f, ControlSettingsPanel.Step(180f, -1, 90f, 180f, 900f));
            Assert.AreEqual(900f, ControlSettingsPanel.Step(900f, +1, 90f, 180f, 900f));
            float v = 1f;
            for (int i = 0; i < 7; i++) v = ControlSettingsPanel.Step(v, +1, 0.1f, 0.5f, 2f);
            Assert.AreEqual(1.7f, v, 1e-5f, "no accumulated float drift");
        }

        [Test]
        public void StartRequest_IsConsumedOnce()
        {
            StartRequest.Consume(out _, out _);
            LogAssert.Expect(LogType.Log, new Regex(@"\[START\] menu choice 'G3-B'"));
            StartRequest.Set("G3-B", StartRequest.G3BStartS, StartRequest.G3BEndS);
            Assert.IsTrue(StartRequest.Consume(out float s, out float e));
            Assert.AreEqual(1232f, s); Assert.AreEqual(1718f, e);
            Assert.IsFalse(StartRequest.Consume(out _, out _));
        }

        /// <summary>Explicit: renders the panel to artifacts/ui/control-settings.png (960x540). Needs a GPU.</summary>
        [UnityTest, Explicit("visual capture, run on demand")]
        public IEnumerator Capture_SettingsPanel()
        {
            var camGo = new GameObject("CaptureCam");
            var cam = camGo.AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(0.30f, 0.34f, 0.38f);
            var p = ControlSettingsPanel.Create(cam, ControlSettings.Defaults(), null, null);
            yield return null;
            var rt = new RenderTexture(960, 540, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            cam.targetTexture = rt;
            Canvas.ForceUpdateCanvases();
            cam.Render();
            yield return null;
            cam.Render();
            RenderTexture.active = rt;
            var tex = new Texture2D(960, 540, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, 960, 540), 0, 0); tex.Apply();
            RenderTexture.active = null;
            string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "artifacts", "ui"));
            Directory.CreateDirectory(dir);
            File.WriteAllBytes(Path.Combine(dir, "control-settings.png"), tex.EncodeToPNG());
            Object.Destroy(p.gameObject); Object.Destroy(camGo);
        }
    }
}
