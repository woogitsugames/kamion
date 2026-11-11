using System;
using System.Collections;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    public class RoadPaintLaneFieldTests
    {
        static readonly Type Node=Type.GetType("Game.World.Import.GlbReader+MeshNode, Game.World.Import.Editor",true);
        static readonly Type Primitive=Type.GetType("Game.World.Import.GlbReader+Primitive, Game.World.Import.Editor",true);
        static readonly Type Field=Type.GetType("Game.World.Import.RoadPaintLaneField, Game.World.Import.Editor",true);
        static object MakeNode(params object[] primitives){var n=Activator.CreateInstance(Node);var list=(IList)Node.GetField("Primitives").GetValue(n);foreach(var p in primitives)list.Add(p);return n;}
        static object MakePrimitive(string material,Vector3[] points,Vector2[] uv,int[] indices)
        {var p=Activator.CreateInstance(Primitive);Primitive.GetField("Material").SetValue(p,material);Primitive.GetField("Positions").SetValue(p,points);Primitive.GetField("Normals").SetValue(p,new Vector3[points.Length]);Primitive.GetField("Uv0").SetValue(p,new Vector2[points.Length]);Primitive.GetField("Uv1").SetValue(p,uv);Primitive.GetField("Indices").SetValue(p,indices);return p;}
        static object Road(float offset=0,float height=0)
        {return MakePrimitive("road_asphalt",new[]{new Vector3(0,height,0),new Vector3(1,height,0),new Vector3(0,height,1),new Vector3(1,height,1)},new[]{new Vector2(offset,5),new Vector2(1+offset,5),new Vector2(offset,5),new Vector2(1+offset,5)},new[]{0,1,2,1,3,2});}
        static object Paint(bool outside=false,bool existing=false)
        {return MakePrimitive("marking_white",new[]{new Vector3(.1f,.006f,.1f),new Vector3(.9f,.006f,.1f),new Vector3(.1f,.006f,.9f),new Vector3(outside?1.2f:.9f,.006f,.9f)},new[]{new Vector2(.5f,.125f),new Vector2(existing?.8f:.5f,.25f),new Vector2(.5f,.375f),new Vector2(.5f,.5f)},new[]{0,1,2,1,3,2});}
        static object Transfer(object road,object paint,out object stats)
        {object field=Activator.CreateInstance(Field,new[]{road});var args=new[]{MakeNode(paint),null};var node=Field.GetMethod("Transfer").Invoke(field,args);stats=args[1];return ((IList)Node.GetField("Primitives").GetValue(node))[0];}
        static int Changed(object stats){return (int)stats.GetType().GetField("ChangedVertices").GetValue(stats);}

        [Test] public void SupportedWholeGlyphReusesLaneButPreservesExactAgeAndGeometry()
        {
            var original=Paint();var result=Transfer(MakeNode(Road()),original,out var stats);Assert.That(Changed(stats),Is.EqualTo(4));
            var uv=(Vector2[])Primitive.GetField("Uv1").GetValue(result);var old=(Vector2[])Primitive.GetField("Uv1").GetValue(original);
            Assert.That(uv[0].x,Is.EqualTo(.1f).Within(1e-6));Assert.That(uv[1].x,Is.EqualTo(.9f).Within(1e-6));
            for(int i=0;i<uv.Length;i++){Assert.That(uv[i].y,Is.EqualTo(old[i].y));Assert.That(old[i].x,Is.EqualTo(.5f));}
            foreach(string f in new[]{"Positions","Normals","Indices","Uv0","Colors"})Assert.That(Primitive.GetField(f).GetValue(result),Is.SameAs(Primitive.GetField(f).GetValue(original)));
        }
        [Test] public void ExistingVaryingPaintFieldIsNeverReplaced()
        {var p=Paint(existing:true);Assert.That(Transfer(MakeNode(Road()),p,out var stats),Is.SameAs(p));Assert.That(Changed(stats),Is.Zero);}
        [Test] public void UnknownPartRejectsEntireConnectedGlyphIncludingSupportedTriangle()
        {var p=Paint(outside:true);Assert.That(Transfer(MakeNode(Road()),p,out var stats),Is.SameAs(p));Assert.That(Changed(stats),Is.Zero);}
        [Test] public void SplitVerticesAtSamePositionAndAgeStillRejectWholeGlyph()
        {
            var p=MakePrimitive("marking_white",new[]{new Vector3(.1f,.006f,.1f),new Vector3(.9f,.006f,.1f),new Vector3(.1f,.006f,.9f),new Vector3(.9f,.006f,.1f),new Vector3(1.2f,.006f,.9f),new Vector3(.1f,.006f,.9f)},new[]{new Vector2(.5f,.2f),new Vector2(.5f,.2f),new Vector2(.5f,.2f),new Vector2(.5f,.2f),new Vector2(.5f,.2f),new Vector2(.5f,.2f)},new[]{0,1,2,3,4,5});
            Assert.That(Transfer(MakeNode(Road()),p,out var stats),Is.SameAs(p));Assert.That(Changed(stats),Is.Zero);
        }
        [Test] public void AmbiguousOverlappingRoadFieldsAreRejected()
        {var p=Paint();Assert.That(Transfer(MakeNode(Road(),Road(.2f)),p,out var stats),Is.SameAs(p));Assert.That(Changed(stats),Is.Zero);}
        [Test] public void OtherRoadHeightCannotSupplyPaintLane()
        {var p=Paint();Assert.That(Transfer(MakeNode(Road(height:.2f)),p,out var stats),Is.SameAs(p));Assert.That(Changed(stats),Is.Zero);}
        [Test] public void LaneWrapDiscontinuityRejectsComponentInsteadOfInterpolatingAcrossReset()
        {
            var left=Road();var right=Road(-1);
            // Adjacent half-road fields: at x=.5 the lane jumps from .5 to -.5.
            var lp=(Vector3[])Primitive.GetField("Positions").GetValue(left);var rp=(Vector3[])Primitive.GetField("Positions").GetValue(right);
            for(int i=0;i<lp.Length;i++){lp[i].x*=.5f;rp[i].x=.5f+rp[i].x*.5f;}
            var p=Paint();Assert.That(Transfer(MakeNode(left,right),p,out var stats),Is.SameAs(p));Assert.That(Changed(stats),Is.Zero);
        }
    }
}
