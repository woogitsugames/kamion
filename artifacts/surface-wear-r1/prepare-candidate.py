"""Generate an inactive, git-apply-checkable D correctness patch. Never edits production source."""
from pathlib import Path
import difflib
import hashlib
import json
import uuid

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/surface-wear-r1'
files={}
name='game/Assets/_Project/World/Import/WorldMeshBake.cs'
old=(ROOT/name).read_text(encoding='utf-8-sig')
new=old.replace('            public bool Uv1;\n','            public bool Uv1;\n            /// <summary>Road-only missing data: preserve the shader no-lane sentinel; other layers keep zero defaults.</summary>\n            public bool RoadWearSentinel;\n',1)
anchor='                if (uv1 != null && p.Uv1 != null) Array.Copy(p.Uv1, 0, uv1, b, p.Uv1.Length);'
assert anchor in new
new=new.replace(anchor,'''                if (uv1 != null)
                {
                    if (p.Uv1 != null) Array.Copy(p.Uv1, 0, uv1, b, p.Uv1.Length);
                    else if (o.RoadWearSentinel)
                        for (int i = 0; i < p.Positions.Length; i++) uv1[b + i] = new Vector2(-1f, 5f);
                }''',1)
files[name]=(old,new)

name='game/Assets/_Project/World/Import/RegionImporter.cs';old=(ROOT/name).read_text(encoding='utf-8-sig')
anchor='                bool uv = false, uv1 = false, colors = false;'
assert old.count(anchor)==1
new=old.replace(anchor,anchor+'\n                bool roadWear = false;',1)
anchor='                        uv1 |= p1 && nd.Primitives[i].Uv1 != null;'
assert new.count(anchor)==1
new=new.replace(anchor,anchor+'''
                        // ADR0099: an all-missing road primitive still needs an explicit no-lane value.
                        // Zero is valid lane0/edge0 and would incorrectly apply maximum gutter dirt.
                        if (layer == "road" && p1 && (id == "road_asphalt" || id == "road_asphalt_new"))
                        { roadWear = true; uv1 = true; }''',1)
anchor='new WorldMeshBake.Options { Uv0 = uv, Uv1 = uv1, Colors = colors }'
assert new.count(anchor)==1
new=new.replace(anchor,'new WorldMeshBake.Options { Uv0 = uv, Uv1 = uv1, Colors = colors, RoadWearSentinel = roadWear }',1)
files[name]=(old,new)

test='''using System;
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
'''
name='game/Assets/_Project/Tests/EditMode/RoadWearUvContractTests.cs';assert not (ROOT/name).exists();files[name]=('',test)
files[name+'.meta']=('','fileFormatVersion: 2\nguid: '+uuid.uuid5(uuid.NAMESPACE_URL,'kamion/ADR0099/RoadWearUvContractTests').hex+'\n')

patch=[];pins={}
for name,(old,new) in files.items():
    patch.append(f'diff --git a/{name} b/{name}\n')
    if not old:patch.append('new file mode 100644\n')
    patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=f'a/{name}' if old else '/dev/null',tofile=f'b/{name}'))
    if not old:
        scratch=OUT/'candidate-sandbox'/name
        assert scratch.resolve().is_relative_to((OUT/'candidate-sandbox').resolve())
        if scratch.is_file():scratch.unlink()
    if old:
        p=OUT/'candidate-sandbox'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(old,encoding='utf-8',newline='\n')
        pins[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
(OUT/'candidate-r1.patch').write_text(''.join(patch),encoding='utf-8',newline='\n')
(OUT/'candidate-source-pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
print('Prepared narrow UV mask contract patch only; no shader/material calibration changes; no production writes.')
