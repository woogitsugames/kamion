using Game.Editor.VisualQA;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Tests
{
    public class AsphaltScopeTests
    {
        static Shader shader;

        [OneTimeSetUp]
        public void BuildActualScopeShader()
        {
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null)
                Assert.Ignore("Requires graphics-enabled GPU scope readback.");
            shader = AsphaltScopeProbe.BuildShader();
        }

        [TestCase(625f, -475f, 0f)]
        [TestCase(-200f, -244f, 1f)]
        public void Scope_ProtectsSiteAndPreservesPublicProbe_AfterOriginShift(float east, float north, float expected)
        {
            var bounds = new Vector4(400f, -700f, 850f, -250f);
            foreach (var shift in new[] { Vector3.zero, new Vector3(-1024f, 0f, 2048f) })
                Assert.That(AsphaltScopeProbe.Read(shader, new Vector2(east, north), shift, bounds),
                    Is.EqualTo(expected).Within(0.001f), "Object translation must not move the protected authoring area");
        }

        [Test]
        public void MissingScope_DoesNotSuppressWear()
        {
            Assert.That(AsphaltScopeProbe.Read(shader, new Vector2(625f, -475f), Vector3.zero, Vector4.zero),
                Is.EqualTo(1f).Within(0.001f));
        }
    }
}
