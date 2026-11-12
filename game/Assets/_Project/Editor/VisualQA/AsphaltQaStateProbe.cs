using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    /// <summary>Opt-in editor-only evidence for asphalt ablations; no player/runtime behaviour.</summary>
    [InitializeOnLoad]
    public static class AsphaltQaStateProbe
    {
        static readonly HashSet<string> seen = new HashSet<string>();
        [Serializable] sealed class CameraInventory
        {
            public string[] ids, duplicateIds;
            public string note = "All scene ControlCamera IDs after the supplied gate camera fixture was loaded; independent of the selected render filter.";
        }
        [Serializable] sealed class GroundSnapshot
        {
            public string id, shader, baseMap, maskMap;
            public bool exists, grimeEnabled;
            public Vector4 tint, tile, grime, grimeBase, exclusion;
            public float normalStrength, smoothnessScale;
        }
        [Serializable] sealed class Snapshot
        {
            public string camera, maskFormat;
            public int width, height;
            public float fov, aspect;
            public Vector3 position;
            public float[] view, projection;
            public float[] rootToWorld;
            public double anchorZ;
            public Vector3 originShift;
            public Vector4 roadWear, paintWear, freshPaintWear;
            public Vector4 roadExclusion;
            public float roadCrackStrength, roadDetailFade, roadSealStrength;
            public bool roadCracksEnabled, roadPhotoEnabled, roadSealStrengthProperty;
            public Vector4 kerbWear, pavingGrime, yardGrime;
            public Vector4 kerbExclusion, pavingExclusion, pavingGrimeBase;
            public GroundSnapshot[] grounds;
            public bool detailGlobal, paintUnderlay;
        }
        static AsphaltQaStateProbe()
        {
            if (Environment.GetEnvironmentVariable("KAMION_ASPHALT_QA_STATE") == "1")
                RenderPipelineManager.beginCameraRendering += Log;
        }

        static void Log(ScriptableRenderContext context, Camera camera)
        {
            if (camera.targetTexture == null || camera.targetTexture.width < 1000
                || !camera.name.StartsWith("QA_", StringComparison.Ordinal) || camera.name == "QA_UICamera"
                || !seen.Add(camera.name)) return;
            var material = AssetDatabase.LoadAssetAtPath<Material>(
                "Assets/_Generated/World/bialystok-industrial-c/Materials/M_road_asphalt.mat");
            if (material != null)
                Debug.Log($"[ASPHALT_STATE] camera={camera.name} frame={Time.frameCount} " +
                    $"detailGlobal={Shader.IsKeywordEnabled("_KAMION_WORLD_DETAIL")} " +
                    $"detailMaterial={material.IsKeywordEnabled("_KAMION_WORLD_DETAIL")} " +
                    $"wear={material.GetVector("_AsphaltWear").ToString("R")} shader={material.shader.name} " +
                    $"keywords={string.Join(",", material.shaderKeywords)}");
            string directory = Environment.GetEnvironmentVariable("KAMION_ASPHALT_QA_DIRECTORY");
            if (material == null || string.IsNullOrEmpty(directory)) return;
            string inventoryPath = Path.Combine(directory, "camera-inventory.json");
            if (!File.Exists(inventoryPath))
            {
                var ids = new List<string>(); var duplicates = new HashSet<string>(); var unique = new HashSet<string>();
                foreach (var control in UnityEngine.Object.FindObjectsByType<Game.Rendering.ControlCamera>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                {
                    ids.Add(control.id);
                    if (!unique.Add(control.id)) duplicates.Add(control.id);
                }
                ids.Sort(StringComparer.Ordinal);
                Directory.CreateDirectory(directory);
                File.WriteAllText(inventoryPath, JsonUtility.ToJson(new CameraInventory {
                    ids = ids.ToArray(), duplicateIds = new List<string>(duplicates).ToArray()
                }, true));
            }
            var paint = AssetDatabase.LoadAssetAtPath<Material>(
                "Assets/_Generated/World/bialystok-industrial-c/Materials/M_marking_white.mat");
            var mask = material.GetTexture("_MaskMap") as Texture2D;
            Vector4 GroundState(string id, string property)
            {
                var ground = AssetDatabase.LoadAssetAtPath<Material>(
                    $"Assets/_Generated/World/bialystok-industrial-c/Materials/M_{id}.mat");
                return ground != null && ground.HasProperty(property) ? ground.GetVector(property) : Vector4.zero;
            }
            GroundSnapshot[] GroundRecords()
            {
                string[] ids = { "road_paving", "yard_asphalt", "yard_behaton", "yard_paving", "yard_concrete",
                    "yard_concrete_worn", "yard_slabs", "decal_yard_patch_light", "decal_yard_patch_dark" };
                var records = new GroundSnapshot[ids.Length];
                for (int i = 0; i < ids.Length; i++)
                {
                    var ground = AssetDatabase.LoadAssetAtPath<Material>(
                        $"Assets/_Generated/World/bialystok-industrial-c/Materials/M_{ids[i]}.mat");
                    var record = new GroundSnapshot { id = ids[i], exists = ground != null };
                    if (ground != null)
                    {
                        Vector4 V(string property) => ground.HasProperty(property) ? ground.GetVector(property) : Vector4.zero;
                        float F(string property) => ground.HasProperty(property) ? ground.GetFloat(property) : 0f;
                        string T(string property) => ground.HasProperty(property) && ground.GetTexture(property) != null
                            ? ground.GetTexture(property).name : "none";
                        record.shader = ground.shader != null ? ground.shader.name : "none";
                        record.baseMap = T("_BaseMap"); record.maskMap = T("_MaskMap");
                        record.grimeEnabled = ground.IsKeywordEnabled("_GRIME");
                        record.tint = V("_Tint"); record.tile = V("_Tile"); record.grime = V("_Grime");
                        record.grimeBase = V("_GroundGrimeBase"); record.exclusion = V("_GroundWearExclude");
                        record.normalStrength = F("_NormalStrength"); record.smoothnessScale = F("_SmoothnessScale");
                    }
                    records[i] = record;
                }
                return records;
            }
            var root = UnityEngine.Object.FindAnyObjectByType<Game.World.WorldRegionRoot>();
            var state = new Snapshot {
                camera = camera.name, width = camera.targetTexture.width, height = camera.targetTexture.height,
                fov = camera.fieldOfView, aspect = camera.aspect, position = camera.transform.position,
                view = RowMajor(camera.worldToCameraMatrix), projection = RowMajor(camera.projectionMatrix),
                rootToWorld = root != null ? RowMajor(root.transform.localToWorldMatrix) : Array.Empty<float>(),
                anchorZ = root != null ? root.anchorZ : 0.0,
                originShift = root != null ? root.originShift : Vector3.zero,
                roadWear = material.GetVector("_AsphaltWear"), detailGlobal = Shader.IsKeywordEnabled("_KAMION_WORLD_DETAIL"),
                roadExclusion = GroundState("road_asphalt", "_GroundWearExclude"),
                roadCrackStrength = material.GetFloat("_CrackStrength"), roadDetailFade = material.GetFloat("_DetailFade"),
                roadCracksEnabled = material.IsKeywordEnabled("_CRACKS"), roadPhotoEnabled = material.IsKeywordEnabled("_PHOTO_DETAIL"),
                roadSealStrengthProperty = material.HasProperty("_CrackSealStrength"),
                roadSealStrength = material.HasProperty("_CrackSealStrength") ? material.GetFloat("_CrackSealStrength") : 0f,
                paintWear = paint != null ? paint.GetVector("_PaintWear") : Vector4.zero,
                freshPaintWear = paint != null ? paint.GetVector("_PaintFreshWear") : Vector4.one,
                kerbWear = GroundState("curb_concrete", "_KerbWear"),
                pavingGrime = GroundState("sidewalk_paving", "_Grime"),
                yardGrime = GroundState("yard_paving", "_Grime"),
                kerbExclusion = GroundState("curb_concrete", "_GroundWearExclude"),
                pavingExclusion = GroundState("sidewalk_paving", "_GroundWearExclude"),
                pavingGrimeBase = GroundState("sidewalk_paving", "_GroundGrimeBase"),
                grounds = GroundRecords(),
                paintUnderlay = paint != null && paint.IsKeywordEnabled("_ROADWEAR"),
                maskFormat = mask != null ? mask.format.ToString() : "none"
            };
            string output = Path.Combine(directory, "runtime-cameras");
            Directory.CreateDirectory(output);
            string name = System.Text.RegularExpressions.Regex.Replace(camera.name, "[^A-Za-z0-9._-]", "_");
            File.WriteAllText(Path.Combine(output, name + ".json"), JsonUtility.ToJson(state, true));
        }

        static float[] RowMajor(Matrix4x4 matrix)
        {
            var values = new float[16];
            for (int r = 0; r < 4; r++) for (int c = 0; c < 4; c++) values[r * 4 + c] = matrix[r, c];
            return values;
        }
    }
}
