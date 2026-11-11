// Artifact-only observer. Copy to ignored Assets/_Generated/Editor only after ROOT release.
// No render-state writes. Activated only by an explicit process environment variable.
using System;
using System.IO;
using System.Linq;
using Game.Rendering;
using Game.Vehicle.Runtime;
using Game.World;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

[InitializeOnLoad]
public static class R4PosePacket
{
    [Serializable] public class Node
    {
        public string path;
        public Vector3 worldPosition, localPosition, localScale;
        public Quaternion worldRotation, localRotation;
        public Matrix4x4 localToWorld;
    }
    [Serializable] public class Packet
    {
        public string cameraId, phase, scene, quality, pipeline, unity, sourceHead, sourceProofSha;
        public int frame, targetWidth, targetHeight, pixelWidth, pixelHeight, msaa;
        public float time, fov, aspect, near, far, pipelineScale, fsrSharpness;
        public bool fsrOverride, post, glassFast;
        public string upscalingFilter;
        public Matrix4x4 view, projection;
        public Rect pixelRect;
        public Vector4 giRect;
        public Node[] cameraParents, vehicleHierarchy, regionRoots;
        public string regionState;
        public Paint[] paintMaterials;
        public string note="Target and live pipeline fields are observed; actual internal URP descriptor/pass execution is NOT established by this packet.";
    }
    [Serializable] public class Paint
    {
        public string name, path, shader, baseMap, normalMap, maskMap;
        public Color tint;
        public float albedoScale;
        public Vector4 flake;
        public bool carPaint, meshUv0, meshUv1;
    }

    static R4PosePacket()
    {
        if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable("KAMION_G_POSE_OUTPUT"))) return;
        RenderPipelineManager.beginCameraRendering += (context, camera) => Save(camera,"begin");
        RenderPipelineManager.endCameraRendering += (context, camera) => Save(camera,"end");
    }

    static string PathOf(Transform t) => t.parent == null ? t.name : PathOf(t.parent)+"/"+t.name;
    static Node Read(Transform t) => new Node {path=PathOf(t),worldPosition=t.position,localPosition=t.localPosition,
        localScale=t.localScale,worldRotation=t.rotation,localRotation=t.localRotation,localToWorld=t.localToWorldMatrix};

    static void Save(Camera camera,string phase)
    {
        var qa=camera.GetComponent<ControlCamera>();
        if (qa==null) return; // Excludes mirrors, environment captures and UI.
        var root=Environment.GetEnvironmentVariable("KAMION_G_POSE_OUTPUT");
        if (string.IsNullOrEmpty(root)) return;
        var urp=GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
        var parents=new System.Collections.Generic.List<Node>();
        for(var t=camera.transform;t!=null;t=t.parent) parents.Add(Read(t));
        var roots=UnityEngine.Object.FindObjectsByType<TruckVisualRig>(FindObjectsInactive.Include,FindObjectsSortMode.None)
            .Select(t=>t.transform.root)
            .Concat(UnityEngine.Object.FindObjectsByType<TrailerBody>(FindObjectsInactive.Include,FindObjectsSortMode.None).Select(t=>t.transform.root))
            .Distinct().ToArray();
        var regions=UnityEngine.Object.FindObjectsByType<WorldRegionRoot>(FindObjectsInactive.Include,FindObjectsSortMode.None);
        camera.TryGetComponent<UniversalAdditionalCameraData>(out var data);
        var p=new Packet {cameraId=qa.id,phase=phase,scene=camera.gameObject.scene.path,
            quality=QualitySettings.names[QualitySettings.GetQualityLevel()],pipeline=urp==null?"null":urp.name,
            unity=Application.unityVersion,sourceHead=Environment.GetEnvironmentVariable("KAMION_G_SOURCE_HEAD"),
            sourceProofSha=Environment.GetEnvironmentVariable("KAMION_G_SOURCE_PROOF_SHA"),
            frame=Time.frameCount,time=Time.time,targetWidth=camera.targetTexture==null?0:camera.targetTexture.width,
            targetHeight=camera.targetTexture==null?0:camera.targetTexture.height,pixelWidth=camera.pixelWidth,pixelHeight=camera.pixelHeight,
            msaa=camera.targetTexture==null?QualitySettings.antiAliasing:camera.targetTexture.antiAliasing,
            fov=camera.fieldOfView,aspect=camera.aspect,near=camera.nearClipPlane,far=camera.farClipPlane,
            pipelineScale=urp==null?0:urp.renderScale,fsrSharpness=urp==null?0:urp.fsrSharpness,
            fsrOverride=urp!=null&&urp.fsrOverrideSharpness,upscalingFilter=urp==null?"null":urp.upscalingFilter.ToString(),
            post=data!=null&&data.renderPostProcessing,glassFast=Shader.IsKeywordEnabled("_KAMION_GLASS_FAST"),
            view=camera.worldToCameraMatrix,projection=camera.projectionMatrix,pixelRect=camera.pixelRect,
            giRect=Shader.GetGlobalVector("_KamionGIRect"),cameraParents=parents.ToArray(),
            vehicleHierarchy=roots.SelectMany(t=>t.GetComponentsInChildren<Transform>(true)).Distinct().OrderBy(PathOf).Select(Read).ToArray(),
            regionRoots=regions.OrderBy(t=>PathOf(t.transform)).Select(t=>Read(t.transform)).ToArray(),
            regionState=string.Join("\n",regions.Select(t=>JsonUtility.ToJson(t))),
            paintMaterials=Resources.FindObjectsOfTypeAll<Material>().Where(m=>m.name.Contains("car_paint_")&&m.HasProperty("_CarFlake"))
                .OrderBy(m=>AssetDatabase.GetAssetPath(m)).Select(m=>new Paint {name=m.name,path=AssetDatabase.GetAssetPath(m),shader=m.shader.name,
                    tint=m.GetColor("_Tint"),albedoScale=m.GetFloat("_AlbedoScale"),flake=m.GetVector("_CarFlake"),
                    carPaint=m.IsKeywordEnabled("_CARPAINT"),meshUv0=m.IsKeywordEnabled("_UV_MESH0"),meshUv1=m.IsKeywordEnabled("_UV_MESH1"),
                    baseMap=AssetDatabase.GetAssetPath(m.GetTexture("_BaseMap")),normalMap=AssetDatabase.GetAssetPath(m.GetTexture("_NormalMap")),
                    maskMap=AssetDatabase.GetAssetPath(m.GetTexture("_MaskMap"))}).ToArray()};
        Directory.CreateDirectory(root);
        var safe=string.Concat(qa.id.Select(c=>Path.GetInvalidFileNameChars().Contains(c)?'_':c));
        File.WriteAllText(Path.Combine(root,safe+"-"+phase+".json"),JsonUtility.ToJson(p,true));
    }
}
