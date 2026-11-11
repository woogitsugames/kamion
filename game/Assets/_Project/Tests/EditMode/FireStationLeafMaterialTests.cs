using System;
using System.Reflection;
using Game.Rendering;
using Game.World;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    public class FireStationLeafMaterialTests
    {
        const BindingFlags PrivateInstance=BindingFlags.Instance|BindingFlags.NonPublic;
        static void SetTier(QualityProfile.Tier tier,bool hasCurrent)
        {
            typeof(QualityProfileApplier).GetProperty("Current").GetSetMethod(true).Invoke(null,new object[]{tier});
            typeof(QualityProfileApplier).GetProperty("HasCurrent").GetSetMethod(true).Invoke(null,new object[]{hasCurrent});
        }
        static Material[] Bound(WorldInstances world) =>
            (Material[])typeof(WorldInstances).GetField("m_Mats",PrivateInstance).GetValue(world);

        [Test]
        public void HeroRuntimeCopyTracksHighLowWithSameSimpleFlagAndNeverMutatesSharedAssets()
        {
            var oldTier=QualityProfileApplier.Current;bool oldHas=QualityProfileApplier.HasCurrent;
            float oldBlend=Shader.GetGlobalFloat("_KamionImpostorBlend");
            var importer=Type.GetType("Game.World.Import.RegionImporter, Game.World.Import.Editor");
            Assert.That(importer,Is.Not.Null);
            var factory=importer.GetMethod("LitMaterial",BindingFlags.Static|BindingFlags.Public);
            Assert.That(factory,Is.Not.Null);
            if(!AssetDatabase.IsValidFolder("Assets/_Generated"))AssetDatabase.CreateFolder("Assets","_Generated");
            string folder="Assets/_Generated/FireStationLeafPolicyTests_"+Guid.NewGuid().ToString("N");
            AssetDatabase.CreateFolder("Assets/_Generated",System.IO.Path.GetFileName(folder));
            var texture=new Texture2D(2,2);var go=new GameObject("HeroLeafPolicyTest");
            var set=ScriptableObject.CreateInstance<WorldInstanceSet>();
            var hedge=new Material(Shader.Find("Universal Render Pipeline/Lit")){name="M_hedge_shell_thuja"};
            var text=new Material(Shader.Find("Universal Render Pipeline/Lit")){name="M_fire_station_alpha"};
            try
            {
                SetTier(default,false);
                var world=go.AddComponent<WorldInstances>();
                var build=typeof(WorldInstances).GetMethod("BuildMaterials",PrivateInstance);
                var read=typeof(WorldInstances).GetMethod("ReadTier",PrivateInstance);
                var low=new QualityProfile.Tier{name="Low",simpleFoliage=true,leafAlphaToCoverage=true,treeCullM=600f};
                var high=low;high.name="High";
                string hedgeBefore=EditorJsonUtility.ToJson(hedge,true),textBefore=EditorJsonUtility.ToJson(text,true);
                for(int reimport=0;reimport<2;reimport++)
                {
                    // Real generic importer factory on the SAME path; persisted source must remain Lit.
                    var hero=(Material)factory.Invoke(null,new object[]{folder+"/hero.mat",new Color(1.76558f,1.55454f,2.45559f),.97f,0f,texture,true,.5f,true,null});
                    hero.name="M_fire_station_thuja_shell";hero.SetTextureScale("_BaseMap",new Vector2(2,3));
                    Assert.That(hero.shader.name,Is.EqualTo("Universal Render Pipeline/Lit"));
                    set.materials=new[]{hero,hedge,text};world.set=set;
                    var stored=hero.GetColor("_BaseColor");string sourceBefore=EditorJsonUtility.ToJson(hero,true);
                    SetTier(low,true);build.Invoke(world,new object[]{true});
                    Assert.That(Bound(world)[0],Is.SameAs(hero));
                    SetTier(high,true);read.Invoke(world,null); // simpleFoliage is STILL true: quality cache must rebuild.
                    var copy=Bound(world)[0];
                    Assert.That(copy,Is.Not.SameAs(hero));
                    Assert.That(copy.shader.name,Is.EqualTo("Kamion/Vegetation"));
                    Assert.That(Vector4.Distance(copy.GetColor("_BaseColor"),stored),Is.LessThan(1e-6f));
                    Assert.That(copy.GetTexture("_BaseMap"),Is.SameAs(texture));
                    Assert.That(copy.GetTextureScale("_BaseMap"),Is.EqualTo(new Vector2(2,3)));
                    Assert.That(copy.GetFloat("_Cutoff"),Is.EqualTo(.5f));
                    Assert.That(copy.GetFloat("_AlphaToMask"),Is.EqualTo(1f));
                    Assert.That(copy.GetFloat("_Cull"),Is.Zero);
                    Assert.That(copy.GetFloat("_Transmission"),Is.EqualTo(.25f));
                    Assert.That(copy.GetFloat("_CrownShade"),Is.Zero);
                    Assert.That(Bound(world)[1],Is.SameAs(hedge));Assert.That(Bound(world)[2],Is.SameAs(text));
                    SetTier(low,true);read.Invoke(world,null); // High -> Low with unchanged simple flag.
                    Assert.That(Bound(world)[0],Is.SameAs(hero));
                    Assert.That(hero.shader.name,Is.EqualTo("Universal Render Pipeline/Lit"));
                    Assert.That(EditorJsonUtility.ToJson(hero,true),Is.EqualTo(sourceBefore));
                }
                Assert.That(EditorJsonUtility.ToJson(hedge,true),Is.EqualTo(hedgeBefore));
                Assert.That(EditorJsonUtility.ToJson(text,true),Is.EqualTo(textBefore));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(go);UnityEngine.Object.DestroyImmediate(set);
                AssetDatabase.DeleteAsset(folder);UnityEngine.Object.DestroyImmediate(texture);
                UnityEngine.Object.DestroyImmediate(hedge);UnityEngine.Object.DestroyImmediate(text);
                SetTier(oldTier,oldHas);Shader.SetGlobalFloat("_KamionImpostorBlend",oldBlend);
            }
        }
    }
}
