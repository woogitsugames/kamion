using System;
using System.Collections;
using Game.Controls;
using Game.Gameplay;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using TruckSim.Audio;
using UnityEngine;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0145: tyre scrub vs squeal. Mapping at the operating points measured in tools/physics-runner (circles with the
    /// tridem semi-trailer, tools/audio/tyre_slip_scan.py) and the full chain physics -> TruckAudioController on a 40 t
    /// combination in script simulation mode (0.01 s): standstill and straight driving are silent, a tight turn at
    /// 10 km/h scrubs and does not squeal, the audio step allocates nothing.
    /// </summary>
    public sealed class TyreScrubTests
    {
        const float Dt = 0.01f;
        static readonly Vector3 O = new Vector3(0f, -600f, 0f);
        SimulationMode m_PrevMode;
        GameObject m_World;
        VehicleBody m_Body;
        TrailerBody m_Trailer;

        // ------------------------------------------------------------------ mapping (pure)

        [Test]
        public void Mapping_AtMeasuredOperatingPoints()
        {
            float deg = Mathf.Deg2Rad;
            // R 12 m, 10 km/h, 40 t: trailer axles 1/3 at 9.4 deg, combined slip 1.64 (runner scrub_r12_10kmh@laden40)
            Assert.AreEqual(1f, LayerMath.ScrubGain(9.4f * deg, 10f / 3.6f), 1e-4f, "tight turn at 10 km/h scrubs fully");
            Assert.AreEqual(0f, LayerMath.SquealGain(1.64f, 10f / 3.6f), 1e-6f, "... and does not squeal");
            // R 12 m, 15 km/h: before ADR 0145 this was a full-level squeal
            Assert.AreEqual(0f, LayerMath.SquealGain(1.65f, 15f / 3.6f), 1e-6f);
            Assert.Greater(LayerMath.ScrubGain(9.5f * deg, 15f / 3.6f), 0.95f);
            // R 9 m at walking pace (5 km/h): 21 deg
            Assert.Greater(LayerMath.ScrubGain(21f * deg, 5f / 3.6f), 0.95f);
            // straight / standstill
            Assert.AreEqual(0f, LayerMath.ScrubGain(0.1f * deg, 80f / 3.6f), 1e-6f);
            Assert.AreEqual(0f, LayerMath.ScrubGain(20f * deg, 0f), 1e-6f, "no scrub at a standstill");
            Assert.AreEqual(0f, LayerMath.SquealGain(8f, 0f), 1e-6f, "no squeal at a standstill");
            // R 50 m at 50 km/h laden (3.9 m/s2): worst combined slip 1.0 -> no squeal, scrub faded out by speed
            Assert.AreEqual(0f, LayerMath.SquealGain(1.0f, 50f / 3.6f), 1e-6f);
            Assert.AreEqual(0f, LayerMath.ScrubGain(5.7f * deg, 50f / 3.6f), 1e-6f);
            // locked wheels (slip ratio 1) at 60 km/h: full squeal
            Assert.AreEqual(1f, LayerMath.SquealGain(LayerMath.CombinedSlip(1f, 0f), 60f / 3.6f), 1e-6f);
            // pitch rises with the sliding speed
            Assert.Less(LayerMath.ScrubPitch(2f * deg, 1f), LayerMath.ScrubPitch(20f * deg, 3f));
            Assert.AreEqual(LayerMath.SurfaceCount, LayerMath.SurfaceScrubbable.Length);
        }

        // ------------------------------------------------------------------ physics -> audio

        [SetUp]
        public void SetUp()
        {
            m_PrevMode = Physics.simulationMode;
            Physics.simulationMode = SimulationMode.Script;
            m_World = new GameObject("TyreScrubWorld");
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.transform.SetParent(m_World.transform, false);
            go.transform.SetPositionAndRotation(O + new Vector3(0, -0.5f, 0), Quaternion.identity);
            go.transform.localScale = new Vector3(900, 1, 900);
            go.AddComponent<GroundSurface>().kind = SurfaceKind.DryAsphalt;
        }

        [TearDown]
        public void TearDown()
        {
            if (m_Body != null) Object.DestroyImmediate(m_Body.gameObject);
            if (m_Trailer != null) Object.DestroyImmediate(m_Trailer.gameObject);
            Object.DestroyImmediate(m_World);
            Physics.simulationMode = m_PrevMode;
        }

        TruckAudioController Spawn(float kmh)
        {
            Physics.SyncTransforms();
            var data = VehicleDataAsset.LoadDefault();
            var mats = GrayboxMaterials.CreateRuntime();
            m_Body = GrayboxTractorBuilder.Build(data, null, mats);
            m_Trailer = GrayboxTrailerBuilder.Build(data, null, mats);
            m_Body.ResetPose(O, Quaternion.identity);
            m_Trailer.Initialize(m_Body.Data, CargoPreset.Gross40t, m_Body.Model.MassProps.Mass);
            m_Body.ConnectTrailer(m_Trailer, true);
            CombinationPlacement.Tractor(m_Body.Model, O, Quaternion.identity, out Vector3 vp, out Quaternion vq);
            m_Body.SetPose(vp, vq);
            CombinationPlacement.Coupled(m_Body.Model, vp, vq, m_Trailer.Model, 0f, out Vector3 tp, out Quaternion tq);
            m_Trailer.SetPose(tp, tq);
            Physics.SyncTransforms();
            m_Body.Model.InitParking(false);
            m_Body.Input = new DriverInput { Selector = GearSelector.Drive };
            if (kmh > 0f)
            {
                m_Body.SetMoving(kmh / 3.6f, 0);
                Physics.SyncTransforms();
            }
            var audio = m_Body.gameObject.AddComponent<TruckAudioController>();
            audio.vehicle = m_Body;
            return audio;
        }

        void Step(TruckAudioController audio, float throttle, float brake, float steer)
        {
            var inp = m_Body.Input;
            inp.Throttle = throttle; inp.Brake = brake; inp.Steer = steer; inp.Selector = GearSelector.Drive; inp.ParkingBrake = false;
            m_Body.Input = inp;
            m_Body.Tick(Dt);
            Physics.Simulate(Dt);
            audio.AudioStep(Dt);
        }

        /// <summary>Speed hold (P on km/h) for the straight run.</summary>
        void Hold(TruckAudioController audio, float kmh, float steer)
        {
            float err = kmh - (float)m_Body.Model.SpeedForward * 3.6f;
            Step(audio, Mathf.Clamp01(0.08f * err), Mathf.Clamp01(-0.05f * err), steer);
        }

        IEnumerator Ready(TruckAudioController audio)
        {
            yield return null; // Start: library + loops
            if (!audio.HasAudio) Assert.Ignore("VehicleAudioLibrary not generated");
        }

        [UnityTest]
        public IEnumerator Standstill_IsSilent()
        {
            var audio = Spawn(0f);
            yield return Ready(audio);
            float scrub = 0f, squeal = 0f;
            for (int i = 0; i < 300; i++)
            {
                Step(audio, 0f, 1f, i < 150 ? 0f : 1f); // steering at a standstill on the brake
                if (i > 50) { scrub = Mathf.Max(scrub, audio.ScrubLevel); squeal = Mathf.Max(squeal, audio.SquealLevel); }
            }
            Debug.Log($"[TEST] tyre scrub standstill: max scrub {scrub:F4}, squeal {squeal:F4}, slip angle {audio.ScrubSlipAngle * Mathf.Rad2Deg:F2} deg");
            Assert.Less(scrub, 0.01f, "no scrub at a standstill");
            Assert.Less(squeal, 0.01f, "no squeal at a standstill");
        }

        [UnityTest]
        public IEnumerator Straight_IsSilent()
        {
            var audio = Spawn(30f);
            yield return Ready(audio);
            float scrub = 0f, squeal = 0f, alpha = 0f;
            for (int i = 0; i < 1000; i++)
            {
                Hold(audio, 30f, 0f);
                if (i > 300) { scrub = Mathf.Max(scrub, audio.ScrubLevel); squeal = Mathf.Max(squeal, audio.SquealLevel); alpha = Mathf.Max(alpha, audio.ScrubSlipAngle); }
            }
            Debug.Log($"[TEST] tyre scrub straight 30 km/h: max scrub {scrub:F4}, squeal {squeal:F4}, max trailer slip angle {alpha * Mathf.Rad2Deg:F2} deg, speed {m_Body.Model.SpeedForward * 3.6:F1} km/h");
            Assert.Less(scrub, 0.02f, "no scrub driving straight");
            Assert.Less(squeal, 0.01f, "no squeal driving straight");
        }

        [UnityTest]
        public IEnumerator TightTurn10kmh_Scrubs_DoesNotSqueal_NoGc()
        {
            var audio = Spawn(10f);
            yield return Ready(audio);
            const float R = 12f;
            var ap = new AutopilotDriverInput { CircleCenter = O + new Vector3(-R, 0f, 0f), Radius = R, Clockwise = false, TargetSpeedKmh = 10f, LookAhead = 6f, Enabled = true };
            var intent = new DriverIntent();
            float scrubMin = 1f, squeal = 0f, alpha = 0f, combined = 0f, vSum = 0f; int n = 0;
            for (int i = 0; i < 3000; i++)
            {
                ap.Sample(Dt, new VehicleFeedback { Position = m_Body.Body.position, Forward = m_Body.transform.forward, ForwardSpeed = (float)m_Body.Model.SpeedForward }, ref intent);
                Step(audio, intent.Throttle, intent.Brake, intent.Steer);
                if (i >= 2000)
                {
                    scrubMin = Mathf.Min(scrubMin, audio.ScrubLevel);
                    squeal = Mathf.Max(squeal, audio.SquealLevel);
                    alpha = Mathf.Max(alpha, audio.ScrubSlipAngle);
                    combined = Mathf.Max(combined, audio.WorstCombinedSlip);
                    vSum += (float)m_Body.Model.SpeedForward * 3.6f; n++;
                }
            }
            float art = (float)(m_Body.Combination.FifthWheel.Articulation * MathUtil.Rad2Deg);
            Debug.Log($"[TEST] tyre scrub tight turn R {R} m: mean {vSum / n:F1} km/h, articulation {art:F1} deg, max trailer slip angle {alpha * Mathf.Rad2Deg:F1} deg, " +
                      $"worst combined slip {combined:F2}, scrub min {scrubMin:F3}, squeal max {squeal:F4}, scrub loop {(audio.ScrubLoop.ExtClip != null ? audio.ScrubLoop.ExtClip.name : "none")}, squeal loop {(audio.SquealLoop.ExtClip != null ? audio.SquealLoop.ExtClip.name : "none")}");
            Assert.That(vSum / n, Is.InRange(7f, 13f), "the autopilot holds ~10 km/h");
            Assert.Greater(alpha * Mathf.Rad2Deg, 4f, "the trailer axles are dragged sideways");
            Assert.Greater(scrubMin, 0.3f, "tight turn at 10 km/h: scrub audible the whole time");
            Assert.Less(squeal, 0.01f, "tight turn at 10 km/h: no squeal");
            Assert.Greater(audio.ScrubLoop.ExtVolume + audio.ScrubLoop.CabVolume, 0.01f, "scrub loop is playing");

            for (int i = 0; i < 20; i++) audio.AudioStep(Dt);
            long before = GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 300; i++) audio.AudioStep(Dt);
            long allocated = GC.GetAllocatedBytesForCurrentThread() - before;
            Assert.AreEqual(0, allocated, "audio step with the scrub layer must not allocate");
        }
    }
}
