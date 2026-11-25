using System;
using System.Linq;
using Game.Cameras;
using Game.Controls;
using Game.Rendering;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    /// <summary>
    /// Regression tests for CRITIC s24 build #8 item 10 ("kierownica z przyciskami tylko w t1380 i t3330"):
    /// verifies that the steering-wheel switch pods and icon decals live in the single STEERING_WHEEL_LOD0 mesh/renderer
    /// (zero extra draw calls), stay active and unculled across all quality tiers (Low..Ultra) and steer angles
    /// (-540..+540 deg), and that their appearance only in turned frames (t3330 ~35 deg, t1380 ~180 deg) is purely
    /// due to the ADR 0294 straight-ahead framing (SPOKE_ANG = -14 deg lies below the bottom edge at 0 deg).
    /// </summary>
    public class SteeringWheelVisibilityTests
    {
        const string PrefabPath = "Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab";
        static readonly float[] SteerAnglesDeg = { -540f, -360f, -180f, -90f, -45f, -35f, 0f, 35f, 45f, 90f, 180f, 360f, 540f };

        GameObject m_Truck;
        GameObject m_CamGo;

        [TearDown]
        public void TearDown()
        {
            if (m_CamGo != null) Object.DestroyImmediate(m_CamGo);
            if (m_Truck != null) Object.DestroyImmediate(m_Truck);
        }

        GameObject InstantiateTruckOrIgnore()
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
            if (prefab == null) Assert.Ignore("TRAKT prefab not generated (outside git): Kamion/Setup/Rebuild TRAKT truck");
            m_Truck = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            return m_Truck;
        }

        Camera CreateCabDriverCamera(GameObject truck)
        {
            var eye = truck.GetComponentsInChildren<Transform>(true).First(t => t.name == "DriverEyePoint");
            m_CamGo = new GameObject("TestCabDriverCamera");
            m_CamGo.transform.position = eye.position;
            m_CamGo.transform.rotation = truck.transform.rotation * Quaternion.Euler(DriverHead.RestPitchDownDeg, 0f, 0f);
            var cam = m_CamGo.AddComponent<Camera>();
            cam.fieldOfView = ControlSettings.DefaultCabFovDeg;
            cam.aspect = 16f / 9f;
            cam.nearClipPlane = 0.03f;
            cam.farClipPlane = 1400f;
            return cam;
        }

        [Test]
        public void SteeringWheel_SingleRenderer_ContainsRimPodsAndButtonIcons()
        {
            var truck = InstantiateTruckOrIgnore();
            var vis = truck.GetComponent<VehicleVisuals>();
            Assert.IsNotNull(vis.steeringWheel, "VehicleVisuals.steeringWheel pivot");

            var wheelRenderers = vis.steeringWheel.GetComponentsInChildren<MeshRenderer>(true);
            var lod0 = wheelRenderers.Single(r => r.name == "STEERING_WHEEL_LOD0");
            var mesh = lod0.GetComponent<MeshFilter>().sharedMesh;
            Assert.IsNotNull(mesh, "STEERING_WHEEL_LOD0 mesh");

            var slotNames = lod0.sharedMaterials.Select(m => m != null ? m.name.Replace(" (Instance)", "") : "").ToArray();
            int leatherSub = Array.FindIndex(slotNames, s => s.StartsWith("MI_Cab_Leather", StringComparison.Ordinal));
            int plasticSub = Array.FindIndex(slotNames, s => s.StartsWith("MI_Cab_Plastic", StringComparison.Ordinal));
            int decalSub = Array.FindIndex(slotNames, s => s.StartsWith("MI_Cab_Decal", StringComparison.Ordinal));

            Assert.That(leatherSub, Is.GreaterThanOrEqualTo(0), "rim leather submesh in STEERING_WHEEL_LOD0");
            Assert.That(plasticSub, Is.GreaterThanOrEqualTo(0), "spoke/pod/button plastic submesh in STEERING_WHEEL_LOD0");
            Assert.That(decalSub, Is.GreaterThanOrEqualTo(0), "button icon decal submesh in STEERING_WHEEL_LOD0");
            Assert.That(mesh.GetTriangles(leatherSub).Length, Is.GreaterThan(0), "leather rim triangles");
            Assert.That(mesh.GetTriangles(plasticSub).Length, Is.GreaterThan(0), "button/spoke plastic triangles");
            Assert.That(mesh.GetTriangles(decalSub).Length, Is.GreaterThan(0), "button pictogram decal triangles");

            // Verify button icon vertices exist on BOTH left and right side spokes in the pod radius band (0.11..0.19 m).
            var verts = mesh.vertices;
            var toCol = vis.steeringWheel.worldToLocalMatrix * lod0.transform.localToWorldMatrix;
            int leftPodVerts = 0, rightPodVerts = 0;
            foreach (int idx in mesh.GetTriangles(decalSub).Distinct())
            {
                Vector3 p = toCol.MultiplyPoint3x4(verts[idx]);
                float r = new Vector2(p.x, p.y).magnitude;
                if (r >= 0.11f && r <= 0.19f)
                {
                    if (p.x < -0.10f) leftPodVerts++;
                    else if (p.x > 0.10f) rightPodVerts++;
                }
            }
            Assert.That(leftPodVerts, Is.GreaterThanOrEqualTo(12), "left switch pod icon vertices on STEERING_WHEEL_LOD0");
            Assert.That(rightPodVerts, Is.GreaterThanOrEqualTo(12), "right switch pod icon vertices on STEERING_WHEEL_LOD0");
        }

        [Test]
        public void SteeringWheel_ActiveAndUnculled_ForAllTiersAndSteerAngles()
        {
            var truck = InstantiateTruckOrIgnore();
            var rig = truck.GetComponent<TruckVisualRig>();
            var vis = truck.GetComponent<VehicleVisuals>();
            var cam = CreateCabDriverCamera(truck);
            var frustum = GeometryUtility.CalculateFrustumPlanes(cam);

            var wheelLod0 = vis.steeringWheel.GetComponentsInChildren<MeshRenderer>(true).Single(r => r.name == "STEERING_WHEEL_LOD0");
            var otherLods = vis.steeringWheel.GetComponentsInChildren<MeshRenderer>(true).Where(r => r != wheelLod0).ToArray();
            var profile = QualityProfile.Load();
            Quaternion rest = vis.steeringWheel.localRotation;

            try
            {
                for (int level = 0; level < 4; level++)
                {
                    string tierName = level == 3 ? "Ultra" : TruckVisualRig.TierNames[level];
                    float lodBias = profile != null && profile.TryGet(tierName, out var ts) ? ts.lodBias : 0.5f;
                    // Even with ExtraViewCostMonitor's worst-case 0.6x LOD bias reduction, the cab interior must not cull.
                    float worstLodBias = lodBias * 0.6f;

                    foreach (float deg in SteerAnglesDeg)
                    {
                        vis.steeringWheel.localRotation = rest * Quaternion.AngleAxis(-deg, Vector3.forward);
                        rig.forceLevel = level;
                        rig.Apply();

                        Assert.IsTrue(wheelLod0.enabled, $"STEERING_WHEEL_LOD0 enabled at tier {tierName}, steer {deg} deg");
                        Assert.IsTrue(wheelLod0.gameObject.activeInHierarchy, $"STEERING_WHEEL_LOD0 active at tier {tierName}, steer {deg} deg");
                        foreach (var other in otherLods)
                            Assert.IsFalse(other.enabled, $"{other.name} disabled at tier {tierName}, steer {deg} deg");

                        var lods = rig.interiorGroup.GetLODs();
                        Assert.AreEqual(1, lods.Length, $"single interior LOD level (no LOD0->LOD1 switch) on {tierName}");
                        Assert.That(Array.IndexOf(lods[0].renderers, wheelLod0), Is.GreaterThanOrEqualTo(0), $"STEERING_WHEEL_LOD0 in interiorGroup on {tierName}");

                        // Verify LODGroup screen-relative height from the driver eye stays well above interiorCull.
                        Vector3 groupCenterW = rig.interiorGroup.transform.TransformPoint(rig.interiorGroup.localReferencePoint);
                        float dist = Vector3.Distance(cam.transform.position, groupCenterW);
                        float tanHalf = Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
                        float screenHeight = rig.interiorGroup.size / (2f * Mathf.Max(dist, 0.01f) * tanHalf) * worstLodBias;
                        Assert.That(screenHeight, Is.GreaterThan(rig.interiorCull * 2f),
                            $"interiorGroup screen height ({screenHeight:F2}) well above cull ({rig.interiorCull}) at tier {tierName}, steer {deg} deg");

                        // Verify renderer world bounds stay valid and intersect the cab-driver frustum at every angle.
                        Bounds b = wheelLod0.bounds;
                        Assert.That(b.size.magnitude, Is.InRange(0.4f, 1.3f), $"valid steering wheel bounds at {deg} deg");
                        Assert.IsTrue(GeometryUtility.TestPlanesAABB(frustum, b), $"steering wheel intersects cab-driver frustum at {deg} deg");
                    }
                }
            }
            finally
            {
                vis.steeringWheel.localRotation = rest;
                rig.forceLevel = -1;
                rig.Apply();
            }
        }

        [Test]
        public void SteeringWheel_ButtonPodsProjection_BelowFrameAtZero_VisibleWhenTurned()
        {
            var truck = InstantiateTruckOrIgnore();
            var rig = truck.GetComponent<TruckVisualRig>();
            var vis = truck.GetComponent<VehicleVisuals>();
            var cam = CreateCabDriverCamera(truck);
            rig.forceLevel = 2;
            rig.Apply();

            var wheelLod0 = vis.steeringWheel.GetComponentsInChildren<MeshRenderer>(true).Single(r => r.name == "STEERING_WHEEL_LOD0");
            var mesh = wheelLod0.GetComponent<MeshFilter>().sharedMesh;
            int decalSub = Array.FindIndex(wheelLod0.sharedMaterials, m => m != null && m.name.StartsWith("MI_Cab_Decal", StringComparison.Ordinal));
            var verts = mesh.vertices;
            var toCol = vis.steeringWheel.worldToLocalMatrix * wheelLod0.transform.localToWorldMatrix;

            var leftPodIndices = mesh.GetTriangles(decalSub).Distinct().Where(i =>
            {
                var p = toCol.MultiplyPoint3x4(verts[i]);
                float r = new Vector2(p.x, p.y).magnitude;
                return r >= 0.11f && r <= 0.19f && p.x < -0.10f;
            }).ToArray();
            var rightPodIndices = mesh.GetTriangles(decalSub).Distinct().Where(i =>
            {
                var p = toCol.MultiplyPoint3x4(verts[i]);
                float r = new Vector2(p.x, p.y).magnitude;
                return r >= 0.11f && r <= 0.19f && p.x > 0.10f;
            }).ToArray();

            int VisibleCount(int[] indices)
            {
                int count = 0;
                foreach (int i in indices)
                {
                    Vector3 vp = cam.WorldToViewportPoint(wheelLod0.transform.TransformPoint(verts[i]));
                    if (vp.z > cam.nearClipPlane && vp.x >= 0f && vp.x <= 1f && vp.y >= 0f && vp.y <= 1f) count++;
                }
                return count;
            }

            Quaternion rest = vis.steeringWheel.localRotation;
            try
            {
                // Straight ahead (0 deg): SPOKE_ANG = -14 deg puts both switch pods below the bottom edge of the ADR 0294 cab-driver frame.
                vis.steeringWheel.localRotation = rest;
                Assert.AreEqual(0, VisibleCount(leftPodIndices), "left pod below bottom edge at 0 deg");
                Assert.AreEqual(0, VisibleCount(rightPodIndices), "right pod below bottom edge at 0 deg");

                // Moderate right turn (+35 deg, as in critic frame t3330): left pod rotates up into view, right pod stays below.
                vis.steeringWheel.localRotation = rest * Quaternion.AngleAxis(-35f, Vector3.forward);
                Assert.That(VisibleCount(leftPodIndices), Is.GreaterThan(0), "left pod rotates into cab-driver frame at +35 deg");
                Assert.AreEqual(0, VisibleCount(rightPodIndices), "right pod stays below frame at +35 deg");

                // Roundabout turn (+180 deg, as in critic frame t1380): both switch pods rotate up into view.
                vis.steeringWheel.localRotation = rest * Quaternion.AngleAxis(-180f, Vector3.forward);
                Assert.That(VisibleCount(leftPodIndices), Is.GreaterThan(0), "left pod visible at +180 deg");
                Assert.That(VisibleCount(rightPodIndices), Is.GreaterThan(0), "right pod visible at +180 deg");
            }
            finally
            {
                vis.steeringWheel.localRotation = rest;
                rig.forceLevel = -1;
                rig.Apply();
            }
        }
    }
}
