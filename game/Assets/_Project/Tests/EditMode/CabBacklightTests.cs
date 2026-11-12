using System.IO;
using Game.Rendering;
using NUnit.Framework;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Tests.EditMode
{
    public class CabBacklightTests
    {
        const string EnvironmentKey = "_CabBacklightEnvironment";

        [SetUp]
        public void EmptyScene() => EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        [Test]
        public void MissingEnvironment_ClearsStaleBacklightState()
        {
            var go = new GameObject("cab-backlight-test");
            try
            {
                var cab = go.AddComponent<CabInteriorLighting>();
                Shader.SetGlobalVector(EnvironmentKey, new Vector4(-5f, .01f, 1f, 0f));
                cab.Refresh(null);
                Assert.That(Shader.GetGlobalVector(EnvironmentKey), Is.EqualTo(Vector4.zero));
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void Environment_IsAvailableWithoutMainCamera_AndClearedOnDisable()
        {
            var host = new GameObject("environment-backlight-test");
            var cabGo = new GameObject("cab-backlight-test");
            var clear = LightingPreset.CreateClear();
            var dusk = LightingPreset.CreateDusk();
            try
            {
                var env = host.AddComponent<EnvironmentLighting>();
                env.presets = new[] { clear, dusk };
                var cab = cabGo.AddComponent<CabInteriorLighting>();
                Assert.That(env.SetPreset("clear"), Is.True);
                cab.Refresh(null);
                var day = Shader.GetGlobalVector(EnvironmentKey);
                Assert.That(day.z, Is.EqualTo(1f));
                Assert.That(day.x, Is.GreaterThan(6f));
                Assert.That(day.y, Is.GreaterThan(0f));
                Assert.That(env.SetPreset("dusk"), Is.True);
                cab.Refresh(null);
                var night = Shader.GetGlobalVector(EnvironmentKey);
                Assert.That(night.x, Is.LessThan(0f), "true elevation, not the Perez daylight clamp");
                Assert.That(night.y, Is.GreaterThan(day.y));
                Assert.That(night.z, Is.EqualTo(1f));
                cab.enabled = false;
                Assert.That(Shader.GetGlobalVector(EnvironmentKey), Is.EqualTo(Vector4.zero));
            }
            finally
            {
                Object.DestroyImmediate(cabGo); Object.DestroyImmediate(host);
                Object.DestroyImmediate(clear); Object.DestroyImmediate(dusk);
            }
        }

        [Test]
        public void RenderedBacklight_IsIconOnly_DarkWhenDisabledOrDay_AndCappedAtNight()
        {
            var shader = Shader.Find("Kamion/Cab Interior");
            Assert.That(shader, Is.Not.Null);
            Assert.That(shader.isSupported, Is.True);
            int quality = QualitySettings.GetQualityLevel();
            string[] keys = { EnvironmentKey, "_CabFill", "_CabShadowLift", "_KamionToeParity", "_KamionCabToeInv" };
            var saved = new Vector4[keys.Length];
            for (int i = 0; i < keys.Length; i++) saved[i] = Shader.GetGlobalVector(keys[i]);
            float oldGain = Shader.GetGlobalFloat("_CabGain"), oldEnclosure = Shader.GetGlobalFloat("_CabEnclosure");
            bool fog = RenderSettings.fog;
            var ambientMode = RenderSettings.ambientMode;
            var ambient = RenderSettings.ambientLight;
            var probe = RenderSettings.ambientProbe;
            float reflection = RenderSettings.reflectionIntensity;
            var material = new Material(shader);
            var meshes = new Mesh[2];
            var root = new GameObject("backlight-render-fixture");
            var rt = new RenderTexture(128, 64, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Linear);
            var previousTarget = RenderTexture.active;
            var pixels = new Texture2D(128, 64, TextureFormat.RGBA32, false, true);
            try
            {
                QualitySettings.SetQualityLevel(0, true);
                RenderSettings.fog = false;
                RenderSettings.ambientMode = AmbientMode.Flat;
                RenderSettings.ambientLight = Color.black;
                RenderSettings.ambientProbe = new SphericalHarmonicsL2();
                RenderSettings.reflectionIntensity = 0f;
                for (int i = 0; i < keys.Length; i++) Shader.SetGlobalVector(keys[i], Vector4.zero);
                Shader.SetGlobalFloat("_CabGain", 1f); Shader.SetGlobalFloat("_CabEnclosure", 1f);
                material.EnableKeyword("_KAMION_CAB_DECAL");
                material.SetTexture("_DecalAtlas", Texture2D.whiteTexture);
                material.SetTexture("_AO", Texture2D.whiteTexture);
                material.SetFloat("_LegendLuminance", 8f); material.SetFloat("_LegendMaxDisplay", .06f);
                material.SetColor("_LegendColor", Color.white);
                material.SetFloat("_LegendStartSunDeg", 6f); material.SetFloat("_LegendFullSunDeg", 0f);
                for (int side = 0; side < 2; side++)
                {
                    var quad = GameObject.CreatePrimitive(PrimitiveType.Quad);
                    quad.transform.SetParent(root.transform, false);
                    quad.transform.localPosition = new Vector3(side == 0 ? -.6f : .6f, 0f, 0f);
                    var filter = quad.GetComponent<MeshFilter>();
                    var mesh = Object.Instantiate(filter.sharedMesh); meshes[side] = mesh;
                    var uv = new Vector2[mesh.vertexCount]; var colors = new Color[mesh.vertexCount];
                    for (int i = 0; i < uv.Length; i++) { uv[i] = new Vector2(.25f, side == 0 ? .25f : .9f); colors[i] = Color.white; }
                    mesh.uv = uv; mesh.uv2 = new Vector2[uv.Length]; mesh.uv3 = new Vector2[uv.Length]; mesh.uv4 = new Vector2[uv.Length];
                    mesh.colors = colors; filter.sharedMesh = mesh;
                    quad.GetComponent<MeshRenderer>().sharedMaterial = material;
                }
                var cameraGo = new GameObject("backlight-fixture-camera"); cameraGo.transform.SetParent(root.transform, false);
                cameraGo.transform.localPosition = new Vector3(0f, 0f, -3f);
                var camera = cameraGo.AddComponent<Camera>();
                camera.enabled = false; camera.orthographic = true; camera.orthographicSize = 1f;
                camera.aspect = 2f; camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = Color.black;
                camera.GetUniversalAdditionalCameraData().renderPostProcessing = false;
                camera.targetTexture = rt;
                string output = Path.GetFullPath(Path.Combine(Application.dataPath, "../../artifacts/cab-r3/backlight-fixture"));
                Directory.CreateDirectory(output);
                Vector2 Draw(string name, bool enabled, float elevation, float exposure)
                {
                    if (enabled) material.EnableKeyword("_KAMION_CAB_BACKLIGHT"); else material.DisableKeyword("_KAMION_CAB_BACKLIGHT");
                    Shader.SetGlobalVector(EnvironmentKey, new Vector4(elevation, exposure, 1f, 0f));
                    camera.Render(); RenderTexture.active = rt;
                    pixels.ReadPixels(new Rect(0, 0, 128, 64), 0, 0); pixels.Apply();
                    File.WriteAllBytes(Path.Combine(output, name + ".png"), pixels.EncodeToPNG());
                    var result = new Vector2(pixels.GetPixel(45, 32).r, pixels.GetPixel(83, 32).r);
                    Debug.Log($"CAB_BACKLIGHT_FIXTURE {name}: icon={result.x:F5} stitch={result.y:F5}");
                    return result;
                }
                var off = Draw("night-off", false, -5f, .01f);
                var day = Draw("day-on", true, 42f, .01f);
                var night = Draw("night-on", true, -5f, .01f);
                var cap = Draw("night-high-exposure", true, -5f, 1f);
                Assert.That(off.x, Is.LessThan(.003f)); Assert.That(off.y, Is.LessThan(.003f));
                Assert.That(day.x, Is.LessThan(.003f)); Assert.That(day.y, Is.LessThan(.003f));
                Assert.That(night.x, Is.GreaterThan(.02f), "test must actually render the emissive icon");
                Assert.That(night.y, Is.LessThan(.003f), "stitch band must remain unlit");
                Assert.That(cap.x, Is.EqualTo(night.x).Within(.005f), "exposure cap limits emitted light");
                Assert.That(cap.y, Is.LessThan(.003f));
                camera.targetTexture = null;
            }
            finally
            {
                RenderTexture.active = previousTarget;
                Object.DestroyImmediate(root);
                foreach (var mesh in meshes) if (mesh != null) Object.DestroyImmediate(mesh);
                Object.DestroyImmediate(material); Object.DestroyImmediate(pixels); rt.Release(); Object.DestroyImmediate(rt);
                for (int i = 0; i < keys.Length; i++) Shader.SetGlobalVector(keys[i], saved[i]);
                Shader.SetGlobalFloat("_CabGain", oldGain); Shader.SetGlobalFloat("_CabEnclosure", oldEnclosure);
                RenderSettings.fog = fog; RenderSettings.ambientMode = ambientMode; RenderSettings.ambientLight = ambient;
                RenderSettings.ambientProbe = probe; RenderSettings.reflectionIntensity = reflection;
                QualitySettings.SetQualityLevel(quality, true);
            }
        }
    }
}
