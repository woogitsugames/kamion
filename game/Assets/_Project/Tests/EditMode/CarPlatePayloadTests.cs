using System;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    public class CarPlatePayloadTests
    {
        static bool Invoke(string name, params object[] args) => (bool)Type.GetType(
            "Game.World.Import.WorldCarPlateMaterials, Game.World.Import.Editor", true).GetMethod(name).Invoke(null, args);

        static Vector2[] Corners() => new[] { Vector2.zero, Vector2.right, Vector2.one, Vector2.up,
            Vector2.zero, Vector2.right, Vector2.one, Vector2.up };

        [Test]
        public void CompletePlateCornersPreserveAtlasEndpointOrientation()
        {
            var local = Corners();
            var atlas = Array.ConvertAll(local, p => new Vector2(.5039f + .2422f * p.x, .7598f + .1054f * p.y));
            Assert.True(Invoke("ValidCorners", atlas, local));
            local[0] = Vector2.one; // A mixed/zero-filled payload must never be enabled globally.
            Assert.False(Invoke("ValidCorners", atlas, local));
            Assert.False(Invoke("ValidCorners", atlas, new Vector2[8]));
            Assert.False(Invoke("ValidCorners", atlas, null));
        }

        [TestCase("car_plate", true)]
        [TestCase("car_paint_black", false)]
        [TestCase("truck_plate", false)]
        public void MaterialEligibilityIsExactIdAndRejectsUnsupportedBindings(string id, bool expected)
        {
            var material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            try
            {
                material.SetTexture("_BaseMap", Texture2D.whiteTexture);
                Assert.That(Invoke("EligibleMaterial", id, material), Is.EqualTo(expected));
                material.SetTextureScale("_BaseMap", Vector2.one * 2);
                Assert.False(Invoke("EligibleMaterial", id, material));
                material.SetTextureScale("_BaseMap", Vector2.one);
                material.EnableKeyword("LIGHTMAP_ON");
                Assert.False(Invoke("EligibleMaterial", id, material));
            }
            finally { UnityEngine.Object.DestroyImmediate(material); }
        }

        [Test]
        public void OwnedPlateShaderDefaultsToLegacyUv0AndPreservesOpaquePasses()
        {
            var shader = Shader.Find("Kamion/World Car Plate");
            Assert.NotNull(shader);
            var material = new Material(shader);
            try
            {
                Assert.That(material.GetFloat("_PlatePayloadVersion"), Is.Zero);
                foreach (string pass in new[] { "ForwardLit", "ShadowCaster", "DepthOnly", "DepthNormals", "GBuffer" })
                    Assert.That(material.FindPass(pass), Is.GreaterThanOrEqualTo(0), pass);
            }
            finally { UnityEngine.Object.DestroyImmediate(material); }
        }
    }
}
