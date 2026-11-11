using Game.Editor.VisualQA;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Tests.EditMode
{
    public sealed class TruckLampEncodingTests
    {
        GameObject sunObject, lampObject;
        Light oldSun;
        Texture oldTexture;
        float oldScale, oldExposure;
        TruckLights lights;
        [SetUp] public void Create()
        {
            oldSun=RenderSettings.sun; oldTexture=Shader.GetGlobalTexture("_TruckLightState");
            oldScale=Shader.GetGlobalFloat("_TruckLightNitsScale"); oldExposure=Shader.GetGlobalFloat("_KamionExposure");
            sunObject=new GameObject("Lamp test sun");
            var sun=sunObject.AddComponent<Light>(); sun.type=LightType.Directional; sun.transform.rotation=Quaternion.Euler(40f,0,0);
            RenderSettings.sun=sun;
            lampObject=new GameObject("Lamp test state"); lights=lampObject.AddComponent<TruckLights>();
        }
        [TearDown] public void Restore()
        {
            Object.DestroyImmediate(lampObject); Object.DestroyImmediate(sunObject); RenderSettings.sun=oldSun;
            Shader.SetGlobalTexture("_TruckLightState",oldTexture); Shader.SetGlobalFloat("_TruckLightNitsScale",oldScale);
            Shader.SetGlobalFloat("_KamionExposure",oldExposure);
        }
        [TestCase(40f,false,false)] [TestCase(40f,true,false)]
        [TestCase(-5f,false,true)] [TestCase(-5f,true,true)]
        public void DayNightAndHighBeamStateSurviveHalfStorage(float elevation,bool high,bool low)
        {
            sunObject.transform.rotation=Quaternion.Euler(elevation,0,0); lights.highBeam=high; lights.Refresh();
            Assert.That(lights.LowBeamOn,Is.EqualTo(low));
            Assert.That(lights.StateTexture.format,Is.EqualTo(TextureFormat.RGBAHalf));
            Assert.That(lights.StateTexture.width,Is.EqualTo(16)); Assert.That(lights.StateTexture.height,Is.EqualTo(1));
            foreach(var c in lights.StateTexture.GetPixels())
                foreach(float value in new[]{c.r,c.g,c.b,c.a}) Assert.That(float.IsNaN(value)||float.IsInfinity(value),Is.False);
            CheckNits(1,low?56000f:160000f); CheckNits(2,low?50000f:0f); CheckNits(3,high?80000f:0f);
        }
        void CheckNits(int group,float expected)
        {
            float decoded=lights.StateTexture.GetPixel(group,0).r*TruckLights.NitsPerEncodedUnit;
            Assert.That(decoded,Is.EqualTo(expected).Within(Mathf.Max(0.01f,expected*0.001f)));
        }
        [TestCase(1,16f)] [TestCase(3,8f)]
        public void ActualProductionShaderDecodesFiniteTextureBeforeExposure(int group,float expected)
        {
            if(SystemInfo.graphicsDeviceType==GraphicsDeviceType.Null) Assert.Ignore("Actual GPU readback requires graphics device");
            lights.highBeam=true; lights.Refresh(); Shader.SetGlobalFloat("_KamionExposure",0.0001f);
            string u=((group+0.5f)/16f).ToString("R",System.Globalization.CultureInfo.InvariantCulture);
            var shader=TruckPaintProbe.BuildProbeShader("TruckLampRadiance(SAMPLE_TEXTURE2D_LOD(_TruckLightState, sampler_point_clamp, float2("+u+",0.5),0).rgb)");
            float value=TruckPaintProbe.Read(shader,1f,false,true,out _);
            Assert.That(float.IsNaN(value)||float.IsInfinity(value),Is.False);
            Assert.That(value,Is.EqualTo(expected).Within(0.01f));
        }
        [TestCase(0f)] [TestCase(0.00001f)] [TestCase(0.0001f)] [TestCase(1f)]
        public void DrlHighlightRemainsFiniteAndBoundedBeforeHalfConversion(float exposure)
        {
            if(SystemInfo.graphicsDeviceType==GraphicsDeviceType.Null) Assert.Ignore("Actual GPU readback requires graphics device");
            lights.Refresh(); Shader.SetGlobalFloat("_KamionExposure",exposure);
            const string raw="TruckLampRadiance(SAMPLE_TEXTURE2D_LOD(_TruckLightState, sampler_point_clamp, float2(1.5/16.0,0.5),0).rgb)";
            var shader=TruckPaintProbe.BuildProbeShader("dot(TruckDrlHighlight("+raw+", _DrlHighlightShoulder),float3(0.2126,0.7152,0.0722)).xxx");
            float value=TruckPaintProbe.Read(shader,1f,false,true,out _);
            Assert.That(float.IsNaN(value)||float.IsInfinity(value),Is.False);
            Assert.That(value,Is.InRange(0f,0.801f));
            if(exposure>0f) Assert.That(value,Is.GreaterThan(0f));
            else Assert.That(value,Is.EqualTo(0f));
        }
        [Test] public void DisabledDrlHighlightPreservesUncompressedRadiance()
        {
            if(SystemInfo.graphicsDeviceType==GraphicsDeviceType.Null) Assert.Ignore("Actual GPU readback requires graphics device");
            var shader=TruckPaintProbe.BuildProbeShader("TruckDrlHighlight(float3(16,15.52,14.72),0)");
            Assert.That(TruckPaintProbe.Read(shader,1f,false,true,out _),Is.EqualTo(16f).Within(0.01f));
        }
    }
}
