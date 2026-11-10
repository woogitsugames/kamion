using Game.Controls;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>Turn-signal stalk (request, flash rate, self-cancel, hazard, input plumbing) and the cluster instrument models.</summary>
    public class TurnSignalAndInstrumentTests
    {
        const float Dt = 0.01f;

        static int CountFlashes(TurnSignal t, float seconds, float steer = 0f)
        {
            int rises = 0;
            for (float x = 0; x < seconds; x += Dt) if (t.Step(Dt, steer) > 0) rises++;
            return rises;
        }

        [Test]
        public void Request_LeftRightHazard_Toggle()
        {
            var t = new TurnSignal();
            t.Request(TurnSignalRequest.Left); Assert.AreEqual(-1, t.Lever);
            t.Request(TurnSignalRequest.Right); Assert.AreEqual(+1, t.Lever);   // opposite side switches over
            t.Request(TurnSignalRequest.Right); Assert.AreEqual(0, t.Lever);    // same side again cancels
            t.Request(TurnSignalRequest.Hazard); Assert.AreEqual(2, t.Lever);
            t.Request(TurnSignalRequest.Left); Assert.AreEqual(2, t.Lever, "hazard overrides the stalk");
            t.Request(TurnSignalRequest.Hazard); Assert.AreEqual(0, t.Lever);
        }

        [Test]
        public void Flasher_IsOnePointFiveHz_WithinR48Band()
        {
            var t = new TurnSignal();
            t.Request(TurnSignalRequest.Right);
            int flashes = CountFlashes(t, 10f);
            Assert.AreEqual(15, flashes, 1, "1.5 Hz = 90 flashes/min = 15 in 10 s");
            Assert.That(flashes * 6, Is.InRange(60, 120), "UN ECE R48: 90 +/- 30 flashes per minute");
        }

        [Test]
        public void Flasher_FirstFlashIsLitImmediately_AndStopsDarkOnCancel()
        {
            var t = new TurnSignal();
            t.Request(TurnSignalRequest.Left);
            Assert.AreEqual(1, t.Step(Dt, 0f), "relay closes at once");
            Assert.IsTrue(t.LeftLit); Assert.IsFalse(t.RightLit);
            t.Request(TurnSignalRequest.Left);
            Assert.AreEqual(-1, t.Step(Dt, 0f), "relay opens when switched off while lit");
            Assert.IsFalse(t.Lit);
        }

        [Test]
        public void Flasher_RateIsClampedToR48Band()
        {
            var t = new TurnSignal { FlashHz = 5f };
            Assert.AreEqual(TurnSignal.MaxHz, t.FlashHz);
            t.FlashHz = 0.1f;
            Assert.AreEqual(TurnSignal.MinHz, t.FlashHz);
        }

        [Test]
        public void Hazard_LightsBothSides()
        {
            var t = new TurnSignal();
            t.Request(TurnSignalRequest.Hazard);
            t.Step(Dt, 0f);
            Assert.IsTrue(t.LeftLit && t.RightLit);
        }

        [Test]
        public void SelfCancel_AfterTurnAndReturn_Right()
        {
            var t = new TurnSignal();
            t.Request(TurnSignalRequest.Right);
            for (float x = 0; x < 2f; x += Dt) t.Step(Dt, 0.1f);          // small angle: below the arm threshold, stays on
            Assert.AreEqual(1, t.Lever);
            for (float x = 0; x < 2f; x += Dt) t.Step(Dt, 0.6f);          // turn right
            Assert.IsTrue(t.Armed); Assert.AreEqual(1, t.Lever);
            for (float x = 0; x < 2f; x += Dt) t.Step(Dt, 0.03f);         // wheel returns to centre
            Assert.AreEqual(0, t.Lever, "cancels after the steering wheel returns");
            Assert.IsFalse(t.Lit);
        }

        [Test]
        public void SelfCancel_Left_UsesNegativeAngles()
        {
            var t = new TurnSignal();
            t.Request(TurnSignalRequest.Left);
            t.Step(Dt, +0.6f);                                             // steering the wrong way does not arm
            Assert.IsFalse(t.Armed);
            t.Step(Dt, -0.5f);
            Assert.IsTrue(t.Armed);
            t.Step(Dt, 0.0f);
            Assert.AreEqual(0, t.Lever);
        }

        [Test]
        public void Hazard_NeverSelfCancels()
        {
            var t = new TurnSignal();
            t.Request(TurnSignalRequest.Hazard);
            for (float x = 0; x < 1f; x += Dt) t.Step(Dt, 0.7f);
            for (float x = 0; x < 1f; x += Dt) t.Step(Dt, 0f);
            Assert.AreEqual(2, t.Lever);
        }

        [Test]
        public void Cancel_ClearsEverything()
        {
            var t = new TurnSignal();
            t.Request(TurnSignalRequest.Hazard); t.Step(Dt, 0f);
            t.Cancel();
            Assert.AreEqual(0, t.Lever); Assert.IsFalse(t.Lit);
        }

        [Test]
        public void TouchButton_QueuesOneShotRequest_AndMixerForwardsIt()
        {
            var touch = new TouchControls();
            var mixer = new DriverInputMixer();
            mixer.Add(touch);
            touch.RequestTurnSignal(TurnSignalRequest.Right);
            var fb = new VehicleFeedback();
            Assert.AreEqual(TurnSignalRequest.Right, mixer.Sample(0.016f, fb).TurnSignal);
            Assert.AreEqual(TurnSignalRequest.None, mixer.Sample(0.016f, fb).TurnSignal, "one-shot: consumed after one sample");
        }

        // ------------------------------------------------------------ instruments

        [Test]
        public void FuelFlow_IdleFloor_AndPartLoadPenalty()
        {
            Assert.AreEqual(FuelFlowModel.IdleLitresPerHour, FuelFlowModel.LitresPerHour(0, 0), 1e-9);
            Assert.AreEqual(FuelFlowModel.IdleLitresPerHour, FuelFlowModel.LitresPerHour(3, 0.05), 1e-9, "tiny power: idle floor");
            Assert.Greater(FuelFlowModel.Bsfc(0.1), FuelFlowModel.Bsfc(0.85), "part load burns more per kWh");
            Assert.AreEqual(FuelFlowModel.BestBsfcGPerKWh, FuelFlowModel.Bsfc(1.0), 1e-9);
            // 300 kW at 85 % load ~ 198 * 1.01 g/kWh -> ~ 72 l/h
            double lph = FuelFlowModel.LitresPerHour(300, 0.85);
            Assert.That(lph, Is.InRange(65.0, 80.0));
        }

        [Test]
        public void FuelFlow_MoreWorkMoreFuel()
        {
            Assert.Greater(FuelFlowModel.LitresPerHour(200, 0.6), FuelFlowModel.LitresPerHour(100, 0.3));
        }

        [Test]
        public void Coolant_WarmsUpFirstOrder_AndRegulatesAtThermostat()
        {
            double T = 20.0;
            double prev = T;
            for (int i = 0; i < 20 * 60; i++)   // 20 min idle, 1 s steps
            {
                T = CoolantModel.Step(T, 1.0, true, 0.05, 15.0);
                Assert.GreaterOrEqual(T, prev - 1e-9, "monotone warm-up");
                prev = T;
            }
            Assert.That(T, Is.InRange(CoolantModel.RegulatedIdleC - 2, CoolantModel.RegulatedIdleC + 4), "regulated near the idle target after 20 min");
        }

        [Test]
        public void Coolant_ColdStartTakesMinutes_NotSeconds()
        {
            double T = 20.0;
            for (int i = 0; i < 60; i++) T = CoolantModel.Step(T, 1.0, true, 0.05, 20.0);   // 1 min
            Assert.Less(T, 40.0);
            for (int i = 0; i < 6 * 60; i++) T = CoolantModel.Step(T, 1.0, true, 0.05, 20.0);   // 7 min total
            Assert.Less(T, CoolantModel.ThermostatC);
        }

        [Test]
        public void Coolant_LoadWarmsFasterAndRunsHotter()
        {
            double idle = 20, load = 20;
            for (int i = 0; i < 300; i++) { idle = CoolantModel.Step(idle, 1, true, 0.0, 20); load = CoolantModel.Step(load, 1, true, 1.0, 20); }
            Assert.Greater(load, idle);
            for (int i = 0; i < 1800; i++) load = CoolantModel.Step(load, 1, true, 1.0, 20);
            Assert.That(load, Is.InRange(CoolantModel.RegulatedIdleC + 6, CoolantModel.RegulatedIdleC + CoolantModel.RegulatedSpanC + 2));
            Assert.Less(load, CoolantModel.WarnC, "full load stays below the overheat telltale");
        }

        [Test]
        public void Coolant_EngineOff_CoolsSlowlyTowardsAmbient()
        {
            double T = 88;
            for (int i = 0; i < 600; i++) T = CoolantModel.Step(T, 1, false, 0, 10);   // 10 min
            Assert.That(T, Is.InRange(70.0, 85.0));
            for (int i = 0; i < 6 * 3600; i++) T = CoolantModel.Step(T, 1, false, 0, 10);
            Assert.That(T, Is.InRange(10.0, 15.0));
        }

        [Test]
        public void Coolant_NonPositiveDt_IsNoOp()
        {
            Assert.AreEqual(50.0, CoolantModel.Step(50.0, 0, true, 1, 20));
            Assert.AreEqual(50.0, CoolantModel.Step(50.0, -1, true, 1, 20));
        }

        [Test]
        public void GameClock_AnchorsToSun_ThenFollowsGameTime()
        {
            var c = new GameClock();
            Assert.AreEqual(14 * 60 + 32, c.Advance(0.0, 14 * 60 + 32));
            for (int i = 0; i < 125; i++) c.Advance(1.0, 14 * 60 + 32);        // static sun, 125 s
            Assert.AreEqual(14 * 60 + 34, (int)c.Minutes, "ticks on with game time (+2 min 5 s)");
            int m = c.Advance(0.0, 9 * 60);                                    // sun jumped (other lighting preset): re-anchor
            Assert.AreEqual(9 * 60, m);
        }

        [Test]
        public void GameClock_WrapsAtMidnight()
        {
            var c = new GameClock();
            c.Advance(0, 23 * 60 + 59);
            for (int i = 0; i < 90; i++) c.Advance(1.0, 23 * 60 + 59);
            Assert.AreEqual(0, (int)c.Minutes / 60, "00:xx after midnight");
        }
    }
}
