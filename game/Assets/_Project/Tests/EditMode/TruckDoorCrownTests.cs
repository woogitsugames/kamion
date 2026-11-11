using System;
using System.Linq;
using Game.Editor.VisualQA;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Tests.EditMode
{
    public sealed class TruckDoorCrownTests
    {
        float oldOff;
        [SetUp] public void Setup(){oldOff=Shader.GetGlobalFloat("_KamionDoorCrownOff");Shader.SetGlobalFloat("_KamionDoorCrownOff",0);}
        [TearDown] public void Restore(){Shader.SetGlobalFloat("_KamionDoorCrownOff",oldOff);}
        static void RequireGpu(){if(SystemInfo.graphicsDeviceType==GraphicsDeviceType.Null)Assert.Ignore("Actual production HLSL requires GPU");}
        static string GradientAt(string p,string n="float3(1,0,0)",string paint="1",string layer="1025u") => "KamionDoorCrownGradient("+p+","+n+","+paint+","+layer+")";
        static float LengthAt(string p,string n="float3(1,0,0)",string paint="1",string layer="1025u") => TruckDoorCrownProbe.Gradient("float3(length("+GradientAt(p,n,paint,layer)+"),0,0)",Matrix4x4.identity);
        [Test] public void ActualHelperIsBoundedAndHasZeroHeightBoundaryGradient()
        {
            RequireGpu();float peak=LengthAt("float3(0,-0.1525,-1.0902)");
            Assert.That(peak,Is.InRange(0.0173f,Mathf.Tan(Mathf.Deg2Rad)));
            foreach(string p in new[]{"float3(0,-0.315,-1.0902)","float3(0,0.335,-1.0902)","float3(0,0.01,-1.7402)","float3(0,0.01,-0.4402)","float3(0,0.01,-1.0902)"})
                Assert.That(LengthAt(p),Is.LessThan(0.00001f),p);
        }
        [Test] public void ActualHelperRejectsBodyTrimGlassInnerSkinAndOutsideDoorPatch()
        {
            RequireGpu();const string p="float3(0,-0.1525,-1.0902)";
            Assert.That(LengthAt(p,layer:"1u"),Is.EqualTo(0));
            Assert.That(LengthAt(p,paint:"0"),Is.EqualTo(0));
            Assert.That(LengthAt(p,n:"float3(0,1,0)"),Is.EqualTo(0));
            foreach(string outside in new[]{"float3(0.03,-0.1525,-1.0902)","float3(0,0.5,-1.0902)","float3(0,-0.5,-1.0902)","float3(0,-0.1525,0)"})
                Assert.That(LengthAt(outside),Is.EqualTo(0),outside);
            Shader.SetGlobalFloat("_KamionDoorCrownOff",1);
            Assert.That(LengthAt(p),Is.EqualTo(0));
        }
        [Test] public void ActualHelperPreservesBothDoorSidesAndObjectLocalCoordinatesThroughHingeSuspensionRebase()
        {
            RequireGpu();const string local="float3(0,-0.1525,-1.0902)";
            float closed=LengthAt(local),left=LengthAt(local,n:"float3(-1,0,0)");Assert.That(left,Is.EqualTo(closed).Within(0.000001f));
            string p="TransformWorldToObject(TransformObjectToWorld("+local+"))";
            foreach(var pose in new[]{Matrix4x4.TRS(new Vector3(-1.245f,1.6f,4.8902f),Quaternion.Euler(0,80,0),Vector3.one),
                Matrix4x4.TRS(new Vector3(-1.245f,1.68f,4.8902f),Quaternion.Euler(3,80,2),Vector3.one),
                Matrix4x4.TRS(new Vector3(1000.3f,-20,2000.2f),Quaternion.Euler(3,-70,2),Vector3.one)})
            {
                float actual=TruckDoorCrownProbe.Gradient("float3(length("+GradientAt(p)+"),0,0)",pose);
                Assert.That(actual,Is.EqualTo(closed).Within(0.00005f));
            }
        }
        static MeshRenderer[] ActualDoors()
        {
            var prefab=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab");
            Assert.That(prefab,Is.Not.Null,"Build canonical truck before fixture tests");
            var renderers=prefab.GetComponentsInChildren<MeshRenderer>(true);
            var doors=renderers.Where(r=>r.name.StartsWith("DOOR_L_LOD",StringComparison.Ordinal)||r.name.StartsWith("DOOR_R_LOD",StringComparison.Ordinal)).ToArray();
            Assert.That(doors.Length,Is.EqualTo(6),"Both doors all3LOD");
            foreach(var r in renderers)
            {
                bool actualDoor=doors.Contains(r);
                Assert.That((r.renderingLayerMask&(1u<<10))!=0,Is.EqualTo(actualDoor),r.name);
                if(actualDoor)Assert.That((r.renderingLayerMask&1u)!=0,Is.True,"Default lightlayer0 preserved "+r.name);
            }
            return doors;
        }
        [Test] public void CanonicalPrefabTagsExactlyBothDoorsAllThreeLods(){ActualDoors();}
        [TestCase(false)] [TestCase(true)]
        public void ActualCanonicalMeshesAndRendererLayerDataReachGpuWithLightLayersDefinitionOffAndOn(bool lightLayers)
        {
            RequireGpu();foreach(var r in ActualDoors())
                Assert.That(TruckDoorCrownProbe.ActualDoorTag(r,lightLayers),Is.EqualTo(1).Within(0.001f),r.name);
        }
    }
}
