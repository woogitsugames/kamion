using System;
using System.Collections;
using System.Globalization;
using System.IO;
using System.Text;
using Game.Cameras;
using Game.Core;
using Game.Gameplay;
using Game.UI.Driving;
using Game.Vehicle.Physics;
using NUnit.Framework;
using TruckSim.Audio;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    public class HornRattlePlayModeTests
    {
        static string EventLogPath()
        {
            string env = Environment.GetEnvironmentVariable("KAMION_HORN_RATTLE_LOG");
            if (!string.IsNullOrEmpty(env)) return env;
            return Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "artifacts", "agy-horn-rattle-s24", "drivinglab-events.log"));
        }

        static void AppendLog(string text)
        {
            string path = EventLogPath();
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.AppendAllText(path, text);
        }

        [UnityTest]
        public IEnumerator DrivingLab_ProceduralHorn_ShortPressVsHold_HudButton_ZeroGc()
        {
            int savedSrc = AudioPreferences.EngineSource;
            bool savedHeld = AudioCues.HornHeld, savedHud = AudioCues.HornHudHeld;
            AudioPreferences.EngineSource = AudioPreferences.EngineProcedural;
            try
            {
                Physics.simulationMode = SimulationMode.FixedUpdate;
                SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
                yield return null;
                var audio = Object.FindAnyObjectByType<TruckAudioController>();
                var hud = Object.FindAnyObjectByType<DrivingHud>();
                Assert.IsNotNull(audio);
                Assert.IsNotNull(hud);
                Assert.IsTrue(audio.HasAudio);
                audio.enabled = false;

                var lib = VehicleAudioLibrary.LoadDefault();
                Assert.IsNotNull(lib);
                Assert.IsTrue(lib.hornAir.IsValid && lib.hornAir.cab != null, "procedural horn clips missing");
                Assert.AreSame(lib.hornAir.ext, audio.HornLoop.ExtClip, "procedural set uses procedural air horn");
                Assert.AreSame(lib.hornAir.cab, audio.HornLoop.CabClip);

                var sb = new StringBuilder();
                var ci = CultureInfo.InvariantCulture;
                sb.AppendLine("# DrivingLab Horn + Trailer Rattle Event Telemetry (Win64 PlayMode)");

                // 1) Short press (30 ms) -> minimum pneumatic blast (~0.22 s), then release
                audio.rig.SetMode(CameraMode.Chase);
                for (int i = 0; i < 20; i++) audio.AudioStep(0.01f);
                AudioCues.HornHeld = true;
                for (int i = 0; i < 3; i++) audio.AudioStep(0.01f); // 30 ms tap
                AudioCues.HornHeld = false;
                for (int i = 0; i < 8; i++) audio.AudioStep(0.01f); // 110 ms elapsed: still inside min blast
                float shortPeak = audio.HornLevel;
                float shortExtVol = audio.HornLoop.ExtVolume;
                Assert.Greater(shortPeak, 0.5f * audio.hornVolume, "short press must sustain minimum blast");
                for (int i = 0; i < 35; i++) audio.AudioStep(0.01f); // 460 ms total: decayed
                Assert.Less(audio.HornLevel, 0.05f, "short press released cleanly");

                // 2) Long hold (0.60 s) -> stays full through hold, fades in cab view too
                audio.rig.SetMode(CameraMode.Cab);
                AudioCues.HornHeld = true;
                for (int i = 0; i < 60; i++) audio.AudioStep(0.01f);
                float holdLevel = audio.HornLevel;
                float holdCabVol = audio.HornLoop.CabVolume;
                Assert.Greater(holdLevel, 0.85f * audio.hornVolume, "hold sustains full horn level");
                Assert.Less(holdCabVol, shortExtVol, "cab perspective horn volume is quieter than exterior");
                AudioCues.HornHeld = false;
                for (int i = 0; i < 30; i++) audio.AudioStep(0.01f);
                Assert.Less(audio.HornLevel, 0.05f, "hold releases after key up");

                // 3) PC HUD button press & release
                hud.OverrideScreen(new Vector2(1920f, 1080f), new Rect(0f, 0f, 1920f, 1080f), 96f, desktop: true);
                hud.RefreshNow();
                var hornTf = hud.transform.Find("SafeArea/DesktopHorn");
                Assert.IsNotNull(hornTf, "DesktopHorn HUD button missing");
                Assert.IsTrue(hornTf.gameObject.activeInHierarchy, "DesktopHorn active in desktop HUD");
                var widget = hornTf.GetComponent<HornButtonWidget>();
                Assert.IsNotNull(widget);
                var ev = new PointerEventData(EventSystem.current) { pointerId = 1 };
                widget.OnPointerDown(ev);
                Assert.IsTrue(AudioCues.HornHudHeld);
                for (int i = 0; i < 10; i++) { audio.AudioStep(0.01f); hud.RefreshNow(); }
                float hudHoldLevel = audio.HornLevel;
                Assert.Greater(hudHoldLevel, 0.7f * audio.hornVolume, "PC HUD horn button drives horn");
                widget.OnPointerUp(ev);
                Assert.IsFalse(AudioCues.HornHudHeld);
                for (int i = 0; i < 40; i++) { audio.AudioStep(0.01f); hud.RefreshNow(); }
                Assert.Less(audio.HornLevel, 0.05f);

                // 4) Zero GC allocations across 300 audio + HUD updates
                for (int i = 0; i < 10; i++) { audio.AudioStep(0.01f); hud.RefreshNow(); }
                long gcBefore = GC.GetAllocatedBytesForCurrentThread();
                for (int i = 0; i < 300; i++)
                {
                    if (i == 20) widget.OnPointerDown(ev);
                    if (i == 80) widget.OnPointerUp(ev);
                    audio.AudioStep(0.01f);
                    hud.RefreshNow();
                }
                long gcBytes = GC.GetAllocatedBytesForCurrentThread() - gcBefore;
                Assert.AreEqual(0L, gcBytes, "horn + PC HUD loop must allocate 0 bytes");

                sb.AppendLine(string.Format(ci,
                    "[HORN] proc_ext={0} proc_cab={1} short_peak={2:F3} short_ext_vol={3:F3} hold_level={4:F3} hold_cab_vol={5:F3} hud_hold={6:F3} gc_bytes={7}/300",
                    lib.hornAir.ext.name, lib.hornAir.cab.name, shortPeak, shortExtVol, holdLevel, holdCabVol, hudHoldLevel, gcBytes));
                File.WriteAllText(EventLogPath(), sb.ToString());
                Debug.Log(sb.ToString().TrimEnd());
                audio.enabled = true;
            }
            finally
            {
                AudioCues.HornHeld = savedHeld;
                AudioCues.HornHudHeld = savedHud;
                AudioPreferences.EngineSource = savedSrc;
            }
        }

        [UnityTest]
        public IEnumerator DrivingLab_TrailerRattle_BumpsAndCobbles_QuieterInCab_ZeroGc()
        {
            int savedSrc = AudioPreferences.EngineSource;
            AudioPreferences.EngineSource = AudioPreferences.EngineProcedural;
            Physics.simulationMode = SimulationMode.Script;
            try
            {
                SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
                yield return null;
                var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
                var audio = Object.FindAnyObjectByType<TruckAudioController>();
                Assert.IsNotNull(boot);
                Assert.IsNotNull(audio);
                Assert.IsTrue(audio.HasAudio);
                audio.enabled = false;

                var lib = VehicleAudioLibrary.LoadDefault();
                Assert.IsTrue(lib.trailerRattleChainA.IsValid && lib.trailerRattleChainB.IsValid &&
                              lib.trailerRattleTarpA.IsValid && lib.trailerRattleKingpin.IsValid);

                var ci = CultureInfo.InvariantCulture;
                var sb = new StringBuilder();

                // A) Smooth asphalt cruise (solo & 40 t) -> zero rattle events on flat smooth asphalt
                boot.SpawnAt(DrivingLabBootstrap.LabSpawn.Gross40t, new Vector3(0f, 0f, -180f), Quaternion.identity);
                var body = audio.vehicle;
                audio.ResetEvents();
                body.SetMoving(10f, 6); // 36 km/h
                for (int i = 0; i < 40; i++) { body.Tick(0.01f); Physics.Simulate(0.01f); } // settle spawn
                audio.ResetEvents();
                int beforeFlat = audio.TrailerRattleEvents;
                for (int i = 0; i < 150; i++)
                {
                    var inp = body.Input; inp.Throttle = 0.25f; inp.Brake = 0f; inp.ParkingBrake = false; body.Input = inp;
                    body.Tick(0.01f); Physics.Simulate(0.01f); audio.AudioStep(0.01f);
                }
                int flatEvents = audio.TrailerRattleEvents - beforeFlat;
                Assert.AreEqual(0, flatEvents, "smooth flat asphalt must not rattle");

                // B) DrivingLab obstacle lane (x = 100 m: 8 cm platform, 15 cm platform, speed bump, ruts) in Chase vs Cab
                int extEvents = 0, cabEvents = 0;
                float peakVertAccel = 0f, peakCompRate = 0f;
                long totalGc = 0;
                foreach (var cam in new[] { CameraMode.Chase, CameraMode.Cab })
                {
                    boot.SpawnAt(DrivingLabBootstrap.LabSpawn.Gross40t, new Vector3(DrivingLabLayout.ObstacleX, 0f, -168f), Quaternion.identity);
                    audio.rig.SetMode(cam);
                    body.SetMoving(11.5f, 7); // ~41 km/h approaching 8 cm / 15 cm platforms, bump, ruts
                    for (int i = 0; i < 30; i++) { body.Tick(0.01f); Physics.Simulate(0.01f); }
                    audio.ResetEvents();
                    int startEv = audio.TrailerRattleEvents;
                    for (int i = 0; i < 1000; i++)
                    {
                        var inp = body.Input; inp.Throttle = 0.65f; inp.Brake = 0f; inp.ParkingBrake = false; inp.Steer = 0f; inp.Selector = GearSelector.Drive; body.Input = inp;
                        body.Tick(0.01f);
                        Physics.Simulate(0.01f);
                        int prevEv = audio.TrailerRattleEvents;
                        long gc0 = GC.GetAllocatedBytesForCurrentThread();
                        audio.AudioStep(0.01f);
                        totalGc += GC.GetAllocatedBytesForCurrentThread() - gc0;
                        var tm = body.Trailer.Model;
                        peakVertAccel = Mathf.Max(peakVertAccel, Mathf.Abs((float)tm.LocalAcceleration.y));
                        foreach (var w in tm.Wheels)
                            if (w.Contact) peakCompRate = Mathf.Max(peakCompRate, Mathf.Abs((float)w.CompressionRate));
                        if (audio.TrailerRattleEvents > prevEv)
                        {
                            string expectedSuffix = cam == CameraMode.Cab ? "_cab" : "";
                            Assert.IsNotNull(audio.LastTrailerRattle);
                            if (cam == CameraMode.Cab) StringAssert.EndsWith(expectedSuffix, audio.LastTrailerRattle.name);
                            else Assert.IsFalse(audio.LastTrailerRattle.name.EndsWith("_cab", StringComparison.Ordinal));
                            if (sb.Length < 4096)
                            {
                                sb.AppendLine(string.Format(ci,
                                    "[RATTLE] view={0} t={1:F2}s z={2:F1}m v={3:F1}km/h ay={4:F2}m/s2 compRate={5:F2}m/s kpFz={6:F1}kN E={7:F2} kind={8} clip={9}",
                                    cam, i * 0.01f, body.transform.position.z, body.SpeedKmh,
                                    Mathf.Abs((float)tm.LocalAcceleration.y), peakCompRate,
                                    (float)body.Combination.FifthWheel.KingpinLoadLocal.y / 1000f,
                                    audio.TrailerRattleEnergy, audio.LastTrailerRattleKind, audio.LastTrailerRattle.name));
                            }
                        }
                    }
                    int count = audio.TrailerRattleEvents - startEv;
                    if (cam == CameraMode.Chase) extEvents = count; else cabEvents = count;
                }

                Assert.GreaterOrEqual(extEvents, 3, "bumps/ruts must trigger exterior trailer rattle");
                Assert.GreaterOrEqual(cabEvents, 3, "bumps/ruts must trigger cab-perspective trailer rattle");
                Assert.AreEqual(0L, totalGc, "trailer rattle update must allocate 0 bytes");
                string summary = string.Format(ci,
                    "[RATTLE_SUMMARY] flat={0} ext_events={1} cab_events={2} peak_ay={3:F2}m/s2 peak_compRate={4:F2}m/s cab_factor={5:F2} gc_bytes={6}/1800\n",
                    flatEvents, extEvents, cabEvents, peakVertAccel, peakCompRate, audio.cabTrailerRattleFactor, totalGc);
                AppendLog(summary + sb);
                Debug.Log(summary);
                audio.enabled = true;
            }
            finally
            {
                Physics.simulationMode = SimulationMode.FixedUpdate;
                AudioPreferences.EngineSource = savedSrc;
            }
        }

        [UnityTearDown]
        public IEnumerator UnloadLab()
        {
            var lab = SceneManager.GetSceneByName(DrivingLabLayout.SceneName);
            if (!lab.IsValid() || !lab.isLoaded) yield break;
            var empty = SceneManager.CreateScene("Empty_HR_" + Time.frameCount);
            SceneManager.SetActiveScene(empty);
            yield return SceneManager.UnloadSceneAsync(lab);
        }
    }
}
