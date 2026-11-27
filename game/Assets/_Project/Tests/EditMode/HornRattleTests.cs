using Game.Controls;
using Game.Core;
using Game.Gameplay;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    public class HornRattleTests
    {
        [Test]
        public void Horn_StableBinding_AndRebindPersistence()
        {
            using var actions = new DrivingActions();
            const string action = DrivingActionCatalog.Horn;
            Assert.AreEqual("<Keyboard>/k", actions.EffectivePath(DrivingActionCatalog.KeyboardMap, action, 0));
            Assert.AreEqual("<Gamepad>/rightStickPress", actions.EffectivePath(DrivingActionCatalog.GamepadMap, action, 0));
            actions.SetOverride(DrivingActionCatalog.KeyboardMap, action, 0, "<Keyboard>/j");
            string stored = actions.SaveOverrides();
            using var restored = new DrivingActions();
            Assert.IsTrue(restored.LoadOverrides(stored));
            Assert.AreEqual("<Keyboard>/j", restored.EffectivePath(DrivingActionCatalog.KeyboardMap, action, 0));
        }

        [Test]
        public void AudioCues_HudAndInputFlags_AreIndependent()
        {
            bool savedInput = AudioCues.HornHeld;
            bool savedHud = AudioCues.HornHudHeld;
            try
            {
                AudioCues.HornHeld = false;
                AudioCues.HornHudHeld = false;
                Assert.IsFalse(AudioCues.AnyHornHeld);
                AudioCues.HornHudHeld = true;
                Assert.IsTrue(AudioCues.AnyHornHeld);
                AudioCues.HornHeld = false; // polling input must not clear HUD hold
                Assert.IsTrue(AudioCues.AnyHornHeld);
                AudioCues.HornHudHeld = false;
                AudioCues.HornHeld = true;
                Assert.IsTrue(AudioCues.AnyHornHeld);
            }
            finally
            {
                AudioCues.HornHeld = savedInput;
                AudioCues.HornHudHeld = savedHud;
            }
        }

        [Test]
        public void TrailerRattle_UncoupledOrSmoothStationary_NeverTriggers()
        {
            var gate = new TrailerRattleGate();
            var rng = new System.Random(101);
            for (int i = 0; i < 200; i++)
            {
                Assert.IsFalse(gate.Step(0.01f, i * 0.01, coupled: false, speedKmh: 40f, bodyVertAccelMs2: 8f,
                    maxWheelCompRateMs: 1.2f, signedPeakCompRateMs: 1.2f, kingpinLoadN: 120000f, trailerMassKg: 32000f,
                    roughSurfaceWeight: 1f, sinceCoupled: 10.0, rng, out _, out _, out _));
            }
            Assert.AreEqual(0f, gate.Energy, 1e-6f);

            for (int i = 0; i < 200; i++)
            {
                Assert.IsFalse(gate.Step(0.01f, i * 0.01, coupled: true, speedKmh: 0f, bodyVertAccelMs2: 0f,
                    maxWheelCompRateMs: 0f, signedPeakCompRateMs: 0f, kingpinLoadN: 110000f, trailerMassKg: 32000f,
                    roughSurfaceWeight: 0f, sinceCoupled: 10.0, rng, out _, out _, out _));
            }
            Assert.AreEqual(0f, gate.Energy, 1e-6f);
        }

        [Test]
        public void TrailerRattle_VerticalAxleOrFifthWheelBump_TriggersAndDecays()
        {
            var gate = new TrailerRattleGate();
            var rng = new System.Random(42);
            int hits = 0, kingpinHits = 0;
            for (int i = 0; i < 300; i++)
            {
                float rate = (i % 12 < 6) ? 0.65f : -0.65f;
                float kp = 110000f + ((i % 4 < 2) ? 45000f : -45000f);
                if (gate.Step(0.01f, (i + 1) * 0.01, coupled: true, speedKmh: 38f, bodyVertAccelMs2: 4.5f,
                    maxWheelCompRateMs: 0.7f, signedPeakCompRateMs: rate, kingpinLoadN: kp, trailerMassKg: 32000f,
                    roughSurfaceWeight: 0f, sinceCoupled: 15.0, rng, out var kind, out float gain, out float pitch))
                {
                    hits++;
                    if (kind == TrailerRattleKind.Kingpin) kingpinHits++;
                    Assert.That(gain, Is.InRange(0.15f, 1.0f));
                    Assert.That(pitch, Is.InRange(0.85f, 1.15f));
                }
            }
            Assert.GreaterOrEqual(hits, 6, "vertical bumps on trailer axles & fifth wheel trigger metallic rattle hits");
            Assert.GreaterOrEqual(kingpinHits, 1, "fifth-wheel load jolts trigger kingpin slack hits");
            Assert.Greater(gate.Energy, 0.25f);

            // Smooth asphalt afterwards: energy decays below trigger threshold.
            for (int i = 300; i < 600; i++)
            {
                gate.Step(0.01f, (i + 1) * 0.01, coupled: true, speedKmh: 50f, bodyVertAccelMs2: 0.1f,
                    maxWheelCompRateMs: 0.01f, signedPeakCompRateMs: 0.01f, kingpinLoadN: 110000f, trailerMassKg: 32000f,
                    roughSurfaceWeight: 0f, sinceCoupled: 20.0, rng, out _, out _, out _);
            }
            Assert.Less(gate.Energy, 0.05f);
        }

        [Test]
        public void TrailerRattle_RoughSurfaceNeedsSpeed()
        {
            var gate = new TrailerRattleGate();
            var rng = new System.Random(77);
            int stillHits = 0;
            for (int i = 0; i < 200; i++)
            {
                if (gate.Step(0.01f, (i + 1) * 0.01, coupled: true, speedKmh: 0.5f, bodyVertAccelMs2: 0f,
                    maxWheelCompRateMs: 0f, signedPeakCompRateMs: 0f, kingpinLoadN: 110000f, trailerMassKg: 32000f,
                    roughSurfaceWeight: 1f, sinceCoupled: 10.0, rng, out _, out _, out _))
                    stillHits++;
            }
            Assert.AreEqual(0, stillHits);

            int cobbleHits = 0;
            for (int i = 200; i < 500; i++)
            {
                if (gate.Step(0.01f, (i + 1) * 0.01, coupled: true, speedKmh: 28f, bodyVertAccelMs2: 0.2f,
                    maxWheelCompRateMs: 0.02f, signedPeakCompRateMs: 0.02f, kingpinLoadN: 110000f, trailerMassKg: 32000f,
                    roughSurfaceWeight: 1f, sinceCoupled: 15.0, rng, out _, out _, out _))
                    cobbleHits++;
            }
            Assert.GreaterOrEqual(cobbleHits, 3, "cobbles/gravel at speed excite trailer rattle");
        }

        [Test]
        public void DesktopHud_HornButton_SitsCleanlyLeftOfBottomBlock()
        {
            foreach (var px in new[] { new Vector2(1920, 1080), new Vector2(2560, 1080), new Vector2(5120, 1440), new Vector2(1080, 1920) })
            {
                HudScaleModel.Solve(new HudScaleInput { SafePx = new Rect(0, 0, px.x, px.y), Dpi = 96f, Desktop = true, UserScale = 1f }, out var sc);
                var s = new DesktopHudInput
                {
                    Width = sc.SizeUnits.x, Height = sc.SizeUnits.y, Strip = true, Extended = true, DevToggle = true,
                    MirrorLeft = true, MirrorRight = true, MirrorAspect = 0.55f,
                };
                DesktopHudLayout.Solve(s, out var r);
                Assert.IsTrue(r.ShowHorn, px.ToString());
                Assert.AreEqual(DesktopHudLayout.HornSize, r.Horn.size);
                Assert.AreEqual(r.Strip.xMin - DesktopHudLayout.ToggleGap, r.Horn.xMax, 0.01f);
                Assert.IsFalse(DesktopHudLayout.Intersects(r.Horn, r.ClearView));
                Assert.IsFalse(DesktopHudLayout.Intersects(r.Horn, r.Strip));
                Assert.IsFalse(DesktopHudLayout.Intersects(r.Horn, r.Telltales));
                if (r.ShowNav) Assert.IsFalse(DesktopHudLayout.Intersects(r.Horn, r.Nav));
            }
        }
    }
}
