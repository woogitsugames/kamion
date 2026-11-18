using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Game.Editor.Build;
using Game.Rendering;
using Game.Vehicle.Runtime;
using UnityEngine;

namespace Game.Editor.VisualQA
{
    /// <summary>
    /// D84 / P1-4 (cab-view-s24): helpers of the visual QA for the driver-view variants (Game.Cameras.CabViewVariants).
    /// <list type="bullet">
    /// <item>-qaTruckPose E,N,headingDeg : moves the tractor and trailer (rigidly, as one combination) to region-local
    /// metres E,N with a compass heading (0 = north, 90 = east), keeping the tractor root's height above the road
    /// collision it had at the installed pose. A static pose for a "frame from the drive" (e.g. on a roundabout ring);
    /// the trailer stays straight behind the tractor (no articulation), so only forward views are meaningful.</item>
    /// <item>-qaCabViewAudit &lt;tsv&gt; : for every cab-view / cab-driver control camera at the render aspect, how much of
    /// each mirror head (renderer OBB projected to the viewport) and of the windscreen top edge is inside the frame.
    /// Geometry only (no occlusion by pillars / door frames - that is judged on the renders).</item>
    /// </list>
    /// </summary>
    public static class CabViewQa
    {
        static readonly CultureInfo Ci = CultureInfo.InvariantCulture;

        public static void ApplyTruckPose(string spec)
        {
            if (string.IsNullOrEmpty(spec)) return;
            var p = spec.Split(',').Select(s => double.Parse(s.Trim(), Ci)).ToArray();
            if (p.Length != 3) throw new ArgumentException("-qaTruckPose E,N,headingDeg");
            var root = UnityEngine.Object.FindAnyObjectByType<Game.World.WorldRegionRoot>();
            var tractor = UnityEngine.Object.FindObjectsByType<VehicleBody>(FindObjectsSortMode.None).FirstOrDefault();
            if (root == null || tractor == null) throw new InvalidOperationException("-qaTruckPose needs a world scene with a tractor");
            var trailer = UnityEngine.Object.FindObjectsByType<TrailerBody>(FindObjectsSortMode.None).FirstOrDefault();
            var ignore = new[] { tractor.transform, trailer != null ? trailer.transform : null }.Where(t => t != null).ToArray();
            var t0 = tractor.transform;
            Vector3 old = t0.position;
            if (!Game.Gameplay.Gate3Cameras.TryGroundY(old.x, old.z, old.y + 6f, ignore, out float g0))
                throw new InvalidOperationException("no road collision under the installed tractor");
            float above = old.y - g0;
            Vector3 target = root.LocalToUnity(p[0], p[1], 0.0);
            if (!Game.Gameplay.Gate3Cameras.TryGroundY(target.x, target.z, 400f, ignore, out float g1))
                throw new InvalidOperationException($"no road collision at E={p[0]} N={p[1]}");
            target.y = g1 + above;
            // Rigid move of the combination: the trailer keeps its pose relative to the tractor.
            Matrix4x4 trailerInTractor = trailer != null ? t0.worldToLocalMatrix * trailer.transform.localToWorldMatrix : Matrix4x4.identity;
            var rot = Quaternion.Euler(0f, (float)p[2], 0f);
            t0.SetPositionAndRotation(target, rot);
            if (trailer != null)
            {
                Matrix4x4 m = t0.localToWorldMatrix * trailerInTractor;
                trailer.transform.SetPositionAndRotation(m.GetColumn(3), m.rotation);
            }
            Physics.SyncTransforms();
            Debug.Log($"[CABVIEW] truck pose E={p[0]:F2} N={p[1]:F2} heading={p[2]:F1} deg -> unity {target} (road {g1:F2} m, root {above:F3} m above)");
        }

        public static void Audit(string path, ControlCamera[] cams, int width, int height)
        {
            if (string.IsNullOrEmpty(path)) return;
            float aspect = width / (float)height;
            var mirrors = UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                .Where(r => r.name.StartsWith("MIRROR_", StringComparison.Ordinal) && r.name.EndsWith("_LOD0", StringComparison.Ordinal))
                .OrderBy(r => r.name, StringComparer.Ordinal).ToArray();
            var glass = UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                .FirstOrDefault(r => r.name == "GLASS_Windscreen_LOD0");
            var sb = new StringBuilder();
            sb.AppendLine($"# cab-view-s24 geometry audit, aspect {aspect:F4} ({width}x{height}); OBB of the LOD0 renderer projected to the viewport, no occlusion");
            sb.AppendLine("camera\tvfov_deg\thfov_deg\tpitch_down_deg\tobject\tyaw_min_deg\tyaw_max_deg\telev_min_deg\telev_max_deg\tinside_frac\tviewport_rect");
            foreach (var qa in cams.Where(c => c.id.StartsWith("cab-view", StringComparison.Ordinal) || c.id.StartsWith("cab-driver", StringComparison.Ordinal)))
            {
                var cam = qa.GetComponent<Camera>();
                float prevAspect = cam.aspect;
                cam.aspect = aspect;
                Transform frame = cam.transform.parent != null ? cam.transform.parent : cam.transform;   // ControlCameras_A7 = tractor frame
                float pitch = -Mathf.DeltaAngle(0f, -cam.transform.localEulerAngles.x);
                float hfov = Game.Cameras.CabViewVariants.HorizontalFov(cam.fieldOfView, aspect);
                void Row(string name, Vector3[] pts)
                {
                    float yMin = 999, yMax = -999, eMin = 999, eMax = -999;
                    float vx0 = 9, vx1 = -9, vy0 = 9, vy1 = -9; bool behind = false;
                    foreach (var w in pts)
                    {
                        Vector3 d = frame.InverseTransformDirection(w - cam.transform.position);
                        float yaw = Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
                        float el = Mathf.Atan2(d.y, new Vector2(d.x, d.z).magnitude) * Mathf.Rad2Deg;
                        yMin = Mathf.Min(yMin, yaw); yMax = Mathf.Max(yMax, yaw); eMin = Mathf.Min(eMin, el); eMax = Mathf.Max(eMax, el);
                        Vector3 v = cam.WorldToViewportPoint(w);
                        if (v.z <= 0f) { behind = true; continue; }
                        vx0 = Mathf.Min(vx0, v.x); vx1 = Mathf.Max(vx1, v.x); vy0 = Mathf.Min(vy0, v.y); vy1 = Mathf.Max(vy1, v.y);
                    }
                    float area = Mathf.Max(1e-6f, (vx1 - vx0) * (vy1 - vy0));
                    float ix = Mathf.Max(0f, Mathf.Min(1f, vx1) - Mathf.Max(0f, vx0)), iy = Mathf.Max(0f, Mathf.Min(1f, vy1) - Mathf.Max(0f, vy0));
                    float inside = behind ? 0f : ix * iy / area;
                    sb.AppendLine(string.Join("\t", qa.id, F(cam.fieldOfView), F(hfov), F(pitch), name, F(yMin), F(yMax), F(eMin), F(eMax),
                        inside.ToString("F3", Ci), behind ? "behind" : $"x {vx0:F3}..{vx1:F3} y {vy0:F3}..{vy1:F3}"));
                }
                foreach (var m in mirrors) Row(m.name, ObbCorners(m));
                if (glass != null)
                {
                    // Top edge of the windscreen (the sun visors are parked in its frit band): the corners with the highest y in the tractor frame.
                    var c = ObbCorners(glass).OrderByDescending(w => frame.InverseTransformPoint(w).y).Take(4).ToArray();
                    Row("windscreen_top_edge", c);
                }
                cam.aspect = prevAspect;
            }
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path)));
            File.WriteAllText(path, sb.ToString());
            Debug.Log("[CABVIEW] audit -> " + path + "\n" + sb);
        }

        static string F(float v) => v.ToString("F1", Ci);

        static Vector3[] ObbCorners(Renderer r)
        {
            var b = r.localBounds;
            var pts = new Vector3[8];
            int i = 0;
            for (int x = -1; x <= 1; x += 2)
                for (int y = -1; y <= 1; y += 2)
                    for (int z = -1; z <= 1; z += 2)
                        pts[i++] = r.transform.TransformPoint(b.center + Vector3.Scale(b.extents, new Vector3(x, y, z)));
            return pts;
        }
    }
}
