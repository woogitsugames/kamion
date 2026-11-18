using System.IO;
using Game.Editor.Build;
using Game.Editor.Setup;
using NUnit.Framework;
using UnityEditor;

namespace Game.Tests
{
    /// <summary>
    /// full-build-s23 (review 2026-11-17 cabin-pc P1-1): on Windows the cab AO atlas must not use the automatic BC1 format -
    /// its few dark levels per 4x4 block, through the cab shader's smoothstep(0.04, 0.28) on the albedo, drew stair-stepped
    /// black blocks in the driver's view. AO atlases get BC4; other truck textures keep Unity's automatic Standalone format.
    /// </summary>
    public class TruckTextureStandaloneFormatTests
    {
        [TestCase("T_Cab_AO_LOD0", TextureImporterFormat.BC4)]
        [TestCase("T_Cab_AO_LOD2", TextureImporterFormat.BC4)]
        public void AoAtlases_AreBc4(string name, TextureImporterFormat expected) =>
            Assert.AreEqual(expected, TruckAssetBuilder.StandaloneFormatFor(name));

        [TestCase("T_Cab_Decal")]
        [TestCase("T_Cab_Normal_LOD0")]
        [TestCase("T_Display_cluster")]
        public void OtherTextures_KeepAutomatic(string name) => Assert.IsNull(TruckAssetBuilder.StandaloneFormatFor(name));

        [Test]
        public void ImportedCabAoAtlas_HasTheStandaloneOverride()
        {
            const string p = "Assets/_Generated/Truck/Source/Interior/Textures/High/T_Cab_AO_LOD0.png";
            if (!File.Exists(Path.Combine(EditorTools.ProjectRoot, p))) Assert.Ignore("truck assets not built (TruckAssetBuilder.BuildBatch)");
            var ti = (TextureImporter)AssetImporter.GetAtPath(p);
            var s = ti.GetPlatformTextureSettings("Standalone");
            Assert.IsTrue(s.overridden, "Standalone override missing - run TruckAssetBuilder.BuildBatch");
            Assert.AreEqual(TextureImporterFormat.BC4, s.format);
        }
    }
}
