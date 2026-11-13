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
        // ---------------------------------------------------------------- ADR 0178: lamp hue (signal colour) at dusk
        static Vector2 Chromaticity(Color linear)
        {
            // Linear sRGB (D65) -> CIE XYZ (IEC 61966-2-1).
            float x=0.4124f*linear.r+0.3576f*linear.g+0.1805f*linear.b;
            float y=0.2126f*linear.r+0.7152f*linear.g+0.0722f*linear.b;
            float z=0.0193f*linear.r+0.1192f*linear.g+0.9505f*linear.b;
            float sum=x+y+z; return new Vector2(x/sum,y/sum);
        }
        [Test] public void SignalColoursLieInsideEceChromaticityBands()
        {
            Vector2 red=Chromaticity(TruckLights.Red), amber=Chromaticity(TruckLights.Amber);
            Assert.That(red.y,Is.LessThanOrEqualTo(0.335f),"R48 red: limit towards yellow y <= 0.335");
            Assert.That(amber.y,Is.InRange(0.398f,0.429f),"amber: 0.398 <= y <= 0.429 (towards red / towards green)");
        }
        static string F(float v)=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture);
        static string Raw(Color c,float scale)=>"float3("+F(c.r*scale)+","+F(c.g*scale)+","+F(c.b*scale)+")";
        // Exposed max-channel radiance from 0.1 (day) to 200 (brake / indicator at night).
        [TestCase("red",0.1f)] [TestCase("red",3f)] [TestCase("red",40f)] [TestCase("red",200f)]
        [TestCase("amber",0.1f)] [TestCase("amber",3f)] [TestCase("amber",40f)] [TestCase("amber",200f)]
        public void LampHueLimitPreservesChannelRatiosAndBoundsMaxChannel(string colour,float scale)
        {
            if(SystemInfo.graphicsDeviceType==GraphicsDeviceType.Null) Assert.Ignore("Actual GPU readback requires graphics device");
            Color c=colour=="red"?TruckLights.Red:TruckLights.Amber;
            string limited="TruckLampHueLimit("+Raw(c,scale)+", _LampHueKnee, _LampHueCeiling)";
            float r=TruckPaintProbe.Read(TruckPaintProbe.BuildProbeShader(limited+".rrr"),1f,false,true,out _);
            float g=TruckPaintProbe.Read(TruckPaintProbe.BuildProbeShader(limited+".ggg"),1f,false,true,out _);
            float b=TruckPaintProbe.Read(TruckPaintProbe.BuildProbeShader(limited+".bbb"),1f,false,true,out _);
            foreach(float v in new[]{r,g,b}) Assert.That(float.IsNaN(v)||float.IsInfinity(v),Is.False);
            // Shader defaults: knee 0.4, ceiling 0.8. Max channel stays under the High D23 clip region and Low's 1.0.
            Assert.That(Mathf.Max(r,Mathf.Max(g,b)),Is.LessThanOrEqualTo(0.8f+1e-4f));
            if(scale<=0.4f) Assert.That(r,Is.EqualTo(c.r*scale).Within(1e-4f),"identity below the knee (day look unchanged)");
            Assert.That(g,Is.EqualTo(r*c.g/c.r).Within(1e-4f),"green/red ratio (hue) preserved");
            Assert.That(b,Is.EqualTo(r*c.b/c.r).Within(1e-4f),"blue/red ratio (hue) preserved");
            Assert.That(r,Is.GreaterThan(0.75f*Mathf.Min(scale,0.8f)),"lamp stays bright (no over-darkening)");
        }
        [Test] public void LampHueLimitDisabledPreservesRadiance()
        {
            if(SystemInfo.graphicsDeviceType==GraphicsDeviceType.Null) Assert.Ignore("Actual GPU readback requires graphics device");
            var shader=TruckPaintProbe.BuildProbeShader("TruckLampHueLimit(float3(20,5,0),0.4,0)");
            Assert.That(TruckPaintProbe.Read(shader,1f,false,true,out _),Is.EqualTo(20f).Within(0.01f));
        }
    }
}
