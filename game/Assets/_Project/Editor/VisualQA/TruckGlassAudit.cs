using System;
using System.Collections.Generic;
using System.IO;
using Unity.Collections;
using UnityEditor;
using UnityEngine;

namespace Game.Editor.VisualQA
{
    // Read-only actual generated mesh audit, including residual exterior submeshes using the glass shader.
    public static class TruckGlassAudit
    {
        [Serializable] public sealed class Row
        {
            public string renderer, mesh, asset, material, lodGroup;
            public bool enabled, forcedOff, active, readable;
            public int submesh, triangles, inward, outward, mixed, sameWindingCoincident, reverseWindingCoincident;
            public uint grimeSlot; public int glazingBandTriangles, glazingBandInward, glazingBandOutward, dedicatedPaneAabbCandidates;
            public float area, minWorldY, maxWorldY, exteriorTransmission, farClutter;
            public Vector3 cabCentreOS;
        }
        [Serializable] sealed class Packet { public string note; public List<Row> rows=new List<Row>(); }
        static string Point(Vector3 p) => Mathf.RoundToInt(p.x*100000)+","+Mathf.RoundToInt(p.y*100000)+","+Mathf.RoundToInt(p.z*100000);
        static string Hierarchy(Transform t) => t.parent==null?t.name:Hierarchy(t.parent)+"/"+t.name;
        public static void Write(string output)
        {
            var paneBounds=new List<Bounds>();
            foreach(var r in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include,FindObjectsSortMode.None))
                if(r.name.StartsWith("GLASS_",StringComparison.Ordinal)){var b=r.bounds;b.Expand(.01f);paneBounds.Add(b);}
            var frame=Shader.GetGlobalVectorArray("_KamionGrimeUp");
            var packet=new Packet { note="Read-only generated mesh/submesh audit. LOD meshes are listed individually, not added as simultaneous runtime layers. Coincident counts within each submesh only. Non-dedicated pane AABB count is broadphase candidate count, NOT proof of coincident geometry. Inside test matches shader normal dot(CabCentreOS-positionOS)." };
            foreach(var renderer in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include,FindObjectsSortMode.None))
            {
                var filter=renderer.GetComponent<MeshFilter>(); var mesh=filter==null?null:filter.sharedMesh;
                if(mesh==null)continue;
                var materials=renderer.sharedMaterials;
                for(int si=0;si<Math.Min(materials.Length,mesh.subMeshCount);si++)
                {
                    var material=materials[si];
                    if(material==null||material.shader==null||!(material.shader.name=="Kamion/Truck Glass"||material.shader.name.StartsWith("Hidden/Kamion/TruckGlassDiagnostic_",StringComparison.Ordinal)))continue;
                    var row=new Row { renderer=Hierarchy(renderer.transform),mesh=mesh.name,asset=AssetDatabase.GetAssetPath(mesh),material=material.name,
                        lodGroup=renderer.GetComponentInParent<LODGroup>()?.name,enabled=renderer.enabled,forcedOff=renderer.forceRenderingOff,
                        active=renderer.gameObject.activeInHierarchy,readable=mesh.isReadable,submesh=si,grimeSlot=renderer.GetShaderUserValue(),minWorldY=float.PositiveInfinity,maxWorldY=float.NegativeInfinity,
                        cabCentreOS=material.GetVector("_CabCentreOS"),exteriorTransmission=material.GetFloat("_ExteriorTransmission"),farClutter=material.GetFloat("_SeeThroughClutter") };
                    using(var data=MeshUtility.AcquireReadOnlyMeshData(mesh))
                    using(var vertices=new NativeArray<Vector3>(data[0].vertexCount,Allocator.Temp))
                    using(var normals=new NativeArray<Vector3>(data[0].vertexCount,Allocator.Temp))
                    using(var indices=new NativeArray<int>(data[0].GetSubMesh(si).indexCount,Allocator.Temp))
                    {
                        var d=data[0];d.GetVertices(vertices);d.GetNormals(normals);d.GetIndices(indices,si);
                        var seen=new Dictionary<string,int>();
                        for(int k=0;k+2<indices.Length;k+=3)
                        {
                            int ia=indices[k],ib=indices[k+1],ic=indices[k+2];Vector3 a=vertices[ia],b=vertices[ib],c=vertices[ic];
                            Vector3 cross=Vector3.Cross(b-a,c-a);float area=cross.magnitude*.5f;if(area<1e-10f)continue;
                            row.triangles++;row.area+=area;
                            int inside=0;foreach(int index in new[]{ia,ib,ic})
                            {
                                if(Vector3.Dot(normals[index],row.cabCentreOS-vertices[index])>0)inside++;
                                float y=renderer.transform.TransformPoint(vertices[index]).y;row.minWorldY=Mathf.Min(row.minWorldY,y);row.maxWorldY=Mathf.Max(row.maxWorldY,y);
                            }
                            if(inside==3)row.inward++;else if(inside==0)row.outward++;else row.mixed++;
                            Vector3 centre=renderer.transform.TransformPoint((a+b+c)/3);
                            if(row.grimeSlot>=1 && row.grimeSlot<=frame.Length)
                            {
                                Vector4 up=frame[row.grimeSlot-1];float height=Vector3.Dot(centre,new Vector3(up.x,up.y,up.z))+up.w;
                                if(height>=1.6f && height<=3.2f){row.glazingBandTriangles++;if(inside==3)row.glazingBandInward++;if(inside==0)row.glazingBandOutward++;}
                            }
                            if(!renderer.name.StartsWith("GLASS_",StringComparison.Ordinal))foreach(var bounds in paneBounds)if(bounds.Contains(centre)){row.dedicatedPaneAabbCandidates++;break;}
                            string[] points={Point(a),Point(b),Point(c)};Array.Sort(points,StringComparer.Ordinal);string key=string.Join("|",points);
                            Vector3 n=cross.normalized;int axis=Mathf.Abs(n.x)>Mathf.Abs(n.y)?0:1;if(Mathf.Abs(n.z)>Mathf.Abs(n[axis]))axis=2;
                            int sign=n[axis]>=0?1:-1;
                            if(seen.TryGetValue(key,out int old)){if(old==sign)row.sameWindingCoincident++;else row.reverseWindingCoincident++;}else seen.Add(key,sign);
                        }
                    }
                    packet.rows.Add(row);
                }
            }
            File.WriteAllText(output,JsonUtility.ToJson(packet,true));
            Debug.Log("TRUCK_GLASS_AUDIT: rows="+packet.rows.Count+" path="+output);
        }
    }
}
