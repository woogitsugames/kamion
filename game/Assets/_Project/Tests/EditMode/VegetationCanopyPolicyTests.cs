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
                VegetationCanopyPolicy.Apply(material);
                Assert.That(material.GetFloat("_AmbientTransmission"), Is.EqualTo(transmission).Within(1e-6));
                Assert.That(material.GetFloat("_CrownShade"), Is.EqualTo(shade).Within(1e-6));
                Assert.That(material.GetColor("_BaseColor"), Is.EqualTo(color));
                Assert.That(material.IsKeywordEnabled("_EMISSION"), Is.False);
            }
            finally { Object.DestroyImmediate(material); }
        }
    }
}
