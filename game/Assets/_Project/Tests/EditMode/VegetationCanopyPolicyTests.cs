using Game.World;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    public class VegetationCanopyPolicyTests
    {
        [TestCase("M_leaves_pine", .40f, .25f)]
        [TestCase("M_impostor_tree_pine_0", .40f, .25f)]
        [TestCase("M_forest_edge_conifer", .40f, .50f)]
        [TestCase("M_forest_edge_mixed", .32f, .50f)]
        [TestCase("M_leaves_linden", .25f, .50f)]
        [TestCase("M_fab_elderberry", .25f, .50f)]
        public void OnlyPineOrPineStandGetsAdditionalScattering(string name, float transmission, float shade)
        {
            var material = new Material(Shader.Find("Kamion/Vegetation")) { name = name };
            try
            {
                var color = new Color(.3f, .5f, .2f, .8f);
                material.SetColor("_BaseColor", color);
                // Unity Color storage may round-trip by an ulp; compare against the stored
                // pre-policy value so this checks whether the policy changes the palette.
                var storedColor = material.GetColor("_BaseColor");
                VegetationCanopyPolicy.Apply(material);
                Assert.That(material.GetFloat("_AmbientTransmission"), Is.EqualTo(transmission).Within(1e-6));
                Assert.That(material.GetFloat("_CrownShade"), Is.EqualTo(shade).Within(1e-6));
                Assert.That(material.GetColor("_BaseColor"), Is.EqualTo(storedColor));
                Assert.That(material.IsKeywordEnabled("_EMISSION"), Is.False);
            }
            finally { Object.DestroyImmediate(material); }
        }

        // ADR 0352: per-tree tint / clump shading only on library tree foliage; conifers vary less than broadleaves.
        [TestCase("M_leaves_linden (simple)", .11f, .05f, .30f)]
        [TestCase("M_leaves_oak", .11f, .05f, .30f)]
        [TestCase("M_impostor_tree_birch_2", .11f, .05f, .30f)]
        [TestCase("M_leaves_pine", .07f, .02f, .18f)]
        [TestCase("M_impostor_tree_spruce_1", .07f, .02f, .18f)]
        [TestCase("M_forest_edge_mixed", 0f, 0f, 0f)]
        [TestCase("M_fab_elderberry", 0f, 0f, 0f)]
        [TestCase("M_fire_station_thuja_shell", 0f, 0f, 0f)]
        public void TreeVariationOnlyOnLibraryTrees(string name, float brightness, float hue, float clump)
        {
            var material = new Material(Shader.Find("Kamion/Vegetation")) { name = name };
            try
            {
                Assert.That(material.GetVector("_TreeVar"), Is.EqualTo(new Vector4(0f, 0f, 0f, 1.5f)), "shader default = off");
                VegetationCanopyPolicy.Apply(material);
                var v = material.GetVector("_TreeVar");
                Assert.That(v.x, Is.EqualTo(brightness).Within(1e-6));
                Assert.That(v.y, Is.EqualTo(hue).Within(1e-6));
                Assert.That(v.z, Is.EqualTo(clump).Within(1e-6));
                Assert.That(v.w, Is.GreaterThan(0.5f));
            }
            finally { Object.DestroyImmediate(material); }
        }
    }
}
