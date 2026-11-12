using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    // Candidate tests, outside Assets until the baseline and controlled ablations are reviewed.
    public class LightCloudHorizonTests
    {
        static Vector3 Direction(float elevation, float azimuth)
        {
            float e = elevation*Mathf.Deg2Rad, a = azimuth*Mathf.Deg2Rad;
            return new Vector3(Mathf.Sin(a)*Mathf.Cos(e), Mathf.Sin(e), Mathf.Cos(a)*Mathf.Cos(e));
        }

        [TestCase(9f,60f), TestCase(25f,200f), TestCase(42f,200f), TestCase(60f,320f)]
        public void HorizonLock_PreservesEveryRayElevation_AndMatchesSourceAzimuth(float elevation,float azimuth)
        {
            Vector3 sun = Direction(elevation,azimuth), source = Direction(47.856f,180f);
            var rotation = PhotographicClouds.SourceRotation(sun,source,true);
            for(int a=0;a<360;a+=15)
            foreach(float e in new[]{-5f,0f,0.5f,10f,45f,85f})
            {
                var ray = Direction(e,a);
                Assert.That((rotation*ray).y,Is.EqualTo(ray.y).Within(1e-5f),
                    $"Source cut must stay at the world horizon: ray elevation={e}, azimuth={a}");
            }
            Vector3 rotatedSun=rotation*sun;
            rotatedSun.y=0f;source.y=0f;
            Assert.That(Vector3.Angle(rotatedSun,source),Is.LessThan(0.03f));
        }

        [TestCase(9f,60f), TestCase(25f,200f), TestCase(42f,200f), TestCase(60f,320f)]
        public void DefaultRotation_StillMatchesFullSourceSun(float elevation,float azimuth)
        {
            Vector3 sun=Direction(elevation,azimuth), source=Direction(47.856f,180f);
            Assert.That(Vector3.Angle(PhotographicClouds.SourceRotation(sun,source)*sun,source),Is.LessThan(0.03f));
            Assert.That(Quaternion.Angle(PhotographicClouds.SourceRotation(sun,source),
                PhotographicClouds.SourceRotation(sun,source,false)),Is.LessThan(0.03f));
        }

        [Test]
        public void NewPreset_LeavesHorizonLockDisabled()
        {
            var preset=ScriptableObject.CreateInstance<LightingPreset>();
            try {Assert.That(preset.clearCloudHorizonLocked,Is.False);}
            finally {Object.DestroyImmediate(preset);}
        }

        [Test]
        public void Parse_ResetsHorizonOverride_WhenNextJobHasNoArgument()
        {
            try
            {
                RenderOverrides.Parse(k=>k=="rq_cloudhorizon"?"1":null);
                Assert.That(WorldAtmosphere.ClearCloudHorizonOverride,Is.True);
                RenderOverrides.Parse(_=>null);
                Assert.That(WorldAtmosphere.ClearCloudHorizonOverride,Is.Null);
                RenderOverrides.Parse(k=>k=="rq_cloudhorizon"?"0":null);
                Assert.That(WorldAtmosphere.ClearCloudHorizonOverride,Is.False);
            }
            finally {RenderOverrides.Parse(_=>null);}
        }
    }
}
