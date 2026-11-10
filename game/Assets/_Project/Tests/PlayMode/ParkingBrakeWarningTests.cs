using Game.Gameplay;
using Game.UI.CabDisplays;
using Game.UI.Driving;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    /// <summary>Parking-brake drive-away warning plumbing (ADR 0004 addendum): HUD tracker, cluster chime, cluster telltale flash.</summary>
    public class ParkingBrakeWarningTests
    {
        const float Dt = 0.01f;
        static readonly Vector3 O = new Vector3(0f, -900f, 0f);
        SimulationMode m_PrevMode;
        VehicleBody m_Body;
        GameObject m_Ground;

        [SetUp]
        public void SetUp() { m_PrevMode = Physics.simulationMode; Physics.simulationMode = SimulationMode.Script; }

        [TearDown]
        public void TearDown()
        {
            if (m_Body != null) Object.DestroyImmediate(m_Body.gameObject);
            if (m_Ground != null) Object.DestroyImmediate(m_Ground);
            Physics.simulationMode = m_PrevMode;
        }

        // ------------------------------------------------------------------ tracker (pure logic)

        [Test]
        public void Tracker_ShowsWhileWarning_FadesOverOneSecondAfter()
        {
            var t = new ParkingBrakeWarningTracker();
            t.Poll(false, 0, 0f);
            Assert.AreEqual(0f, t.Alpha);
            t.Poll(true, 1, 1f);
            Assert.AreEqual(1f, t.Alpha);
            t.Poll(true, 1, 2.5f);
            Assert.AreEqual(1f, t.Alpha, "full for as long as the flag is on");
            t.Poll(false, 1, 3f);                                  // flag clears at t = 3
            Assert.AreEqual(1f, t.Alpha, 1e-4f);
            t.Poll(false, 1, 3.5f);
            Assert.AreEqual(0.5f, t.Alpha, 1e-4f);
            t.Poll(false, 1, 4.1f);
            Assert.AreEqual(0f, t.Alpha);
            t.Poll(false, 1, 9f);
            Assert.AreEqual(0f, t.Alpha, "stays hidden");
        }

        [Test]
        public void Tracker_ReappearingWarningCancelsTheFade()
        {
            var t = new ParkingBrakeWarningTracker();
            t.Poll(true, 1, 0f);
            t.Poll(false, 1, 1f);
            t.Poll(false, 1, 1.6f);
            Assert.Less(t.Alpha, 0.5f);
            t.Poll(true, 2, 1.7f);
            Assert.AreEqual(1f, t.Alpha);
        }

        [Test]
        public void Tracker_ChimesOncePerIncrement_NotWhileHeld_NotOnFirstPoll()
        {
            var t = new ParkingBrakeWarningTracker();
            Assert.IsFalse(t.Poll(false, 3, 0f), "first poll only synchronises (a count carried over from earlier is not a new event)");
            Assert.IsTrue(t.Poll(true, 4, 0.1f), "rising edge");
            for (int i = 0; i < 100; i++) Assert.IsFalse(t.Poll(true, 4, 0.2f + i * 0.01f), "held: no repeat");
            Assert.IsFalse(t.Poll(false, 4, 2f), "clearing is silent");
            Assert.IsTrue(t.Poll(true, 5, 3f), "second event chimes again");
            Assert.IsTrue(t.Poll(true, 7, 3.1f), "several increments between two polls -> one chime");
            Assert.IsFalse(t.Poll(true, 7, 3.2f));
        }

        [Test]
        public void Tracker_CounterReset_ResynchronisesSilently()
        {
            var t = new ParkingBrakeWarningTracker();
            t.Poll(false, 5, 0f);
            Assert.IsFalse(t.Poll(false, 0, 1f), "new model after a respawn: counter went down");
            Assert.IsTrue(t.Poll(true, 1, 2f));
        }

        [Test]
        public void ChimeWaveform_IsShortBoundedAndFadesOut()
        {
            var d = ClusterChime.Synthesize();
            Assert.AreEqual(Mathf.RoundToInt(ClusterChime.SampleRate * ClusterChime.DurationSeconds), d.Length);
            float peak = 0f;
            foreach (var v in d) peak = Mathf.Max(peak, Mathf.Abs(v));
            Assert.That(peak, Is.InRange(0.2f, 0.9f), "audible but not clipping");
            float tail = 0f;
            for (int i = d.Length - 200; i < d.Length; i++) tail = Mathf.Max(tail, Mathf.Abs(d[i]));
            Assert.Less(tail, 0.02f, "no click at the end");
        }

        // ------------------------------------------------------------------ with the real vehicle model

        void Spawn()
        {
            var g = GameObject.CreatePrimitive(PrimitiveType.Cube);
            g.name = "ParkWarnGround";
            g.transform.SetPositionAndRotation(O + new Vector3(0f, -0.5f, 0f), Quaternion.identity);
            g.transform.localScale = new Vector3(600f, 1f, 600f);
            g.AddComponent<GroundSurface>().kind = SurfaceKind.DryAsphalt;
            m_Ground = g;
            Physics.SyncTransforms();
            m_Body = GrayboxTractorBuilder.Build(VehicleDataAsset.LoadDefault(), null, null);
            m_Body.ResetPose(O, Quaternion.identity);
            m_Body.Model.InitParking(true);
            m_Body.Input = new DriverInput { Selector = GearSelector.Drive, ParkingBrake = true };
        }

        void Step(int n) { for (int i = 0; i < n; i++) { m_Body.Tick(Dt); Physics.Simulate(Dt); } }

        [Test]
        public void Chime_OncePerDriveAwayAttempt_OnTheRealModel()
        {
            Spawn();
            var chime = m_Body.gameObject.AddComponent<ClusterChime>();
            chime.vehicle = m_Body;
            float now = 0f;
            void Run(int steps) { for (int i = 0; i < steps; i++) { Step(1); now += Dt; chime.Tick(now); } }

            Run(100);
            Assert.AreEqual(0, chime.ChimesPlayed, "P applied, nothing pressed: silent");
            m_Body.Input = new DriverInput { Selector = GearSelector.Drive, ParkingBrake = true, Throttle = 0.6 };
            Run(300);
            Assert.IsTrue(m_Body.Model.ParkingBrakeWarning, "drive-away attempt raises the warning");
            Assert.AreEqual(1, chime.ChimesPlayed, "one chime for the attempt, none while throttle is held");
            m_Body.Input = new DriverInput { Selector = GearSelector.Drive, ParkingBrake = true };
            Run(200);
            Assert.IsFalse(m_Body.Model.ParkingBrakeWarning);
            m_Body.Input = new DriverInput { Selector = GearSelector.Drive, ParkingBrake = true, Throttle = 0.6 };
            Run(200);
            Assert.AreEqual(2, chime.ChimesPlayed, "second attempt chimes again");
        }

        [Test]
        public void ClusterState_TelltaleFlashesOnlyWhileWarning()
        {
            Spawn();
            var source = new CabDisplaySource();
            var state = new CabDisplayState();
            Step(100);
            source.Sample(m_Body.Model, null, false, null, m_Body.transform, null, 0.1, ref state);
            Assert.IsTrue(state.ParkingBrake, "P applied: telltale lit");
            Assert.IsFalse(state.ParkingBrakeWarning);
            Assert.IsFalse(state.ParkingBrakeFlashOn);

            m_Body.Input = new DriverInput { Selector = GearSelector.Drive, ParkingBrake = true, Throttle = 0.6 };
            Step(300);
            int on = 0, off = 0;
            for (int i = 0; i < 80; i++)
            {
                source.Sample(m_Body.Model, null, false, null, m_Body.transform, null, i * 0.01, ref state);
                Assert.IsTrue(state.ParkingBrakeWarning);
                if (state.ParkingBrakeFlashOn) on++; else off++;
            }
            Assert.AreEqual(40, on, "0.8 s period, 50 % duty");
            Assert.AreEqual(40, off);
        }
    }
}
