using System;
using System.Collections.Generic;
using UnityEngine;

namespace Game.World.Import
{
    /// <summary>ADR0099: editor-only reuse of existing asphalt lane data. Never extrapolates a lane.
    /// Coordinates are already in the same region Unity frame, before chunk baking. Geometry/UV0/age stay unchanged.</summary>
    public sealed class RoadPaintLaneField
    {
        const float Cell = 8f;
        // WORKING tolerances: paint is lifted6mm. Reject other road levels and discontinuous lane fields.
        const float HeightTolerance = .035f, OverlapTolerance = .02f, LinearTolerance = .025f;
        struct Triangle { public Vector3 A,B,C; public Vector3 Lane; public bool Known; }
        readonly List<Triangle> triangles = new List<Triangle>();
        readonly Dictionary<Vector2Int,List<int>> cells = new Dictionary<Vector2Int,List<int>>();
        public sealed class Stats { public int AcceptedComponents, RejectedComponents, ChangedVertices; public double AcceptedArea; }

        public RoadPaintLaneField(GlbReader.MeshNode road)
        {
            if(road==null)return;
            foreach(var p in road.Primitives)
            {
                if(p.Material!="road_asphalt"&&p.Material!="road_asphalt_new")continue;
                for(int i=0;i<p.Indices.Length;i+=3)
                {
                    int a=p.Indices[i],b=p.Indices[i+1],c=p.Indices[i+2];
                    bool known=p.Uv1!=null&&p.Uv1[a].x>=-.5f&&p.Uv1[b].x>=-.5f&&p.Uv1[c].x>=-.5f;
                    var t=new Triangle{A=p.Positions[a],B=p.Positions[b],C=p.Positions[c],Known=known,Lane=known?new Vector3(p.Uv1[a].x,p.Uv1[b].x,p.Uv1[c].x):Vector3.zero};
                    int index=triangles.Count;triangles.Add(t);
                    Vector3 min=Vector3.Min(t.A,Vector3.Min(t.B,t.C)),max=Vector3.Max(t.A,Vector3.Max(t.B,t.C));
                    for(int x=Mathf.FloorToInt(min.x/Cell);x<=Mathf.FloorToInt(max.x/Cell);x++)
                        for(int z=Mathf.FloorToInt(min.z/Cell);z<=Mathf.FloorToInt(max.z/Cell);z++)
                        {var key=new Vector2Int(x,z);if(!cells.TryGetValue(key,out var list))cells[key]=list=new List<int>();list.Add(index);}
                }
            }
        }

        public bool TrySample(Vector3 p,out float lane)
        {
            lane=0;if(!cells.TryGetValue(new Vector2Int(Mathf.FloorToInt(p.x/Cell),Mathf.FloorToInt(p.z/Cell)),out var list))return false;
            int count=0;float lo=float.PositiveInfinity,hi=float.NegativeInfinity;
            foreach(int index in list)
            {
                var t=triangles[index];Vector3 ab=t.B-t.A,ac=t.C-t.A,ap=p-t.A;
                // Double arithmetic avoids large-region float cancellation at triangle boundaries.
                double det=(double)ab.x*ac.z-(double)ab.z*ac.x;if(Math.Abs(det)<1e-8)continue;
                float b=(float)(((double)ap.x*ac.z-(double)ap.z*ac.x)/det),c=(float)(((double)ab.x*ap.z-(double)ab.z*ap.x)/det),a=1-b-c;
                if(Mathf.Min(a,Mathf.Min(b,c))<-.0001f||Mathf.Abs(a*t.A.y+b*t.B.y+c*t.C.y-p.y)>HeightTolerance)continue;
                // A coplanar no-data junction patch is an ambiguity blocker, never an invisible hole in the field.
                if(!t.Known){lane=0;return false;}
                float value=a*t.Lane.x+b*t.Lane.y+c*t.Lane.z;
                lo=Mathf.Min(lo,value);hi=Mathf.Max(hi,value);lane+=value;count++;
            }
            if(count==0||hi-lo>OverlapTolerance){lane=0;return false;}
            lane/=count;return true;
        }

        static int Find(int[] parent,int i){while(parent[i]!=i){parent[i]=parent[parent[i]];i=parent[i];}return i;}
        static void Join(int[] parent,int a,int b){parent[Find(parent,b)]=Find(parent,a);}

        /// <summary>Clones only UV1 when an entire disconnected constant-half paint component is supported.
        /// Existing varying lane data is untouched. Rejecting any triangle rejects its whole component.</summary>
        public GlbReader.MeshNode Transfer(GlbReader.MeshNode paint,out Stats stats)
        {
            stats=new Stats();if(paint==null)return null;
            var result=new GlbReader.MeshNode{Name=paint.Name,Extras=paint.Extras};
            foreach(var p in paint.Primitives)
            {
                if((p.Material!="marking_white"&&p.Material!="marking_yellow")||p.Uv1==null){result.Primitives.Add(p);continue;}
                int count=p.Positions.Length;var parent=new int[count];for(int i=0;i<count;i++)parent[i]=i;
                // Exporters may duplicate vertices for normal/UV seams. Grouping metadata only: never weld geometry.
                var coincident=new Dictionary<(Vector3 Position,float Age),int>();
                for(int i=0;i<count;i++)
                {
                    var key=(p.Positions[i],p.Uv1[i].y);
                    if(coincident.TryGetValue(key,out int other))Join(parent,other,i);else coincident[key]=i;
                }
                for(int j=0;j<p.Indices.Length;j+=3){Join(parent,p.Indices[j],p.Indices[j+1]);Join(parent,p.Indices[j],p.Indices[j+2]);}
                var groups=new Dictionary<int,List<int>>();for(int j=0;j<p.Indices.Length;j+=3)
                {int root=Find(parent,p.Indices[j]);if(!groups.TryGetValue(root,out var ts))groups[root]=ts=new List<int>();ts.Add(j);}
                var newUv=(Vector2[])p.Uv1.Clone();bool any=false;
                foreach(var group in groups.Values)
                {
                    bool constant=true;var vertices=new HashSet<int>();
                    foreach(int j in group)for(int k=0;k<3;k++){int v=p.Indices[j+k];vertices.Add(v);if(Mathf.Abs(p.Uv1[v].x-.5f)>1e-5f)constant=false;}
                    if(!constant)continue;
                    bool valid=true;var lanes=new Dictionary<int,float>();double area=0;
                    foreach(int v in vertices){if(!TrySample(p.Positions[v],out float lane)){valid=false;break;}lanes[v]=lane;}
                    if(valid)foreach(int j in group)
                    {
                        int a=p.Indices[j],b=p.Indices[j+1],c=p.Indices[j+2];Vector3 va=p.Positions[a],vb=p.Positions[b],vc=p.Positions[c];
                        if(!Check((va+vb)*.5f,(lanes[a]+lanes[b])*.5f)||!Check((vb+vc)*.5f,(lanes[b]+lanes[c])*.5f)||!Check((vc+va)*.5f,(lanes[c]+lanes[a])*.5f)||!Check((va+vb+vc)/3f,(lanes[a]+lanes[b]+lanes[c])/3f)){valid=false;break;}
                        area+=Vector3.Cross(vb-va,vc-va).magnitude*.5;
                    }
                    if(!valid){stats.RejectedComponents++;continue;}
                    stats.AcceptedComponents++;stats.AcceptedArea+=area;
                    foreach(int v in vertices)if(Mathf.Abs(newUv[v].x-lanes[v])>1e-6f){newUv[v].x=lanes[v];stats.ChangedVertices++;any=true;}
                }
                result.Primitives.Add(any?new GlbReader.Primitive{Material=p.Material,Positions=p.Positions,Normals=p.Normals,Uv0=p.Uv0,Uv1=newUv,Colors=p.Colors,Indices=p.Indices}:p);
            }
            return result;
        }
        bool Check(Vector3 p,float expected){return TrySample(p,out float actual)&&Mathf.Abs(actual-expected)<=LinearTolerance;}
    }
}
