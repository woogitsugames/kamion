using System.Collections;
using Game.Gameplay;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>ADR 0009 R7 in the Unity adapter: a load change keeps the trailer model and re-masses the Rigidbody.</summary>
    public class TrailerCargoSwapTests
    {
        [UnityTest]
        public IEnumerator SetCargo_InPlace_RemassesRigidbody_AndSettles()
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            var trailer = Object.FindAnyObjectByType<TrailerBody>();
            boot.Spawn(DrivingLabBootstrap.LabSpawn.Gross40t);
            yield return new WaitForSeconds(1f);
            var model = trailer.Model;
            var combo = body.Combination;
            float laden = trailer.Body.mass;

            trailer.SetCargo(CargoPreset.Empty, body.Model.MassProps.Mass, body.Combination);
            Assert.AreSame(model, trailer.Model, "trailer model must be kept (no rebuild)");
            Assert.AreSame(combo, body.Combination, "combination must be kept (no rebuild)");
            Assert.AreEqual((float)model.MassProps.Mass, trailer.Body.mass, 1f, "Rigidbody mass follows MassProps");
            Assert.Less(trailer.Body.mass, laden - 10000f, "empty trailer is lighter");
            Assert.AreEqual(((Vector3)model.MassProps.CenterOfMass.ToUnity() - trailer.Body.centerOfMass).magnitude, 0f, 1e-3f, "CoM copied");

            Vector3 p0 = trailer.transform.position;
            yield return new WaitForSeconds(2f);
            var fw = body.Combination.FifthWheel;
            Debug.Log($"[TEST] cargo swap 40 t -> empty: trailer {laden / 1000f:F1} t -> {trailer.Body.mass / 1000f:F1} t, drift {(trailer.transform.position - p0).magnitude * 1000f:F1} mm, kingpin err {fw.PositionError * 1000:F2} mm");
            Assert.IsTrue(body.Coupled, "still coupled");
            Assert.Less(fw.PositionError, 0.005, "kingpin in the jaw after the swap");
            Assert.Less((trailer.transform.position - p0).magnitude, 0.08f, "combination settles after the swap");
        }
    }
}
