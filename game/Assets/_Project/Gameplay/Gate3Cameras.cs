using System;
using System.Collections.Generic;
using Game.Rendering;
using Game.World;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Stage 3 gate cameras (launch argument qacam_set=gate3). Loads gate3_cameras.json (a copy of
    /// Data/Regions/&lt;region&gt;/gate3_cameras.json in Resources, refreshed by scripts/gate3-run.ps1) and creates a disabled
    /// <see cref="ControlCamera"/> per entry. The file's heights are bare-earth NMT plus a nominal height, so each camera
    /// is re-seated by a raycast onto the imported road collision: y = hit + height above the road (WORKING_VALUE per
    /// kind), the look-at point is shifted by the same amount. Without a hit (collision not there) the file height is used.
    /// </summary>
    public static class Gate3Cameras
    {
        public const string ResourceName = "gate3_cameras";

        [Serializable] public class Entry { public string id; public string kind; public float[] pos; public float[] look_at; public float fov_deg; public string note; }
        [Serializable] public class File { public Entry[] cameras; }

        /// <summary>Camera height above the road surface per camera kind (m). WORKING_VALUE, from the notes of the file.</summary>
        public static float HeightAboveRoad(string kind)
        {
            switch (kind)
            {
                case "driver_eye": return 2.5f;
                case "exterior_3q": return 2.2f;
                case "rondo_eye": return 2.5f;
                case "photo_match": return 1.7f;
                case "rondo_above": return 45f;
                default: return 2.5f;
            }
        }

        public static File Parse(string json) => string.IsNullOrEmpty(json) ? null : JsonUtility.FromJson<File>(json);

        /// <summary>Normalised id: file ids use underscores, scene control cameras use dashes.</summary>
        public static string Norm(string id) => (id ?? "").Replace('_', '-').ToLowerInvariant();

        /// <summary>
        /// Creates the cameras (disabled) under a new "Gate3ControlCameras" object. <paramref name="ignore"/> roots
        /// (tractor, trailer) are skipped by the ground raycast. Returns how many were created.
        /// </summary>
        public static int CreateAll(WorldRegionRoot root, IList<Transform> ignore, string json = null)
        {
            if (root == null) { Debug.LogWarning("[GATE3] no WorldRegionRoot: gate3 cameras need a world scene"); return 0; }
            var file = Parse(json ?? Resources.Load<TextAsset>(ResourceName)?.text);
            if (file == null || file.cameras == null) { Debug.LogWarning("[GATE3] gate3_cameras resource missing"); return 0; }
            var parent = new GameObject("Gate3ControlCameras").transform;
            int n = 0, seated = 0;
            foreach (var e in file.cameras)
            {
                if (e.pos == null || e.pos.Length < 3 || e.look_at == null || e.look_at.Length < 3) continue;
                Vector3 pos = root.LocalToUnity(e.pos[0], e.pos[1], e.pos[2]);
                Vector3 look = root.LocalToUnity(e.look_at[0], e.look_at[1], e.look_at[2]);
                if (TryGroundY(pos.x, pos.z, pos.y + 4f, ignore, out float groundY))
                {
                    float dy = groundY + HeightAboveRoad(e.kind) - pos.y;
                    pos.y += dy; look.y += dy; seated++;
                }
                var go = new GameObject("QA_" + e.id);
                go.transform.SetParent(parent, false);
                go.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(look - pos, Vector3.up));
                var cam = go.AddComponent<Camera>();
                cam.fieldOfView = e.fov_deg > 1f ? e.fov_deg : 60f; cam.nearClipPlane = 0.1f; cam.farClipPlane = 1400f;
                cam.enabled = false;
                var qa = go.AddComponent<ControlCamera>();
                qa.id = e.id; qa.note = e.note;
                go.SetActive(false);
                n++;
            }
            Debug.Log($"[GATE3] {n} cameras created, {seated} re-seated on the road collision");
            return n;
        }

        /// <summary>Highest non-vehicle collider surface below <paramref name="fromY"/> at (x, z).</summary>
        public static bool TryGroundY(float x, float z, float fromY, IList<Transform> ignore, out float y)
        {
            y = 0f;
            var hits = Physics.RaycastAll(new Vector3(x, fromY, z), Vector3.down, 400f, ~0, QueryTriggerInteraction.Ignore);
            float best = float.NegativeInfinity;
            foreach (var h in hits)
            {
                if (IsUnder(h.collider.transform, ignore)) continue;
                if (h.point.y > best) best = h.point.y;
            }
            if (float.IsNegativeInfinity(best)) return false;
            y = best;
            return true;
        }

        static bool IsUnder(Transform t, IList<Transform> roots)
        {
            if (roots == null) return false;
            foreach (var r in roots) if (r != null && t.IsChildOf(r)) return true;
            return false;
        }
    }
}
