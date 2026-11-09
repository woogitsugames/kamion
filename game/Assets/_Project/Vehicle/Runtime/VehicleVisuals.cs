using Game.Vehicle.Physics;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Drives the graybox visuals from the solver state: wheel suspension travel, steer angle and spin,
    /// cab body pitch/roll from the cab-suspension output, and the in-cab steering wheel. Values are captured
    /// every fixed step and interpolated in LateUpdate with the same factor Rigidbody interpolation uses, so
    /// wheels and body move together. Wheel order = <see cref="VehicleModel.Wheels"/> order.
    /// </summary>
    [DefaultExecutionOrder(60)]
    public sealed class VehicleVisuals : MonoBehaviour
    {
        public VehicleBody body;
        /// <summary>Suspension + steer pivot per wheel end (local position = wheel centre).</summary>
        public Transform[] wheelPivots = new Transform[0];
        /// <summary>Child of the pivot rotated about local X by the wheel spin.</summary>
        public Transform[] wheelSpinners = new Transform[0];
        /// <summary>Cab body pivot (rotated by cab pitch/roll).</summary>
        public Transform cabPivot;
        /// <summary>Steering wheel; its local +Z is the column axis pointing away from the driver.</summary>
        public Transform steeringWheel;

        Quaternion m_SteeringWheelRest = Quaternion.identity;
        Quaternion m_CabRest = Quaternion.identity;
        float[] m_PrevS, m_CurS, m_SpinDeg, m_PrevSpinDeg;
        Vector3[] m_Hardpoints;
        bool m_Ready;

        void Start() => Setup();

        void Setup()
        {
            if (m_Ready || body == null || !body.Initialized) return;
            var wheels = body.Model.Wheels;
            int n = Mathf.Min(wheels.Length, wheelPivots.Length);
            m_PrevS = new float[n]; m_CurS = new float[n]; m_SpinDeg = new float[n]; m_PrevSpinDeg = new float[n];
            m_Hardpoints = new Vector3[n];
            for (int i = 0; i < n; i++)
            {
                m_Hardpoints[i] = wheels[i].HardpointLocal.ToUnity();
                m_PrevS[i] = m_CurS[i] = (float)wheels[i].S;
            }
            if (steeringWheel != null) m_SteeringWheelRest = steeringWheel.localRotation;
            if (cabPivot != null) m_CabRest = cabPivot.localRotation;
            m_Ready = true;
        }

        void FixedUpdate() => Capture(Time.fixedDeltaTime);

        /// <summary>Records the solver state after a step (also called by script-mode drivers).</summary>
        public void Capture(float dt)
        {
            if (!m_Ready) { Setup(); if (!m_Ready) return; }
            var wheels = body.Model.Wheels;
            for (int i = 0; i < m_CurS.Length; i++)
            {
                m_PrevS[i] = m_CurS[i];
                m_CurS[i] = (float)wheels[i].S;
                m_PrevSpinDeg[i] = m_SpinDeg[i];
                m_SpinDeg[i] = Mathf.Repeat(m_SpinDeg[i] + (float)(wheels[i].Omega * dt) * Mathf.Rad2Deg, 360f);
            }
        }

        void LateUpdate()
        {
            if (!m_Ready) { Setup(); if (!m_Ready) return; }
            var model = body.Model;
            var wheels = model.Wheels;
            float alpha = Time.fixedDeltaTime > 0 ? Mathf.Clamp01((Time.time - Time.fixedTime) / Time.fixedDeltaTime) : 1f;
            for (int i = 0; i < m_CurS.Length; i++)
            {
                float s = Mathf.Lerp(m_PrevS[i], m_CurS[i], alpha);
                var pivot = wheelPivots[i];
                pivot.localPosition = m_Hardpoints[i] - new Vector3(0f, s, 0f);
                pivot.localRotation = Quaternion.Euler(0f, (float)wheels[i].SteerAngle * Mathf.Rad2Deg, 0f);
                if (i < wheelSpinners.Length && wheelSpinners[i] != null)
                {
                    float spin = Mathf.LerpAngle(m_PrevSpinDeg[i], m_SpinDeg[i], alpha);
                    wheelSpinners[i].localRotation = Quaternion.Euler(spin, 0f, 0f);
                }
            }
            if (cabPivot != null)
            {
                // Pitch > 0 = nose down (rotation about +X); roll > 0 = left side down (rotation about +Z).
                cabPivot.localRotation = m_CabRest * Quaternion.Euler((float)model.Cab.Pitch * Mathf.Rad2Deg, 0f, (float)model.Cab.Roll * Mathf.Rad2Deg);
            }
            if (steeringWheel != null)
            {
                // Positive handwheel angle = right turn = clockwise as seen by the driver = negative about +Z.
                steeringWheel.localRotation = m_SteeringWheelRest * Quaternion.AngleAxis(-(float)model.Steering.HandwheelDeg, Vector3.forward);
            }
        }
    }
}
