using System;
using System.Linq;
using UnityEditor;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;

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
        public void NativeValidationRejectsZeroFilledPayloadDespiteIdenticalDescriptor()
        {
            Mesh Build(bool valid)
            {
                var mesh = new Mesh();
                mesh.SetVertexBufferParams(8, new VertexAttributeDescriptor(VertexAttribute.Position, VertexAttributeFormat.Float32, 3),
                    new VertexAttributeDescriptor(VertexAttribute.Normal, VertexAttributeFormat.SNorm8, 4),
                    new VertexAttributeDescriptor(VertexAttribute.TexCoord0, VertexAttributeFormat.Float16, 2),
                    new VertexAttributeDescriptor(VertexAttribute.TexCoord1, VertexAttributeFormat.Float16, 2));
                var bytes = new byte[8 * 24];
                var local = Corners();
                void Half(int offset, float value) => Array.Copy(BitConverter.GetBytes(Mathf.FloatToHalf(value)), 0, bytes, offset, 2);
                for (int i = 0; i < 8; i++)
                {
                    Half(i * 24 + 16, .25f + local[i].x * .2421875f);
                    Half(i * 24 + 18, .5f + local[i].y * .10546875f);
                    Half(i * 24 + 20, valid ? local[i].x : 0);
                    Half(i * 24 + 22, valid ? local[i].y : 0);
                }
                mesh.SetVertexBufferData(bytes, 0, 0, bytes.Length);
                mesh.SetIndices(new[] { 0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7 }, MeshTopology.Triangles, 0);
                mesh.UploadMeshData(true);
                return mesh;
            }
            var good = Build(true);
            var stale = Build(false);
            try
            {
                Assert.False(good.isReadable);
                Assert.That(good.GetVertexBufferStride(0), Is.EqualTo(stale.GetVertexBufferStride(0)));
                Assert.True(Invoke("ValidNativePlate", good, 0));
                Assert.False(Invoke("ValidNativePlate", stale, 0));
            }
            finally { UnityEngine.Object.DestroyImmediate(good); UnityEngine.Object.DestroyImmediate(stale); }
        }

        [Test]
        public void RepeatedShaderSwitchPreservesDisabledMotionAndEnabledDepthPasses()
        {
            var lit = Shader.Find("Universal Render Pipeline/Lit");
            var material = new Material(lit);
            var type = Type.GetType("Game.World.Import.WorldCarPlateMaterials, Game.World.Import.Editor", true);
            try
            {
                material.SetShaderPassEnabled("MotionVectors", false);
                material.SetShaderPassEnabled("DepthOnly", true);
                foreach (var shader in new[] { Shader.Find("Kamion/World Car Plate"), lit, Shader.Find("Kamion/World Car Plate") })
                {
                    type.GetMethod("ChangeShaderPreservingPasses").Invoke(null, new object[] { material, shader });
                    Assert.False(material.GetShaderPassEnabled("MotionVectors"));
                    Assert.True(material.GetShaderPassEnabled("DepthOnly"));
                }
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
                Assert.False(material.IsKeywordEnabled("_PLATE_LOCAL_CORNERS"));
                // EditMode does not activate a URP renderer. Inspect imported subshader
                // metadata rather than Material.FindPass's currently active pipeline.
                var subshader = ShaderUtil.GetShaderData(shader).GetSubshader(0);
                var names = Enumerable.Range(0, subshader.PassCount).Select(i => subshader.GetPass(i).Name.ToUpperInvariant()).ToArray();
                foreach (string pass in new[] { "ForwardLit", "ShadowCaster", "DepthOnly", "DepthNormals", "GBuffer" })
                    Assert.Contains(pass.ToUpperInvariant(), names);
            }
            finally { UnityEngine.Object.DestroyImmediate(material); }
        }
    }
}
