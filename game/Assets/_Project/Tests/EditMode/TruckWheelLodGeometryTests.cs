using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.Editor.Setup;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using Json = Game.Editor.Setup.TruckAssetBuilder.Json;

namespace Game.Tests
{
    /// <summary>
    /// REVIEW r5 R-W1 / ADR 0039: the TRAKT B2.1 LOD2 wheels (the only exterior LOD on Low) were shredded - collapse
    /// decimation pushed tyre vertices to r 0.638 m (LOD0 0.538 m), spikes and flipped black triangles. Every exterior
    /// LOD a tier selects (TruckVisualRig: High LOD0-1, Medium LOD1-2, Low LOD2) is imported from art-source with the
    /// vehicle importer settings (TruckAssetBuilder.ApplyModelSettings) and its wheels must stay a wheel: radius and
    /// width of LOD0, >= 16 segments around, unit normals pointing out of the tread, no degenerate or flipped triangles.
    /// </summary>
    public class TruckWheelLodGeometryTests
    {
        const string Manifest = "art-source/truck/exterior/export/truck_exterior_manifest.json";
        const string TmpDir = "Assets/_TestTmp_WheelLod";
        static readonly string[] Roles = { "WHEEL_FL", "WHEEL_FR", "WHEEL_RL", "WHEEL_RR" };
        static readonly Dictionary<string, int[]> TierLods = new Dictionary<string, int[]>
        {
            { "Low", new[] { 2 } }, { "Medium", new[] { 1, 2 } }, { "High", new[] { 0, 1 } },
        };

        static Dictionary<string, object> s_Manifest;
        static readonly Dictionary<int, GameObject> s_Imported = new Dictionary<int, GameObject>();

        static Dictionary<string, object> Lods => Json.Obj((s_Manifest ??= Json.Obj(Json.Parse(
            File.ReadAllText(Path.Combine(EditorTools.RepoRoot, Manifest)))))["lods"]);

        static Dictionary<string, object> Obj(int lod, string role) =>
            Json.Obj(Json.Obj(Json.Obj(Lods["LOD" + lod])["objects"])[$"{role}_LOD{lod}"]);

        static GameObject Import(int lod)
        {
            if (s_Imported.TryGetValue(lod, out var go) && go != null) return go;
            string src = Path.Combine(EditorTools.RepoRoot, Json.Str(Json.Obj(Lods["LOD" + lod])["file"]));
            Assert.That(File.Exists(src), "missing " + src);
            Assert.That(new FileInfo(src).Length > 1024, "LFS pointer, not the FBX: " + src);
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, TmpDir));
            string dst = $"{TmpDir}/LOD{lod}.fbx";
            File.Copy(src, Path.Combine(EditorTools.ProjectRoot, dst), true);
            AssetDatabase.ImportAsset(dst, ImportAssetOptions.ForceSynchronousImport);
            var mi = (ModelImporter)AssetImporter.GetAtPath(dst);
            mi.materialImportMode = ModelImporterMaterialImportMode.None;
            TruckAssetBuilder.ApplyModelSettings(mi);
            mi.materialImportMode = ModelImporterMaterialImportMode.None;   // geometry only (no material extraction)
            mi.SaveAndReimport();
            go = AssetDatabase.LoadAssetAtPath<GameObject>(dst);
            Assert.That(go, Is.Not.Null, dst);
            s_Imported[lod] = go;
            return go;
        }

        [OneTimeTearDown]
        public void Cleanup()
        {
            s_Imported.Clear();
            if (AssetDatabase.IsValidFolder(TmpDir)) AssetDatabase.DeleteAsset(TmpDir);
        }

        [TestCase("Low"), TestCase("Medium"), TestCase("High")]
        public void WheelsOfEveryLodOfTheTier_AreWheels(string tier)
        {
            var failures = new List<string>();
            foreach (int lod in TierLods[tier])
            {
                var root = Import(lod);
                foreach (string role in Roles)
                {
                    string name = $"{role}_LOD{lod}";
                    var t = root.GetComponentsInChildren<Transform>(true).FirstOrDefault(x => x.name == name);
                    if (t == null) { failures.Add(name + " missing"); continue; }
                    var mf = t.GetComponent<MeshFilter>();
                    if (mf == null || mf.sharedMesh == null) { failures.Add(name + " has no mesh"); continue; }
                    var r0 = Obj(0, role);
                    Check(name, mf.sharedMesh, root.transform.worldToLocalMatrix * t.localToWorldMatrix, t.position,
                          root.transform, (float)Json.Num(r0["tyre_outer_radius_m"]), (float)Json.Num(r0["width_m"]), failures);
                }
            }
            Assert.That(failures, Is.Empty, $"{tier}: " + string.Join("\n", failures));
        }

        /// <summary>Geometry in the FBX root frame (vehicle axes: spin axis X), centred on the wheel pivot.</summary>
        static void Check(string name, Mesh mesh, Matrix4x4 toRoot, Vector3 pivotWorld, Transform root, float r0, float w0,
                          List<string> failures)
        {
            var vs = mesh.vertices;
            var ns = mesh.normals;
            var tris = mesh.triangles;
            Vector3 c = root.InverseTransformPoint(pivotWorld);
            var p = new Vector3[vs.Length];
            var n = new Vector3[vs.Length];
            for (int i = 0; i < vs.Length; i++)
            {
                p[i] = toRoot.MultiplyPoint3x4(vs[i]) - c;
                n[i] = ns.Length == vs.Length ? toRoot.MultiplyVector(ns[i]) : Vector3.zero;
            }
            float R(Vector3 q) => Mathf.Sqrt(q.y * q.y + q.z * q.z);

            // bounds: radius and width of LOD0 (the shredded B2.1 LOD2: r 0.638 vs 0.538, width 0.287 vs 0.384)
            float rMax = p.Max(R);
            float w = p.Max(q => q.x) - p.Min(q => q.x);
            if (Mathf.Abs(rMax / r0 - 1f) > 0.02f) failures.Add($"{name}: tyre radius {rMax:F4} m vs LOD0 {r0:F4} m (> 2 %)");
            // LOD2 drops hub and nuts (front width -18 % by design); wider than LOD0 = exploded
            if (w > 1.05f * w0 || w < 0.75f * w0) failures.Add($"{name}: width {w:F4} m vs LOD0 {w0:F4} m (outside 75-105 %)");
            if (vs.Length < 96) failures.Add($"{name}: {vs.Length} vertices (< 96)");

            // segments around the circumference: distinct angles of the tread vertices (r > 0.97 r0), 1 degree bins
            var bins = new HashSet<int>();
            int tread = 0, outward = 0, badNormal = 0;
            for (int i = 0; i < p.Length; i++)
            {
                float nl = n[i].magnitude;
                if (Mathf.Abs(nl - 1f) > 0.02f) badNormal++;
                if (R(p[i]) < 0.97f * r0) continue;
                tread++;
                bins.Add(Mathf.RoundToInt(Mathf.Atan2(p[i].z, p[i].y) * Mathf.Rad2Deg) % 360);
                var radial = new Vector3(0f, p[i].y, p[i].z).normalized;
                if (Vector3.Dot(n[i], radial) > 0.2f) outward++;
            }
            if (bins.Count < 16) failures.Add($"{name}: {bins.Count} segments around the tread (< 16)");
            if (badNormal > 0) failures.Add($"{name}: {badNormal} non-unit normals");
            if (tread == 0 || outward < 0.9f * tread) failures.Add($"{name}: tread normals outward {outward}/{tread} (< 90 %)");

            // triangles: degenerate (area < 1e-8 m2) and flipped (face normal against its vertex normals)
            int degenerate = 0, flipped = 0, count = tris.Length / 3;
            for (int k = 0; k < tris.Length; k += 3)
            {
                Vector3 a = p[tris[k]], b = p[tris[k + 1]], d = p[tris[k + 2]];
                var fn = Vector3.Cross(b - a, d - a);
                if (fn.magnitude * 0.5f < 1e-8f) { degenerate++; continue; }
                var vn = n[tris[k]] + n[tris[k + 1]] + n[tris[k + 2]];
                // the root frame may mirror X (FBX handedness): compare in the same frame, sign-corrected by det
                float s = toRoot.determinant < 0f ? -1f : 1f;
                if (s * Vector3.Dot(fn, vn) < 0f) flipped++;
            }
            if (degenerate > 0.01f * count) failures.Add($"{name}: {degenerate}/{count} degenerate triangles (> 1 %)");
            if (flipped > 0.02f * count) failures.Add($"{name}: {flipped}/{count} flipped triangles (> 2 %)");
        }
    }
}
