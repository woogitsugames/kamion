using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
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
            public float clearCloudSourceMinElevationDeg;
            public Vector4 cloudSourceLimits;
            public int pools, enabledPointLights;
            public Vector4[] headsAndWeights;
            public Vector4 exposedPoolColor;
            public bool projectedHeadlamps;
            public string headlampDiagnostics;
            public Vector4 headlampLeft, headlampRight, exposedHeadlampColor;
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
            m_Cameras[qa.id] = new Snapshot {
                camera = qa.id, diagnostics = StreetLamps.Diagnostics,
                position = camera.transform.position, forward = camera.transform.forward,
                sunElevation = model.TrueSunElevationDeg, skyHorizontalLux = model.HorizontalIlluminanceLux,
                exposure = model.Exposure, lampsOn = StreetLamps.On,
                presetExposureCompensation = environment.Active.exposureCompensation,
                skyDisplayGain = environment.Active.skyDisplayGain, skyDisplayDesaturation = environment.Active.skyDisplayDesaturation,
                actualWetness = Shader.GetGlobalVector("_KamionWet").x,
                actualPuddleShare = Shader.GetGlobalVector("_KamionWet").y,
                clearCloudSourceMinElevationDeg = environment.Active.clearCloudSourceMinElevationDeg,
                cloudSourceLimits = Shader.GetGlobalVector("_KamionClearCloudSourceLimits"),
                pools = count, headsAndWeights = positions,
                projectedHeadlamps = KamionHeadlamps.Enabled, headlampDiagnostics = KamionHeadlamps.Diagnostics,
                headlampLeft = Shader.GetGlobalVector("_KamionHeadlampLeft"),
                headlampRight = Shader.GetGlobalVector("_KamionHeadlampRight"),
                exposedHeadlampColor = Shader.GetGlobalVector("_KamionHeadlampColor"),
                exposedPoolColor = Shader.GetGlobalVector("_KamionLampColor"),
                enabledPointLights = environment.GetComponentsInChildren<Light>()
                    .Count(l => l.enabled && l.type == LightType.Point && l.name.StartsWith("StreetLampLight "))
            };
        }

        public void Write(string folder, int expected, int expectedHeadlamps = 0, float? expectedWetness = null)
        {
            if (m_Cameras.Count != expected)
                throw new InvalidOperationException($"Incomplete lamp probes: {m_Cameras.Count}, expected {expected}");
            if (expectedHeadlamps > 0 && m_Cameras.Values.Any(s => s.projectedHeadlamps != (expectedHeadlamps == 2)))
                throw new InvalidOperationException("Projected headlamp state does not match the requested on/off proof");
            if (expectedWetness.HasValue && m_Cameras.Values.Any(s => Mathf.Abs(s.actualWetness-expectedWetness.Value) > 0.0001f))
                throw new InvalidOperationException("Actual per-camera wetness does not match the requested proof");
            File.WriteAllText(Path.Combine(folder, "lamp-probes.json"), JsonUtility.ToJson(new Document {
                cameras = m_Cameras.OrderBy(p => p.Key, StringComparer.Ordinal).Select(p => p.Value).ToArray()
            }, true));
        }
    }
}
