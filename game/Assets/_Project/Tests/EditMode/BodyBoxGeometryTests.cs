using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0228: one geometry source. The body boxes of the physics definitions (JSON, shipped in VehicleDataAsset) feed the
    /// runner's chassis-ground contact and the tractor-trailer contact of the coupling solver; the graybox builders still make
    /// their own PhysX BoxColliders from TractorDimensions / TrailerDimensions. This test keeps both in step: every
    /// ground-flagged box has a collider of the same name, centre and size, and the coupling-only mudguard boxes match the
    /// graybox mudguards. It also checks that the parsed definition reaches the coupling contact (JsonUtility path).
    /// </summary>
    public class BodyBoxGeometryTests
    {
        const float Tol = 1e-4f;

        static Vector3 V(Vec3 v) => new Vector3((float)v.x, (float)v.y, (float)v.z);

        static void AssertColliders(Transform root, BodyBoxDefinition[] boxes)
        {
            var cols = root.Find("Colliders");
            Assert.IsNotNull(cols, "Colliders child missing");
            int ground = 0;
            foreach (var b in boxes)
            {
                if (!b.ground) continue;
                ground++;
                var t = cols.Find(b.name);
                Assert.IsNotNull(t, $"collider '{b.name}' missing");
                var bc = t.GetComponent<BoxCollider>();
                Assert.IsNotNull(bc, $"'{b.name}' has no BoxCollider");
                Assert.Less((t.localPosition + bc.center - V(b.center)).magnitude, Tol, $"{b.name} centre");
                Assert.Less((bc.size - V(b.size)).magnitude, Tol, $"{b.name} size");
            }
            Assert.AreEqual(ground, cols.GetComponentsInChildren<BoxCollider>(true).Length, "collider count");
        }

        [Test]
        public void TractorColliders_MatchDefinitionBodyBoxes()
        {
            var data = VehicleDataAsset.LoadDefault();
            var body = GrayboxTractorBuilder.Build(data, null, null);
            try
            {
                var boxes = data.Vehicle.bodyBoxes;
                Assert.Greater(boxes.Length, 0, "tractor definition has no bodyBoxes");
                AssertColliders(body.transform, boxes);
                foreach (var b in boxes)
                {
                    if (b.ground || !b.name.StartsWith("Mudguard")) continue;
                    var m = body.transform.Find("Chassis/" + b.name);
                    Assert.IsNotNull(m, $"graybox {b.name} missing");
                    Assert.Less((m.localPosition - V(b.center)).magnitude, Tol, $"{b.name} centre");
                    Assert.Less((m.localScale - V(b.size)).magnitude, Tol, $"{b.name} size");
                }
            }
            finally { Object.DestroyImmediate(body.gameObject); }
        }

        [Test]
        public void TrailerColliders_MatchDefinitionBodyBoxes()
        {
            var data = VehicleDataAsset.LoadDefault();
            Assume.That(data.HasTrailer, "default data asset has no trailer");
            var trailer = GrayboxTrailerBuilder.Build(data, null, null);
            try
            {
                Assert.Greater(data.Trailer.bodyBoxes.Length, 0, "trailer definition has no bodyBoxes");
                AssertColliders(trailer.transform, data.Trailer.bodyBoxes);
            }
            finally { Object.DestroyImmediate(trailer.gameObject); }
        }

        /// <summary>The parsed definitions give the coupling contact its geometry and the jackknife limit of ADR 0228 (117.1 deg).</summary>
        [Test]
        public void CouplingContact_FromParsedDefinitions()
        {
            var data = VehicleDataAsset.LoadDefault();
            Assume.That(data.HasTrailer, "default data asset has no trailer");
            var combo = new CombinationModel(data.CreateModel(), data.CreateTrailer(), true);
            Assert.IsTrue(combo.FifthWheel.Contact.HasGeometry);
            double deg = CouplingContact.FirstContactArticulationDeg(data.Vehicle, data.Trailer);
            Assert.That(deg, Is.InRange(117.0, 117.25));
        }
    }
}
