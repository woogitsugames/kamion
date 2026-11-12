using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering.Editor
{
    /// <summary>ADR 0108: serial lighting/post comparisons in one licensed Unity slot.
    /// Calls the existing visual-QA renderer; no scene, camera, material or geometry implementation is duplicated.
    /// -executeMethod Game.Rendering.Editor.LightQaBatch.Run -lightQaJobs absolute/jobs.json
    /// Common -qaGate3 works as in visual-qa.ps1. Do not also pass -qaRq (each job supplies rq).</summary>
    public static class LightQaBatch
    {
        [Serializable] public sealed class Jobs { public Job[] jobs; }
        [Serializable] public sealed class Job
        {
            public string scene = "WorldC", tier = "High", lighting = "clear", cameras, output, rq;
            public int width = 2340, height = 1080;
            public bool overrideWhiteClip;
            public float whiteClip;
            public int shadowFilter; // 0 keeps the light's state; 1/2/3 = URP Low/Medium/High.
            public bool shadowWallProbe; // hall3: establish a physical 10 m span for the PNG edge measurement.
            public float clearSkySaturation; // 0 leaves preset unchanged; diagnostic display-only chroma.
            public bool lampProbe;
            public bool actualDriverEye; // QA only: cab-dash eye, horizontal actual cab forward. Never a light source.
            public int expectedHeadlamps; // 0 unchecked, 1 off, 2 on. Requires per-camera probes.
            public bool overrideSkyDisplay;
            public float skyDisplayGain = 1f, skyDisplayDesaturation;
        }

        static string Arg(string key)
        {
            var args = Environment.GetCommandLineArgs();
            int i = Array.IndexOf(args, key);
            return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
        }

        public static void Run()
        {
            int exit = 1;
            QualityProfile profile = null;
            QualityProfile.Tier[] originalTiers = null;
            var pipelineSnapshots = new Dictionary<UniversalRenderPipelineAsset, string>();
            var presetSnapshots = new Dictionary<LightingPreset, string>();
            try
            {
                if (!string.IsNullOrEmpty(Arg("-qaRq"))) throw new ArgumentException("Use job.rq, not -qaRq");
                var jobs = JsonUtility.FromJson<Jobs>(File.ReadAllText(Arg("-lightQaJobs")));
                if (jobs?.jobs == null || jobs.jobs.Length == 0) throw new ArgumentException("No lighting QA jobs");
                profile = QualityProfile.Load();
                if (profile == null) throw new InvalidOperationException("Missing QualityProfile");
                originalTiers = (QualityProfile.Tier[])profile.tiers.Clone();
                foreach (var preset in LookDevAssets.Presets())
                    if (preset != null) presetSnapshots[preset] = EditorJsonUtility.ToJson(preset);
                foreach (var t in originalTiers)
                {
                    var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(
                        $"Assets/_Project/Rendering/Settings/URP_{t.name}.asset");
                    if (pipeline != null) pipelineSnapshots[pipeline] = EditorJsonUtility.ToJson(pipeline);
                }
                // The QA runner belongs to Game.Editor, which intentionally is not an asmdef dependency here.
                var renderer = Type.GetType("Game.Editor.VisualQA.VisualQaRunner, Game.Editor", true)
                    .GetMethod("Render", BindingFlags.Public | BindingFlags.Static);
                if (renderer == null) throw new MissingMethodException("VisualQaRunner.Render");
                int total = 0;
                foreach (var job in jobs.jobs)
                {
                    if (job.width <= 0 || job.height <= 0 || string.IsNullOrEmpty(job.output))
                        throw new ArgumentException("Each job needs positive dimensions and an output directory");
                    int tierIndex = Array.FindIndex(originalTiers,
                        t => string.Equals(t.name, job.tier, StringComparison.OrdinalIgnoreCase));
                    if (tierIndex < 0) throw new ArgumentException("Unknown lighting QA tier: " + job.tier);
                    job.tier = originalTiers[tierIndex].name;
                    foreach (var item in pipelineSnapshots) EditorJsonUtility.FromJsonOverwrite(item.Value, item.Key);
                    foreach (var item in presetSnapshots) EditorJsonUtility.FromJsonOverwrite(item.Value, item.Key);
                    if (job.overrideWhiteClip)
                    {
                        if (job.whiteClip < 0.55f || job.whiteClip > 3f) throw new ArgumentException("whiteClip outside preset bounds");
                        var preset = presetSnapshots.Keys.Single(p => string.Equals(p.name, "LP_" + job.lighting, StringComparison.OrdinalIgnoreCase));
                        preset.lookWhiteClip = job.whiteClip;
                    }
                    if (job.clearSkySaturation > 0f)
                    {
                        if (job.clearSkySaturation < 1f || job.clearSkySaturation > 4f)
                            throw new ArgumentException("clearSkySaturation outside 1..4");
                        var preset = presetSnapshots.Keys.Single(p => string.Equals(p.name, "LP_" + job.lighting, StringComparison.OrdinalIgnoreCase));
                        preset.clearSkySaturation = job.clearSkySaturation;
                    }
                    if (job.overrideSkyDisplay)
                    {
                        if (job.skyDisplayGain < 0.001f || job.skyDisplayGain > 1f || job.skyDisplayDesaturation < 0f || job.skyDisplayDesaturation > 1f)
                            throw new ArgumentException("sky display values outside preset bounds");
                        var preset = presetSnapshots.Keys.Single(p => string.Equals(p.name, "LP_" + job.lighting, StringComparison.OrdinalIgnoreCase));
                        preset.skyDisplayGain = job.skyDisplayGain;
                        preset.skyDisplayDesaturation = job.skyDisplayDesaturation;
                    }
                    profile.tiers = (QualityProfile.Tier[])originalTiers.Clone();
                    var overrides = (job.rq ?? "").Split(',').Where(s => !string.IsNullOrWhiteSpace(s))
                        .Select(s => s.Split('=')).ToDictionary(p => p[0].Trim(), p => p[1].Trim());
                    RenderOverrides.Parse(k => overrides.TryGetValue(k, out var v) ? v : null);
                    profile.tiers[tierIndex] = RenderOverrides.ApplyTo(profile.tiers[tierIndex]);
                    Directory.CreateDirectory(job.output);
                    if (job.shadowFilter < 0 || job.shadowFilter > 3) throw new ArgumentException("shadowFilter must be 0..3");
                    var lampProbe = job.lampProbe ? new LightQaLampProbe() : null;
                    if (job.expectedHeadlamps < 0 || job.expectedHeadlamps > 2 || (job.expectedHeadlamps > 0 && lampProbe == null))
                        throw new ArgumentException("expectedHeadlamps requires lampProbe and a value0..2");
                    Action<ScriptableRenderContext, Camera> filter = (_, camera) => {
                        if (job.shadowFilter > 0)
                            foreach (var light in UnityEngine.Object.FindObjectsByType<Light>(FindObjectsSortMode.None))
                                if (light.type == LightType.Directional)
                                    light.GetUniversalAdditionalLightData().softShadowQuality = (SoftShadowQuality)job.shadowFilter;
                        lampProbe?.Capture(camera);
                    };
                    int count;
                    void AddDriverEye(Scene scene, OpenSceneMode mode)
                    {
                        var eye = UnityEngine.Object.FindObjectsByType<ControlCamera>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                            .Single(c => c.gameObject.scene == scene && c.id == "cab-dash");
                        var cab = UnityEngine.Object.FindObjectsByType<CabInteriorLighting>(FindObjectsInactive.Exclude, FindObjectsSortMode.None)
                            .Single(c => c.gameObject.scene == scene && c.cab != null).cab;
                        var go = new GameObject("Light QA actual driver eye");
                        SceneManager.MoveGameObjectToScene(go, scene);
                        var camera = go.AddComponent<Camera>();
                        camera.CopyFrom(eye.GetComponent<Camera>());
                        // CopyFrom also copies the camera transform in this Unity version. Set the QA pose last.
                        go.transform.SetPositionAndRotation(eye.transform.position, Quaternion.LookRotation(cab.forward, cab.up));
                        if (Vector3.Dot(go.transform.forward, cab.forward.normalized) < 0.9999f ||
                            Mathf.Abs(go.transform.forward.y) > 0.1f)
                            throw new InvalidOperationException("Actual driver eye must follow the level parked cab frame");
                        camera.fieldOfView = 60f;
                        camera.enabled = false;
                        var control = go.AddComponent<ControlCamera>();
                        control.id = "light-night-driver";
                        control.note = "QA-only actual cab-dash eye; actual cab forward; FOV60. Not a matched photo pose.";
                        go.SetActive(false);
                        File.WriteAllText(Path.Combine(job.output, "actual-eye.json"), JsonUtility.ToJson(new EyeProof {
                            position = go.transform.position, forward = go.transform.forward, up = go.transform.up,
                            source = "cab-dash.position + CabInteriorLighting.cab.forward/up", fieldOfView = camera.fieldOfView
                        }, true));
                    }
                    if (job.actualDriverEye) EditorSceneManager.sceneOpened += AddDriverEye;
                    RenderPipelineManager.beginCameraRendering += filter;
                    try
                    {
                        count = (int)renderer.Invoke(null, new object[] {
                            job.scene, job.width, job.height, job.tier, job.output, job.lighting, job.cameras });
                    }
                    finally {
                        RenderPipelineManager.beginCameraRendering -= filter;
                        if (job.actualDriverEye) EditorSceneManager.sceneOpened -= AddDriverEye;
                    }
                    if (count <= 0) throw new InvalidOperationException("Job rendered no cameras: " + job.output);
                    int expected = string.IsNullOrEmpty(job.cameras) ? count : job.cameras.Split(',')
                        .Select(id => id.Trim()).Where(id => id.Length > 0).Distinct(StringComparer.OrdinalIgnoreCase).Count();
                    if (count != expected) throw new InvalidOperationException($"Incomplete lighting QA: expected={expected}, rendered={count}");
                    lampProbe?.Write(job.output, expected, job.expectedHeadlamps);
                    var environment = UnityEngine.Object.FindAnyObjectByType<EnvironmentLighting>();
                    if (environment == null || environment.Active == null || environment.Model == null)
                        throw new InvalidOperationException("Lighting QA requires a configured EnvironmentLighting");
                    if (!string.Equals(environment.Active.name, job.lighting, StringComparison.OrdinalIgnoreCase) &&
                        !string.Equals(environment.Active.name, "LP_" + job.lighting, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidOperationException("Requested lighting preset was not applied: " + job.lighting);
                    if (!QualityProfileApplier.HasCurrent || QualityProfileApplier.Current.name != job.tier)
                        throw new InvalidOperationException("Requested lighting QA tier was not applied: " + job.tier);
                    if (job.overrideWhiteClip && Mathf.Abs(environment.Active.lookWhiteClip - job.whiteClip) > 0.0001f)
                        throw new InvalidOperationException($"Requested white clip was not retained: requested={job.whiteClip}, actual={environment.Active.lookWhiteClip}");
                    if (job.overrideSkyDisplay && (Mathf.Abs(environment.Active.skyDisplayGain-job.skyDisplayGain) > 0.0001f ||
                        Mathf.Abs(environment.Active.skyDisplayDesaturation-job.skyDisplayDesaturation) > 0.0001f))
                        throw new InvalidOperationException("Requested sky presentation grade was not retained");
                    var actualFilter = environment.sun.GetUniversalAdditionalLightData().softShadowQuality;
                    if (job.shadowFilter > 0 && (int)actualFilter != job.shadowFilter)
                        throw new InvalidOperationException("Requested shadow filter was not retained: " + actualFilter);
                    if (job.shadowWallProbe) WriteShadowWallProbe(job);
                    total += count;
                    Debug.Log($"LIGHT_QA_JOB: OK rendered={count} tier={job.tier} lighting={job.lighting} rq={job.rq} whiteClipOverride={job.overrideWhiteClip}/{job.whiteClip} actualWhiteClip={environment.Active.lookWhiteClip} shadowFilter={job.shadowFilter} actualShadowFilter={actualFilter} output={job.output}");
                }
                Debug.Log($"LIGHT_QA_RESULT: OK jobs={jobs.jobs.Length} rendered={total}");
                exit = 0;
            }
            catch (Exception e)
            {
                Debug.LogException(e is TargetInvocationException invocation ? invocation.InnerException ?? e : e);
                Debug.Log("LIGHT_QA_RESULT: FAILED");
            }
            finally
            {
                if (profile != null && originalTiers != null) profile.tiers = originalTiers;
                foreach (var item in pipelineSnapshots) EditorJsonUtility.FromJsonOverwrite(item.Value, item.Key);
                foreach (var item in presetSnapshots) EditorJsonUtility.FromJsonOverwrite(item.Value, item.Key);
                RenderOverrides.Parse(_ => null);
            }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [Serializable] sealed class EyeProof
        {
            public Vector3 position, forward, up;
            public float fieldOfView;
            public string source;
        }

        [Serializable] sealed class ShadowWallProbe
        {
            public string camera, collider, scope;
            public int width, height;
            public Vector3 worldCenter, normal, worldStart, worldEnd, pixelStart, pixelEnd;
            public float spanMetres;
        }

        static void WriteShadowWallProbe(Job job)
        {
            var qa = UnityEngine.Object.FindObjectsByType<ControlCamera>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                .Single(c => c.id == "r10_hall_3");
            var cam = qa.GetComponent<Camera>();
            float aspect = cam.aspect;
            cam.aspect = (float)job.width/job.height;
            try
            {
                // Native 2340x1080 hall3 ROI, reviewed visually: a long vertical warehouse wall.
                var ray = cam.ViewportPointToRay(new Vector3(1300f/2340f, 1f-560f/1080f, 0f));
                if (!Physics.Raycast(ray, out var hit, cam.farClipPlane, ~0, QueryTriggerInteraction.Ignore) ||
                    Mathf.Abs(hit.normal.y) > 0.03f)
                    throw new InvalidOperationException("Shadow wall probe did not hit a vertical collider");
                Vector3 tangent = Vector3.Cross(Vector3.up, hit.normal).normalized;
                var proof = new ShadowWallProbe {
                    camera = qa.id, collider = hit.collider.name,
                    scope = "10 m horizontal segment on raycast vertical wall; pixel coordinates origin top-left; edge measured separately",
                    width = job.width, height = job.height, worldCenter = hit.point, normal = hit.normal,
                    worldStart = hit.point-5f*tangent, worldEnd = hit.point+5f*tangent, spanMetres = 10f
                };
                foreach (var p in new[] { proof.worldStart, proof.worldEnd })
                {
                    var check = cam.WorldToViewportPoint(p);
                    if (check.z <= 0f || check.x <= 0f || check.x >= 1f || check.y <= 0f || check.y >= 1f ||
                        !Physics.Raycast(cam.ViewportPointToRay(check), out var endHit, cam.farClipPlane, ~0, QueryTriggerInteraction.Ignore) ||
                        Vector3.Distance(endHit.point, p) > 0.2f || Vector3.Dot(endHit.normal, hit.normal) < 0.99f)
                        throw new InvalidOperationException("10 m shadow-wall span is not visible/on one plane");
                }
                Vector3 Pixel(Vector3 p) {
                    var v = cam.WorldToViewportPoint(p);
                    return new Vector3(v.x*job.width, (1f-v.y)*job.height, v.z);
                }
                proof.pixelStart = Pixel(proof.worldStart); proof.pixelEnd = Pixel(proof.worldEnd);
                File.WriteAllText(Path.Combine(job.output, "shadow-wall-10m.json"), JsonUtility.ToJson(proof, true));
                Debug.Log("LIGHT_QA_SHADOW_WALL: " + JsonUtility.ToJson(proof));
            }
            finally { cam.aspect = aspect; }
        }
    }
}
