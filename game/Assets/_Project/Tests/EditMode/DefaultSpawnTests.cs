using Game.Gameplay;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>ADR 0134 owner decision: first start / no explicit choice = 24 t payload; an explicit stored choice is kept.</summary>
    public class DefaultSpawnTests
    {
        [Test]
        public void NoStoredChoice_DefaultsToCargo24t()
        {
            Assert.AreEqual(DrivingLabBootstrap.LabSpawn.Cargo24t, DrivingLabBootstrap.DefaultSpawn);
            Assert.AreEqual(DrivingLabBootstrap.LabSpawn.Cargo24t, DrivingLabBootstrap.StoredOrDefaultSpawn(false, 0));
        }

        [TestCase(0, DrivingLabBootstrap.LabSpawn.Solo)]
        [TestCase(1, DrivingLabBootstrap.LabSpawn.Empty)]
        [TestCase(3, DrivingLabBootstrap.LabSpawn.Gross40t)]
        [TestCase(9, DrivingLabBootstrap.LabSpawn.Gross40t)]
        public void StoredChoice_IsKept(int stored, DrivingLabBootstrap.LabSpawn expected)
        {
            Assert.AreEqual(expected, DrivingLabBootstrap.StoredOrDefaultSpawn(true, stored));
        }
    }
}
