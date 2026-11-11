using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Tests
{
    public class RoadWearUvContractTests
    {
        static Mesh Build(bool sentinel)
        {
            var bake=Type.GetType("Game.World.Import.WorldMeshBake, Game.World.Import.Editor",true);
            var optionsType=bake.GetNestedType("Options");
            var primitiveType=Type.GetType("Game.World.Import.GlbReader+Primitive, Game.World.Import.Editor",true);
            var list=(IList)Activator.CreateInstance(typeof(List<>).MakeGenericType(primitiveType));
            for(int j=0;j<2;j++)
            {
                var primitive=Activator.CreateInstance(primitiveType);
                primitiveType.GetField("Positions").SetValue(primitive,new[]{new Vector3(j*2,0,0),new Vector3(j*2+1,0,0),new Vector3(j*2,0,1)});
                primitiveType.GetField("Normals").SetValue(primitive,new[]{Vector3.up,Vector3.up,Vector3.up});
                primitiveType.GetField("Indices").SetValue(primitive,new[]{0,1,2});
                primitiveType.GetField("Material").SetValue(primitive,"road_asphalt");
                if(j==0)primitiveType.GetField("Uv1").SetValue(primitive,new[]{Vector2.zero,new Vector2(.5f,.25f),new Vector2(-1,5)});
                list.Add(primitive);
            }
            object options=Activator.CreateInstance(optionsType);
            optionsType.GetField("Uv1").SetValue(options,true);
            var policy=optionsType.GetField("RoadWearSentinel");Assert.NotNull(policy);
            policy.SetValue(options,sentinel);
            return (Mesh)bake.GetMethod("Compact",BindingFlags.Public|BindingFlags.Static).Invoke(null,new object[]{"road-uv-contract",list,options});
        }

        static byte[] Bytes(Mesh mesh)
        {
            using(var data=MeshUtility.AcquireReadOnlyMeshData(mesh))return data[0].GetVertexData<byte>().ToArray();
        }
        static Vector2 Uv(Mesh mesh,byte[] bytes,int vertex)
        {
            int at=vertex*mesh.GetVertexBufferStride(0)+mesh.GetVertexAttributeOffset(VertexAttribute.TexCoord1);
            return new Vector2(Mathf.HalfToFloat((ushort)(bytes[at]|bytes[at+1]<<8)),Mathf.HalfToFloat((ushort)(bytes[at+2]|bytes[at+3]<<8)));
        }

        [Test]
        public void MissingRoadUvUsesSentinelButValidZeroAndExistingDataSurvive()
        {
            var mesh=Build(true);
            try
            {
                var bytes=Bytes(mesh);
                Assert.That(Uv(mesh,bytes,0),Is.EqualTo(Vector2.zero));
                Assert.That(Uv(mesh,bytes,1),Is.EqualTo(new Vector2(.5f,.25f)));
                Assert.That(Uv(mesh,bytes,2),Is.EqualTo(new Vector2(-1,5)));
                for(int i=3;i<6;i++)Assert.That(Uv(mesh,bytes,i),Is.EqualTo(new Vector2(-1,5)));
            }
            finally{UnityEngine.Object.DestroyImmediate(mesh);}
        }
        [Test]
        public void OtherLayersKeepTheirLegacyZeroFallback()
        {
            var mesh=Build(false);
            try{var bytes=Bytes(mesh);for(int i=3;i<6;i++)Assert.That(Uv(mesh,bytes,i),Is.EqualTo(Vector2.zero));}
            finally{UnityEngine.Object.DestroyImmediate(mesh);}
        }
        [Test]
        public void PolicyChangesOnlyMissingUvBytesNotGeometryOrSubmeshes()
        {
            var before=Build(false);var after=Build(true);
            try
            {
                Assert.That(before.vertexCount,Is.EqualTo(after.vertexCount));Assert.That(before.subMeshCount,Is.EqualTo(after.subMeshCount));
                Assert.That(before.bounds,Is.EqualTo(after.bounds));
                var a=Bytes(before);var b=Bytes(after);int stride=before.GetVertexBufferStride(0),offset=before.GetVertexAttributeOffset(VertexAttribute.TexCoord1);
                for(int i=0;i<before.vertexCount;i++)for(int j=0;j<stride;j++)
                    if(i<3||j<offset||j>=offset+4)Assert.That(a[i*stride+j],Is.EqualTo(b[i*stride+j]));
                using(var da=MeshUtility.AcquireReadOnlyMeshData(before))using(var db=MeshUtility.AcquireReadOnlyMeshData(after))
                    CollectionAssert.AreEqual(da[0].GetIndexData<ushort>().ToArray(),db[0].GetIndexData<ushort>().ToArray());
            }
            finally{UnityEngine.Object.DestroyImmediate(before);UnityEngine.Object.DestroyImmediate(after);}
        }
    }
}
