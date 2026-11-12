using System;
using System.Collections;
using Game.Core;
using Game.Gameplay;
using Game.Vehicle.Physics;
using NUnit.Framework;
using TruckSim.Audio;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0142: ElevenLabs effect set (tools/audio/el_fx.py) - library content, live switch synthesis/ElevenLabs in the
    /// driving lab (clip swap, cabin mix, turbo v2), event-driven sounds (cab switch on selector change, reversing beeper,
    /// horn envelope) and no GC allocation in the audio update. Ignored when the set is not imported.
    /// </summary>
    public sealed class ElevenLabsFxAudioTests
    {
        static VehicleAudioLibrary Lib()
        {
            var lib = VehicleAudioLibrary.LoadDefault();
            if (lib == null || !lib.HasElevenLabsFx) Assert.Ignore("VehicleAudioLibrary with the ElevenLabs effect set not imported");
            return lib;
        }

        [Test]
        public void Library_HasEveryEffect_MonoAt48k()
        {
            var lib = Lib();
            var pairs = new[]
            {
                lib.elAirBrakeRelease, lib.elParkingBrakeSet, lib.elParkingBrakeRelease, lib.elAirDryerPurge, lib.elAirDryerPurgeB,
                lib.elGearshiftUp, lib.elGearshiftDown, lib.elTrailerCouple, lib.elSuspBump, lib.elIndicatorTick, lib.elIndicatorTock,
                lib.elCabSwitch, lib.elDoorOpen, lib.elDoorClose, lib.elCompressor, lib.elHorn, lib.elReverseBeeper, lib.elAmbientBed,
                lib.elTurboWhine, lib.elTurboRush,
            };
            foreach (var p in pairs)
            {
                Assert.IsTrue(p.IsValid);
                Assert.IsNotNull(p.cab, p.ext.name + ": cabin clip");
                foreach (var c in new[] { p.ext, p.cab })
                {
                    Assert.AreEqual(1, c.channels, c.name + " mono");
                    Assert.AreEqual(48000, c.frequency, c.name);
                    Assert.Greater(c.length, 0.15f, c.name);
                }
            }
            Assert.IsNotNull(lib.elTyreDryCab);
            Assert.IsNotNull(lib.elWindCab);
            Assert.IsNotNull(lib.elGearWhineCab);
            Assert.AreEqual(LayerMath.SurfaceCount, lib.elTyreSurface.Length);
            Assert.IsTrue(lib.elTyreSurface[1].IsValid && lib.elTyreSurface[2].IsValid && lib.elTyreSurface[4].IsValid, "wet, concrete, gravel");
            Assert.IsFalse(lib.elTyreSurface[3].IsValid || lib.elTyreSurface[5].IsValid, "cobbles / grass stay procedural");
            Assert.Less(lib.elIndicatorTick.ext.length, 0.3f, "relay click is a short one-shot");
            Assert.That(lib.elReverseBeeper.ext.length, Is.InRange(0.95f, 1.05f), "beeper loop = one 1.0 s period");
        }

        static IEnumerator LoadLab()
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
        }

        [UnityTest]
        public IEnumerator DrivingLab_SetSwitch_SwapsEffectClips()
        {
            var lib = Lib();
            int saved = AudioPreferences.EngineSource;
            AudioPreferences.EngineSource = AudioPreferences.EngineElevenLabs;
            try
            {
                yield return LoadLab();
                var audio = Object.FindAnyObjectByType<TruckAudioController>();
                Assert.IsNotNull(audio);
                yield return null;
                Assert.IsTrue(audio.ElevenLabsFx, "ElevenLabs set active");
                Assert.AreSame(lib.elTyreSurface[1].ext, audio.TyreLoop(1).ExtClip);
                Assert.AreSame(lib.elTyreSurface[4].cab, audio.TyreLoop(4).CabClip);
                Assert.AreSame(lib.tyreSurface[3].ext, audio.TyreLoop(3).ExtClip, "cobbles stay procedural");
                Assert.AreSame(lib.elTyreDryCab, audio.TyreLoop(0).CabClip, "dry asphalt: recorded cabin loop");
                Assert.AreSame(lib.tyreSurface[0].ext, audio.TyreLoop(0).ExtClip, "dry asphalt: procedural exterior");
                Assert.AreSame(lib.elWindCab, audio.WindLoop.CabClip);
                Assert.AreSame(lib.elCompressor.ext, audio.CompressorLoop.ExtClip);
                Assert.AreSame(lib.elAmbientBed.ext, audio.Ambient.BedClip);
                Assert.IsTrue(audio.Engine.TurboV2);
                Assert.AreEqual(0f, audio.Ambient.forkliftVolume, "procedural forklift = the owner's 'siren' (4.0 s 380-900 Hz sweep), muted");
                Assert.AreEqual(audio.elCabEngineScale, audio.Engine.CabEngineScale, 1e-6f);

                AudioPreferences.EngineSource = AudioPreferences.EngineProcedural;
                yield return null;
                yield return null;
                Assert.IsFalse(audio.ElevenLabsFx);
                Assert.AreSame(lib.tyreSurface[1].ext, audio.TyreLoop(1).ExtClip, "procedural set restored");
                Assert.AreSame(lib.tyreSurface[0].cab, audio.TyreLoop(0).CabClip);
                Assert.AreSame(lib.windLoopCab, audio.WindLoop.CabClip);
                Assert.AreSame(lib.compressor.ext, audio.CompressorLoop.ExtClip);
                Assert.AreSame(lib.ambientBed.ext, audio.Ambient.BedClip);
                Assert.IsFalse(audio.Engine.TurboV2, "procedural set keeps the v1 whistle");
                Assert.AreEqual(1f, audio.Engine.CabEngineScale, 1e-6f, "procedural cabin mix unchanged");
            }
            finally { AudioPreferences.EngineSource = saved; }
        }

        [UnityTest]
        public IEnumerator DrivingLab_EventsAndHorn()
        {
            var lib = Lib();
            int saved = AudioPreferences.EngineSource;
            AudioPreferences.EngineSource = AudioPreferences.EngineElevenLabs;
            try
            {
                yield return LoadLab();
                var audio = Object.FindAnyObjectByType<TruckAudioController>();
                var body = audio.vehicle;
                yield return null;

                // horn: tap from the settings preview -> fast attack, release after the tap
                AudioCues.Request(AudioCue.HornTap);
                float t = 0f;
                while (t < 0.15f) { yield return null; t += Time.deltaTime; }
                Assert.Greater(audio.HornLevel, 0.5f * audio.hornVolume, "horn attack");
                while (t < 1.4f) { yield return null; t += Time.deltaTime; }
                Assert.Less(audio.HornLevel, 0.05f, "horn released");

                // selector change = cab switch click; selector R with the engine running = reversing beeper
                int sw = audio.SwitchEvents;
                // the lab bootstrap rewrites Input from its own selector state every frame: stop it, drive Input directly
                var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
                if (boot != null) boot.enabled = false;
                GearSelector before = body.Input.Selector;
                Game.Vehicle.Physics.DriverInput inp;
                bool beeperHeard = false;
                for (int i = 0; i < 10 && !beeperHeard; i++)
                {
                    inp = body.Input; inp.Selector = GearSelector.Reverse; body.Input = inp;
                    yield return null;
                    beeperHeard = audio.BeeperLoop != null && audio.BeeperLoop.ExtVolume + audio.BeeperLoop.CabVolume > 0.01f;
                }
                Debug.Log($"[TEST] fx events: selector {before}->R, switch {sw}->{audio.SwitchEvents}, beeper {beeperHeard}, last={audio.LastOneShot}, rpm {audio.Rpm:F0}");
                if (audio.Rpm > 300f) Assert.IsTrue(beeperHeard, "reversing beeper with selector R and the engine running");
                Assert.Greater(audio.SwitchEvents, sw, "selector change clicks the cab switch");
            }
            finally { AudioPreferences.EngineSource = saved; }
        }

        [UnityTest]
        public IEnumerator DrivingLab_AudioUpdate_DoesNotAllocate()
        {
            Lib();
            int saved = AudioPreferences.EngineSource;
            AudioPreferences.EngineSource = AudioPreferences.EngineElevenLabs;
            try
            {
                yield return LoadLab();
                var audio = Object.FindAnyObjectByType<TruckAudioController>();
                yield return null;
                var mi = typeof(TruckAudioController).GetMethod("Update", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic);
                var update = (Action)Delegate.CreateDelegate(typeof(Action), audio, mi);
                var engMi = typeof(EngineAudio).GetMethod("Update", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic);
                var engUpdate = (Action)Delegate.CreateDelegate(typeof(Action), audio.Engine, engMi);
                for (int i = 0; i < 20; i++) { update(); engUpdate(); }
                AudioCues.HornHeld = true;
                GcAllocCounter.AssertZero(
                    () => { for (int i = 0; i < 300; i++) { update(); engUpdate(); } },
                    message: "TruckAudioController + EngineAudio update must not allocate (ElevenLabs set)");
                AudioCues.HornHeld = false;
            }
            finally { AudioPreferences.EngineSource = saved; AudioCues.HornHeld = false; }
        }
    }
}
