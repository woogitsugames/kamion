using System;

namespace Game.Controls
{
    /// <summary>
    /// PC wheel bundle for the gameplay bridge (ADR 0263): the HID wheel input source, the force-feedback model and its
    /// output sink. The sink is <see cref="NullForceFeedbackSink"/> until a native backend exists (proposal in the ADR);
    /// <see cref="StepForceFeedback"/> runs in the fixed physics step with plain numbers from the vehicle model
    /// (Game.Controls does not reference the physics assembly). Allocation-free per step.
    /// </summary>
    public sealed class PcWheel : IDisposable
    {
        public readonly HidWheelDriverInput Input = new HidWheelDriverInput();
        public readonly ForceFeedbackModel ForceFeedback = new ForceFeedbackModel();
        public IForceFeedbackSink Sink = NullForceFeedbackSink.Instance;

        /// <summary>Loads player settings (PlayerPrefs) and the shipped profiles. Call from Awake, not a constructor.</summary>
        public void Load()
        {
            Input.Settings = WheelSettings.Load();
            Input.Profiles = WheelProfiles.LoadDefault();
            ForceFeedback.Settings = Input.Settings.forceFeedback;
            Input.Rebind();
        }

        /// <summary>
        /// One fixed step of force feedback. <paramref name="driving"/> = the player is driving (not paused, no menu, no
        /// autopilot). Loads = normal load of the steered axle's left / right wheel end [N].
        /// </summary>
        public float StepForceFeedback(float dt, bool driving, float forwardSpeed, float aligningTorqueNm, float steeringRatio,
                                       float steeredLoadLeftN, float steeredLoadRightN)
        {
            var inp = new ForceFeedbackInputs
            {
                Active = driving && Input.Enabled && Input.Connected && Input.Settings.forceFeedbackEnabled && Sink.Available,
                ForwardSpeed = forwardSpeed,
                AligningTorqueNm = aligningTorqueNm,
                SteeringRatio = steeringRatio,
                CabPerDeviceDeg = Input.CabPerDeviceDeg,
                DeviceRateDegS = Input.DeviceRateDegS,
                PastSoftLockDeg = Input.PastSoftLockDeg,
                SteeredLoadLeftN = steeredLoadLeftN,
                SteeredLoadRightN = steeredLoadRightN,
            };
            return ForceFeedback.Step(dt, inp, Sink);
        }

        /// <summary>Removes every force now (pause, focus lost, menu, scene exit).</summary>
        public void Stop()
        {
            ForceFeedback.Reset();
            Sink.Stop();
        }

        public void Dispose()
        {
            Stop();
            Input.Dispose();
        }
    }
}
