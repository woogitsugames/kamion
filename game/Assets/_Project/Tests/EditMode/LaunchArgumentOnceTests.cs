using System.IO;
using Game.Gameplay;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// Review H3 P1-141-1 (int-h3-s23): the launch argument scene= (Kamion-&lt;region&gt;.cmd, adb -e scene) is used by the first
    /// Boot of the process only. Without it a start with no free place (ADR 0277: region → Boot) reloaded the region forever,
    /// and "Menu" after a launcher start went straight back into the region.
    /// </summary>
    public class LaunchArgumentOnceTests
    {
        [SetUp] public void SetUp() => GameBootstrap.ResetLaunchArguments();
        [TearDown] public void TearDown() => GameBootstrap.ResetLaunchArguments();

        [Test]
        public void FirstBootTakesTheArguments_LaterBootsShowTheMenu()
        {
            Assert.IsTrue(GameBootstrap.TakeLaunchArguments(), "process start: -scene is honoured");
            // FailStart → Boot (ADR 0277), then the menu button → Boot: neither may jump into the scene again.
            Assert.IsFalse(GameBootstrap.TakeLaunchArguments(), "back in Boot after a failed start");
            Assert.IsFalse(GameBootstrap.TakeLaunchArguments(), "back in Boot through the menu button");
        }

        [Test]
        public void ProcessStartResetsTheFlag()
        {
            GameBootstrap.TakeLaunchArguments();
            GameBootstrap.ResetLaunchArguments();   // RuntimeInitializeOnLoadMethod(SubsystemRegistration) = new process / play mode
            Assert.IsTrue(GameBootstrap.TakeLaunchArguments());
        }

        [Test]
        public void SceneArgumentIsReadOnlyBehindTheGuard()
        {
            // Source guard: the pending scene is set only inside the TakeLaunchArguments() branch of Awake.
            string path = Path.Combine(Application.dataPath, "_Project/Gameplay/GameBootstrap.cs");
            string src = File.ReadAllText(path);
            int guard = src.IndexOf("if (TakeLaunchArguments())", System.StringComparison.Ordinal);
            int pending = src.IndexOf("m_PendingScene = scene", System.StringComparison.Ordinal);
            int autoshot = src.IndexOf("DesktopAutoShot.StartFromArguments(", System.StringComparison.Ordinal);
            Assert.Greater(guard, 0, "guard present in GameBootstrap.Awake");
            Assert.Greater(pending, guard, "m_PendingScene is assigned after (inside) the guard");
            Assert.Greater(autoshot, guard, "DesktopAutoShot (DontDestroyOnLoad) is created once per process");
            Assert.AreEqual(pending, src.LastIndexOf("m_PendingScene = scene", System.StringComparison.Ordinal),
                "no second assignment of the launch scene outside the guard");
        }
    }
}
