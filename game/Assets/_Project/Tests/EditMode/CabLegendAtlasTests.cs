using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    // The baked sets must not accidentally share the biased Low atlas with the other tiers.
    public class CabLegendAtlasTests
    {
        [TestCase("Low", 256, -0.75f)]
        [TestCase("Medium", 512, 0f)]
        [TestCase("High", 1024, 0f)]
        public void BakedLegendMaterial_UsesTierSpecificAtlasAndBias(string tier, int size, float bias)
        {
            var set = AssetDatabase.LoadAssetAtPath<TruckMaterialSet>(
                "Assets/_Generated/Truck/Resources/TRAKT/TruckMaterials_" + tier + ".asset");
            if (set == null) Assert.Ignore("TRAKT material sets not built");
            var material = set.Get("MI_Cab_Decal");
            Assert.That(material, Is.Not.Null);
            Assert.That(material.GetFloat("_Cutoff"), Is.EqualTo(0.5f).Within(1e-5f));


            var texture = material.GetTexture("_DecalAtlas") as Texture2D;
            Assert.That(texture, Is.Not.Null);
            Assert.That(texture.width, Is.EqualTo(size));
            Assert.That(texture.height, Is.EqualTo(size));
            var path = AssetDatabase.GetAssetPath(texture);
            StringAssert.Contains("/" + tier + "/T_Cab_Decal.png", path);
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            Assert.That(importer, Is.Not.Null);
            Assert.That(importer.mipmapEnabled, Is.True);
            Assert.That(importer.mipMapBias, Is.EqualTo(bias).Within(1e-5f));
        }
    }
}



