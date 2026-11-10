using System.Collections;
using System.IO;
using Game.Cameras;
using Game.Gameplay;
using Game.UI.CabDisplays;
using Game.UI.Driving;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// Visual evidence for the parking-brake warning (ADR 0004 addendum): HUD text + P button and the cluster telltale (lit and dark flash phases). Explicit; writes to artifacts/visual-qa/parking-brake-warning/. Needs a GPU.
    /// </summary>
    [Explicit("visual capture, run on demand")]
    public class ParkingBrakeWarningCaptureTests
    {
        const float Dt = 0.01f;
        static string OutDir => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "artifacts", "visual-qa", "parking-brake-warning"));

        static void SaveRt(RenderTexture rt, string id)
        {
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            File.WriteAllBytes(Path.Combine(OutDir, id + ".png"), tex.EncodeToPNG());
            Object.Destroy(tex);
        }

        static void SaveCam(Camera cam, string id, int w = 1560, int h = 720)
        {
            var rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            var prev = cam.targetTexture;
            cam.targetTexture = rt;
            cam.Render();
            cam.targetTexture = prev;
            SaveRt(rt, id);
            rt.Release();
            Object.Destroy(rt);
        }

        [UnityTest]
        public IEnumerator Capture_ParkingBrakeWarning()
        {
            Directory.CreateDirectory(OutDir);
            Physics.simulationMode = SimulationMode.Script;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            var rig = Object.FindAnyObjectByType<CameraRig>();
            boot.enabled = false;
            var vis = body.GetComponent<VehicleVisuals>();
            var tv = Object.FindAnyObjectByType<TrailerBody>()?.GetComponent<TrailerVisuals>();
            void Step(int n) { for (int i = 0; i < n; i++) { body.Tick(Dt); Physics.Simulate(Dt); vis.Capture(Dt); if (tv != null) tv.Capture(Dt); } }

            var old = Object.FindAnyObjectByType<DrivingHud>();
            if (old != null) Object.Destroy(old.gameObject);
            yield return null;
            var hud = DrivingHud.Create(rig.cam, new DrivingHudContext { Vehicle = body, Rig = rig });
            hud.OverrideSafeAreaNormalized(new Rect(0.04f, 0f, 0.96f, 1f));

            // 1. P applied, driver idle.
            body.Model.InitParking(true);
            body.Input = new DriverInput { Selector = GearSelector.Drive, ParkingBrake = true };
            Step(200);
            yield return null;
            hud.RefreshNow();
            SaveCam(rig.cam, "hud-p-applied");

            // 2. Drive-away attempt: warning on, HUD text visible, telltale flashing.
            body.Input = new DriverInput { Selector = GearSelector.Drive, ParkingBrake = true, Throttle = 0.7 };
            Step(200);
            Assert.IsTrue(body.Model.ParkingBrakeWarning);
            yield return null;
            hud.RefreshNow();
            SaveCam(rig.cam, "hud-warning");

#if UNITY_EDITOR
            // Cluster and cab view need the art truck (TRAKT prefab, generated outside git); the DrivingLab uses the graybox.
            var prefab = UnityEditor.AssetDatabase.LoadAssetAtPath<GameObject>("Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab");
            Assume.That(prefab, Is.Not.Null, "TRAKT prefab not generated (Kamion/Setup/Rebuild TRAKT truck)");
            var O = new Vector3(0f, -900f, 0f);
            var g = GameObject.CreatePrimitive(PrimitiveType.Cube);
            g.transform.SetPositionAndRotation(O + new Vector3(0f, -0.5f, 0f), Quaternion.identity);
            g.transform.localScale = new Vector3(600f, 1f, 600f);
            g.AddComponent<GroundSurface>().kind = SurfaceKind.DryAsphalt;
            Physics.SyncTransforms();
            var truck = Object.Instantiate(prefab, O, Quaternion.identity);
            var b2 = truck.GetComponent<VehicleBody>();
            if (!b2.Initialized) b2.Initialize(b2.Data);
            b2.ResetPose(O, Quaternion.identity);
            b2.Model.InitParking(true);
            b2.Input = new DriverInput { Selector = GearSelector.Drive, ParkingBrake = true, Throttle = 0.7 };
            var v2 = b2.GetComponent<VehicleVisuals>();
            truck.AddComponent<TruckLights>().body = b2;
            var screens = CabScreens.Install(b2, null, "");
            Assert.NotNull(screens, "art truck cluster installed");
            void Step2(int n) { for (int i = 0; i < n; i++) { b2.Tick(Dt); Physics.Simulate(Dt); v2.Capture(Dt); } }
            Step2(300);
            Assert.IsTrue(b2.Model.ParkingBrakeWarning);
            for (int phase = 0; phase < 2; phase++)
            {
                for (int guard = 0; guard < 200; guard++)
                {
                    Step2(1);
                    screens.RenderNow();
                    if (screens.State.ParkingBrakeFlashOn == (phase == 0)) break;
                }
                SaveRt(screens.Cluster.Texture, phase == 0 ? "cluster-flash-lit" : "cluster-flash-dark");
            }
            Object.Destroy(truck); Object.Destroy(g);
#endif
            Physics.simulationMode = SimulationMode.FixedUpdate;
        }

        [UnityTearDown]
        public IEnumerator Unload()
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            var lab = SceneManager.GetSceneByName(DrivingLabLayout.SceneName);
            if (!lab.IsValid() || !lab.isLoaded) yield break;
            var empty = SceneManager.CreateScene("Empty_" + Time.frameCount);
            SceneManager.SetActiveScene(empty);
            yield return SceneManager.UnloadSceneAsync(lab);
        }
    }
}
