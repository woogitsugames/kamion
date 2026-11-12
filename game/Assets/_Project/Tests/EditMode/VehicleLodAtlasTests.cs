using System;
using System.Collections.Generic;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;
using Game.World;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    public class VehicleLodAtlasTests
    {
        static Type Factory => Type.GetType("Game.World.Import.VehicleLodAtlasMaterials, Game.World.Import.Editor", true);
        static float[] Ends(params object[] values) => (float[])Factory.GetMethod("LodEnds").Invoke(null,
            new object[] { new Dictionary<string, object> { ["vehicle_lod_ends_m"] = values.ToList() }, 3 });

        [Test]
        public void Distances_KeepFixedVehicleCullAndThreeIncreasingBands()
        {
            CollectionAssert.AreEqual(new[] { 40f, 100f, WorldInstances.VehicleCullM }, Ends(40.0, 100.0, 300.0));
        }

        [TestCase(100.0, 40.0, 300.0)]
        [TestCase(40.0, 40.0, 300.0)]
        [TestCase(40.0, 100.0, 150.0)]
        public void Distances_RejectInvalidBandsOrChangedCull(double a, double b, double c)
        {
            var ex = Assert.Throws<TargetInvocationException>(() => Ends(a, b, c));
            Assert.IsInstanceOf<InvalidOperationException>(ex.InnerException);
        }

        [Test]
        public void Distances_RejectMissingBand()
        {
            var ex = Assert.Throws<TargetInvocationException>(() => Ends(40.0, 300.0));
            Assert.IsInstanceOf<InvalidOperationException>(ex.InnerException);
        }

        [Test]
        public void AtlasFlag_RequiresUv0WithoutPaintPayload()
        {
            var type = Type.GetType("Game.World.Import.WorldPbrMaterials, Game.World.Import.Editor", true);
            object[] args = { new Dictionary<string, object> { ["vehicle_lod_atlas"] = true }, "vehicle_lod_details", false, false, false };
            type.GetMethod("Channels", BindingFlags.Static | BindingFlags.Public).Invoke(null, args);
            Assert.IsTrue((bool)args[2]);
            Assert.IsFalse((bool)args[3]);
            Assert.IsFalse((bool)args[4]);
        }

        [Test]
        public void MigratedLibrary_StillRejectsCorruptLod0PlateCorners()
        {
            string path = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "art-source/world/props/street_props.glb"));
            if (!File.Exists(path)) Assert.Ignore("Prototype library not generated: " + path);
            var reader = Type.GetType("Game.World.Import.GlbReader, Game.World.Import.Editor", true);
            object library = reader.GetMethod("Load").Invoke(null, new object[] { path });
            var validator = Type.GetType("Game.World.Import.WorldCarPlateMaterials, Game.World.Import.Editor", true).GetMethod("ValidLibrary");
            Assert.IsTrue((bool)validator.Invoke(null, new[] { library }), "Complete migrated library must remain eligible");
            var nodes = ((IEnumerable)reader.GetField("Nodes").GetValue(library)).Cast<object>();
            object root = nodes.First(n => (string)n.GetType().GetField("Name").GetValue(n) == "car_hatch_white");
            var primitives = ((IEnumerable)root.GetType().GetField("Primitives").GetValue(root)).Cast<object>();
            object plate = primitives.First(p => (string)p.GetType().GetField("Material").GetValue(p) == "car_plate");
            var corners = (Vector2[])plate.GetType().GetField("Uv1").GetValue(plate);
            corners[0] = new Vector2(.3f, .7f);
            Assert.IsFalse((bool)validator.Invoke(null, new[] { library }), "Atlas LOD1 must not relax the LOD0 corner guard");
        }

        [Test]
        public void ImportedVehicles_HaveTwoFarSubmeshes_AndYardAliasReusesNativeMesh()
        {
            const string path = "Assets/_Generated/World/bialystok-industrial-c/Instances.asset";
            var set = AssetDatabase.LoadAssetAtPath<WorldInstanceSet>(path);
            if (set == null) Assert.Ignore("Region not imported: " + path);
            var vehicles = set.prototypes.Where(p => p.name.StartsWith("car_") || p.name.StartsWith("van_")
                || p.name.StartsWith("tractor_") || p.name.StartsWith("trailer_")).ToArray();
            Assert.IsNotEmpty(vehicles);
            var plate = set.materials.FirstOrDefault(m => m != null && m.shader.name == "Kamion/World Car Plate");
            Assert.NotNull(plate, "LOD1 atlas must not disable the original LOD0 plate remap");
            Assert.IsTrue(plate.IsKeywordEnabled("_PLATE_LOCAL_CORNERS"), "LOD0 per-instance plate remapping");
            foreach (var p in vehicles)
            {
                Assert.AreEqual(3, p.lods.Length, p.name);
                Assert.LessOrEqual(p.lods[1].subMeshCount, 2, p.name + " LOD1");
                Assert.LessOrEqual(p.lods[2].subMeshCount, 2, p.name + " LOD2");
                Assert.AreEqual(p.lods.Length, p.lodEndM.Length, p.name + " distance count");
                if (p.name.StartsWith("tractor_") || p.name.StartsWith("trailer_"))
                {
                    Assert.AreSame(p.lods[1], p.lods[2], p.name + " mesh alias");
                    Assert.AreEqual(p.materialStart[1], p.materialStart[2], p.name + " material alias");
                }
            }
        }
    }
}
