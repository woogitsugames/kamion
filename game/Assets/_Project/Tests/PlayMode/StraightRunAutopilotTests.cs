using System.Collections;
using System.Globalization;
using Game.Gameplay;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0195: the gate 1-2 autopilot straight080 in the DrivingLab scene (PhysX bodies + the game's vehicle model, inputs
    /// only through the driver commands). Limits = docs/04 s6.3/s6.5 bands of tests/physics/scenarios/straight_0_80_0.json;
    /// parity with the .NET runner (same pilot source) within a few per cent. Editor numbers, not the phone.
    /// </summary>
    public class StraightRunAutopilotTests
    {
        // .NET runner reference (straight_0_80_0, commit of ADR 0195): t80 [s], stop distance [m].
        const float RunnerT80Solo = 13.60f, RunnerT80Empty = 20.54f, RunnerT8040t = 47.52f;
        const float RunnerStopSolo = 35.69f, RunnerStopEmpty = 39.49f, RunnerStop40t = 40.52f;

        DrivingLabBootstrap m_Boot;
        VehicleBody m_Body;

        IEnumerator LoadLab()
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            m_Boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            m_Body = Object.FindAnyObjectByType<VehicleBody>();
            Assert.IsNotNull(m_Boot);
            Assert.IsNotNull(m_Body);
        }

        /// <summary>Runs one straight run to the stop (real-time timeout) and returns the pilot's online results.</summary>
        IEnumerator RunOnce(DrivingLabBootstrap.LabSpawn preset, StraightRunResult[] result, int slot, string csvOut = null)
        {
            m_Boot.StartStraightRun(preset, "80");
            var rec = m_Body.GetComponent<VehicleTelemetryRecorder>();
            if (csvOut != null) rec.StartRecording();
            Time.timeScale = 8f;
            float end = Time.realtimeSinceStartup + 240f;
            while (m_Boot.StraightPilot.Phase != StraightRunPhase.Stopped && Time.realtimeSinceStartup < end) yield return null;
            Time.timeScale = 1f;
            if (csvOut != null)
            {
                string f = rec.CurrentFile;
                rec.StopRecording();
                System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(csvOut));
                System.IO.File.Copy(f, csvOut, true);
                var lines = System.IO.File.ReadAllLines(csvOut);
                StringAssert.StartsWith("t,x,y,z,speed_kmh", lines[0]);
                Assert.Greater(lines.Length, 1000, "CSV rows at 100 Hz");
            }
            Assert.AreEqual(StraightRunPhase.Stopped, m_Boot.StraightPilot.Phase, $"{preset}: run did not reach the stop (pilot time {m_Boot.StraightPilot.Time:F1} s)");
            result[slot] = m_Boot.StraightPilot.Result;
            var r = result[slot];
            Debug.Log(string.Format(CultureInfo.InvariantCulture,
                "[TEST] straight080 {0} mass {1:F1} t: t60 {2:F2} s, t80 {3:F2} s, s80 {4:F1} m, hold {5:F2}+-{6:F2} km/h, v_brake {7:F2}, stop {8:F2} m / {9:F2} s, MFDD {10:F2}, max decel {11:F2} m/s2, lat {12:F3} m, pos ({13:F1}, {14:F1})",
                preset, m_Body.Model.TotalMass / 1000, r.TimeTo60, r.TimeTo80, r.DistanceTo80, r.HoldSpeedMean, r.HoldSpeedStd, r.BrakeSpeedKmh,
                r.StopDistance, r.StopTime, r.Mfdd, r.MaxDecel, r.MaxLateralDeviation, m_Body.transform.position.x, m_Body.transform.position.z));
        }

        static void AssertCommon(in StraightRunResult r, float stopMin, float stopMax)
        {
            Assert.IsTrue(r.Complete);
            Assert.That(r.BrakeSpeedKmh, Is.InRange(78.5, 81.5), "braking starts at 80 km/h");
            Assert.Less(r.HoldSpeedStd, 1.0, "hold 80 km/h steady");
            Assert.That(r.StopDistance, Is.InRange(stopMin, stopMax), "stop distance 80 -> 0 (docs/04 s6.5)");
            Assert.That(r.Mfdd, Is.InRange(5.0, 8.0), "MFDD (R13 Annex 4)");
            Assert.Less(r.MaxLateralDeviation, 0.5, "stays on the line");
        }

        static string CsvPath(string name) =>
            System.IO.Path.Combine(Application.dataPath, "..", "..", "artifacts", "autopilot-0195", "playmode", name + ".csv");

        [UnityTest]
        public IEnumerator Straight080_Solo_ThreeRuns_RepeatableAndInTolerance()
        {
            yield return LoadLab();
            var res = new StraightRunResult[3];
            for (int i = 0; i < 3; i++) yield return RunOnce(DrivingLabBootstrap.LabSpawn.Solo, res, i, i == 0 ? CsvPath("s080_solo") : null);
            double mean = (res[0].TimeTo80 + res[1].TimeTo80 + res[2].TimeTo80) / 3;
            for (int i = 0; i < 3; i++)
            {
                Assert.That(res[i].TimeTo60, Is.InRange(7.0, 20.0), "0-60 solo (docs/04 s6.3 band)");
                Assert.That(res[i].TimeTo80, Is.InRange(12.0, 32.0), "0-80 solo");
                Assert.LessOrEqual(System.Math.Abs(res[i].TimeTo80 - mean) / mean, 0.03, "gate 1: 0-80 x3 within +/-3 %");
                AssertCommon(res[i], 32f, 55f);
            }
            Assert.AreEqual(RunnerT80Solo, res[0].TimeTo80, 0.05 * RunnerT80Solo, "parity with the .NET runner (0-80)");
            Assert.AreEqual(RunnerStopSolo, res[0].StopDistance, 0.10 * RunnerStopSolo, "parity with the .NET runner (stop)");
        }

        [UnityTest]
        public IEnumerator Straight080_EmptyCombination_InTolerance()
        {
            yield return LoadLab();
            var res = new StraightRunResult[1];
            yield return RunOnce(DrivingLabBootstrap.LabSpawn.Empty, res, 0, CsvPath("s080_empty"));
            Assert.IsTrue(m_Body.Coupled, "trailer coupled");
            Assert.That(res[0].TimeTo80, Is.InRange(20.0, 55.0), "0-80 empty combination");
            AssertCommon(res[0], 35f, 61.2f);
            Assert.AreEqual(RunnerT80Empty, res[0].TimeTo80, 0.05 * RunnerT80Empty, "parity with the .NET runner (0-80)");
            Assert.AreEqual(RunnerStopEmpty, res[0].StopDistance, 0.10 * RunnerStopEmpty, "parity with the .NET runner (stop)");
        }

        [UnityTest]
        public IEnumerator Straight080_40t_InTolerance_StaysOnTheStraight()
        {
            yield return LoadLab();
            var res = new StraightRunResult[1];
            yield return RunOnce(DrivingLabBootstrap.LabSpawn.Gross40t, res, 0, CsvPath("s080_40t"));
            Assert.IsTrue(m_Body.Coupled, "trailer coupled");
            Assert.That(res[0].TimeTo60, Is.InRange(25.0, 60.0), "0-60 40 t");
            Assert.That(res[0].TimeTo80, Is.InRange(40.0, 95.0), "0-80 40 t");
            AssertCommon(res[0], 35f, 61.2f);
            Assert.Less(m_Body.transform.position.x, DrivingLabLayout.StraightX1 - 50f, "stops on the measurement straight");
            Assert.AreEqual(RunnerT8040t, res[0].TimeTo80, 0.05 * RunnerT8040t, "parity with the .NET runner (0-80)");
            Assert.AreEqual(RunnerStop40t, res[0].StopDistance, 0.10 * RunnerStop40t, "parity with the .NET runner (stop)");
        }

        [UnityTearDown]
        public IEnumerator UnloadLab()
        {
            Time.timeScale = 1f;
            var lab = SceneManager.GetSceneByName(DrivingLabLayout.SceneName);
            if (!lab.IsValid() || !lab.isLoaded) yield break;
            var empty = SceneManager.CreateScene("Empty_" + Time.frameCount);
            SceneManager.SetActiveScene(empty);
            yield return SceneManager.UnloadSceneAsync(lab);
        }
    }
}
