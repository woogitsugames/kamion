using System;
using System.Collections.Generic;
using System.IO;
using Game.Core;
using Game.Telemetry;
using Game.Vehicle.Physics;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Per-fixed-step vehicle telemetry CSV (docs/04 §4) written to
    /// persistentDataPath/telemetry/drive-&lt;timestamp&gt;.csv. Column names match the .NET physics runner
    /// (tools/physics-runner/Sim/Telemetry.cs) so tools/telemetry/plot.py works on Unity recordings too.
    /// Recording is a toggle; rows are buffered and formatted without per-step allocations.
    /// </summary>
    [DefaultExecutionOrder(100)]
    public sealed class VehicleTelemetryRecorder : MonoBehaviour
    {
        public VehicleBody body;
        CsvRecorder m_Csv;

        public bool IsRecording => m_Csv != null;
        public string CurrentFile => m_Csv?.FilePath;
        public long RowsWritten => m_Csv != null ? m_Csv.RowsWritten : 0;
        public static string TelemetryDirectory => Path.Combine(Application.persistentDataPath, "telemetry");

        public void Toggle() { if (IsRecording) StopRecording(); else StartRecording(); }

        public void StartRecording()
        {
            if (IsRecording || body == null || !body.Initialized) return;
            var m = body.Model;
            var cols = new List<string>
            {
                "t", "x", "y", "z", "speed_kmh", "v_fwd", "a_long", "a_lat", "yaw_rate_dps", "heading_deg", "pitch_deg", "roll_deg",
                "throttle_in", "brake_in", "steer_in", "parking_in", "throttle_eff", "brake_demand", "parking_state", "hill_hold",
                "rpm", "gear", "amt_state", "clutch_cmd", "engine_torque", "clutch_torque", "boost", "asr_factor",
                "steer_angle_deg", "handwheel_deg", "aligning_torque", "cab_pitch_deg", "cab_roll_deg",
            };
            foreach (var w in m.Wheels)
            {
                string n = w.Name;
                cols.AddRange(new[] { n + "_fz", n + "_fx", n + "_fy", n + "_slip", n + "_alpha_deg", n + "_comp", n + "_omega",
                    n + "_brake_t", n + "_abs", n + "_drive_t", n + "_tire_defl", n + "_contact", n + "_surface" });
            }
            cols.AddRange(new[] { "axle0_load", "axle1_load", "step_us", "frame_ms" });
            var build = BuildInfo.Current;
            string file = Path.Combine(TelemetryDirectory, "drive-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".csv");
            string trailer = (body.Model.Def.id + "," + build.ShortLabel).Replace("\n", "");
            m_Csv = new CsvRecorder(file, cols.ToArray(), "config_id,commit", trailer, null, 128);
            Debug.Log($"[TELEMETRY] recording → {file}");
        }

        public void StopRecording()
        {
            if (m_Csv == null) return;
            string f = m_Csv.FilePath;
            long rows = m_Csv.RowsWritten;
            m_Csv.Dispose();
            m_Csv = null;
            Debug.Log($"[TELEMETRY] stopped, {rows} rows (+buffer) → {f}");
        }

        void FixedUpdate()
        {
            if (m_Csv == null || body == null || !body.Initialized) return;
            Record();
        }

        void Record()
        {
            var m = body.Model;
            var rb = body.Body;
            var r = m_Csv.Row;
            int i = 0;
            Vector3 p = rb.position;
            Vector3 fwd = rb.rotation * Vector3.forward, right = rb.rotation * Vector3.right;
            var inp = body.Input;
            r[i++] = m.Time; r[i++] = p.x; r[i++] = p.y; r[i++] = p.z;
            r[i++] = rb.linearVelocity.magnitude * 3.6; r[i++] = m.SpeedForward; r[i++] = m.LocalAcceleration.z; r[i++] = m.LocalAcceleration.x;
            r[i++] = m.YawRate * MathUtil.Rad2Deg; r[i++] = Mathf.Atan2(fwd.x, fwd.z) * Mathf.Rad2Deg;
            r[i++] = Mathf.Asin(Mathf.Clamp(fwd.y, -1f, 1f)) * Mathf.Rad2Deg; r[i++] = Mathf.Asin(Mathf.Clamp(right.y, -1f, 1f)) * Mathf.Rad2Deg;
            r[i++] = inp.Throttle; r[i++] = inp.Brake; r[i++] = inp.Steer; r[i++] = inp.ParkingBrake ? 1 : 0;
            r[i++] = m.ThrottleDemand; r[i++] = m.BrakeDemand; r[i++] = m.ParkingBrakeState; r[i++] = m.HillHoldActive ? 1 : 0;
            r[i++] = m.Engine.Rpm; r[i++] = m.Amt.Gear; r[i++] = (int)m.Amt.State; r[i++] = m.Amt.ClutchCommand;
            r[i++] = m.EngineTorque; r[i++] = m.ClutchTorque; r[i++] = m.Engine.Boost; r[i++] = m.AsrFactor;
            r[i++] = m.Steering.Angle * MathUtil.Rad2Deg; r[i++] = m.Steering.HandwheelDeg; r[i++] = m.AligningTorqueTotal;
            r[i++] = m.Cab.Pitch * MathUtil.Rad2Deg; r[i++] = m.Cab.Roll * MathUtil.Rad2Deg;
            double a0 = 0, a1 = 0;
            var wheels = m.Wheels;
            for (int k = 0; k < wheels.Length; k++)
            {
                var w = wheels[k];
                r[i++] = w.Fz; r[i++] = w.Fx; r[i++] = w.Fy; r[i++] = w.SlipRatio; r[i++] = w.SlipAngle * MathUtil.Rad2Deg;
                r[i++] = w.Compression; r[i++] = w.Omega; r[i++] = w.BrakeTorque; r[i++] = w.AbsFactor; r[i++] = w.DriveTorque;
                r[i++] = w.TireDeflection; r[i++] = w.Contact ? 1 : 0; r[i++] = w.SurfaceId;
                if (w.AxleIndex == 0) a0 += w.Fz; else a1 += w.Fz;
            }
            r[i++] = a0; r[i++] = a1; r[i++] = body.LastStepMicros; r[i++] = Time.unscaledDeltaTime * 1000.0;
            m_Csv.CommitRow();
        }

        void OnApplicationPause(bool paused) { if (paused) m_Csv?.Flush(); }
        void OnDestroy() => StopRecording();
    }
}
