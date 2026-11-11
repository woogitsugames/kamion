using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;
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
            try
            {
                if (!string.IsNullOrEmpty(Arg("-qaRq"))) throw new ArgumentException("Use job.rq, not -qaRq");
                var jobs = JsonUtility.FromJson<Jobs>(File.ReadAllText(Arg("-lightQaJobs")));
                if (jobs?.jobs == null || jobs.jobs.Length == 0) throw new ArgumentException("No lighting QA jobs");
                profile = QualityProfile.Load();
                if (profile == null) throw new InvalidOperationException("Missing QualityProfile");
                originalTiers = (QualityProfile.Tier[])profile.tiers.Clone();
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
                    foreach (var item in pipelineSnapshots) EditorJsonUtility.FromJsonOverwrite(item.Value, item.Key);
                    profile.tiers = (QualityProfile.Tier[])originalTiers.Clone();
                    var overrides = (job.rq ?? "").Split(',').Where(s => !string.IsNullOrWhiteSpace(s))
                        .Select(s => s.Split('=')).ToDictionary(p => p[0].Trim(), p => p[1].Trim());
                    RenderOverrides.Parse(k => overrides.TryGetValue(k, out var v) ? v : null);
                    for (int i = 0; i < profile.tiers.Length; i++)
                        if (profile.tiers[i].name == job.tier) profile.tiers[i] = RenderOverrides.ApplyTo(profile.tiers[i]);
                    Directory.CreateDirectory(job.output);
                    int count = (int)renderer.Invoke(null, new object[] {
                        job.scene, job.width, job.height, job.tier, job.output, job.lighting, job.cameras });
                    if (count <= 0) throw new InvalidOperationException("Job rendered no cameras: " + job.output);
                    total += count;
                    Debug.Log($"LIGHT_QA_JOB: OK rendered={count} tier={job.tier} lighting={job.lighting} rq={job.rq} output={job.output}");
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
                RenderOverrides.Parse(_ => null);
            }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
