using System.Collections;
using Game.World;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// Automatic depot boom barrier (<see cref="DepotBarrier"/>, map audit MA-003): approach -> opens -> the whole
    /// combination passes -> closes; a closed boom stops a slow body; a fast body breaks the boom away without being
    /// stopped by an immovable wall. Bodies are plain boxes (tractor / trailer proxies) with gravity off, so the test
    /// does not depend on the vehicle model or on a world scene.
    /// </summary>
    public class DepotBarrierTests
    {
        static readonly Vector3 O = new Vector3(0f, -300f, 0f);
        const float BoomL = 5.85f;
        GameObject m_Root;
        float m_PrevScale;
        SimulationMode m_PrevMode;

        [SetUp]
        public void SetUp()
        {
            m_PrevScale = Time.timeScale;
            m_PrevMode = Physics.simulationMode;
            Physics.simulationMode = SimulationMode.FixedUpdate;
            Time.timeScale = 8f;
            m_Root = new GameObject("BarrierTest");
        }

        [TearDown]
        public void TearDown()
        {
            Object.DestroyImmediate(m_Root);
            Time.timeScale = m_PrevScale;
            Physics.simulationMode = m_PrevMode;
        }

        /// <summary>Same construction as WorldSceneBuilder.BuildBarriers: hinge at the origin, boom along +x, traffic along +z.</summary>
        DepotBarrier Barrier(bool automatic)
        {
            var go = new GameObject("DepotBarrier") { layer = 2 };
            go.transform.SetParent(m_Root.transform, false);
            go.transform.position = O + new Vector3(0f, 0.95f, 0f);
            var bc = go.AddComponent<BoxCollider>();
            bc.center = new Vector3(BoomL * 0.5f, 0f, 0f);
            bc.size = new Vector3(BoomL, 0.10f, 0.10f);
            var rb = go.AddComponent<Rigidbody>();
            rb.isKinematic = true;
            rb.useGravity = false;
            var bar = go.AddComponent<DepotBarrier>();
            bar.boomLengthM = BoomL;
            bar.travelSign = 1f;
            bar.automatic = automatic;
            return bar;
        }

        /// <summary>Box body 2.5 m wide, 3 m high, centred on the lane; z = centre.</summary>
        Rigidbody Body(string name, float z, float lengthM, float massKg, float speedMps)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(m_Root.transform, false);
            go.transform.position = O + new Vector3(BoomL * 0.5f, 1.7f, z);
            go.transform.localScale = new Vector3(2.5f, 3f, lengthM);
            var rb = go.AddComponent<Rigidbody>();
            rb.mass = massKg;
            rb.useGravity = false;
            rb.linearDamping = 0f;
            rb.constraints = RigidbodyConstraints.FreezeRotation | RigidbodyConstraints.FreezePositionX | RigidbodyConstraints.FreezePositionY;
            rb.linearVelocity = new Vector3(0f, 0f, speedMps);
            return rb;
        }

        [UnityTest]
        public IEnumerator Combination_Approach_Opens_Passes_Closes()
        {
            var bar = Barrier(true);
            const float v = 2.5f;                       // 9 km/h, depot speed
            var tractor = Body("Tractor", -20f, 6f, 7500f, v);
            var trailer = Body("Trailer", -31f, 13.6f, 12000f, v);
            yield return new WaitForFixedUpdate();
            yield return new WaitForFixedUpdate();
            Assert.AreEqual(DepotBarrier.BarrierState.Opening, bar.State, "boom starts up when the tractor enters the loop");
            bool openBeforeArrival = false, closedOnTrailer = false;
            float tOpen = -1f, t0 = Time.fixedTime;
            for (int i = 0; i < 6000 && trailer.position.z - O.z < 30f; i++)
            {
                tractor.linearVelocity = new Vector3(0f, 0f, v);
                trailer.linearVelocity = new Vector3(0f, 0f, v);
                yield return new WaitForFixedUpdate();
                if (bar.State == DepotBarrier.BarrierState.Open && tOpen < 0f) tOpen = Time.fixedTime - t0;
                float front = tractor.position.z - O.z + 3f, rear = trailer.position.z - O.z - 6.8f;
                if (front < -0.5f && bar.State == DepotBarrier.BarrierState.Open) openBeforeArrival = true;
                // while any part of the combination is over the boom line the boom must stay fully up
                if (front > -0.5f && rear < 0.5f && bar.State != DepotBarrier.BarrierState.Open) closedOnTrailer = true;
                Assert.AreNotEqual(DepotBarrier.BarrierState.Broken, bar.State, "boom must not be hit at depot speed");
            }
            Assert.IsTrue(openBeforeArrival, "boom fully open before the tractor reaches it");
            Assert.That(tOpen, Is.InRange(3f, 6f), "opening time (s)");
            Assert.IsFalse(closedOnTrailer, "boom never comes down on the combination");
            Assert.Greater(trailer.position.z - O.z - 6.8f, bar.exitM, "combination is past the loop");
            for (int i = 0; i < 3000 && bar.State != DepotBarrier.BarrierState.Closed; i++) yield return new WaitForFixedUpdate();
            Assert.AreEqual(DepotBarrier.BarrierState.Closed, bar.State, "boom closes after the combination");
            Assert.That(bar.AngleDeg, Is.EqualTo(0f).Within(0.01f));
            Debug.Log($"[TEST] DepotBarrier: open after {tOpen:F2} s, combination passed, closed");
        }

        [UnityTest]
        public IEnumerator Closed_Boom_Blocks_Slow_Body()
        {
            var bar = Barrier(false);
            var car = Body("Car", -6f, 4f, 1500f, 1.0f);
            for (int i = 0; i < 1200; i++) yield return new WaitForFixedUpdate();
            Assert.AreEqual(DepotBarrier.BarrierState.Closed, bar.State);
            Assert.Less(car.position.z - O.z + 2f, 0.2f, "front of the body stays before the boom line");
        }

        [UnityTest]
        public IEnumerator Forced_Passage_Breaks_Boom_Away()
        {
            var bar = Barrier(false);
            const float v = 6f;
            var truck = Body("Truck", -10f, 6f, 7500f, v);
            for (int i = 0; i < 600 && truck.position.z - O.z < 12f; i++) yield return new WaitForFixedUpdate();
            Assert.AreEqual(DepotBarrier.BarrierState.Broken, bar.State, "boom released by the impact");
            Assert.IsFalse(bar.GetComponent<Rigidbody>().isKinematic, "released boom is a free dynamic body");
            Assert.Greater(truck.position.z - O.z, 10f, "truck went through");
            Assert.Greater(truck.linearVelocity.z, v * 0.9f, "a 14 kg boom does not stop a 7.5 t truck (no immovable wall)");
            Debug.Log($"[TEST] DepotBarrier: forced passage, truck speed after {truck.linearVelocity.z:F2} m/s of {v:F1}");
        }
    }
}
