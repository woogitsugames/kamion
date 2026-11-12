using Game.Rendering;
using NUnit.Framework;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.TestTools;
using UnityEngine.SceneManagement;

namespace Game.Tests
{
    public class HeadlampProjectionTests
    {
        Texture m_PreviousState;
        Texture2D m_State;
        LightingPreset m_Night;

        [SetUp]
        public void Setup()
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            KamionHeadlamps.Reset();
            m_PreviousState = Shader.GetGlobalTexture("_TruckLightState");
            m_State = new Texture2D(16, 1, TextureFormat.RGBAFloat, false, true);
            m_State.SetPixels(new Color[16]); m_State.Apply();
            Shader.SetGlobalTexture("_TruckLightState", m_State);
            m_Night = LightingPreset.CreateNight();
        }

        [TearDown]
        public void Teardown()
        {
            KamionHeadlamps.Reset();
            Shader.SetGlobalTexture("_TruckLightState", m_PreviousState);
            Object.DestroyImmediate(m_State); Object.DestroyImmediate(m_Night);
        }

        static CabInteriorLighting MakeCab(string name, bool anchors = true)
        {
            var root = new GameObject(name);
            root.transform.SetPositionAndRotation(new Vector3(17f, 2f, -40f), Quaternion.Euler(0f, 25f, 0f));
            var cab = root.AddComponent<CabInteriorLighting>();
            cab.cab = root.transform;
            if (anchors)
                foreach (int side in new[] { -1, 1 })
                {
                    var anchor = new GameObject(side < 0 ? "LIGHT_LowBeam_L" : "LIGHT_LowBeam_R").transform;
                    anchor.SetParent(root.transform, false);
                    anchor.localPosition = new Vector3(side*1.02669f, 0.248f, 1.03425f);
                }
            return cab;
        }

        void LowBeam(bool on)
        {
            m_State.SetPixel(2, 0, on ? new Color(50f, 48.5f, 46f) : Color.clear);
            m_State.Apply();
        }

        [Test]
        public void RequiresPresetOptInAndActualVehicleState_UsesAnchorsInsteadOfCamera()
        {
            var cab = MakeCab("player");
            var model = m_Night.CreateModel();
            LowBeam(true);
            KamionHeadlamps.Push(model, false, 20000f);
            Assert.IsFalse(KamionHeadlamps.Enabled);
            LowBeam(false);
            KamionHeadlamps.Push(model, true, 20000f);
            Assert.IsFalse(KamionHeadlamps.Enabled);
            LowBeam(true);
            KamionHeadlamps.Push(model, true, 20000f);
            Assert.IsTrue(KamionHeadlamps.Enabled);
            var expected = cab.cab.Find("LIGHT_LowBeam_L").position;
            Assert.Less(Vector3.Distance(expected, Shader.GetGlobalVector("_KamionHeadlampLeft")), 0.0001f);
            var camera = new GameObject("unrelated QA camera").AddComponent<Camera>();
            camera.transform.position = new Vector3(-800f, 70f, 900f);
            KamionHeadlamps.Push(model, true, 20000f);
            Assert.Less(Vector3.Distance(expected, Shader.GetGlobalVector("_KamionHeadlampLeft")), 0.0001f);
            Assert.AreEqual(0, Object.FindObjectsByType<Light>(FindObjectsSortMode.None).Length,
                "projection must never create Unity lights");
            cab.gameObject.SetActive(false);
            KamionHeadlamps.Push(model, true, 20000f);
            Assert.IsFalse(KamionHeadlamps.Enabled, "inactive source cannot leave a beam behind");
            Assert.AreEqual(0f, Shader.GetGlobalFloat("_KamionHeadlampOn"));
        }

        [Test]
        public void MissingActualAnchorsFailsClosedWithoutInventedCameraFallback()
        {
            MakeCab("player without anchors", false); LowBeam(true);
            LogAssert.Expect(LogType.Warning, "[HEADLAMP] projection disabled: missing or ambiguous actual LIGHT_LowBeam_L/R anchors");
            KamionHeadlamps.Push(m_Night.CreateModel(), true, 20000f);
            Assert.IsFalse(KamionHeadlamps.Enabled);
        }

        [Test]
        public void AmbiguousPlayerCabsFailClosedOnBinding()
        {
            MakeCab("player one"); MakeCab("player two"); LowBeam(true);
            LogAssert.Expect(LogType.Warning, "[HEADLAMP] projection disabled: requires exactly one active player cab; found 2");
            KamionHeadlamps.Push(m_Night.CreateModel(), true, 20000f);
            Assert.IsFalse(KamionHeadlamps.Enabled);
        }

        [Test]
        public void LaterSecondOwnerIsDetectedByBoundedPeriodicRecheck()
        {
            MakeCab("first player"); LowBeam(true); var model = m_Night.CreateModel();
            KamionHeadlamps.Push(model, true, 20000f);
            Assert.IsTrue(KamionHeadlamps.Enabled);
            MakeCab("later player");
            System.Threading.Thread.Sleep(300); // monotonic binding clock; no busy loop, no frame-time dependency
            LogAssert.Expect(LogType.Warning, "[HEADLAMP] projection disabled: requires exactly one active player cab; found 2");
            KamionHeadlamps.Push(model, true, 20000f);
            Assert.IsFalse(KamionHeadlamps.Enabled);
        }

        [Test]
        public void PreviewCabCannotStealMainSceneBindingOrPublishAProjection()
        {
            MakeCab("real player"); LowBeam(true); var model = m_Night.CreateModel();
            var preview = EditorSceneManager.NewPreviewScene();
            try
            {
                var other = MakeCab("preview player");
                SceneManager.MoveGameObjectToScene(other.gameObject, preview);
                KamionHeadlamps.Push(model, true, 20000f);
                Assert.IsTrue(KamionHeadlamps.Enabled, "preview must not count as a second real player");
                KamionHeadlamps.Push(model, true, 20000f, preview);
                Assert.IsFalse(KamionHeadlamps.Enabled, "preview cannot publish into game lighting globals");
            }
            finally { EditorSceneManager.ClosePreviewScene(preview); }
        }

        [Test]
        public void ReparentedAnchorInvalidatesSuccessfulCacheImmediately()
        {
            var cab = MakeCab("player"); LowBeam(true); var model = m_Night.CreateModel();
            KamionHeadlamps.Push(model, true, 20000f);
            Assert.IsTrue(KamionHeadlamps.Enabled);
            cab.cab.Find("LIGHT_LowBeam_L").SetParent(null, true);
            LogAssert.Expect(LogType.Warning, "[HEADLAMP] projection disabled: missing or ambiguous actual LIGHT_LowBeam_L/R anchors");
            KamionHeadlamps.Push(model, true, 20000f);
            Assert.IsFalse(KamionHeadlamps.Enabled);
        }

        [Test]
        public void HeadlampOverrideCanBeExplicitlyDisabledAndResetToPreset()
        {
            try
            {
                RenderOverrides.Parse(key => key == "rq_headlamps" ? "1" : null);
                Assert.AreEqual(true, WorldAtmosphere.HeadlampsOverride);
                Assert.IsTrue(RenderOverrides.Any);
                RenderOverrides.Parse(key => key == "rq_headlamps" ? "0" : null);
                Assert.AreEqual(false, WorldAtmosphere.HeadlampsOverride);
                RenderOverrides.Parse(_ => null);
                Assert.IsNull(WorldAtmosphere.HeadlampsOverride);
            }
            finally { RenderOverrides.Parse(_ => null); }
        }
    }
}
