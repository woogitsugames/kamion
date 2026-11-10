using System.Linq;
using Game.World;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0050: the imported region carries one contact-shadow prototype per distinct vehicle spec (<= 7), culled with the
    /// vehicles, no shadows, one quad, an instanced Kamion/World Vehicle Contact material with the generator's spec, and
    /// as many patch instances as vehicle instances. Reads the imported region (scripts/import-region.ps1); skipped when
    /// no region has been imported in this checkout.
    /// </summary>
    public class VehicleContactImportTests
    {
        const string k_Set = "Assets/_Generated/World/bialystok-industrial-c/Instances.asset";

        static WorldInstanceSet LoadSet()
        {
            var set = AssetDatabase.LoadAssetAtPath<WorldInstanceSet>(k_Set);
            if (set == null) Assert.Ignore($"{k_Set} not imported (run scripts/import-region.ps1 -Region bialystok-industrial-c)");
            return set;
        }

        static bool IsVehicleBody(string n) =>
            n.StartsWith("car_") || n.StartsWith("van_") || n.StartsWith("tractor_") || n.StartsWith("trailer_");

        [Test]
        public void ContactPrototypes_OnePerSpec_NoShadows_CulledWithVehicles()
        {
            var set = LoadSet();
            var contact = set.prototypes.Where(p => p.name.StartsWith("contact_")).ToList();
            Assert.That(contact.Count, Is.InRange(1, 7), "one prototype per distinct contact spec (4 car bodies, van, tractor, trailer)");
            Assert.AreEqual(contact.Count, contact.Select(p => p.name).Distinct().Count());
            foreach (var p in contact)
            {
                Assert.AreEqual(1, p.lods.Length, p.name);
                Assert.AreEqual(0, p.shadowLodMask, $"{p.name} must never cast");
                Assert.AreEqual(WorldInstances.VehicleCullM, p.lodEndM[0], p.name);
                Assert.IsTrue(WorldInstances.IsVehicle(p.name), p.name);
                Assert.AreEqual(2, p.lods[0].triangles.Length / 3, $"{p.name}: one quad");
            }
        }

        [Test]
        public void ContactMaterials_InstancedWithSpec()
        {
            var set = LoadSet();
            var shader = Shader.Find("Kamion/World Vehicle Contact");
            Assert.IsNotNull(shader);
            var defaults = new Material(shader);
            foreach (var p in set.prototypes.Where(p => p.name.StartsWith("contact_")))
            {
                var m = set.materials[p.materialStart[0]];
                Assert.AreEqual(shader, m.shader, p.name);
                Assert.IsTrue(m.enableInstancing, p.name);
                Assert.AreEqual(2499, m.renderQueue, p.name);
                var patch = m.GetVector("_Patch");
                Assert.AreNotEqual(defaults.GetVector("_Patch"), patch, $"{p.name}: generator spec written, not shader defaults");
                Assert.Greater(patch.w, 0.2f, $"{p.name}: edge fade (no outline)");
            }
            Object.DestroyImmediate(defaults);
        }

        [Test]
        public void EveryVehicleInstanceHasOnePatch()
        {
            var set = LoadSet();
            int vehicles = 0, patches = 0, runs = 0;
            foreach (var p in set.prototypes)
            {
                if (p.name.StartsWith("contact_")) patches += p.count;
                else if (IsVehicleBody(p.name)) vehicles += p.count;
            }
            foreach (var r in set.runs)
                if (set.prototypes[r.prototype].name.StartsWith("contact_")) runs += r.count;
            Assert.Greater(vehicles, 0);
            Assert.AreEqual(vehicles, patches);
            Assert.AreEqual(patches, runs, "every patch instance is in a cell run");
        }
    }
}
