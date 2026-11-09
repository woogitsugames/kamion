using System.IO;
using Game.Gameplay;
using Game.Rendering;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace Game.Editor.Setup
{
    /// <summary>
    /// Generates the Boot scene (first scene in build) from code: neutral test environment
    /// (200 m ground with a 1 m checker, 1 m reference cubes, sun, procedural sky), main camera,
    /// GameBootstrap and the visual-QA control cameras. Regenerate instead of hand-editing.
    /// </summary>
    public static class BootSceneBuilder
    {
        public const string ScenePath = "Assets/_Project/Core/Scenes/Boot.unity";
        const string EnvDir = "Assets/_Project/Environment/Boot";

        [MenuItem("Kamion/Setup/Rebuild Boot scene")]
        public static void BuildAndRegister()
        {
            Directory.CreateDirectory(Path.Combine(Build.EditorTools.ProjectRoot, EnvDir));
            Directory.CreateDirectory(Path.Combine(Build.EditorTools.ProjectRoot, Path.GetDirectoryName(ScenePath)));

            var checker = CreateCheckerTexture();
            var groundMat = CreateLit("M_Ground_Checker", new Color(1f, 1f, 1f), 0.15f, checker, new Vector2(100f, 100f));
            // Albedo references (linear reflectance): ~80 % white, 18 % grey, ~4 % black, plus a saturated red.
            var white = CreateLit("M_Ref_White80", LinearAlbedo(0.80f), 0.3f);
            var grey = CreateLit("M_Ref_Grey18", LinearAlbedo(0.18f), 0.3f);
            var black = CreateLit("M_Ref_Black04", LinearAlbedo(0.04f), 0.3f);
            var red = CreateLit("M_Ref_Red", new Color(0.62f, 0.07f, 0.05f), 0.3f);
            var sky = CreateSkybox();

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            // Lighting: deterministic trilight ambient (no baked data needed), procedural sky for visuals.
            RenderSettings.skybox = sky;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.52f, 0.62f, 0.78f);
            RenderSettings.ambientEquatorColor = new Color(0.45f, 0.47f, 0.48f);
            RenderSettings.ambientGroundColor = new Color(0.20f, 0.19f, 0.17f);
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Custom;
            RenderSettings.fog = false;

            var sunGo = new GameObject("Sun");
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.956f, 0.89f);
            sun.intensity = 1.6f;
            sun.shadows = LightShadows.Hard;
            sunGo.transform.rotation = Quaternion.Euler(42f, -35f, 0f);
            sunGo.AddComponent<UniversalAdditionalLightData>();
            RenderSettings.sun = sun;

            var env = new GameObject("TestEnvironment").transform;
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
            ground.name = "Ground_200m";
            ground.transform.SetParent(env, false);
            ground.transform.localScale = new Vector3(20f, 1f, 20f); // Plane is 10 m → 200 m
            ground.GetComponent<MeshRenderer>().sharedMaterial = groundMat;
            ground.isStatic = true;

            // A row of 1 m cubes at increasing distances along +Z (north), plus a 4 m column for height.
            Cube(env, "Cube_1m_Grey18_5m", new Vector3(0f, 0.5f, 5f), grey);
            Cube(env, "Cube_1m_White80_5m", new Vector3(-2f, 0.5f, 5f), white);
            Cube(env, "Cube_1m_Black04_5m", new Vector3(2f, 0.5f, 5f), black);
            Cube(env, "Cube_1m_Red_10m", new Vector3(0f, 0.5f, 10f), red);
            Cube(env, "Cube_1m_Grey18_20m", new Vector3(0f, 0.5f, 20f), grey);
            Cube(env, "Cube_1m_Grey18_50m", new Vector3(0f, 0.5f, 50f), grey);
            for (int i = 0; i < 4; i++)
                Cube(env, $"Column_4m_{i}", new Vector3(-6f, 0.5f + i, 12f), i % 2 == 0 ? white : grey);

            // Main camera: roughly truck-cab eye height (WORKING_VALUE ~2.4 m) looking north.
            var camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            cam.fieldOfView = 60f;
            cam.nearClipPlane = 0.1f;
            cam.farClipPlane = 1000f;
            cam.clearFlags = CameraClearFlags.Skybox;
            camGo.AddComponent<UniversalAdditionalCameraData>();
            camGo.AddComponent<AudioListener>();
            camGo.transform.SetPositionAndRotation(new Vector3(1.2f, 2.4f, -6f), Quaternion.Euler(8f, -4f, 0f));
            var mainQa = camGo.AddComponent<ControlCamera>();
            mainQa.id = "boot-main-overlay";
            mainQa.includeDiagnosticsOverlay = true;
            mainQa.note = "Runtime view with the diagnostics overlay (UI legibility, safe area).";

            var qaRoot = new GameObject("ControlCameras").transform;
            QaCamera(qaRoot, "boot-overview-34", new Vector3(9f, 6f, -3f), LookEuler(new Vector3(9f, 6f, -3f), new Vector3(-1f, 0.5f, 9f)), 50f,
                "Elevated 3/4 view: ground scale, cube row, shadows.");
            QaCamera(qaRoot, "boot-eye-level", new Vector3(0f, 1.7f, -3f), new Vector3(2f, 0f, 0f), 60f,
                "Pedestrian eye height down the cube row to the horizon.");
            QaCamera(qaRoot, "boot-albedo-closeup", new Vector3(0f, 1.6f, 1.8f), new Vector3(18f, 0f, 0f), 45f,
                "White/grey/black reference cubes for exposure and albedo sanity.");

            var boot = new GameObject("Bootstrap");
            boot.AddComponent<GameBootstrap>();

            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            Debug.Log($"[SETUP] Boot scene written: {ScenePath}");
        }

        static Vector3 LookEuler(Vector3 from, Vector3 to) => Quaternion.LookRotation(to - from).eulerAngles;

        static Color LinearAlbedo(float linear)
        {
            float s = Mathf.LinearToGammaSpace(linear);
            return new Color(s, s, s, 1f);
        }

        static void Cube(Transform parent, string name, Vector3 pos, Material mat)
        {
            var c = GameObject.CreatePrimitive(PrimitiveType.Cube);
            c.name = name;
            c.transform.SetParent(parent, false);
            c.transform.localPosition = pos;
            c.GetComponent<MeshRenderer>().sharedMaterial = mat;
            c.isStatic = true;
        }

        static void QaCamera(Transform parent, string id, Vector3 pos, Vector3 euler, float fov, string note)
        {
            var go = new GameObject("QA_" + id);
            go.transform.SetParent(parent, false);
            go.transform.SetPositionAndRotation(pos, Quaternion.Euler(euler));
            var cam = go.AddComponent<Camera>();
            cam.fieldOfView = fov;
            cam.nearClipPlane = 0.1f;
            cam.farClipPlane = 1000f;
            cam.enabled = false; // never renders at runtime
            go.AddComponent<UniversalAdditionalCameraData>();
            var qa = go.AddComponent<ControlCamera>();
            qa.id = id;
            qa.note = note;
        }

        static Material CreateLit(string name, Color color, float smoothness, Texture2D tex = null, Vector2? tiling = null)
        {
            string path = $"{EnvDir}/{name}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            var shader = Shader.Find("Universal Render Pipeline/Lit");
            if (mat == null)
            {
                mat = new Material(shader);
                AssetDatabase.CreateAsset(mat, path);
            }
            mat.shader = shader;
            mat.SetColor("_BaseColor", color);
            mat.SetFloat("_Smoothness", smoothness);
            mat.SetFloat("_Metallic", 0f);
            if (tex != null)
            {
                mat.SetTexture("_BaseMap", tex);
                mat.SetTextureScale("_BaseMap", tiling ?? Vector2.one);
            }
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static Material CreateSkybox()
        {
            string path = $"{EnvDir}/M_Sky_Procedural.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            var shader = Shader.Find("Skybox/Procedural");
            if (mat == null)
            {
                mat = new Material(shader);
                AssetDatabase.CreateAsset(mat, path);
            }
            mat.shader = shader;
            mat.SetFloat("_SunSize", 0.035f);
            mat.SetFloat("_AtmosphereThickness", 0.9f);
            mat.SetColor("_SkyTint", new Color(0.5f, 0.5f, 0.5f));
            mat.SetColor("_GroundColor", new Color(0.37f, 0.35f, 0.32f));
            mat.SetFloat("_Exposure", 1.2f);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        /// <summary>2×2 m checker (1 m cells) with thin grid lines; tiled 100× over the 200 m plane.</summary>
        static Texture2D CreateCheckerTexture()
        {
            string path = $"{EnvDir}/T_Checker_1m.png";
            const int size = 512;
            const int cell = size / 2;
            var tex = new Texture2D(size, size, TextureFormat.RGB24, false);
            var a = new Color32(150, 150, 146, 255);
            var b = new Color32(118, 118, 115, 255);
            var line = new Color32(70, 70, 68, 255);
            for (int y = 0; y < size; y++)
            for (int x = 0; x < size; x++)
            {
                bool onLine = x % cell < 3 || y % cell < 3;
                bool even = (x / cell + y / cell) % 2 == 0;
                tex.SetPixel(x, y, onLine ? line : (even ? a : b));
            }
            File.WriteAllBytes(Path.Combine(Build.EditorTools.ProjectRoot, path), tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.sRGBTexture = true;
            importer.mipmapEnabled = true;
            importer.wrapMode = TextureWrapMode.Repeat;
            importer.filterMode = FilterMode.Trilinear;
            importer.anisoLevel = 4;
            importer.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }
    }
}
