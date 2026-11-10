using System;
using System.Collections;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using Game.Controls;
using Game.Gameplay;
using Game.Rendering;
using Game.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace Game.Tests
{
    /// <summary>Owner feel-test flow: start menu options, [CONTROLS] logging, settings (camera), return to the menu.</summary>
    public class StartMenuFlowTests
    {
        string m_Tier; int m_Fps;

        [SetUp]
        public void SetUp()
        {
            PlayerPrefs.DeleteKey(ControlSettings.PrefKey);
            PlayerPrefs.DeleteKey(StartMenuOptions.PrefLighting);
            m_Tier = QualityTiers.Current; m_Fps = Application.targetFrameRate;
            StartRequest.Consume(out _, out _); StartRequest.ConsumeLighting();
        }

        [TearDown]
        public void TearDown()
        {
            PlayerPrefs.DeleteKey(ControlSettings.PrefKey);
            PlayerPrefs.DeleteKey(StartMenuOptions.PrefLighting);
            QualityTiers.Apply(m_Tier); Application.targetFrameRate = m_Fps;
        }

        static void Click(GameObject root, string buttonName)
        {
            foreach (var b in root.GetComponentsInChildren<Button>(true))
                if (b.name == buttonName) { b.onClick.Invoke(); return; }
            Assert.Fail("button not found: " + buttonName);
        }

        [UnityTest]
        public IEnumerator Menu_OptionsApplyPersistAndLog_StartLogsWholeChoice()
        {
            string started = null;
            var starts = new List<(string, Action)> { ("Trasa test", () => started = "route"), ("DrivingLab test", () => started = "lab") };
            var menu = BootMenu.Create(null, StartMenuOptions.Load(), starts, null);
            yield return null;

            LogAssert.Expect(LogType.Log, new Regex(@"\[CONTROLS\] menu light=dusk"));
            Click(menu.gameObject, "Zmierzch");
            Assert.AreEqual("dusk", menu.Options.LightingId);
            Assert.AreEqual(2, PlayerPrefs.GetInt(StartMenuOptions.PrefLighting), "time of day persists");

            LogAssert.Expect(LogType.Log, new Regex(@"\[CONTROLS\] menu tier=Medium"));
            Click(menu.gameObject, "Medium");
            Assert.AreEqual("Medium", QualityTiers.Current);
            Assert.AreEqual("Medium", QualityTiers.SavedTier, "tier persists");

            LogAssert.Expect(LogType.Log, new Regex(@"\[CONTROLS\] menu fps=60"));
            Click(menu.gameObject, "60 FPS");
            Assert.AreEqual(60, Application.targetFrameRate);
            Assert.AreEqual(60, QualityTiers.SavedFrameRate);

            LogAssert.Expect(LogType.Log, new Regex(@"\[CONTROLS\] menu-start scene=Trasa test light=dusk tier=Medium fps=60"));
            Click(menu.gameObject, "Trasa test");
            Assert.AreEqual("route", started);
            UnityEngine.Object.Destroy(menu.gameObject);
        }

        [UnityTest]
        public IEnumerator Menu_ShowsAllOptionRows_AndSettingsEntry()
        {
            bool settings = false;
            var menu = BootMenu.Create(null, StartMenuOptions.Load(), new List<(string, Action)> { ("A", () => { }) }, () => settings = true);
            yield return null;
            foreach (string n in new[] { "Pochmurno", "Niskie słońce", "Zmierzch", "Low", "Medium", "High", "Ultra", "30 FPS", "60 FPS" })
                Assert.IsNotNull(Find(menu.gameObject, n), "missing control: " + n);
            Click(menu.gameObject, "Ustawienia sterowania");
            Assert.IsTrue(settings);
            UnityEngine.Object.Destroy(menu.gameObject);
        }

        static Button Find(GameObject root, string name)
        {
            foreach (var b in root.GetComponentsInChildren<Button>(true)) if (b.name == name) return b;
            return null;
        }

        [UnityTest]
        public IEnumerator SettingsPanel_CameraRows_EditSaveAndLog()
        {
            var s = ControlSettings.Load();
            var p = ControlSettingsPanel.Create(null, s, null, null);
            yield return null;
            LogAssert.Expect(LogType.Log, new Regex(@"\[CONTROLS\] changed .*headMotion=off"));
            Click(p.gameObject, "wyłączony");
            Assert.IsFalse(s.headMotion);
            Assert.IsFalse(ControlSettings.Load().headMotion, "saved");
            UnityEngine.Object.Destroy(p.gameObject);
        }

        [Test]
        public void StartRequest_CarriesLightingOnce()
        {
            StartRequest.Set("G3-A", 12f, 450f, "lowsun");
            Assert.AreEqual("lowsun", StartRequest.ConsumeLighting());
            Assert.AreEqual("", StartRequest.ConsumeLighting());
            StartRequest.Consume(out _, out _);
        }

        [UnityTest]
        public IEnumerator BootScene_ShowsMenu_AndDrivingLabReturnsToItWithoutRestart()
        {
            SceneManager.LoadScene("Boot", LoadSceneMode.Single);
            yield return null;
            var boot = UnityEngine.Object.FindAnyObjectByType<GameBootstrap>();
            Assert.IsNotNull(boot);
            Assert.IsNotNull(boot.Menu, "start menu missing");
            Click(boot.Menu.gameObject, "DrivingLab — plac testowy");   // menu-start log + scene load
            yield return null; yield return null;
            var lab = UnityEngine.Object.FindAnyObjectByType<DrivingLabBootstrap>();
            Assert.IsNotNull(lab, "DrivingLab did not start");
            lab.ReturnToMenu();
            yield return null; yield return null;
            boot = UnityEngine.Object.FindAnyObjectByType<GameBootstrap>();
            Assert.IsNotNull(boot, "Boot scene not reloaded");
            Assert.IsNotNull(boot.Menu, "start menu missing after returning");
            Assert.IsNull(UnityEngine.Object.FindAnyObjectByType<DrivingLabBootstrap>());
        }
    }
}
