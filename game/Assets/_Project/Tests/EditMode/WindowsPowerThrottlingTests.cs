using Game.Rendering;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>ADR 0333: the power-throttling opt-out is on by default and "-power_throttling default" switches it off.</summary>
    public class WindowsPowerThrottlingTests
    {
        [Test]
        public void OnByDefault()
        {
            Assert.IsTrue(WindowsPowerThrottling.WantedByArguments(null));
            Assert.IsTrue(WindowsPowerThrottling.WantedByArguments(new[] { "Kamion.exe", "-tier", "High" }));
            Assert.IsTrue(WindowsPowerThrottling.WantedByArguments(new[] { "Kamion.exe", "-power_throttling" }));
        }

        [Test]
        public void DefaultArgumentLeavesWindowsDefault()
        {
            Assert.IsFalse(WindowsPowerThrottling.WantedByArguments(new[] { "Kamion.exe", "-power_throttling", "default" }));
            Assert.IsFalse(WindowsPowerThrottling.WantedByArguments(new[] { "Kamion.exe", "-POWER_THROTTLING", "Default" }));
        }
    }
}
