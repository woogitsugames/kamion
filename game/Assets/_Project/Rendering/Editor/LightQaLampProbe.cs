using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEngine;

namespace Game.Rendering.Editor
{
    /// <summary>ADR 0108 r2: editor-only evidence of the actual per-camera lamp selection.
    /// Capture after VisualQaRunner.RefreshLights and before drawing that camera, including inactive QA cameras.</summary>
    public sealed class LightQaLampProbe
    {
        [Serializable] sealed class Snapshot
        {
            public string camera, diagnostics;
            public Vector3 position, forward;
            public float sunElevation, skyHorizontalLux, exposure, lampsOn;
            public float presetExposureCompensation, skyDisplayGain, skyDisplayDesaturation;
            public float actualWetness, actualPuddleShare;
            public float actualWetFilmSmoothness, actualDimColourDesaturation;
            public float presetDimColourDesaturation;
            public float clearCloudSourceMinElevationDeg;
            public Vector4 cloudSourceLimits;
            public int pools, enabledPointLights;
            public Vector4[] headsAndWeights;
            public Vector4[] axes;   // ADR 0191: arm x, arm z, sodium, road optic
            public Vector4[] poolGroundPoints, poolGroundViewport;
            public float[] nominalRoadLuxNoOcclusion;
            public LampSurface[] lampSurfaces;
            public Vector4 exposedPoolColor;
            public bool projectedHeadlamps;
            public string headlampDiagnostics;
            public Vector4 headlampLeft, headlampRight, exposedHeadlampColor;
        }
        [Serializable] sealed class LampSurface
        {
            public string name, shader;
            public Vector4 emission;
            public float cull;
            public bool registered;
        }
        [Serializable] sealed class Document
        {
            public string scope = "Actual editor lamp state per QA camera; nominal model photometry, not a measured GPU/device result. Pool colour may remain stale at pools=0 and is then ignored by the shader.";
            public Snapshot[] cameras;
        }
        readonly Dictionary<string, Snapshot> m_Cameras = new Dictionary<string, Snapshot>();

        public void Capture(Camera camera)
        {
            var qa = camera.GetComponent<ControlCamera>();
            var environment = EnvironmentLighting.Instance;
            if (qa == null || environment == null || environment.Model == null) return;
            var model = environment.Model;
            int count = StreetLamps.PoolCount;
            var positions = new Vector4[count];
            Array.Copy(StreetLamps.PoolPositions, positions, count);
            var axes = new Vector4[count];
            Array.Copy(StreetLamps.PoolAxes, axes, count);
            var ground=new Vector4[count];var viewport=new Vector4[count];var nominalLux=new float[count];
            for(int i=0;i<count;i++)
            {
                Vector3 head=new Vector3(positions[i].x,positions[i].y,positions[i].z);
                if(Physics.Raycast(head-Vector3.up*.15f,Vector3.down,out var hit,80f,~(1<<8),QueryTriggerInteraction.Ignore) &&
                    hit.normal.y>.7f && head.y-hit.point.y>1f)
                {
                    ground[i]=new Vector4(hit.point.x,hit.point.y,hit.point.z,1);
                    Vector3 projected=camera.WorldToViewportPoint(hit.point);
                    viewport[i]=new Vector4(projected.x,projected.y,projected.z,positions[i].w);
                    // Nominal luminaire directly below its head: inverse square * incidence, without occlusion.
                    nominalLux[i]=StreetLamps.DownIntensityCd*Mathf.Clamp01(hit.normal.y)/Mathf.Max((head-hit.point).sqrMagnitude,1f)*positions[i].w;
                }
            }
            var lampSurfaces=((IEnumerable<Material>)typeof(StreetLamps).GetField("s_Glass",BindingFlags.NonPublic|BindingFlags.Static).GetValue(null))
                    .Where(m=>m!=null)
                    .Select(m=>new LampSurface{name=m.name,shader=m.shader!=null?m.shader.name:"missing",
                        registered=true,emission=m.HasProperty("_Emission")?m.GetVector("_Emission"):Vector4.zero,cull=m.HasProperty("_Cull")?m.GetFloat("_Cull"):-1})
                    .ToArray();
            m_Cameras[qa.id] = new Snapshot {
                camera = qa.id, diagnostics = StreetLamps.Diagnostics,
                position = camera.transform.position, forward = camera.transform.forward,
                sunElevation = model.TrueSunElevationDeg, skyHorizontalLux = model.HorizontalIlluminanceLux,
                exposure = model.Exposure, lampsOn = StreetLamps.On,
                presetExposureCompensation = environment.Active.exposureCompensation,
                skyDisplayGain = environment.Active.skyDisplayGain, skyDisplayDesaturation = environment.Active.skyDisplayDesaturation,
                actualDimColourDesaturation=Shader.GetGlobalFloat("_KamionDimColourDesaturation"),
                presetDimColourDesaturation=environment.Active.dimColourDesaturation,
                actualWetness = Shader.GetGlobalVector("_KamionWet").x,
                actualPuddleShare = Shader.GetGlobalVector("_KamionWet").y,
                actualWetFilmSmoothness = Shader.GetGlobalVector("_KamionWet").w > 0f ? Shader.GetGlobalVector("_KamionWet").w : 0.52f,
                clearCloudSourceMinElevationDeg = environment.Active.clearCloudSourceMinElevationDeg,
                cloudSourceLimits = Shader.GetGlobalVector("_KamionClearCloudSourceLimits"),
                pools = count, headsAndWeights = positions, axes = axes,
                poolGroundPoints=ground,poolGroundViewport=viewport,nominalRoadLuxNoOcclusion=nominalLux,lampSurfaces=lampSurfaces,
                projectedHeadlamps = KamionHeadlamps.Enabled, headlampDiagnostics = KamionHeadlamps.Diagnostics,
                headlampLeft = Shader.GetGlobalVector("_KamionHeadlampLeft"),
                headlampRight = Shader.GetGlobalVector("_KamionHeadlampRight"),
                exposedHeadlampColor = Shader.GetGlobalVector("_KamionHeadlampColor"),
                exposedPoolColor = Shader.GetGlobalVector("_KamionLampColor"),
                enabledPointLights = environment.GetComponentsInChildren<Light>()
                    .Count(l => l.enabled && l.type == LightType.Point && l.name.StartsWith("StreetLampLight "))
            };
        }

        public void Write(string folder, int expected, int expectedHeadlamps = 0, float? expectedWetness = null, float? expectedDimColour = null)
        {
            if (m_Cameras.Count != expected)
                throw new InvalidOperationException($"Incomplete lamp probes: {m_Cameras.Count}, expected {expected}");
            if (expectedHeadlamps > 0 && m_Cameras.Values.Any(s => s.projectedHeadlamps != (expectedHeadlamps == 2)))
                throw new InvalidOperationException("Projected headlamp state does not match the requested on/off proof");
            if (expectedWetness.HasValue && m_Cameras.Values.Any(s => Mathf.Abs(s.actualWetness-expectedWetness.Value) > 0.0001f))
                throw new InvalidOperationException("Actual per-camera wetness does not match the requested proof");
            if(expectedDimColour.HasValue && m_Cameras.Values.Any(s=>Mathf.Abs(s.actualDimColourDesaturation-expectedDimColour.Value)>.0001f || Mathf.Abs(s.presetDimColourDesaturation-expectedDimColour.Value)>.0001f))
                throw new InvalidOperationException("Actual per-camera dim colour/preset does not match requested proof");
            File.WriteAllText(Path.Combine(folder, "lamp-probes.json"), JsonUtility.ToJson(new Document {
                cameras = m_Cameras.OrderBy(p => p.Key, StringComparer.Ordinal).Select(p => p.Value).ToArray()
            }, true));
        }
    }
}

