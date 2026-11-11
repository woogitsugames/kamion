using System.Linq;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests.EditMode
{
    public class MirrorPresentationTests
    {
        [TestCase(0, -1f), TestCase(1, 1f)]
        public void OwnTrailerSide_AppearsAtInnerGlassEdge(int phase, float side)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab");
            Assert.NotNull(prefab, "build TRAKT before testing mirror presentation");
            var mirror = prefab.GetComponentsInChildren<RenderTextureMirror>(true).Single(m => m.phase == phase);
            var eye = prefab.GetComponentsInChildren<Transform>(true).Single(t => t.name == "DriverEyePoint");
            var cam = mirror.GetComponent<Camera>();
            // Same 2.55m trailer side used by MirrorFieldOfVisionTests; 15m behind the ocular point.
            var target = prefab.transform.TransformPoint(new Vector3(side * 1.275f, 1.5f,
                prefab.transform.InverseTransformPoint(eye.position).z - 15f));
            Vector3 cameraPoint = cam.transform.InverseTransformPoint(target);
            float aspect = mirror.fovAspect > 0f ? mirror.fovAspect : mirror.aspect;
            float textureU = .5f + .5f * cameraPoint.x / (cameraPoint.z * Mathf.Tan(cam.fieldOfView * Mathf.Deg2Rad * .5f) * aspect);
            Assert.That(textureU, Is.InRange(0f, 1f), "trailer side in captured field");
            var mesh = mirror.glass.GetComponent<MeshFilter>().sharedMesh;
            var uv = mesh.uv; var vertices = mesh.vertices;
            Vector3 Corner(float u, float v)
            {
                int i = System.Array.FindIndex(uv, p => Mathf.Abs(p.x - u) < .001f && Mathf.Abs(p.y - v) < .001f);
                Assert.GreaterOrEqual(i, 0, "glass UV corner");
                return mirror.glass.transform.TransformPoint(vertices[i]);
            }
            Vector3 p00 = Corner(0, 0), p10 = Corner(1, 0), p01 = Corner(0, 1);
            Vector3 centre = (p10 + p01) * .5f;
            Vector3 eyeRight = Vector3.Cross(Vector3.up, centre - eye.position).normalized;
            float surfaceU = mirror.flipHorizontally ? 1f - textureU : textureU;
            Vector3 shown = p00 + (p10 - p00) * surfaceU + (p01 - p00) * .5f;
            float horizontal = Vector3.Dot(shown - centre, eyeRight);
            TestContext.WriteLine($"phase={phase} textureU={textureU:F3} horizontal={horizontal:F4} flip={mirror.flipHorizontally}");
            Assert.Greater(-side * horizontal, 0f, "own vehicle at inner edge: right in left mirror, left in right mirror; no double flip");
        }
    }
}
