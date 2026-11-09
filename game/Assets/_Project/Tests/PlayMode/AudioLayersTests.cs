using System.Collections;
using Game.Gameplay;
using NUnit.Framework;
using TruckSim.Audio;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>Audio-layers pass: parameter mapping (pure maths) and wiring in the driving lab.</summary>
    public sealed class AudioLayersTests
    {
        [Test]
        public void Squeal_IsSilentBelowOnsetAndFullWellAboveIt()
        {
            Assert.AreEqual(0f, LayerMath.SquealGain(0.5f, 15f), 1e-6f);
            Assert.AreEqual(0f, LayerMath.SquealGain(0.8f, 15f), 1e-6f);
            Assert.AreEqual(1f, LayerMath.SquealGain(1.5f, 15f), 1e-6f);
            Assert.Greater(LayerMath.SquealGain(1.1f, 15f), 0.2f);
            Assert.Less(LayerMath.SquealGain(1.1f, 15f), 0.9f);
            Assert.AreEqual(0f, LayerMath.SquealGain(2f, 1.0f), 1e-6f, "no squeal when (almost) stationary");
        }

        [Test]
        public void CombinedSlip_IsOneAtTheReferenceSlips()
        {
            Assert.AreEqual(1f, LayerMath.CombinedSlip(LayerMath.KappaRef, 0f), 1e-5f);
            Assert.AreEqual(1f, LayerMath.CombinedSlip(0f, LayerMath.AlphaRef), 1e-5f);
            Assert.AreEqual(Mathf.Sqrt(2f), LayerMath.CombinedSlip(LayerMath.KappaRef, LayerMath.AlphaRef), 1e-5f);
        }

        [Test]
        public void SurfaceTables_CoverEverySurfaceKind()
        {
            Assert.AreEqual(LayerMath.SurfaceCount, LayerMath.SurfaceLevel.Length);
            Assert.AreEqual(LayerMath.SurfaceCount, LayerMath.SurfaceSpeedExp.Length);
            Assert.AreEqual(LayerMath.SurfaceCount, LayerMath.SurfaceSquealable.Length);
            Assert.AreEqual(LayerMath.SurfaceCount, System.Enum.GetValues(typeof(Game.Vehicle.Runtime.SurfaceKind)).Length,
                "SurfaceKind changed: extend the tyre loops");
            Assert.Greater(LayerMath.TyreGain(5f, 3, 1f), LayerMath.TyreGain(5f, 0, 1f), "cobbles are louder than asphalt at crawling speed");
            Assert.AreEqual(0f, LayerMath.TyreGain(0f, 0, 1f), 1e-6f);
        }

        [Test]
        public void Pitch_RisesWithSpeedAndRpm()
        {
            Assert.Less(LayerMath.RetarderPitch(5f), LayerMath.RetarderPitch(20f));
            Assert.Less(LayerMath.TyrePitch(5f), LayerMath.TyrePitch(20f));
            Assert.Less(LayerMath.CompressorPitch(700f), LayerMath.CompressorPitch(1500f));
            Assert.AreEqual(0f, LayerMath.RetarderGain(0f, 1f), 1e-6f);
            Assert.AreEqual(1f, LayerMath.RetarderGain(1f, 1f), 1e-6f);
        }

        [Test]
        public void IndicatorClock_TicksAndTocksAtNinetyPerMinute()
        {
            var c = new IndicatorClock();
            int ticks = 0, tocks = 0, first = 0;
            const float dt = 1f / 60f;
            for (int i = 0; i < 600; i++) // 10 s
            {
                int ev = c.Advance(dt, true);
                if (ev != 0 && first == 0) first = ev;
                if (ev == 1) ticks++; else if (ev == 2) tocks++;
            }
            Assert.AreEqual(1, first, "first contact closes immediately");
            Assert.That(ticks, Is.InRange(14, 16), "10 s at 90 flashes/min");
            Assert.That(tocks, Is.InRange(14, 16));
            Assert.AreEqual(0, c.Advance(dt, false));
            Assert.AreEqual(1, c.Advance(dt, true), "re-arming after the lever is released");
        }

        [UnityTest]
        public IEnumerator DrivingLab_HasTheAudioLayers()
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            var lib = VehicleAudioLibrary.LoadDefault();
            if (lib == null) { Assert.Ignore("VehicleAudioLibrary not generated"); yield break; }
            var audio = Object.FindAnyObjectByType<TruckAudioController>();
            Assert.IsNotNull(audio);
            Assert.AreEqual(LayerMath.SurfaceCount, lib.tyreSurface.Length);
            for (int i = 0; i < lib.tyreSurface.Length; i++)
            {
                Assert.IsTrue(lib.tyreSurface[i].IsValid, "tyre loop " + i + " missing (re-run render_all.py + import)");
                Assert.IsNotNull(lib.tyreSurface[i].cab, "tyre cab loop " + i);
            }
            Assert.IsTrue(lib.tyreSqueal.IsValid && lib.retarder.IsValid && lib.compressor.IsValid && lib.ambientBed.IsValid && lib.forklift.IsValid);
            Assert.IsTrue(lib.indicatorTick.IsValid && lib.indicatorTock.IsValid && lib.crowCaw.IsValid);
            Assert.IsNotNull(lib.parkingBrakeRelease);
            Assert.IsNotNull(lib.airBrakeReleaseCab);
            Assert.IsTrue(audio.AmbientReady, "ambient bed not started");
            float sum = 0f;
            for (int i = 0; i < LayerMath.SurfaceCount; i++) sum += audio.SurfaceWeight(i);
            Assert.AreEqual(1f, sum, 0.02f, "surface weights must sum to 1 when the truck stands on the ground");
            Assert.AreEqual(0f, audio.SquealLevel, 0.01f, "parked truck must not squeal");
            Debug.Log($"[TEST] audio layers: surface weights sum {sum:F3}, ambient {audio.AmbientReady}, surface 0 weight {audio.SurfaceWeight(0):F2}");
        }
    }
}
