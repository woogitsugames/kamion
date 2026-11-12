using System.Collections;
using System.Globalization;
using System.IO;
using System.Text;
using Game.Controls;
using Game.Core;
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
    /// ADR 0148: the owner's Fold recording (accelerate D4 -> D9 to ~40 km/h, then lift off and coast in D9 at
    /// 900-1150 rpm, cab camera) replayed through the real physics + TruckAudioController + EngineAudio. Every frame
    /// (fixed 0.01 s) the state of every AudioSource on the truck (clip, volume, pitch, position) is written to
    /// artifacts/audio-idle/capture/capture_{synth,el}.csv; tools/audio/idle_render.py mixes the clips offline with
    /// exactly those parameters (batchmode has no audio output), so the runtime mix can be compared with the recording.
    /// One-shots (PlayOneShot) are not captured. The test also checks that the coast runs at zero load.
    /// </summary>
    public sealed class IdleAudioCaptureTests
    {
        const float Dt = 0.01f;
        static readonly Vector3 O = new Vector3(0f, -600f, 0f);
        SimulationMode m_PrevMode;
        float m_PrevCapture;
        int m_PrevEngine;
        GameObject m_World;
        VehicleBody m_Body;
        TrailerBody m_Trailer;

        [SetUp]
        public void SetUp()
        {
            m_PrevMode = Physics.simulationMode;
            m_PrevCapture = Time.captureDeltaTime;
            m_PrevEngine = AudioPreferences.EngineSource;
            Physics.simulationMode = SimulationMode.Script;
            m_World = new GameObject("IdleAudioWorld");
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.transform.SetParent(m_World.transform, false);
            go.transform.SetPositionAndRotation(O + new Vector3(0, -0.5f, 0), Quaternion.identity);
            go.transform.localScale = new Vector3(4000, 1, 4000);
            go.AddComponent<GroundSurface>().kind = SurfaceKind.DryAsphalt;
        }

        [TearDown]
        public void TearDown()
        {
            if (m_Body != null) Object.DestroyImmediate(m_Body.gameObject);
            if (m_Trailer != null) Object.DestroyImmediate(m_Trailer.gameObject);
            Object.DestroyImmediate(m_World);
            Physics.simulationMode = m_PrevMode;
            Time.captureDeltaTime = m_PrevCapture;
            AudioPreferences.EngineSource = m_PrevEngine;
        }

        TruckAudioController Spawn()
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
            var audio = m_Body.gameObject.AddComponent<TruckAudioController>();
            audio.vehicle = m_Body;
            return audio;
        }

        void Physics1(float throttle, float brake)
        {
            var inp = m_Body.Input;
            inp.Throttle = throttle; inp.Brake = brake; inp.Steer = 0f; inp.Selector = GearSelector.Drive; inp.ParkingBrake = false;
            m_Body.Input = inp;
            m_Body.Tick(Dt);
            Physics.Simulate(Dt);
        }

        static string OutDir()
        {
            string env = System.Environment.GetEnvironmentVariable("KAMION_AUDIO_CAPTURE_DIR");
            if (!string.IsNullOrEmpty(env)) return env;
            return Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "artifacts", "audio-idle", "capture"));
        }

        [UnityTest]
        public IEnumerator FoldDrive_Capture_Synth() => Run(AudioPreferences.EngineProcedural, "synth");

        [UnityTest]
        public IEnumerator FoldDrive_Capture_ElevenLabs() => Run(AudioPreferences.EngineElevenLabs, "el");

        IEnumerator Run(int engineSource, string tag)
        {
            AudioPreferences.EngineSource = engineSource;
            Time.captureDeltaTime = Dt; // EngineAudio / TruckAudioController Update see dt = 0.01 s, one physics step per frame
            var audio = Spawn();
            yield return null;
            if (!audio.HasAudio) Assert.Ignore("VehicleAudioLibrary not generated");
            yield return null;
            var sources = m_Body.GetComponentsInChildren<AudioSource>(true);
            var sb = new StringBuilder(1 << 20);
            var ci = CultureInfo.InvariantCulture;
            sb.Append("# sources");
            for (int s = 0; s < sources.Length; s++) sb.Append(';').Append(sources[s].gameObject.name);
            sb.Append('\n');
            sb.Append("t;phase;rpm;load;throttle;ebrake;boost;gear;kmh;src:clip|vol|pitch|playing|timeSamples|spatial...\n");

            float coastRpmMax = 0f, coastRpmMin = 1e9f, coastLoadMax = 0f;
            int frames = 0;
            // Phase A: pull away in D, part throttle (owner: 1000-1600 rpm on the HUD), until 41 km/h or 25 s.
            // Phase B: lift off, coast in the top gear the AMT holds for 12 s.
            bool coast = false; float coastT = 0f;
            while (true)
            {
                float kmh = (float)m_Body.Model.SpeedForward * 3.6f;
                if (!coast && (kmh >= 41f || frames * Dt > 25f)) coast = true;
                if (coast) coastT += Dt;
                if (coastT > 12f) break;
                Physics1(coast ? 0f : 0.55f, 0f);
                yield return null; // TruckAudioController.Update + EngineAudio.Update with dt = 0.01
                var e = m_Body.Model.Engine;
                float rpm = (float)e.Rpm, load = (float)e.LastLoad;
                if (coast && coastT > 1f)
                {
                    coastRpmMax = Mathf.Max(coastRpmMax, rpm); coastRpmMin = Mathf.Min(coastRpmMin, rpm);
                    coastLoadMax = Mathf.Max(coastLoadMax, load);
                }
                sb.Append((frames * Dt).ToString("F2", ci)).Append(';').Append(coast ? "coast" : "pull").Append(';')
                  .Append(rpm.ToString("F1", ci)).Append(';').Append(load.ToString("F4", ci)).Append(';')
                  .Append(((float)m_Body.Model.ThrottleDemand).ToString("F3", ci)).Append(';')
                  .Append(((float)e.EngineBrakeState).ToString("F3", ci)).Append(';')
                  .Append(((float)e.Boost).ToString("F3", ci)).Append(';')
                  .Append(m_Body.Model.Amt.Gear).Append(';')
                  .Append(((float)m_Body.Model.SpeedForward * 3.6f).ToString("F2", ci));
                for (int s = 0; s < sources.Length; s++)
                {
                    var a = sources[s];
                    sb.Append(';');
                    if (a == null || a.clip == null || !a.isPlaying || a.volume <= 0f) { sb.Append('-'); continue; }
                    sb.Append(a.clip.name).Append('|').Append(a.volume.ToString("G6", ci)).Append('|')
                      .Append(a.pitch.ToString("G6", ci)).Append('|').Append('1').Append('|').Append(a.timeSamples)
                      .Append('|').Append(a.spatialBlend.ToString("F2", ci));
                }
                sb.Append('\n');
                frames++;
            }
            string dir = OutDir();
            Directory.CreateDirectory(dir);
            string path = Path.Combine(dir, "capture_" + tag + ".csv");
            File.WriteAllText(path, sb.ToString());
            Debug.Log($"[TEST] idle capture {tag}: {frames} frames -> {path}; coast rpm {coastRpmMin:F0}-{coastRpmMax:F0}, max load {coastLoadMax:F3}, gear {m_Body.Model.Amt.Gear}");
            Assert.Greater(frames, 1200);
            Assert.Less(coastLoadMax, 0.05f, "coasting in gear is fuel cut (load ~0)");
        }
    }
}
