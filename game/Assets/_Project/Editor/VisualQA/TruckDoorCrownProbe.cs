using System;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    // Numeric readback uses the actual production helper and actual per-renderer layer buffer, not a CPU copy.
    public static class TruckDoorCrownProbe
    {
        public static float Gradient(string expression,Matrix4x4 pose)
        {
            var shader=TruckPaintProbe.BuildProbeShader(expression,"v.positionOS");
            var mesh=new Mesh { vertices=new[]{new Vector3(-1,-1,0),new Vector3(1,-1,0),new Vector3(1,1,0),new Vector3(-1,1,0)},
                normals=new[]{Vector3.back,Vector3.back,Vector3.back,Vector3.back},
                triangles=new[]{0,1,2,0,2,3} };
            try{return Pixel(shader,mesh,0,1025u,pose);}finally{UnityEngine.Object.DestroyImmediate(mesh);}
        }
        public static float ActualDoorTag(MeshRenderer source,bool lightLayers)
        {
            var filter=source.GetComponent<MeshFilter>();
            int submesh=Array.FindIndex(source.sharedMaterials,m=>m!=null&&m.name=="MI_Ext_Paint");
            if(filter==null||filter.sharedMesh==null||submesh<0)throw new InvalidOperationException("Actual door paint submesh missing");
            var shader=TruckPaintProbe.BuildProbeShader("float3((GetMeshRenderingLayer() & (1u << 10)) != 0u ? 1.0 : 0.0,0,0)",
                "float4((v.positionOS.z+1.0902)/0.65,(v.positionOS.y-0.01)/0.325,0,1)",lightLayers);
            // Actual canonical source mesh and renderer data copied into a plain renderer: no vehicle lifecycle/global side effects.
            return Pixel(shader,filter.sharedMesh,submesh,source.renderingLayerMask,Matrix4x4.identity);
        }
        static float Pixel(Shader shader,Mesh mesh,int submesh,uint layer,Matrix4x4 pose)
        {
            GameObject go=null;Material material=null;RenderTexture rt=null;Texture2D pixels=null;CommandBuffer cb=null;
            var previous=RenderTexture.active;
            try
            {
                go=new GameObject("Door crown numeric GPU renderer");go.hideFlags=HideFlags.HideAndDontSave;
                go.transform.SetPositionAndRotation(pose.GetColumn(3),pose.rotation);go.transform.localScale=pose.lossyScale;
                go.AddComponent<MeshFilter>().sharedMesh=mesh;var renderer=go.AddComponent<MeshRenderer>();renderer.renderingLayerMask=layer;
                material=new Material(shader);renderer.sharedMaterial=material;
                rt=RenderTexture.GetTemporary(16,16,0,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear);
                cb=new CommandBuffer { name="Actual Truck door shader/layer numeric probe" };cb.SetRenderTarget(rt);
                cb.ClearRenderTarget(true,true,new Color(-9,-9,-9,-9));cb.SetViewProjectionMatrices(Matrix4x4.identity,Matrix4x4.identity);
                cb.DrawRenderer(renderer,material,submesh,0);Graphics.ExecuteCommandBuffer(cb);RenderTexture.active=rt;
                pixels=new Texture2D(1,1,TextureFormat.RGBAFloat,false,true);pixels.ReadPixels(new Rect(8,8,1,1),0,0);pixels.Apply();
                return pixels.GetPixel(0,0).r;
            }
            finally
            {
                RenderTexture.active=previous;cb?.Release();if(rt!=null)RenderTexture.ReleaseTemporary(rt);
                if(pixels!=null)UnityEngine.Object.DestroyImmediate(pixels);if(go!=null)UnityEngine.Object.DestroyImmediate(go);
                if(material!=null)UnityEngine.Object.DestroyImmediate(material);
            }
        }
    }
}
