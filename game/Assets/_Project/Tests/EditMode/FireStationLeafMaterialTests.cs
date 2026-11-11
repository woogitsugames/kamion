using System;
using System.Reflection;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    public class FireStationLeafMaterialTests
    {
        static Material Apply(string id, Material material)
        {
            var type=Type.GetType("Game.World.Import.RegionImporter, Game.World.Import.Editor");
            Assert.That(type,Is.Not.Null);
            var method=type.GetMethod("HeroLeafLighting",BindingFlags.Static|BindingFlags.NonPublic);
            Assert.That(method,Is.Not.Null);
            return (Material)method.Invoke(null,new object[]{id,material});
        }

        [Test]
        public void HeroLeafLightingPreservesCalibratedPaletteCoverageAndReimportState()
        {
            var lit=Shader.Find("Universal Render Pipeline/Lit");
            Assert.That(lit,Is.Not.Null);
            var type=Type.GetType("Game.World.Import.RegionImporter, Game.World.Import.Editor");
            Assert.That(type,Is.Not.Null);
            var factory=type.GetMethod("LitMaterial",BindingFlags.Static|BindingFlags.Public);
            Assert.That(factory,Is.Not.Null);
            if(!AssetDatabase.IsValidFolder("Assets/_Generated"))AssetDatabase.CreateFolder("Assets","_Generated");
            string folder="Assets/_Generated/FireStationLeafPolicyTests_"+Guid.NewGuid().ToString("N");
            AssetDatabase.CreateFolder("Assets/_Generated",System.IO.Path.GetFileName(folder));
            string path=folder+"/hero.mat";
            var texture=new Texture2D(2,2);
            try
            {
                for(int reimport=0;reimport<2;reimport++)
                {
                    // Exercise the actual generic importer factory on the SAME asset path, then hero routing.
                    var material=(Material)factory.Invoke(null,new object[]{path,new Color(1.76558f,1.55454f,2.45559f),.97f,0f,texture,true,.5f,true,null});
                    Assert.That(material.shader.name,Is.EqualTo("Universal Render Pipeline/Lit"));
                    material.SetTextureScale("_BaseMap",new Vector2(2f,3f));
                    var stored=material.GetColor("_BaseColor"); // Unity readback, not an unroundtripped literal.
                    Assert.That(Apply("fire_station_thuja_shell",material),Is.SameAs(material));
                    Assert.That(material.shader.name,Is.EqualTo("Kamion/Vegetation"));
                    Assert.That(Vector4.Distance(material.GetColor("_BaseColor"),stored),Is.LessThan(1e-6f));
                    Assert.That(material.GetTexture("_BaseMap"),Is.SameAs(texture));
                    Assert.That(material.GetTextureScale("_BaseMap"),Is.EqualTo(new Vector2(2f,3f)));
                    Assert.That(material.GetFloat("_Cutoff"),Is.EqualTo(.5f));
                    Assert.That(material.GetFloat("_Cull"),Is.Zero);
                    Assert.That(material.GetFloat("_AlphaToMask"),Is.EqualTo(1f));
                    Assert.That(material.GetFloat("_Transmission"),Is.EqualTo(.25f));
                    Assert.That(material.GetFloat("_CrownShade"),Is.Zero);
                    Assert.That(material.renderQueue,Is.EqualTo(2450));
                }
            }
            finally { AssetDatabase.DeleteAsset(folder);UnityEngine.Object.DestroyImmediate(texture); }
        }

        [TestCase("hedge_shell_thuja")]
        [TestCase("fire_station_alpha")]
        public void HeroLeafLightingLeavesRouteHedgesAndLowTextFenceMaterialUntouched(string id)
        {
            var material=new Material(Shader.Find("Universal Render Pipeline/Lit"));
            try
            {
                var before=EditorJsonUtility.ToJson(material,true);
                Assert.That(Apply(id,material),Is.SameAs(material));
                Assert.That(EditorJsonUtility.ToJson(material,true),Is.EqualTo(before));
            }
            finally { UnityEngine.Object.DestroyImmediate(material); }
        }
    }
}
