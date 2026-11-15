using System.IO;
using Game.Controls;
using Game.Editor.Build;
using Game.Gameplay;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0261: Windows player defaults (tier, frame-rate cap), gamepad axis shaping, evidence-run arguments.</summary>
    public class WindowsBuildTests
    {
        [Test]
        public void DesktopPlayer_DefaultsToHighAnd60_PhonesAndEditorKeepTheirOwn()
        {
            Assert.AreEqual("High", GameBootstrap.DesktopDefaultTier(RuntimePlatform.WindowsPlayer));
            Assert.IsNull(GameBootstrap.DesktopDefaultTier(RuntimePlatform.Android));
            Assert.IsNull(GameBootstrap.DesktopDefaultTier(RuntimePlatform.IPhonePlayer));
            Assert.IsNull(GameBootstrap.DesktopDefaultTier(RuntimePlatform.WindowsEditor));
            Assert.AreEqual(GameBootstrap.DesktopTargetFps, GameBootstrap.DesktopDefaultFps(RuntimePlatform.WindowsPlayer, 30));
            Assert.AreEqual(30, GameBootstrap.DesktopDefaultFps(RuntimePlatform.Android, 30));
            Assert.AreEqual(30, GameBootstrap.DesktopDefaultFps(RuntimePlatform.WindowsEditor, 30));
            Assert.Contains("High", Game.Rendering.QualityTiers.Names);
        }

        [Test]
        public void GamepadAxis_DeadZoneFullRangeSignAndProgressiveCurve()
        {
            Assert.AreEqual(0f, GamepadDriverInput.ShapeAxis(0.1f, 0.12f, 1.8f));
            Assert.AreEqual(0f, GamepadDriverInput.ShapeAxis(-0.12f, 0.12f, 1.8f));
            Assert.AreEqual(1f, GamepadDriverInput.ShapeAxis(1f, 0.12f, 1.8f), 1e-5f);
            Assert.AreEqual(-1f, GamepadDriverInput.ShapeAxis(-1f, 0.12f, 1.8f), 1e-5f);
            float half = GamepadDriverInput.ShapeAxis(0.56f, 0.12f, 1.8f);   // half of the live travel
            Assert.AreEqual(Mathf.Pow(0.5f, 1.8f), half, 1e-4f);
            Assert.Less(half, 0.5f, "progressive: half stick is less than half lock");
            Assert.AreEqual(-half, GamepadDriverInput.ShapeAxis(-0.56f, 0.12f, 1.8f), 1e-6f);
            Assert.AreEqual(0.5f, GamepadDriverInput.ShapeAxis(0.56f, 0.12f, 0.2f), 1e-4f, "curve below 1 is clamped to linear");
        }

        [Test]
        public void GamepadTrigger_DeadZoneAndFullTravel()
        {
            Assert.AreEqual(0f, GamepadDriverInput.ShapeTrigger(0.03f, 0.04f));
            Assert.AreEqual(1f, GamepadDriverInput.ShapeTrigger(1f, 0.04f), 1e-6f);
            Assert.AreEqual(0.5f, GamepadDriverInput.ShapeTrigger(0.52f, 0.04f), 1e-4f);
        }

        [Test]
        public void AutoShot_ParseSeconds_InvariantCulture_FallbackOnGarbage()
        {
            Assert.AreEqual(12.5f, DesktopAutoShot.ParseSeconds("12.5", -1f));
            Assert.AreEqual(-1f, DesktopAutoShot.ParseSeconds(null, -1f));
            Assert.AreEqual(20f, DesktopAutoShot.ParseSeconds("abc", 20f));
            Assert.AreEqual(20f, DesktopAutoShot.ParseSeconds("-3", 20f));
            Assert.IsNull(DesktopAutoShot.StartFromArguments(_ => null), "no arguments = no runner object");
        }

        [Test]
        public void WindowsEntryPoint_ExistsWithTheNameTheScriptCalls()
        {
            Assert.IsNotNull(typeof(BuildCommands).GetMethod("BuildWindowsPlayer"), "scripts/build-windows.ps1 calls Game.Editor.Build.BuildCommands.BuildWindowsPlayer");
            Assert.AreEqual("Kamion.exe", BuildCommands.WindowsExeName);
            string script = Path.Combine(EditorTools.RepoRoot, "scripts", "build-windows.ps1");
            Assert.IsTrue(File.Exists(script), script);
            StringAssert.Contains("Game.Editor.Build.BuildCommands.BuildWindowsPlayer", File.ReadAllText(script));
        }
    }
}
