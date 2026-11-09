using System;
using System.Globalization;
using System.IO;
using System.Text;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    /// <summary>
    /// Unity adapter vs .NET runner on the kerb strike (runner scenario curb_strike_14cm_50kmh_comb, docs/PHYSICS_VALIDATION.md §3a):
    /// the left wheels of the coupled combination run at 50 km/h over a 2.5 × 3 m block (x −3…−0.5, z 30…33).
    /// The block is built three ways: a BoxCollider on the Default layer (the vehicle body colliders can touch it), a
    /// MeshCollider with the DrivingLab slab topology on the WorldKerb layer (wheel rays only, as in WorldC), and the
    /// same mesh 27 cm high at 42 km/h, 40 t: the phone event of DEVICE-RUN-2026-11-09 r3 (s ≈ 598 m), whose per-step
    /// suspension + tyre travel shows a ~0.25–0.27 m effective step, not 14 cm.
    /// Metrics as in the runner (ScenarioRunner.MakeSample, Metrics): tractor Fz / static peak, longest single-wheel
    /// unload (Fz &lt; 500 N or no contact) for tractor and all wheels, peak body pitch asin(fwd.y).
    /// Telemetry CSV (runner column names, tools/telemetry/plot.py) → artifacts/physics/unity-kerb/.
    /// </summary>
    public class KerbStrikeParityTests
    {
        const float Dt = 0.01f;
        static readonly Vector3 O = new Vector3(0f, -500f, 0f);
        SimulationMode m_PrevMode;
        GameObject m_World;
        VehicleBody m_Body;
        TrailerBody m_Trailer;

        public enum KerbKind { BoxDefaultLayer, MeshKerbLayer }

        [SetUp]
        public void SetUp()
        {
            m_PrevMode = Physics.simulationMode;
            Physics.simulationMode = SimulationMode.Script;
            m_World = new GameObject("TestWorld");
        }

        [TearDown]
        public void TearDown()
        {
            if (m_Body != null) Object.DestroyImmediate(m_Body.gameObject);
            if (m_Trailer != null) Object.DestroyImmediate(m_Trailer.gameObject);
            Object.DestroyImmediate(m_World);
            Physics.simulationMode = m_PrevMode;
        }

        // ------------------------------------------------------------------ geometry

        void Flat()
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = "Flat";
            go.transform.SetParent(m_World.transform, false);
            go.transform.SetPositionAndRotation(O + new Vector3(0, -0.5f, 0), Quaternion.identity);
            go.transform.localScale = new Vector3(900, 1, 900);
            go.AddComponent<GroundSurface>().kind = SurfaceKind.DryAsphalt;
        }

        /// <summary>Kerb block x −3…−0.5, z 30…33 (runner box), top at <paramref name="height"/>.</summary>
        void Kerb(KerbKind kind, float height)
        {
            var center = O + new Vector3(-1.75f, height * 0.5f, 31.5f);
            var size = new Vector3(2.5f, height, 3f);
            GameObject go;
            if (kind == KerbKind.BoxDefaultLayer)
            {
                go = GameObject.CreatePrimitive(PrimitiveType.Cube);
                go.transform.localScale = size;
            }
            else
            {
                go = new GameObject("KerbMesh");
                var mesh = SlabMesh(size);
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                go.AddComponent<MeshCollider>().sharedMesh = mesh;
                int kl = LayerMask.NameToLayer("WorldKerb");
                Assert.GreaterOrEqual(kl, 0, "layer WorldKerb missing (ProjectSetup)");
                go.layer = kl;
            }
            go.name = "Kerb_" + kind;
            go.transform.SetParent(m_World.transform, false);
            go.transform.position = center;
            go.AddComponent<GroundSurface>().kind = SurfaceKind.Concrete;
        }

        /// <summary>Same topology as Editor MeshGen.Slab (DrivingLab platforms / side curbs): 6 quads, split vertices.</summary>
        static Mesh SlabMesh(Vector3 size)
        {
            var v = new Vector3[24]; var n = new Vector3[24]; var t = new int[36];
            Vector3 h = size * 0.5f;
            int vi = 0, ti = 0;
            void Face(Vector3 c, Vector3 u, Vector3 w, Vector3 normal)
            {
                int i = vi;
                v[vi++] = c - u - w; v[vi++] = c - u + w; v[vi++] = c + u + w; v[vi++] = c + u - w;
                for (int k = 0; k < 4; k++) n[i + k] = normal;
                t[ti++] = i; t[ti++] = i + 1; t[ti++] = i + 2; t[ti++] = i; t[ti++] = i + 2; t[ti++] = i + 3;
            }
            Face(new Vector3(0, h.y, 0), new Vector3(h.x, 0, 0), new Vector3(0, 0, h.z), Vector3.up);
            Face(new Vector3(0, -h.y, 0), new Vector3(0, 0, h.z), new Vector3(h.x, 0, 0), Vector3.down);
            Face(new Vector3(h.x, 0, 0), new Vector3(0, 0, h.z), new Vector3(0, h.y, 0), Vector3.right);
            Face(new Vector3(-h.x, 0, 0), new Vector3(0, h.y, 0), new Vector3(0, 0, h.z), Vector3.left);
            Face(new Vector3(0, 0, h.z), new Vector3(0, h.y, 0), new Vector3(h.x, 0, 0), Vector3.forward);
            Face(new Vector3(0, 0, -h.z), new Vector3(h.x, 0, 0), new Vector3(0, h.y, 0), Vector3.back);
            var m = new Mesh { name = "KerbSlab", vertices = v, normals = n, triangles = t };
            m.RecalculateBounds();
            return m;
        }

        // ------------------------------------------------------------------ vehicle

        void SpawnCoupled(CargoPreset cargo)
        {
            Physics.SyncTransforms();
            var data = VehicleDataAsset.LoadDefault();
            var mats = GrayboxMaterials.CreateRuntime();
            m_Body = GrayboxTractorBuilder.Build(data, null, mats);
            m_Trailer = GrayboxTrailerBuilder.Build(data, null, mats);
            m_Body.ResetPose(O, Quaternion.identity);
            m_Trailer.Initialize(m_Body.Data, cargo, m_Body.Model.MassProps.Mass);
            m_Body.ConnectTrailer(m_Trailer, true);
            CombinationPlacement.Tractor(m_Body.Model, O, Quaternion.identity, out Vector3 vp, out Quaternion vq);
            m_Body.SetPose(vp, vq);
            CombinationPlacement.Coupled(m_Body.Model, vp, vq, m_Trailer.Model, 0f, out Vector3 tp, out Quaternion tq);
            m_Trailer.SetPose(tp, tq);
            Physics.SyncTransforms();
            m_Body.Model.InitParking(false);
            m_Body.Input = new DriverInput { Selector = GearSelector.Drive };
        }

        /// <summary>Runner SpeedController (tools/physics-runner/Sim/Drivers.cs), same gains.</summary>
        sealed class SpeedHold
        {
            double m_I;
            readonly double m_Target;
            public SpeedHold(double kmh) { m_Target = kmh / 3.6; }
            public void Update(double v, double dt, out double th, out double br)
            {
                double e = m_Target - v;
                m_I = Math.Max(-5, Math.Min(10, m_I + e * dt));
                th = Math.Max(0, Math.Min(1, 0.25 * e + 0.06 * m_I));
                br = e < -0.5 ? Math.Max(0, Math.Min(1, -0.15 * (e + 0.5))) : 0;
                if (br > 0) { th = 0; m_I = Math.Min(m_I, 0); }
            }
        }

        public struct KerbMetrics
        {
            public double FzRatio, TractorAirtime, AllAirtime, FrontAxleAirtime, PitchMaxDeg, MaxDv;
            public int BodyContacts;
            public string FirstContact;
            public override string ToString() =>
                string.Format(CultureInfo.InvariantCulture,
                    "Fz/static {0:F2}, tractor single-wheel unload {1:F2} s, all wheels {2:F2} s, front axle (both) {3:F2} s, pitch max {4:F2}°, max |dv| {5:F3} m/s, body contacts {6} {7}",
                    FzRatio, TractorAirtime, AllAirtime, FrontAxleAirtime, PitchMaxDeg, MaxDv, BodyContacts, FirstContact);
        }

        sealed class ContactCounter : MonoBehaviour
        {
            public int Count;
            public string First = "";
            void OnCollisionEnter(Collision c) => Note(c);
            void OnCollisionStay(Collision c) => Note(c);
            void Note(Collision c)
            {
                if (Count++ == 0)
                    First = $"{c.GetContact(0).thisCollider.name} x {c.collider.name} at {c.GetContact(0).point.y - O.y:F2} m, impulse {c.impulse.magnitude:F0} N s";
            }
        }

        KerbMetrics Run(CargoPreset cargo, KerbKind kind, float height, float kmh, double seconds, string csvName)
        {
            Flat();
            Kerb(kind, height);
            SpawnCoupled(cargo);
            var cc = m_Body.gameObject.AddComponent<ContactCounter>();
            var tcc = m_Trailer.gameObject.AddComponent<ContactCounter>();
            m_Body.SetMoving(kmh / 3.6f, 0);
            Physics.SyncTransforms();
            var sh = new SpeedHold(kmh);
            var vis = m_Body.GetComponent<VehicleVisuals>();
            var tvis = m_Trailer.GetComponent<TrailerVisuals>();
            var tw = m_Body.Model.Wheels;
            var trw = m_Trailer.Model.Wheels;
            int nw = tw.Length + trw.Length;
            var run = new int[nw];
            int bestT = 0, bestAll = 0, frontRun = 0, bestFront = 0;
            double fzRatio = 0, pitchMax = double.MinValue, maxDv = 0;
            var rb = m_Body.Body;
            Vector3 prevV = rb.linearVelocity;
            int groundContactsAfterSpawn = 0;

            var csv = new StringBuilder();
            csv.Append("t,x,z,speed_kmh,pitch_deg,roll_deg,cab_pitch_deg,articulation_deg,kingpin_fz,trailer_x,trailer_z");
            foreach (var w in tw) csv.Append(',').Append(w.Name).Append("_fz,").Append(w.Name).Append("_comp,").Append(w.Name).Append("_tire_defl,").Append(w.Name).Append("_contact");
            foreach (var w in trw) csv.Append(',').Append(w.Name).Append("_fz,").Append(w.Name).Append("_comp,").Append(w.Name).Append("_tire_defl,").Append(w.Name).Append("_contact");
            csv.Append('\n');
            var inv = CultureInfo.InvariantCulture;

            int steps = (int)Math.Round(seconds / Dt);
            for (int i = 0; i < steps; i++)
            {
                sh.Update(Math.Abs(m_Body.Model.SpeedForward), Dt, out double th, out double br);
                var inp = m_Body.Input;
                inp.Throttle = (float)th; inp.Brake = (float)br; inp.Steer = 0; inp.ParkingBrake = false; inp.Selector = GearSelector.Drive;
                m_Body.Input = inp;
                if (i == 1) { groundContactsAfterSpawn = cc.Count + tcc.Count; }
                m_Body.Tick(Dt);
                Physics.Simulate(Dt);
                vis.Capture(Dt);
                tvis.Capture(Dt);

                Vector3 v = rb.linearVelocity;
                maxDv = Math.Max(maxDv, (v - prevV).magnitude);
                prevV = v;
                Vector3 fwd = rb.rotation * Vector3.forward, right = rb.rotation * Vector3.right;
                double pitch = Math.Asin(Mathf.Clamp(fwd.y, -1f, 1f)) * MathUtil.Rad2Deg;
                pitchMax = Math.Max(pitchMax, pitch);
                bool fl = false, fr = false;
                for (int k = 0; k < nw; k++)
                {
                    var w = k < tw.Length ? tw[k] : trw[k - tw.Length];
                    bool off = !w.Contact || w.Fz < 500;
                    run[k] = off ? run[k] + 1 : 0;
                    if (k < tw.Length)
                    {
                        bestT = Math.Max(bestT, run[k]);
                        if (w.StaticLoad > 0) fzRatio = Math.Max(fzRatio, w.Fz / w.StaticLoad);
                        if (w.AxleIndex == 0) { if (k % 2 == 0) fl = off; else fr = off; }
                    }
                    bestAll = Math.Max(bestAll, run[k]);
                }
                frontRun = fl && fr ? frontRun + 1 : 0;
                bestFront = Math.Max(bestFront, frontRun);

                var fw = m_Body.Combination.FifthWheel;
                Vector3 tp = m_Trailer.Body.position;
                csv.AppendFormat(inv, "{0:F2},{1:F4},{2:F4},{3:F4},{4:F4},{5:F4},{6:F4},{7:F4},{8:F1},{9:F4},{10:F4}",
                    m_Body.Model.Time, rb.position.x - O.x, rb.position.z - O.z, m_Body.Model.SpeedForward * 3.6, pitch,
                    Math.Asin(Mathf.Clamp(right.y, -1f, 1f)) * MathUtil.Rad2Deg, m_Body.Model.Cab.Pitch * MathUtil.Rad2Deg,
                    fw.Articulation * MathUtil.Rad2Deg, fw.KingpinLoadLocal.y, tp.x - O.x, tp.z - O.z);
                for (int k = 0; k < nw; k++)
                {
                    var w = k < tw.Length ? tw[k] : trw[k - tw.Length];
                    csv.AppendFormat(inv, ",{0:F1},{1:F5},{2:F5},{3}", w.Fz, w.Compression, w.TireDeflection, w.Contact ? 1 : 0);
                }
                csv.Append('\n');
            }

            string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "artifacts", "physics", "unity-kerb"));
            Directory.CreateDirectory(dir);
            File.WriteAllText(Path.Combine(dir, csvName + ".csv"), csv.ToString());

            return new KerbMetrics
            {
                FzRatio = fzRatio, TractorAirtime = bestT * Dt, AllAirtime = bestAll * Dt, FrontAxleAirtime = bestFront * Dt,
                PitchMaxDeg = pitchMax, MaxDv = maxDv, BodyContacts = cc.Count + tcc.Count - groundContactsAfterSpawn,
                FirstContact = cc.First + (tcc.First.Length > 0 ? " | trailer: " + tcc.First : ""),
            };
        }

        // ------------------------------------------------------------------ tests

        /// <summary>
        /// Runner reference (physics-runner, commit with ADR 0014 dimensions, artifacts/physics run 2026-11-09):
        /// empty: Fz/static 3.90, tractor 0.11 s, all 0.21 s, pitch max 1.66°; 40 t: 3.53, 0.08 s, 0.09 s, 1.99°.
        /// Tolerance: Fz and pitch ±20 %, airtimes ±20 % or ±0.03 s (3 steps), whichever is larger.
        /// </summary>
        [TestCase(CargoPreset.Empty, KerbKind.BoxDefaultLayer, 3.90, 0.11, 0.21, 1.66, TestName = "KerbStrike14cm50_Empty_Box_MatchesRunner")]
        [TestCase(CargoPreset.Empty, KerbKind.MeshKerbLayer, 3.90, 0.11, 0.21, 1.66, TestName = "KerbStrike14cm50_Empty_Mesh_MatchesRunner")]
        [TestCase(CargoPreset.Gross40t, KerbKind.BoxDefaultLayer, 3.53, 0.08, 0.09, 1.99, TestName = "KerbStrike14cm50_40t_Box_MatchesRunner")]
        [TestCase(CargoPreset.Gross40t, KerbKind.MeshKerbLayer, 3.53, 0.08, 0.09, 1.99, TestName = "KerbStrike14cm50_40t_Mesh_MatchesRunner")]
        public void KerbStrike14cm50(CargoPreset cargo, KerbKind kind, double fz, double airT, double airAll, double pitch)
        {
            var m = Run(cargo, kind, 0.14f, 50f, 6.0, $"kerb14_50_{cargo}_{kind}");
            Debug.Log($"[TEST] kerb 14 cm 50 km/h {cargo} {kind}: Unity {m} | runner Fz/static {fz:F2}, tractor {airT:F2} s, all {airAll:F2} s, pitch {pitch:F2}°");
            AssertClose(fz, m.FzRatio, 0.20, 0, "Fz / static");
            AssertClose(airT, m.TractorAirtime, 0.20, 0.03, "tractor single-wheel unload");
            AssertClose(airAll, m.AllAirtime, 0.20, 0.03, "all-wheel single-wheel unload");
            AssertClose(pitch, m.PitchMaxDeg, 0.20, 0.2, "pitch peak");
            Assert.Less(m.MaxDv, 0.35, "max |dv| per step (runner limit)");
            Assert.AreEqual(0, m.BodyContacts, "no PhysX body contact with a 14 cm kerb");
        }

        /// <summary>
        /// Phone event reconstruction: 27 cm effective step, 42 km/h, 40 t (DEVICE-RUN r3: Fz 35 → 239 kN = 6.8×, both front
        /// wheels unloaded ~0.4 s, pitch +8°). Runner (step_27cm_42kmh_comb@laden40, same block): Fz/static 6.50, tractor
        /// 0.42 s, pitch max 6.36°. Shows that the adapter reproduces the core and that the phone values need a ~27 cm step.
        /// </summary>
        [Test]
        public void KerbStep27cm42_40t_Mesh_MatchesRunnerAndPhone()
        {
            var m = Run(CargoPreset.Gross40t, KerbKind.MeshKerbLayer, 0.27f, 42f, 6.0, "kerb27_42_Gross40t_Mesh");
            Debug.Log($"[TEST] kerb 27 cm 42 km/h 40 t mesh: Unity {m} | runner Fz/static 6.50, tractor 0.42 s, pitch 6.36° | phone 6.8×, ~0.4 s, +8°");
            AssertClose(6.50, m.FzRatio, 0.20, 0, "Fz / static");
            AssertClose(0.42, m.TractorAirtime, 0.20, 0.03, "tractor single-wheel unload");
            AssertClose(6.36, m.PitchMaxDeg, 0.20, 0.2, "pitch peak");
        }

        static void AssertClose(double expected, double actual, double rel, double abs, string what)
        {
            double tol = Math.Max(Math.Abs(expected) * rel, abs);
            Assert.AreEqual(expected, actual, tol, $"{what}: Unity {actual:F3} vs runner {expected:F3} (±{tol:F3})");
        }
    }
}
