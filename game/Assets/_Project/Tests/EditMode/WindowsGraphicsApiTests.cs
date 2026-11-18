using Game.Core.Settings;
using Game.Editor.Setup;
using NUnit.Framework;
using UnityEditor;
using UnityEngine.Rendering;

namespace Game.Tests
{
    /// <summary>ADR 0291: Direct3D 11 is the default Windows API, Direct3D 12 the opt-in second (-force-d3d12).</summary>
    public class WindowsGraphicsApiTests
    {
        [Test]
        public void Order_IsD3D11ThenD3D12()
        {
            CollectionAssert.AreEqual(new[] { GraphicsDeviceType.Direct3D11, GraphicsDeviceType.Direct3D12 },
                ProjectSetup.WindowsGraphicsApis);
        }

        [Test]
        public void Apply_WritesExplicitListInOrder_AndIsIdempotent()
        {
            var target = BuildTarget.StandaloneWindows64;
            bool prevAuto = PlayerSettings.GetUseDefaultGraphicsAPIs(target);
            var prevApis = PlayerSettings.GetGraphicsAPIs(target);
            try
            {
                ProjectSetup.ApplyWindowsGraphicsApis();
                ProjectSetup.ApplyWindowsGraphicsApis();
                Assert.IsFalse(PlayerSettings.GetUseDefaultGraphicsAPIs(target), "automatic API list must be off");
                CollectionAssert.AreEqual(ProjectSetup.WindowsGraphicsApis, PlayerSettings.GetGraphicsAPIs(target));
            }
            finally
            {
                PlayerSettings.SetUseDefaultGraphicsAPIs(target, prevAuto);
                if (!prevAuto) PlayerSettings.SetGraphicsAPIs(target, prevApis);
            }
        }

        [Test]
        public void ForcedD3D12_StillGetsExclusiveToBorderlessMitigation()
        {
            var forced = new[] { "Kamion.exe", "-force-d3d12" };
            Assert.AreEqual(WindowModes.Borderless, ExclusiveFullscreenPolicy.Effective(WindowModes.Exclusive, true, forced));
            Assert.AreEqual(WindowModes.Exclusive, ExclusiveFullscreenPolicy.Effective(WindowModes.Exclusive, false, forced));
            var allowed = new[] { "Kamion.exe", "-force-d3d12", ExclusiveFullscreenPolicy.AllowArgument };
            Assert.AreEqual(WindowModes.Exclusive, ExclusiveFullscreenPolicy.Effective(WindowModes.Exclusive, true, allowed));
        }
    }
}
