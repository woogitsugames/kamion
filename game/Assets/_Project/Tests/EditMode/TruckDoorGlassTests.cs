using System.Linq;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0059 (review r7 N-3): Kamion/Truck Glass tells the inside face from the outside face with _CabCentreOS in the
    /// glass OBJECT space. The door glass sits under DOOR_L / DOOR_R, so it needs its own centre: with the windscreen value
    /// the cab centre fell into the door glass plane and the inner face was shaded as an outside face from the seat.
    /// </summary>
    public class TruckDoorGlassTests
    {
        const string PrefabPath = "Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab";
        GameObject m_Go;

        [TearDown]
        public void TearDown() { if (m_Go != null) Object.DestroyImmediate(m_Go); }

        [TestCase("Low"), TestCase("Medium"), TestCase("High")]
        public void DoorGlass_OwnMaterial_NoWiperFilm_InsideFaceTowardsCabCentre(string tier)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
            Assume.That(prefab, Is.Not.Null, "TRAKT prefab not generated (Kamion/Setup/Rebuild TRAKT truck)");
            var set = Resources.Load<TruckMaterialSet>("TRAKT/TruckMaterials_" + tier);
            Assume.That(set, Is.Not.Null, "material set " + tier);
            m_Go = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            var ws = m_Go.GetComponentsInChildren<MeshRenderer>(true).First(r => r.name == "GLASS_Windscreen_LOD0");
            var wsMat = set.Get("MI_Ext_Glass");
            Vector3 centreW = ws.transform.TransformPoint((Vector3)wsMat.GetVector("_CabCentreOS"));
            foreach (var side in new[] { "L", "R" })
            {
                var door = m_Go.GetComponentsInChildren<MeshRenderer>(true).First(r => r.name == "GLASS_Door" + side + "_LOD0");
                var mat = set.Get("MI_Ext_DoorGlass" + side);
                Assert.IsNotNull(mat, "MI_Ext_DoorGlass" + side + " on " + tier);
                Assert.AreEqual(0f, mat.GetFloat("_Wiper"), "no wiper road film on the door glass");
                Vector3 c = mat.GetVector("_CabCentreOS");
                Assert.That(Vector3.Distance(door.transform.TransformPoint(c), centreW), Is.LessThan(0.01f), "door-space cab centre = cab centre");
                // Every vertex is classified like the shader does; the double-sided pane must have both faces, and the
                // face whose normal points towards the centre (inside) must face the cab centreline (x towards 0 in the cab).
                var mesh = door.GetComponent<MeshFilter>().sharedMesh;
                var v = mesh.vertices; var n = mesh.normals;
                int inside = 0, outside = 0;
                for (int i = 0; i < v.Length; i++)
                {
                    bool isIn = Vector3.Dot(n[i], c - v[i]) > 0f;
                    if (isIn) inside++; else outside++;
                    if (isIn)
                    {
                        // vehicle frame: left door (x < 0) inner normal points to +x, right door to -x
                        Vector3 nV = m_Go.transform.InverseTransformDirection(door.transform.TransformDirection(n[i]));
                        Assert.That(side == "L" ? nV.x : -nV.x, Is.GreaterThan(0f), "inside face of door " + side + " faces the cab");
                    }
                }
                Assert.That(inside, Is.GreaterThan(0), "inside face present");
                Assert.That(outside, Is.GreaterThan(0), "outside face present");
                Assert.That(Mathf.Abs(inside - outside), Is.LessThanOrEqualTo(v.Length / 10), "one inside vertex per outside vertex (double-sided pane)");
            }
        }
    }
}
