using Game.Rendering;
using NUnit.Framework;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0056 (review r7 D30/D31): every tier has the vehicle reflection capture, the phone tiers keep it cheap (small cube,
    /// sparse face schedule, no refresh while parked), and the shipped asset matches the code defaults.
    /// </summary>
    public class VehicleReflectionCaptureTierTests
    {
        static void CheckTier(QualityProfile.Tier t)
        {
            Assert.That(t.envCaptureSize, Is.GreaterThan(0), t.name + ": capture off (glass / coat mirror the analytic sky only)");
            Assert.That(t.envCaptureSize & (t.envCaptureSize - 1), Is.EqualTo(0), t.name + ": cube size not a power of two");
            Assert.That(t.envCaptureSize, Is.LessThanOrEqualTo(256), t.name);
            Assert.That(t.envCaptureInterval, Is.GreaterThanOrEqualTo(1), t.name);
            Assert.That(t.envCaptureFarClip, Is.GreaterThan(10f), t.name);
            if (t.name == "Low" || t.name == "Medium")
            {
                // A16 budget (ADR 0056): <= 64 px faces, at most one face every 6 frames, idle when parked.
                Assert.That(t.envCaptureSize, Is.LessThanOrEqualTo(64), t.name);
                Assert.That(t.envCaptureInterval, Is.GreaterThanOrEqualTo(6), t.name);
                Assert.That(t.envCaptureMinMove, Is.GreaterThan(0f), t.name + ": no idle skip");
                Assert.That(t.envCaptureMaxAge, Is.GreaterThan(0f), t.name);
                Assert.That(t.envCaptureFarClip, Is.LessThanOrEqualTo(150f), t.name);
            }
        }

        [Test]
        public void Defaults_EveryTierHasCapture_PhoneTiersCheap()
        {
            foreach (var t in QualityProfile.Defaults()) CheckTier(t);
        }

        [Test]
        public void ShippedProfile_MatchesCaptureDefaults()
        {
            var p = QualityProfile.Load();
            Assert.That(p, Is.Not.Null, "Resources/QualityProfile missing");
            foreach (var d in QualityProfile.Defaults())
            {
                Assert.That(p.TryGet(d.name, out var t), Is.True, d.name);
                CheckTier(t);
                Assert.That(t.envCaptureSize, Is.EqualTo(d.envCaptureSize), d.name + " envCaptureSize");
                Assert.That(t.envCaptureInterval, Is.EqualTo(d.envCaptureInterval), d.name + " envCaptureInterval");
                Assert.That(t.envCaptureMinMove, Is.EqualTo(d.envCaptureMinMove), d.name + " envCaptureMinMove");
            }
        }

        [Test]
        public void RqEnvcapZero_TurnsCaptureOff()
        {
            RenderOverrides.EnvCapture = 0;
            try
            {
                var t = RenderOverrides.ApplyTo(QualityProfile.Defaults()[0]);
                Assert.That(t.envCaptureSize, Is.EqualTo(0));
            }
            finally { RenderOverrides.EnvCapture = null; }
        }
    }
}
