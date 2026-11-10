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
        /// <summary>
        /// The driver's hands hold the wheel at <see cref="Steer"/> (finger on the touch wheel, gyro, key). False = the
        /// wheel is released and self-centres (ADR 0058, <see cref="SteeringColumn"/>).
        /// </summary>
        public bool HandsOn;
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
        /// <summary>One-shot: endurance-brake stalk steps (+1 = one detent more braking, -1 = less).</summary>
        public int RetarderDelta;
        /// <summary>One-shot: arm the fifth-wheel jaw / uncouple.</summary>
        public bool ToggleCoupling;
        /// <summary>One-shot: crank the landing gear down / up.</summary>
        public bool ToggleLandingGear;
        /// <summary>One-shot: downhill speed control (brake cruise) on at the current speed / off.</summary>
        public bool ToggleBrakeCruise;
        /// <summary>One-shot: reversing camera view on / auto.</summary>
        public bool ToggleReverseCamera;
        /// <summary>One-shot: turn-signal stalk / hazard switch request.</summary>
        public TurnSignalRequest TurnSignal;

        public void ClearCommands()
        {
            Selector = SelectorRequest.None;
            ShiftDelta = 0;
            ToggleParkingBrake = false;
            ToggleManual = false;
            RetarderDelta = 0;
            ToggleCoupling = false;
            ToggleLandingGear = false;
            ToggleBrakeCruise = false;
            ToggleReverseCamera = false;
            TurnSignal = TurnSignalRequest.None;
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
        /// <summary>Half lock-to-lock of the cab steering wheel [deg] (road-wheel lock x overall ratio); 0 = unknown.</summary>
        public float HandwheelLockDeg;
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
