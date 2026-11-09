using Game.Vehicle.Physics;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Drives the graybox trailer from the solver: wheel suspension travel and spin, landing-gear inner legs
    /// (crank position <see cref="TrailerModel.LandingGearFootY"/>). Captured every fixed step and interpolated
    /// in LateUpdate with the Rigidbody interpolation factor (same scheme as <see cref="VehicleVisuals"/>).
    /// </summary>
    [DefaultExecutionOrder(61)]
    public sealed class TrailerVisuals : MonoBehaviour
    {
        public TrailerBody body;
        public Transform[] wheelPivots = new Transform[0];
        public Transform[] wheelSpinners = new Transform[0];
        /// <summary>Inner (moving) leg tubes; local origin at the foot, so localPosition.y = foot height.</summary>
        public Transform[] legs = new Transform[0];

        float[] m_PrevS, m_CurS, m_SpinDeg, m_PrevSpinDeg;
        Vector3[] m_Hardpoints;
        float m_PrevFoot, m_CurFoot;
        TrailerModel m_Model;

        void Setup()
        {
            if (body == null || !body.Initialized) return;
            m_Model = body.Model;
            var wheels = m_Model.Wheels;
            int n = Mathf.Min(wheels.Length, wheelPivots.Length);
            m_PrevS = new float[n]; m_CurS = new float[n]; m_SpinDeg = new float[n]; m_PrevSpinDeg = new float[n];
            m_Hardpoints = new Vector3[n];
            for (int i = 0; i < n; i++)
            {
                m_Hardpoints[i] = wheels[i].HardpointLocal.ToUnity();
                m_PrevS[i] = m_CurS[i] = (float)wheels[i].S;
            }
            m_PrevFoot = m_CurFoot = (float)m_Model.LandingGearFootY;
        }

        bool Ready()
        {
            // The trailer model is rebuilt when the load case changes: re-bind.
            if (body == null || !body.Initialized) return false;
            if (!ReferenceEquals(m_Model, body.Model)) Setup();
            return m_Model != null;
        }

        void FixedUpdate() => Capture(Time.fixedDeltaTime);

        public void Capture(float dt)
        {
            if (!Ready()) return;
            var wheels = m_Model.Wheels;
            for (int i = 0; i < m_CurS.Length; i++)
            {
                m_PrevS[i] = m_CurS[i];
                m_CurS[i] = (float)wheels[i].S;
                m_PrevSpinDeg[i] = m_SpinDeg[i];
                m_SpinDeg[i] = Mathf.Repeat(m_SpinDeg[i] + (float)(wheels[i].Omega * dt) * Mathf.Rad2Deg, 360f);
            }
            m_PrevFoot = m_CurFoot;
            m_CurFoot = (float)m_Model.LandingGearFootY;
        }

        void LateUpdate()
        {
            if (!Ready()) return;
            float alpha = Time.fixedDeltaTime > 0 ? Mathf.Clamp01((Time.time - Time.fixedTime) / Time.fixedDeltaTime) : 1f;
            for (int i = 0; i < m_CurS.Length; i++)
            {
                wheelPivots[i].localPosition = m_Hardpoints[i] - new Vector3(0f, Mathf.Lerp(m_PrevS[i], m_CurS[i], alpha), 0f);
                if (i < wheelSpinners.Length && wheelSpinners[i] != null)
                    wheelSpinners[i].localRotation = Quaternion.Euler(Mathf.LerpAngle(m_PrevSpinDeg[i], m_SpinDeg[i], alpha), 0f, 0f);
            }
            float foot = Mathf.Lerp(m_PrevFoot, m_CurFoot, alpha);
            for (int k = 0; k < legs.Length; k++)
            {
                if (legs[k] == null) continue;
                var p = legs[k].localPosition;
                p.y = foot;
                legs[k].localPosition = p;
            }
        }
    }
}
