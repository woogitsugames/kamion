using UnityEngine;

namespace Game.Controls
{
    public enum SelectorRequest : byte { None = 0, Drive = 1, Neutral = 2, Reverse = 3 }

    /// <summary>
    /// What a driver input source wants this frame. Continuous axes plus one-shot commands.
    /// Sign convention (all modes): <see cref="Steer"/> &gt; 0 = turn right (matches the physics core).
    /// </summary>
    public struct DriverIntent
    {
        /// <summary>Normalised steering command -1..1, positive = right.</summary>
        public float Steer;
        /// <summary>True when this source currently has steering authority (finger on wheel, key held, gyro on...).</summary>
        public bool SteerActive;
        /// <summary>Accelerator 0..1.</summary>
        public float Throttle;
        /// <summary>Service brake 0..1.</summary>
        public float Brake;
        /// <summary>One-shot: selector change request.</summary>
        public SelectorRequest Selector;
        /// <summary>One-shot: manual shift request (+1 up, -1 down).</summary>
        public int ShiftDelta;
        /// <summary>One-shot: toggle the spring parking brake.</summary>
        public bool ToggleParkingBrake;
        /// <summary>One-shot: toggle AMT automatic / manual mode.</summary>
        public bool ToggleManual;

        public void ClearCommands()
        {
            Selector = SelectorRequest.None;
            ShiftDelta = 0;
            ToggleParkingBrake = false;
            ToggleManual = false;
        }
    }

    /// <summary>Vehicle state fed back to input sources (self-centring, autopilot). Unity world frame.</summary>
    public struct VehicleFeedback
    {
        /// <summary>Signed speed along the vehicle's forward axis [m/s].</summary>
        public float ForwardSpeed;
        /// <summary>Total aligning torque of the steered wheels [N m] (estimate from the tire model).</summary>
        public float AligningTorque;
        /// <summary>Current road-wheel angle / maximum, -1..1.</summary>
        public float RoadWheelAngleNormalized;
        public Vector3 Position;
        public Vector3 Forward;
    }

    /// <summary>
    /// A source of driver commands (keyboard, touch wheel + pedals, gyro, autopilot; gamepad/wheel later).
    /// Sample is called once per rendered frame from the gameplay bridge; the source writes into its own intent,
    /// the <see cref="DriverInputMixer"/> combines them.
    /// </summary>
    public interface IDriverInput
    {
        string Name { get; }
        bool Enabled { get; set; }
        void Sample(float dt, in VehicleFeedback feedback, ref DriverIntent intent);
    }
}
