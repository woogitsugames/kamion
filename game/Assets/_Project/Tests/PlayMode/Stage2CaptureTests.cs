using System.Collections;
using System.IO;
using Game.Cameras;
using Game.Gameplay;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// Visual QA of the combination in motion (Stage 2): drives the real DrivingLab scene in script simulation mode and
    /// renders the main camera (plus mirrors / reversing camera) to artifacts/visual-qa/DrivingLab-runtime/*.png.
    /// Explicit: run with -testFilter Game.Tests.Stage2CaptureTests (needs a GPU, not part of the default suite).
    /// Also checks dock-bumper contact (PhysX world collision of the trailer).
    /// </summary>
    [Explicit("visual capture, run on demand")]
    public class Stage2CaptureTests
    {
        const float Dt = 0.01f;
        DrivingLabBootstrap m_Boot;
        VehicleBody m_Body;
        TrailerBody m_Trailer;
        CameraRig m_Rig;
        static string OutDir => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "artifacts", "visual-qa", "DrivingLab-runtime"));

        IEnumerator Load()
        {
            Physics.simulationMode = SimulationMode.Script;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            m_Boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            m_Body = Object.FindAnyObjectByType<VehicleBody>();
            m_Trailer = Object.FindAnyObjectByType<TrailerBody>();
            m_Rig = Object.FindAnyObjectByType<CameraRig>();
            m_Boot.enabled = false; // the test drives the inputs
        }

        void Step(int n, System.Action per = null)
        {
            var v = m_Body.GetComponent<VehicleVisuals>();
            var tv = m_Trailer.GetComponent<TrailerVisuals>();
            for (int i = 0; i < n; i++) { per?.Invoke(); m_Body.Tick(Dt); Physics.Simulate(Dt); v.Capture(Dt); tv.Capture(Dt); }
        }

        void Input(float thr, float brk, float steer, GearSelector sel, int lever = 0)
        {
            var i = m_Body.Input;
            i.Throttle = thr; i.Brake = brk; i.Steer = steer; i.Selector = sel; i.ParkingBrake = false; i.RetarderLever = lever;
            m_Body.Input = i;
        }

        static void Save(Camera cam, string id, int w = 1560, int h = 720)
        {
            Directory.CreateDirectory(OutDir);
            var rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            var prev = cam.targetTexture;
            cam.targetTexture = rt;
            cam.Render();
            cam.targetTexture = prev;
            SaveRt(rt, id);
            rt.Release();
            Object.Destroy(rt);
        }

        static void SaveRt(RenderTexture rt, string id)
        {
            var prevA = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
            tex.Apply();
            RenderTexture.active = prevA;
            File.WriteAllBytes(Path.Combine(OutDir, id + ".png"), tex.EncodeToPNG());
            Object.Destroy(tex);
            Debug.Log($"[CAPTURE] {id}");
        }

        /// <summary>Lets LateUpdate run (interpolated visuals, camera rig), then renders mirrors and the camera.</summary>
        IEnumerator Capture(string id)
        {
            yield return null;
            foreach (var m in Object.FindObjectsByType<RenderTextureMirror>(FindObjectsSortMode.None)) m.RenderNow();
            Save(m_Rig.cam, id);
        }

        [UnityTest]
        public IEnumerator Capture_ReverseIntoDock_BumperContact()
        {
            yield return Load();
            float bayX = DrivingLabLayout.DockBay0X + 2 * DrivingLabLayout.DockBayPitch;
            // Heading south, trailer rear toward the dock, rear 25 m from the dock face.
            var south = Quaternion.Euler(0f, 180f, 0f);
            float rearToTractor = 12.0f + 0.55f; // trailer rear behind the kingpin + jaw ahead of the tractor origin
            var pos = new Vector3(bayX, 0f, DrivingLabLayout.DockFaceZ - 25f - rearToTractor);
            m_Boot.SpawnAt(DrivingLabBootstrap.LabSpawn.Gross40t, pos, south);
            yield return null;
            float rearZ() => m_Trailer.transform.TransformPoint(new Vector3(0f, 1.3f, -12.0f)).z;
            double minGap = 1e9; float maxDecel = 0f, prevV = 0f;
            Step(100, () => Input(0, 1, 0, GearSelector.Reverse));
            for (int i = 0; i < 4500; i++)
            {
                float gap = DrivingLabLayout.DockFaceZ - rearZ();
                minGap = System.Math.Min(minGap, gap);
                // Creep at ~3 km/h, keep the trailer straight with a small steer on the articulation (driver correction).
                double v = m_Body.Model.SpeedForward * 3.6;
                double e = -3.0 - v;
                float steer = Mathf.Clamp((float)(m_Body.Combination.FifthWheel.Articulation * 4.0), -0.3f, 0.3f);
                bool closing = gap > 0.25f; // bumpers stand 0.12 m proud of the dock face
                Input(closing ? Mathf.Clamp01((float)-e * 0.1f) : 0f, closing ? (e > 1 ? 0.2f : 0f) : 1f, steer, GearSelector.Reverse);
                Step(1);
                float vv = m_Trailer.Body.linearVelocity.magnitude;
                maxDecel = Mathf.Max(maxDecel, Mathf.Abs(vv - prevV) / Dt);
                prevV = vv;
                if (i == 2000)
                {
                    m_Rig.SetMode(CameraMode.Orbit); yield return Capture("rt-reverse-dock-approach");
                    var rcam = m_Trailer.GetComponentInChildren<ReversingCamera>(true);
                    rcam.RenderNow();
                    Directory.CreateDirectory(OutDir);
                    SaveRt(rcam.Texture, "rt-reverse-dock-trailer-camera");
                }
                if (!closing && m_Body.Model.SpeedForward > -0.05) break;
            }
            // Fixed side view of the trailer rear against the bumpers (the orbit camera would sit inside the warehouse).
            m_Rig.enabled = false;
            m_Rig.cam.transform.SetPositionAndRotation(new Vector3(bayX + 9f, 4.5f, DrivingLabLayout.DockFaceZ - 9f),
                Quaternion.LookRotation(new Vector3(bayX, 1.4f, DrivingLabLayout.DockFaceZ) - new Vector3(bayX + 9f, 4.5f, DrivingLabLayout.DockFaceZ - 9f)));
            m_Rig.cam.fieldOfView = 45f;
            yield return Capture("rt-reverse-dock-at-bumpers");
            Debug.Log($"[TEST] dock: min gap trailer rear → dock face {minGap:F3} m (bumpers 0.12 m proud), articulation {m_Body.Combination.FifthWheel.Articulation * MathUtil.Rad2Deg:F2}°, max trailer decel {maxDecel:F2} m/s²");
            Assert.Greater(minGap, 0.0, "trailer stopped by the bumpers, not inside the dock wall");
        }

        [UnityTest]
        public IEnumerator Capture_JackknifeOnWetPad()
        {
            yield return Load();
            var center = DrivingLabLayout.WetCircleCenter;
            float R = DrivingLabLayout.WetCircleR;
            m_Boot.SpawnAt(DrivingLabBootstrap.LabSpawn.Empty, center + new Vector3(R, 0f, 0f), Quaternion.identity);
            m_Boot.SetAbsFault(true, silent: true);
            m_Body.SetMoving(55f / 3.6f, 0);
            Physics.SyncTransforms();
            var ap = new Game.Controls.AutopilotDriverInput { CircleCenter = center, Radius = R, Clockwise = false, TargetSpeedKmh = 55f, LookAhead = 18f, Enabled = true };
            var intent = new Game.Controls.DriverIntent();
            float held = 0f; double maxArt = 0; bool shot = false;
            m_Rig.SetMode(CameraMode.Chase);
            for (int i = 0; i < 1300; i++)
            {
                float t = i * Dt;
                ap.Sample(Dt, new Game.Controls.VehicleFeedback { Position = m_Body.transform.position, Forward = m_Body.transform.forward, ForwardSpeed = (float)m_Body.Model.SpeedForward }, ref intent);
                if (t < 6f) { held = intent.Steer; Input(intent.Throttle, intent.Brake, intent.Steer, GearSelector.Drive); }
                else Input(0, 0.5f, held, GearSelector.Drive);
                Step(1);
                double a = System.Math.Abs(m_Body.Combination.FifthWheel.Articulation * MathUtil.Rad2Deg);
                maxArt = System.Math.Max(maxArt, a);
                if (t > 6f && !shot && a > 35) { shot = true; yield return Capture("rt-jackknife-wet-folding"); }
            }
            m_Rig.SetMode(CameraMode.Orbit);
            yield return Capture("rt-jackknife-wet-end");
            Debug.Log($"[TEST] capture jackknife: max articulation {maxArt:F1}°");
        }

        [UnityTest]
        public IEnumerator Capture_CabMirror_InLeftTurn()
        {
            yield return Load();
            m_Boot.SpawnAt(DrivingLabBootstrap.LabSpawn.Cargo24t, DrivingLabLayout.CircleR50Center + new Vector3(DrivingLabLayout.CircleR50, 0f, 0f), Quaternion.identity);
            var ap = new Game.Controls.AutopilotDriverInput { CircleCenter = DrivingLabLayout.CircleR50Center, Radius = DrivingLabLayout.CircleR50, Clockwise = false, TargetSpeedKmh = 20f, Enabled = true };
            var intent = new Game.Controls.DriverIntent();
            Step(2500, () =>
            {
                ap.Sample(Dt, new Game.Controls.VehicleFeedback { Position = m_Body.transform.position, Forward = m_Body.transform.forward, ForwardSpeed = (float)m_Body.Model.SpeedForward }, ref intent);
                Input(intent.Throttle, intent.Brake, intent.Steer, GearSelector.Drive);
            });
            m_Rig.SetMode(CameraMode.Cab);
            RenderTextureMirror.GlobalEnabled = true;
            m_Rig.AddLookDelta(new Vector2(-330f, 0f)); // turn the head ~40° left, toward the left mirror
            yield return Capture("rt-cab-left-mirror-turn");
            m_Rig.SetMode(CameraMode.Chase);
            yield return Capture("rt-r50-chase-24t");
            Debug.Log($"[TEST] capture R50 24 t: articulation {m_Body.Combination.FifthWheel.Articulation * MathUtil.Rad2Deg:F1}°, speed {m_Body.SpeedKmh:F1} km/h");
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
