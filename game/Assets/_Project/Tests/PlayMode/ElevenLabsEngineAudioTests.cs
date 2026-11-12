using System.Collections;
using Game.Core;
using NUnit.Framework;
using TruckSim.Audio;
using UnityEngine;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0137: ElevenLabs engine set — bank layout from el_manifest.json, equal-power crossfade of unrelated
    /// recordings, start/stop gating of the loops, the engine-source preference. Plain [Test]s run without frames;
    /// the event test drives EngineAudio by SetInput for a few frames. Skipped (Ignore) when the library or the
    /// ElevenLabs set is not imported (tools/audio render_all.py + Kamion/Audio/Import).
    /// </summary>
    public sealed class ElevenLabsEngineAudioTests
    {
        static VehicleAudioLibrary RequireLibrary()
        {
            var lib = VehicleAudioLibrary.LoadDefault();
            if (lib == null || !lib.HasElevenLabs) Assert.Ignore("VehicleAudioLibrary with the ElevenLabs set not imported");
            return lib;
        }

        [Test]
        public void Banks_CoverTheRpmLoadGrid_WithLoopsPitchedToTheGridPoint()
        {
            var lib = RequireLibrary();
            foreach (var bank in new[] { lib.elExteriorEngine, lib.elCabEngine })
            {
                Assert.IsTrue(bank.Validate(out string err), err);
                Assert.IsTrue(bank.incoherent, bank.name + " must crossfade equal-power");
                CollectionAssert.AreEqual(new[] { 600f, 900f, 1200f, 1500f, 1800f, 2100f }, bank.rpmPoints);
                CollectionAssert.AreEqual(new[] { 0f, 1f }, bank.loadPoints);
                for (int i = 0; i < bank.clips.Length; i++)
                {
                    float nominal = bank.rpmPoints[i % bank.RpmCount];
                    Assert.AreEqual(nominal, bank.clipRpmExact[i], nominal * 0.01f, bank.clips[i].name + ": resampled to the grid rpm");
                    Assert.Greater(bank.clips[i].length, 3f, "loops are long enough not to be heard as a loop");
                    Assert.AreEqual(1, bank.clips[i].channels);
                }
            }
            Assert.AreEqual(1f, lib.elExteriorEngine.spatialBlend, "exterior bank is 3D at the engine bay");
            Assert.AreEqual(0f, lib.elCabEngine.spatialBlend, "cab bank is 2D");
            Assert.IsNotNull(lib.elExteriorEngineBrake);
            Assert.IsTrue(lib.elEngineStart.IsValid && lib.elEngineStart.cab != null);
            Assert.IsTrue(lib.elEngineStop.IsValid && lib.elEngineStop.cab != null);
            Assert.IsTrue(lib.elIdleClatter.IsValid && lib.elRetarder.IsValid && lib.elTurboWastegate.IsValid);
        }

        [Test]
        public void IncoherentGrid_CrossfadesAtConstantPower()
        {
            var lib = RequireLibrary();
            var root = new GameObject("elGridTest");
            try
            {
                var g = new EngineLayerGrid(lib.elExteriorEngine, root.transform, 6, null, 1u, "t") { Coherence = 0f };
                Assert.IsTrue(g.Incoherent);
                var sources = root.GetComponentsInChildren<AudioSource>();
                // sweep the whole range at load 0.5 (four cells): sum of squared voice gains must stay 1 (equal power)
                for (float rpm = 600f; rpm <= 2100f; rpm += 37f)
                {
                    for (int k = 0; k < 10; k++) g.Tick(rpm, 0.5f, 1f, 0.1f); // FadeTime 0.03 s: settled
                    float p = 0f;
                    foreach (var s in sources) p += s.volume * s.volume;
                    Assert.AreEqual(1f, p, 0.02f, $"power at {rpm} rpm");
                    Assert.LessOrEqual(g.ActiveVoices, 4);
                }
            }
            finally { Object.DestroyImmediate(root); }
        }

        [UnityTest]
        public IEnumerator StartAndStop_PlayTheEventClips_AndGateTheLoops()
        {
            var lib = RequireLibrary();
            var go = new GameObject("elEngineTest");
            go.SetActive(false);
            var eng = go.AddComponent<EngineAudio>();
            eng.Configure(lib, null, EngineSoundSource.ElevenLabs);
            go.SetActive(true);
            try
            {
                Assert.AreEqual(EngineSoundSource.ElevenLabs, eng.Source);
                var x = new EngineAudioInput { Rpm = 0f };
                for (int i = 0; i < 3; i++) { eng.SetInput(x); yield return null; }
                Assert.AreEqual(0, eng.StartEvents, "stopped engine at spawn: no event");
                x.Rpm = 600f; // Engine.Restart jumps to idle
                eng.SetInput(x); yield return null;
                eng.SetInput(x); yield return null;
                Assert.AreEqual(1, eng.StartEvents);
                Assert.Less(eng.RunGate, 0.05f, "loops silent while the start clip cranks");
                float t = 0f;
                while (t < 2.6f) { eng.SetInput(x); yield return null; t += Time.deltaTime; }
                Assert.AreEqual(1f, eng.RunGate, 1e-3f, "loops fully in after delay + fade");
                Assert.Greater(eng.ActiveEngineVoices, 0);
                x.Rpm = 200f; // stall
                eng.SetInput(x); yield return null;
                Assert.AreEqual(1, eng.StopEvents);
                t = 0f;
                while (t < 0.4f) { eng.SetInput(x); yield return null; t += Time.deltaTime; }
                Assert.AreEqual(0f, eng.RunGate, 1e-3f, "loops cut after the stop event");

                // procedural set: no event clips, the gate never closes (ADR 0007 behaviour unchanged)
                eng.Configure(lib, null, EngineSoundSource.Procedural);
                Assert.AreEqual(EngineSoundSource.Procedural, eng.Source);
                x.Rpm = 600f;
                for (int i = 0; i < 3; i++) { eng.SetInput(x); yield return null; }
                Assert.AreEqual(0, eng.StartEvents);
                Assert.AreEqual(1f, eng.RunGate, 1e-6f);
            }
            finally { Object.Destroy(go); }
        }

        [Test]
        public void Preference_LaunchArgumentAndToggle()
        {
            int saved = AudioPreferences.EngineSource;
            try
            {
                int v = AudioPreferences.Version;
                AudioPreferences.ApplyArgument("synth");
                Assert.AreEqual(AudioPreferences.EngineProcedural, AudioPreferences.EngineSource);
                AudioPreferences.ApplyArgument("EL");
                Assert.IsTrue(AudioPreferences.ElevenLabsEngine);
                AudioPreferences.ApplyArgument("bogus");
                Assert.IsTrue(AudioPreferences.ElevenLabsEngine, "unknown values are ignored");
                Assert.GreaterOrEqual(AudioPreferences.Version, v + 1);
                Assert.AreEqual(AudioPreferences.EngineElevenLabs, PlayerPrefs.GetInt(AudioPreferences.PrefEngineSource, -1));
            }
            finally { AudioPreferences.EngineSource = saved; }
        }
    }
}
