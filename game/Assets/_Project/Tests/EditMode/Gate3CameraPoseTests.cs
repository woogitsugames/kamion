using System.Collections.Generic;
using Game.Gameplay;
using Game.World;
using NUnit.Framework;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// r8 putry_approach: the phone re-seated "photo_match" cameras on the road collision +1.7 m while the editor kept the file
    /// height (22 % of pixels differed). Both paths now go through Gate3Cameras.CreateAll / ComputePose; the file height is the truth
    /// for photo_match, other kinds are re-seated.
    /// </summary>
    public class Gate3CameraPoseTests
    {
        // File coordinates are (E, N, absolute height); a default WorldRegionRoot maps them to Unity (x = E, y = height, z = N).
        const string Json = "{\"cameras\":[" +
            "{\"id\":\"g3b_rondo_putry_approach\",\"kind\":\"photo_match\",\"pos\":[10,5,134.48],\"look_at\":[10,40,137.8],\"fov_deg\":60}," +
            "{\"id\":\"g3b_eye_s1532\",\"kind\":\"driver_eye\",\"pos\":[30,5,134.0],\"look_at\":[30,40,134.0],\"fov_deg\":60}," +
            "{\"id\":\"g3_forced_file\",\"kind\":\"driver_eye\",\"seat\":\"file\",\"pos\":[50,5,134.0],\"look_at\":[50,40,134.0],\"fov_deg\":60}," +
            "{\"id\":\"g3_forced_road\",\"kind\":\"photo_match\",\"seat\":\"road\",\"pos\":[70,5,134.0],\"look_at\":[70,40,134.0],\"fov_deg\":60}]}";

        WorldRegionRoot m_Root;

        [SetUp]
        public void Setup()
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            m_Root = new GameObject("Root").AddComponent<WorldRegionRoot>();
            var ground = GameObject.CreatePrimitive(PrimitiveType.Cube);   // top surface at y = 4 m
            ground.transform.position = new Vector3(40f, 3f, 20f);
            ground.transform.localScale = new Vector3(200f, 2f, 200f);
            Physics.SyncTransforms();
        }

        [Test]
        public void ReseatPolicy_PhotoMatchKeepsFileHeight_OthersReseat_FileSeatWins()
        {
            Assert.IsFalse(Gate3Cameras.ReseatOnRoad(new Gate3Cameras.Entry { kind = "photo_match" }));
            Assert.IsTrue(Gate3Cameras.ReseatOnRoad(new Gate3Cameras.Entry { kind = "driver_eye" }));
            Assert.IsTrue(Gate3Cameras.ReseatOnRoad(new Gate3Cameras.Entry { kind = "photo_match", seat = "road" }));
            Assert.IsFalse(Gate3Cameras.ReseatOnRoad(new Gate3Cameras.Entry { kind = "driver_eye", seat = "file" }));
        }

        [Test]
        public void ComputePose_ShiftsLookAtWithPosition_AndLeavesFileHeightCameras()
        {
            var e = new Gate3Cameras.Entry { kind = "driver_eye" };
            bool seated = Gate3Cameras.ComputePose(e, new Vector3(0, 100f, 0), new Vector3(0, 100f, 40f), (x, z, from) => (true, 10f), out var p, out var l);
            Assert.IsTrue(seated);
            Assert.AreEqual(12.5f, p.y, 1e-4f);
            Assert.AreEqual(12.5f, l.y, 1e-4f);
            var ph = new Gate3Cameras.Entry { kind = "photo_match" };
            seated = Gate3Cameras.ComputePose(ph, new Vector3(0, 100f, 0), new Vector3(0, 100f, 40f), (x, z, from) => (true, 10f), out p, out l);
            Assert.IsFalse(seated);
            Assert.AreEqual(100f, p.y, 1e-6f);
            Assert.AreEqual(100f, l.y, 1e-6f);
        }

        [Test]
        public void CreateAll_GamePathAndEditorPath_GiveTheSamePose_AndPhotoMatchIsNotMoved()
        {
            // Game path (vehicle roots ignored) and editor path (null) must agree exactly.
            var ignore = new List<Transform> { new GameObject("tractor").transform };
            Gate3Cameras.CreateAll(m_Root, ignore, Json);
            var gameParent = GameObject.Find("Gate3ControlCameras");
            gameParent.name = "GameCams";
            Gate3Cameras.CreateAll(m_Root, null, Json);
            var editorParent = GameObject.Find("Gate3ControlCameras");
            Assert.AreNotSame(gameParent, editorParent);

            foreach (var id in new[] { "g3b_rondo_putry_approach", "g3b_eye_s1532", "g3_forced_file", "g3_forced_road" })
            {
                var g = gameParent.transform.Find("QA_" + id);
                var ed = editorParent.transform.Find("QA_" + id);
                Assert.IsNotNull(g, id); Assert.IsNotNull(ed, id);
                Assert.AreEqual(0f, (g.position - ed.position).magnitude, 1e-5f, id + " position");
                Assert.AreEqual(0f, Quaternion.Angle(g.rotation, ed.rotation), 1e-3f, id + " rotation");
            }
            Assert.AreEqual(134.48f, editorParent.transform.Find("QA_g3b_rondo_putry_approach").position.y, 1e-3f, "photo_match keeps the file height");
            Assert.AreEqual(6.5f, editorParent.transform.Find("QA_g3b_eye_s1532").position.y, 1e-3f, "driver_eye: road 4 m + 2.5 m");
            Assert.AreEqual(134.0f, editorParent.transform.Find("QA_g3_forced_file").position.y, 1e-3f);
            Assert.AreEqual(5.7f, editorParent.transform.Find("QA_g3_forced_road").position.y, 1e-3f, "seat=road: 4 m + 1.7 m");
        }
    }
}
