using Game.World;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0041 r8 (REVIEW r7 N-14): parked vehicles keep LOD0 up to WorldInstances.VehicleLod0MinM on every tier. On Low
    /// (lodBias 0.5) the car policy 25 / 90 / 300 m switched to LOD1 at 12.5 m, i.e. for the cars right beside the route.
    /// </summary>
    public class VehicleLodFloorTests
    {
        [Test]
        public void Lod0Floor_HoldsOnLow_LeavesHighAndSingleLodAlone()
        {
            var car = new[] { 25f, 90f, WorldInstances.VehicleCullM };
            float min = WorldInstances.VehicleLod0MinM;
            Assert.GreaterOrEqual(min, 15f);
            // Low: lodBias 0.5, fixed cull
            Assert.AreEqual(1, WorldInstances.LodAt(car, 15f, 0.5f, 1f), "without the floor");
            Assert.AreEqual(0, WorldInstances.LodAt(car, 15f, 0.5f, 1f, min));
            Assert.AreEqual(1, WorldInstances.LodAt(car, min + 0.5f, 0.5f, 1f, min));
            Assert.AreEqual(2, WorldInstances.LodAt(car, 46f, 0.5f, 1f, min));
            Assert.AreEqual(-1, WorldInstances.LodAt(car, WorldInstances.VehicleCullM + 1f, 0.5f, 1f, min));
            // High: lodBias 1.5, the policy is already above the floor
            Assert.AreEqual(0, WorldInstances.LodAt(car, 37f, 1.5f, 1f, min));
            Assert.AreEqual(1, WorldInstances.LodAt(car, 38f, 1.5f, 1f, min));
            // a single-LOD prototype (contact patch): the floor never extends its cull distance
            Assert.AreEqual(-1, WorldInstances.LodAt(new[] { 10f }, 12f, 1f, 1f, min));
        }
    }
}
