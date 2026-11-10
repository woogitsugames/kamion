using System.IO;
using System.Text.RegularExpressions;
using Game.Rendering;
using NUnit.Framework;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0044 addendum r9: the on-device control camera (qacam=cab-dash) is enabled while the tagged MainCamera is
    /// disabled, so Camera.main is null. CabInteriorLighting used Camera.main and rendered the cab with the exterior state
    /// (no cab-view gain, enclosure 0.88, no shadow lift): A16 cab-dash 25-44 % of pixels below 3 % luma vs ~1.5 % in the
    /// editor (whose runner passes the camera). These tests pin the per-frame (build) path, not the editor runner path.
    /// </summary>
    public class CabViewCameraTests
    {
        static readonly int k_Enclosure = Shader.PropertyToID("_CabEnclosure");

        [SetUp]
        public void EmptyScene() => EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        static Camera MakeCamera(string name, Vector3 pos, bool enabled, bool mainTag = false, float depth = 0f)
        {
            var go = new GameObject(name);
            if (mainTag) go.tag = "MainCamera";
            go.transform.position = pos;
            var c = go.AddComponent<Camera>();
            c.depth = depth;
            c.enabled = enabled;
            return c;
        }

        [Test]
        public void Resolve_FallsBackToTheEnabledScreenCamera_WhenMainCameraIsDisabled()
        {
            var main = MakeCamera("Main Camera", new Vector3(0f, 1.6f, -12f), enabled: false, mainTag: true);
            var qa = MakeCamera("QA_cab-dash", new Vector3(-0.55f, 2.5f, 0.2f), enabled: true, depth: 10f);
            var rt = new RenderTexture(16, 16, 16);
            var mirror = MakeCamera("MirrorCam", Vector3.zero, enabled: true, depth: 50f);
            mirror.targetTexture = rt;
            try
            {
                Assert.That(Camera.main, Is.Null, "precondition: the qacam setup leaves Camera.main null");
                Assert.That(ViewCameraResolver.Resolve(null), Is.SameAs(qa), "on-screen camera, not the render-texture mirror");
                Assert.That(ViewCameraResolver.Resolve(main), Is.SameAs(qa), "a disabled explicit camera is not the view");
                main.enabled = true;
                Assert.That(ViewCameraResolver.Resolve(null), Is.SameAs(main), "gameplay: the tagged main camera");
                Assert.That(ViewCameraResolver.Resolve(qa), Is.SameAs(qa), "an enabled explicit camera wins");
            }
            finally
            {
                mirror.targetTexture = null;
                Object.DestroyImmediate(rt);
            }
        }

        [Test]
        public void CabViewState_IsAppliedUnderTheControlCamera()
        {
            var cabGo = new GameObject("cab");
            MakeCamera("Main Camera", new Vector3(0f, 1.6f, -12f), enabled: false, mainTag: true);
            MakeCamera("QA_cab-dash", new Vector3(-0.55f, 2.5f, 0.2f), enabled: true, depth: 10f);
            var cl = cabGo.AddComponent<CabInteriorLighting>();
            cl.cab = cabGo.transform;
            cl.RefreshForView();
            Assert.That(cl.LastGain, Is.GreaterThanOrEqualTo(Mathf.Pow(2f, cl.cabViewEv) - 1e-4f), "cab-view gain applied");
            Assert.That(Shader.GetGlobalFloat(k_Enclosure), Is.EqualTo(cl.enclosure).Within(1e-4f), "in-cab enclosure, not the exterior one");
        }

        [Test]
        public void ExteriorState_StaysOutsideTheCab()
        {
            var cabGo = new GameObject("cab");
            MakeCamera("Main Camera", new Vector3(6f, 2f, 9f), enabled: true, mainTag: true);
            var cl = cabGo.AddComponent<CabInteriorLighting>();
            cl.cab = cabGo.transform;
            cl.RefreshForView();
            Assert.That(cl.LastGain, Is.EqualTo(1f));
            Assert.That(Shader.GetGlobalFloat(k_Enclosure), Is.EqualTo(cl.exteriorEnclosure).Within(1e-4f));
        }

        /// <summary>Guard: per-view rendering state never reads Camera.main directly (null under the control camera).</summary>
        [Test]
        public void RenderingRuntime_DoesNotUseCameraMainDirectly()
        {
            string root = Path.Combine(Application.dataPath, "_Project/Rendering/Runtime");
            var token = new Regex(@"\bCamera\.main\b");
            foreach (var f in Directory.GetFiles(root, "*.cs", SearchOption.AllDirectories))
            {
                if (Path.GetFileName(f) == "ViewCameraResolver.cs") continue;
                var lines = File.ReadAllLines(f);
                for (int i = 0; i < lines.Length; i++)
                {
                    string code = lines[i];
                    int c = code.IndexOf("//", System.StringComparison.Ordinal);
                    if (c >= 0) code = code.Substring(0, c);
                    Assert.That(token.IsMatch(code), Is.False,
                        $"{Path.GetFileName(f)}:{i + 1} uses Camera.main; use ViewCameraResolver.Resolve (ADR 0044 r9)");
                }
            }
        }
    }
}
