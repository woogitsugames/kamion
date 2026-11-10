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

        [Serializable] public class Entry { public string id; public string kind; public float[] pos; public float[] look_at; public float fov_deg; public string note; public string seat; }
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

        /// <summary>
        /// Whether the camera is re-seated on the road collision. <c>seat</c> in the file wins ("road" | "file"); otherwise
        /// "photo_match" cameras keep the file height (the generator already places them at ground + eye height, r8 putry_approach:
        /// the phone re-seated them +1.7 m while the editor kept 1.6 m) and every other kind is re-seated.
        /// </summary>
        public static bool ReseatOnRoad(Entry e)
        {
            if (!string.IsNullOrEmpty(e.seat)) return e.seat == "road";
            return e.kind != "photo_match";
        }

        /// <summary>
        /// The ONE pose function of the gate cameras, used by the game (qacam_set=gate3) and the editor visual QA. <paramref name="groundY"/>
        /// returns false when there is no collision at (x, z). The look-at point moves by the same height change.
        /// </summary>
        public static bool ComputePose(Entry e, Vector3 pos, Vector3 look, Func<float, float, float, (bool hit, float y)> groundY,
            out Vector3 outPos, out Vector3 outLook)
        {
            outPos = pos; outLook = look;
            if (!ReseatOnRoad(e) || groundY == null) return false;
            var g = groundY(pos.x, pos.z, pos.y + 4f);
            if (!g.hit) return false;
            float dy = g.y + HeightAboveRoad(e.kind) - pos.y;
            outPos.y += dy; outLook.y += dy;
            return true;
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
                if (ComputePose(e, pos, look, (x, z, fromY) => (TryGroundY(x, z, fromY, ignore, out float gy), gy), out pos, out look)) seated++;
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
