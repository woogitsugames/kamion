using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.Rendering;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.World.Import
{
    /// <summary>Editor diagnostic only: real depth-tested visibility against a solo mask. No assets/scenes are saved.</summary>
    public static class VehicleLodVisibilityRenderSearch
    {
        [Serializable] public class Entry
        {
            public string id, kind = "photo_match", seat = "file", note;
            public float[] pos, look_at;
            public float fov_deg = 60, visibleFraction;
            public int soloPixels, visiblePixels, nativeIndex;
        }
        [Serializable] public class FileData { public Entry[] cameras; }

        public static void RunBatch()
        {
            int quality = Array.FindIndex(QualitySettings.names, n => n == "High");
            if (quality >= 0) QualitySettings.SetQualityLevel(quality, true);
            ShaderUtil.allowAsyncCompilation = false;
            EditorSceneManager.OpenScene("Assets/_Generated/World/bialystok-industrial-c/WorldC.unity");
            var env = UnityEngine.Object.FindAnyObjectByType<EnvironmentLighting>();
            if (env != null) { env.SetPreset("overcast"); env.Apply(); }
            var applier = UnityEngine.Object.FindAnyObjectByType<QualityProfileApplier>();
            if (applier != null) applier.ApplyNow();
            var world = UnityEngine.Object.FindAnyObjectByType<WorldInstances>();
            var set = world.set;
            Vector3 offset = world.transform.position;
            var cameraGo = new GameObject("VisibilitySearchCamera");
            var modelGo = new GameObject("VisibilitySearchMask") { layer = 31 };
            var camera = cameraGo.AddComponent<Camera>(); camera.enabled = false;
            camera.fieldOfView = 60; camera.aspect = 640f / 296; camera.nearClipPlane = .03f; camera.farClipPlane = 2500;
            camera.GetUniversalAdditionalCameraData().renderPostProcessing = false;
            var rt = new RenderTexture(640, 296, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            camera.targetTexture = rt;
            var pixels = new Texture2D(640, 296, TextureFormat.RGBA32, false);
            var filter = modelGo.AddComponent<MeshFilter>();
            var renderer = modelGo.AddComponent<MeshRenderer>(); renderer.shadowCastingMode = ShadowCastingMode.Off;
            var magenta = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
            magenta.SetColor("_BaseColor", Color.magenta); magenta.renderQueue = 2450;
            var invisible = new Material(magenta);
            invisible.SetColor("_BaseColor", Color.clear); invisible.SetFloat("_Surface", 1); invisible.SetFloat("_ZWrite", 0);
            invisible.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha); invisible.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
            invisible.EnableKeyword("_SURFACE_TYPE_TRANSPARENT"); invisible.renderQueue = 3000;
            bool oldTrees = RenderOverrides.AbTreesOff, oldProps = RenderOverrides.AbPropsOff;
            var results = new List<Entry>();
            try
            {
                foreach (string family in new[] { "car_hatch_white", "car_suv_black", "tractor_blue", "trailer_curtain_0", "trailer_reefer_0" })
                {
                    int proto = Array.FindIndex(set.prototypes, p => p.name == family);
                    var p = set.prototypes[proto]; bool reefer = family == "trailer_reefer_0";
                    filter.sharedMesh = p.lods[0];
                    var materials = Enumerable.Repeat(reefer ? invisible : magenta, p.lods[0].subMeshCount).ToArray();
                    if (reefer)
                    {
                        int sub = Enumerable.Range(0, materials.Length).First(s => set.materials[p.materialStart[0]+s].name == "M_reefer_grille");
                        materials[sub] = magenta;
                    }
                    renderer.sharedMaterials = materials;
                    var indices = set.runs.Where(r => r.prototype == proto).SelectMany(r => Enumerable.Range(r.start, r.count))
                        .Where(i => Mathf.Abs(set.LocalPosition(i).x) < 900 && Mathf.Abs(set.LocalPosition(i).z) < 900)
                        .OrderBy(i => (new Vector2(set.LocalPosition(i).x-720, set.LocalPosition(i).z+411)).sqrMagnitude).ToArray();
                    foreach (string tier in new[] { "Low", "High" })
                    {
                        bool car = family.StartsWith("car_");
                        float[] boundaries = car ? (tier == "Low" ? new[] {16f,42.5f} : new[] {37.5f,127.5f}) : (tier == "Low" ? new[] {20f,50f} : new[] {60f,150f});
                        foreach (float boundary in boundaries)
                        {
                            Entry best = null;
                            foreach (int index in indices)
                            {
                                var matrix = set.LocalMatrix(index); var origin = set.LocalPosition(index);
                                Vector3 look = matrix.MultiplyPoint3x4(reefer ? new Vector3(0,3.32f,14.025f) : p.lods[0].bounds.center);
                                modelGo.transform.rotation = matrix.rotation; modelGo.transform.localScale = matrix.lossyScale;
                                for (int a=0; a<32; a++)
                                {
                                    float angle = a * Mathf.PI / 16 + .64f;
                                    if (reefer && Mathf.Sin(angle)<.8f) continue;
                                    Vector3 direction = matrix.MultiplyVector(new Vector3(Mathf.Cos(angle),0,Mathf.Sin(angle))).normalized;
                                    // Try driver height first, then a documented elevated diagnostic view.
                                    foreach (float height in new[] {2.5f,6f,12f})
                                    {
                                        if (height >= boundary-.1f) continue;
                                        Vector3 pos = origin + direction * Mathf.Sqrt(boundary*boundary-height*height) + Vector3.up*height;
                                        if (Mathf.Abs(pos.x)>950 || Mathf.Abs(pos.z)>950) continue;
                                        camera.transform.SetPositionAndRotation(pos+offset, Quaternion.LookRotation(look-pos));
                                        // 1 cm camera-facing mask offset avoids self z-fighting; never used by final QA renders.
                                        modelGo.transform.position = origin + offset + (pos-look).normalized*.01f;
                                        RenderOverrides.AbTreesOff = true; RenderOverrides.AbPropsOff = true; camera.cullingMask = 1<<31;
                                        int solo = Count(camera,pixels,rt);
                                        if (solo < 5) continue;
                                        RenderOverrides.AbTreesOff = false; RenderOverrides.AbPropsOff = false; camera.cullingMask = ~(1<<5);
                                        int visible = Count(camera,pixels,rt);
                                        float fraction = Mathf.Min(1, (float)visible/solo);
                                        if (best==null || fraction>best.visibleFraction)
                                            best = new Entry { id=$"clear_{family}_{tier}_{boundary:000.0}".Replace('.', 'p').Replace(',', 'p'), pos=new[]{pos.x,pos.z,pos.y},look_at=new[]{look.x,look.z,look.y},nativeIndex=index,visibleFraction=fraction,soloPixels=solo,visiblePixels=visible,
                                                note=$"ADR0153 working QA pose. Real depth-tested visibility search: {visible}/{solo} mask pixels at640x296; camera height relative to instance {height}m. Mask-only1cm offset is NOT used by final QA renders." };
                                        if (fraction >= .97f) break;
                                    }
                                    if (best!=null && best.visibleFraction>=.97f) break;
                                }
                                if (best!=null && best.visibleFraction>=.97f) break;
                            }
                            if (best==null || best.visibleFraction<.9f) throw new InvalidOperationException("No visible target: "+family+" "+tier+" "+boundary);
                            var anchor = set.LocalPosition(best.nativeIndex); var center = new Vector3(best.pos[0],best.pos[2],best.pos[1]);
                            Vector3 axis = (center-anchor).normalized;
                            foreach (float distance in new[] {boundary-.1f,boundary+.1f})
                            {
                                Vector3 pos=anchor+axis*distance;
                                results.Add(new Entry { id=$"clear_{family}_{tier}_{distance:000.0}".Replace('.', 'p').Replace(',', 'p'),pos=new[]{pos.x,pos.z,pos.y},look_at=best.look_at,nativeIndex=best.nativeIndex,visibleFraction=best.visibleFraction,soloPixels=best.soloPixels,visiblePixels=best.visiblePixels,note=best.note });
                            }
                            Debug.Log($"LOD_VISIBLE {family} {tier} {boundary}: {best.visibleFraction:F3}, native={best.nativeIndex}");
                        }
                    }
                }
                System.IO.File.WriteAllText(Path.Combine(EditorTools.RepoRoot,"artifacts/gpt-s16-r1/clear-cameras.json"),JsonUtility.ToJson(new FileData {cameras=results.ToArray()},true));
                Debug.Log("LOD_VISIBLE_SEARCH: OK cameras="+results.Count);
            }
            finally
            {
                RenderOverrides.AbTreesOff=oldTrees;RenderOverrides.AbPropsOff=oldProps;
                camera.targetTexture=null;rt.Release();
                foreach (var o in new UnityEngine.Object[]{cameraGo,modelGo,rt,pixels,magenta,invisible}) UnityEngine.Object.DestroyImmediate(o);
            }
        }

        static int Count(Camera camera, Texture2D tex, RenderTexture rt)
        {
            camera.Render(); var previous=RenderTexture.active;RenderTexture.active=rt;
            tex.ReadPixels(new Rect(0,0,640,296),0,0);tex.Apply(false);RenderTexture.active=previous;
            var data=tex.GetRawTextureData<Color32>();int count=0;
            for(int i=0;i<data.Length;i++) if(data[i].r>100&&data[i].b>100&&data[i].g<data[i].r*.6f&&data[i].g<data[i].b*.6f) count++;
            return count;
        }
    }
}
