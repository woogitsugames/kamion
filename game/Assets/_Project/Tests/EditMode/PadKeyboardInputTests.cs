using System;
using System.Collections.Generic;
using System.IO;
using Game.Controls;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0264: gamepad and keyboard shaping (dead zone, curve, speed-dependent amplitude and rate, keyboard ramps),
    /// steering direction, the action catalogue, the versioned bindings file (round trip, migration, corrupt input)
    /// and the binding-override round trip through the Input System asset.
    /// </summary>
    public class PadKeyboardInputTests
    {
        const float Dt = 1f / 60f;
        static float Kmh(float kmh) => kmh / 3.6f;
        static PadUserTuning Tuning(PadKeyboardFeel f) => PadUserTuning.From(f);

        // ---------------------------------------------------------------- dead zone + curve

        [Test]
        public void DeadZone_ZeroInside_ContinuousAtEdge_SaturatesOutside_Symmetric()
        {
            Assert.AreEqual(0f, PadSteeringMath.DeadZone(0.1f, 0.12f, 0.03f));
            Assert.AreEqual(0f, PadSteeringMath.DeadZone(-0.12f, 0.12f, 0.03f));
            Assert.Less(PadSteeringMath.DeadZone(0.121f, 0.12f, 0.03f), 0.002f, "no jump at the inner edge");
            Assert.AreEqual(1f, PadSteeringMath.DeadZone(0.97f, 0.12f, 0.03f), 1e-6f, "outer saturation");
            Assert.AreEqual(1f, PadSteeringMath.DeadZone(1.3f, 0.12f, 0.03f), 1e-6f);
            for (float x = 0f; x <= 1f; x += 0.01f)
                Assert.AreEqual(-PadSteeringMath.DeadZone(x, 0.12f, 0.03f), PadSteeringMath.DeadZone(-x, 0.12f, 0.03f), 1e-6f);
            Assert.AreEqual(0f, PadSteeringMath.DeadZone(float.NaN, 0.1f, 0f));
        }

        [Test]
        public void Expo_Monotonic_EndpointsFixed_FinerNearCentre()
        {
            Assert.AreEqual(0f, PadSteeringMath.Expo(0f, 1.8f));
            Assert.AreEqual(1f, PadSteeringMath.Expo(1f, 1.8f), 1e-6f);
            Assert.AreEqual(-1f, PadSteeringMath.Expo(-1f, 1.8f), 1e-6f);
            Assert.AreEqual(0.5f, PadSteeringMath.Expo(0.5f, 1f), 1e-6f, "exponent 1 = linear");
            Assert.Less(PadSteeringMath.Expo(0.5f, 1.8f), 0.5f, "fine control near centre");
            float prev = -2f;
            for (float x = -1f; x <= 1f; x += 0.01f)
            {
                float y = PadSteeringMath.Expo(x, 2.5f);
                Assert.GreaterOrEqual(y, prev);
                prev = y;
            }
            Assert.AreEqual(PadSteeringMath.Expo(0.5f, 4f), PadSteeringMath.Expo(0.5f, 9f), 1e-6f, "exponent clamped to 4");
        }

        [Test]
        public void Shape_IsDeadZoneThenCurve()
        {
            float s = PadSteeringMath.Shape(0.6f, 0.1f, 0f, 2f);
            float expect = Mathf.Pow((0.6f - 0.1f) / 0.9f, 2f);
            Assert.AreEqual(expect, s, 1e-5f);
        }

        // ---------------------------------------------------------------- speed-dependent amplitude + rate

        [Test]
        public void SpeedAmplitude_FullLockWhenManoeuvring_ShrinksWithSpeed_RespectsLatAccelAndFloor()
        {
            var f = PadKeyboardFeel.Defaults();
            Assert.AreEqual(1f, f.Amplitude(0f));
            Assert.AreEqual(1f, f.Amplitude(Kmh(5f)), 1e-6f, "walking pace: full lock");
            float prev = 1f;
            for (float kmh = 5f; kmh <= 120f; kmh += 5f)
            {
                float a = f.Amplitude(Kmh(kmh));
                Assert.LessOrEqual(a, prev + 1e-6f, "never grows with speed");
                Assert.GreaterOrEqual(a, f.minAmplitude - 1e-6f, "evasive floor");
                prev = a;
                // Full stick at this speed: kinematic lateral acceleration v^2 tan(delta) / L never above the limit
                // (unless the floor is what limits it).
                float v = Kmh(kmh);
                float delta = a * f.maxRoadWheelDeg * Mathf.Deg2Rad;
                float latAcc = v * v * Mathf.Tan(delta) / f.wheelbaseM;
                if (a > f.minAmplitude + 1e-4f && a < 1f - 1e-4f) Assert.AreEqual(f.maxLatAccelMs2, latAcc, 0.05f, $"{kmh} km/h");
            }
            Assert.Greater(f.Amplitude(Kmh(80f), 2f), f.Amplitude(Kmh(80f), 1f), "player scale widens the limit");
            Assert.AreEqual(1f, PadSteeringMath.SpeedAmplitude(float.NaN, 3.7f, 4f, 40f, 0.05f), "NaN speed: no limit, no NaN");
        }

        [Test]
        public void PadRateLimit_DependsOnSpeed_StepNeverFasterThanTable()
        {
            var f = PadKeyboardFeel.Defaults();
            var t = Tuning(f);
            foreach (float kmh in new[] { 0f, 30f, 80f })
            {
                var p = new PadSteerFilter();
                float maxStep = 0f, prev = 0f;
                for (int i = 0; i < 600; i++)
                {
                    p.Step(f, t, 1f, Kmh(kmh), prev, Dt);
                    maxStep = Mathf.Max(maxStep, Mathf.Abs(p.Steer - prev));
                    prev = p.Steer;
                }
                Assert.LessOrEqual(maxStep, f.PadRate(kmh) * Dt + 1e-6f, $"rate at {kmh} km/h");
                Assert.AreEqual(f.Amplitude(Kmh(kmh)), p.Steer, 1e-4f, $"reaches the speed amplitude at {kmh} km/h");
            }
            Assert.Greater(f.PadRate(0f), f.PadRate(80f), "slower at speed");
        }

        [Test]
        public void PadRelease_ToPhysics_HandsOff_RegrabContinuesFromWheel()
        {
            var f = PadKeyboardFeel.Defaults();
            Assert.IsTrue(f.padReleaseToPhysics, "default: self-centring from the aligning torque (ADR 0058)");
            var t = Tuning(f);
            var p = new PadSteerFilter();
            for (int i = 0; i < 60; i++) p.Step(f, t, 1f, Kmh(10f), p.Steer, Dt);
            Assert.IsTrue(p.Active);
            p.Step(f, t, 0.05f, Kmh(10f), 0.3f, Dt);   // inside the dead zone = let go
            Assert.IsFalse(p.Active, "released: no steering authority, the column self-centres");
            p.Step(f, t, 0.5f, Kmh(10f), 0.2f, Dt);    // take the wheel again where the physics left it (0.2)
            Assert.IsTrue(p.Active);
            Assert.AreEqual(0.2f, p.Steer, f.PadRate(10f) * Dt + 1e-5f, "no jump on re-grab");
        }

        [Test]
        public void PadRelease_RampMode_ReturnsToCentreAtReturnRate()
        {
            var f = PadKeyboardFeel.Defaults();
            f.padReleaseToPhysics = false;
            var t = Tuning(f);
            var p = new PadSteerFilter();
            for (int i = 0; i < 120; i++) p.Step(f, t, 1f, 0f, 0f, Dt);
            Assert.AreEqual(1f, p.Steer, 1e-4f);
            int steps = 0;
            while (p.Active && steps < 1000) { p.Step(f, t, 0f, 0f, 0f, Dt); steps++; }
            Assert.AreEqual(0f, p.Steer, 1e-3f);
            Assert.AreEqual(1f / Mathf.Max(f.padReturnRatePerS, f.PadRate(0f)), steps * Dt, 3f * Dt, "return time");
        }

        // ---------------------------------------------------------------- direction in every mode

        [Test]
        public void SteeringDirection_RightIsPositive_PadAndKeyboard()
        {
            var f = PadKeyboardFeel.Defaults();
            var t = Tuning(f);
            var p = new PadSteerFilter();
            for (int i = 0; i < 10; i++) p.Step(f, t, +0.8f, Kmh(20f), p.Steer, Dt);
            Assert.Greater(p.Steer, 0f, "stick right = steer right");
            p.Reset();
            for (int i = 0; i < 10; i++) p.Step(f, t, -0.8f, Kmh(20f), p.Steer, Dt);
            Assert.Less(p.Steer, 0f, "stick left = steer left");

            var k = new KeyboardAxisRamp();
            for (int i = 0; i < 10; i++) k.Step(f, t, +1, false, false, Kmh(20f), Dt);
            Assert.Greater(k.Steer, 0f, "right key = steer right");
            k.Reset();
            for (int i = 0; i < 10; i++) k.Step(f, t, -1, false, false, Kmh(20f), Dt);
            Assert.Less(k.Steer, 0f, "left key = steer left");
            k.Reset();
            for (int i = 0; i < 10; i++) k.Step(f, t, +1, false, false, Kmh(-8f), Dt);
            Assert.Greater(k.Steer, 0f, "reversing: same handwheel direction (the physics turns the truck)");
        }

        // ---------------------------------------------------------------- keyboard ramps

        [Test]
        public void KeyboardRamp_PedalsRiseAndFallAtTheirRates()
        {
            var f = PadKeyboardFeel.Defaults();
            var t = Tuning(f);
            var k = new KeyboardAxisRamp();
            int n = 0;
            while (k.Throttle < 1f && n < 1000) { k.Step(f, t, 0, true, false, 0f, Dt); n++; }
            Assert.AreEqual(1f / f.keyThrottleRise, n * Dt, 2f * Dt, "throttle rise time");
            k.Step(f, t, 0, false, false, 0f, Dt);
            Assert.AreEqual(1f - f.keyRelease * Dt, k.Throttle, 1e-5f, "release rate");
            n = 0;
            while (k.Brake < 1f && n < 1000) { k.Step(f, t, 0, false, true, 0f, Dt); n++; }
            Assert.AreEqual(1f / f.keyBrakeRise, n * Dt, 2f * Dt, "brake rise time");
        }

        [Test]
        public void KeyboardRamp_SteerLimitedBySpeed_ReturnsWhenReleased_ScaleApplies()
        {
            var f = PadKeyboardFeel.Defaults();
            var t = Tuning(f);
            var k = new KeyboardAxisRamp();
            for (int i = 0; i < 600; i++) k.Step(f, t, +1, false, false, Kmh(80f), Dt);
            Assert.AreEqual(f.Amplitude(Kmh(80f)), k.Steer, 1e-4f, "held key at 80 km/h stops at the speed amplitude");
            Assert.Less(k.Steer, 0.2f);
            k.Reset();
            for (int i = 0; i < 600; i++) k.Step(f, t, +1, false, false, 0f, Dt);
            Assert.AreEqual(1f, k.Steer, 1e-4f, "full lock at standstill");
            int n = 0;
            while (k.Steer > 0f && n < 1000) { k.Step(f, t, 0, false, false, 0f, Dt); n++; }
            Assert.AreEqual(1f / Mathf.Max(f.keyReturnRatePerS, f.KeyRate(0f)), n * Dt, 2f * Dt, "return to centre");

            var fast = t; fast.KeySteerScale = 2f;
            var a = new KeyboardAxisRamp(); var b = new KeyboardAxisRamp();
            a.Step(f, t, +1, false, false, 0f, Dt); b.Step(f, fast, +1, false, false, 0f, Dt);
            Assert.AreEqual(2f * a.Steer, b.Steer, 1e-5f, "player steering-speed scale");
        }

        [Test]
        public void KeyboardRamp_Reversal_GoesThroughCentreAtReturnRate()
        {
            Assert.AreEqual(0.5f - 2f * 0.1f, PadSteeringMath.RampSteer(0.5f, -1, 1f, 1f, 2f, 0.1f), 1e-6f);
            Assert.AreEqual(0.5f + 1f * 0.1f, PadSteeringMath.RampSteer(0.5f, +1, 1f, 1f, 2f, 0.1f), 1e-6f);
        }

#if UNITY_5_3_OR_NEWER   // needs the Unity runtime (profiler recorder / Resources / Input System)
        [Test]
        public void Steps_AllocateNothing()
        {
            var f = PadKeyboardFeel.Defaults();
            var t = Tuning(f);
            var p = new PadSteerFilter();
            var k = new KeyboardAxisRamp();
            void Run()
            {
                for (int i = 0; i < 500; i++)
                {
                    p.Step(f, t, Mathf.Sin(i * 0.05f), i * 0.05f, p.Steer, Dt);
                    k.Step(f, t, (i / 60) % 3 - 1, i % 2 == 0, i % 3 == 0, i * 0.05f, Dt);
                }
            }
            GcAllocCounter.AssertZero(Run, Run, message: "pad / keyboard shaping in the driving loop");
        }

        // ---------------------------------------------------------------- feel data

        [Test]
        public void FeelJson_MatchesCSharpDefaults_AndSanitizeRepairsBrokenTables()
        {
            var shipped = PadKeyboardFeel.FromJson(Resources.Load<TextAsset>(PadKeyboardFeel.ResourcePath)?.text);
            Assert.AreEqual(JsonUtility.ToJson(PadKeyboardFeel.Defaults()), JsonUtility.ToJson(shipped), "pad_keyboard_feel.json = C# defaults");

            var broken = PadKeyboardFeel.FromJson("{\"rateSpeedsKmh\":[0,50],\"padRatePerS\":[1],\"stickExponent\":99}");
            var d = PadKeyboardFeel.Defaults();
            Assert.AreEqual(d.rateSpeedsKmh.Length, broken.rateSpeedsKmh.Length, "mismatched table replaced");
            Assert.AreEqual(4f, broken.stickExponent, "clamped");
            Assert.AreEqual(PadKeyboardFeel.FromJson("not json").stickDeadZone, d.stickDeadZone, "corrupt = defaults");
        }

#endif

        // ---------------------------------------------------------------- catalogue

        [Test]
        public void Catalogue_NamesUnique_DefaultsWithoutDuplicates_KeyboardKeepsOldKeys()
        {
            var names = new HashSet<string>();
            var kb = new HashSet<string>();
            var pad = new HashSet<string>();
            foreach (var d in DrivingActionCatalog.All)
            {
                Assert.IsTrue(names.Add(d.Name), "unique action " + d.Name);
                foreach (var p in d.Keyboard) Assert.IsTrue(kb.Add(p), "keyboard default used twice: " + p);
                foreach (var p in d.Gamepad) Assert.IsTrue(pad.Add(p), "pad default used twice: " + p);
            }
            foreach (var pair in DrivingActionCatalog.KeyboardSteerPairs) { Assert.IsTrue(kb.Add(pair[0])); Assert.IsTrue(kb.Add(pair[1])); }
            Assert.IsFalse(kb.Contains("<Keyboard>/escape"), "Escape is the menu / back key");
            Assert.IsFalse(pad.Contains("<Gamepad>/start"), "start is left to the menu");

            // Same keys as the Stage 1/2 KeyboardDriverInput (owner muscle memory, ADR 0261 merge).
            Assert.Contains("<Keyboard>/w", DrivingActionCatalog.Find(DrivingActionCatalog.Throttle).Keyboard);
            Assert.Contains("<Keyboard>/s", DrivingActionCatalog.Find(DrivingActionCatalog.Brake).Keyboard);
            Assert.Contains("<Keyboard>/space", DrivingActionCatalog.Find(DrivingActionCatalog.ParkingBrake).Keyboard);
            Assert.Contains("<Keyboard>/e", DrivingActionCatalog.Find(DrivingActionCatalog.ShiftUp).Keyboard);
            Assert.Contains("<Keyboard>/q", DrivingActionCatalog.Find(DrivingActionCatalog.ShiftDown).Keyboard);
            Assert.AreEqual("<Keyboard>/a", DrivingActionCatalog.KeyboardSteerPairs[0][0], "left first (negative = left)");

            // Pad: triggers are the pedals, left stick is the wheel.
            Assert.Contains("<Gamepad>/rightTrigger", DrivingActionCatalog.Find(DrivingActionCatalog.Throttle).Gamepad);
            Assert.Contains("<Gamepad>/leftTrigger", DrivingActionCatalog.Find(DrivingActionCatalog.Brake).Gamepad);
            Assert.Contains("<Gamepad>/leftStick/x", DrivingActionCatalog.Find(DrivingActionCatalog.Steer).Gamepad);
        }

        [Test]
        public void AssetJson_StableIds_UniqueAndRepeatable()
        {
            string a = DrivingActionCatalog.BuildAssetJson(), b = DrivingActionCatalog.BuildAssetJson();
            Assert.AreEqual(a, b, "same JSON every run (binding overrides are matched by id)");
            Assert.AreEqual(DrivingActionCatalog.StableId("DrivingKeyboard/Throttle/0"), DrivingActionCatalog.StableId("DrivingKeyboard/Throttle/0"));
            var ids = new HashSet<string>();
            int at = 0;
            while ((at = a.IndexOf("\"id\":\"", at, StringComparison.Ordinal)) >= 0)
            {
                at += 6;
                string id = a.Substring(at, 36);
                Assert.IsTrue(Guid.TryParse(id, out _), id);
                Assert.IsTrue(ids.Add(id), "duplicate id " + id);
            }
            Assert.Greater(ids.Count, 2 * DrivingActionCatalog.All.Length, "maps + actions + bindings");
            StringAssert.Contains("\"path\":\"<Gamepad>/rightTrigger\"", a);
            StringAssert.Contains("\"name\":\"negative\",", a);
        }

        [Test]
        public void GamepadLabels_GenericPositions_NoMakerGlyphs()
        {
            var banned = new[] { "Xbox", "PlayStation", "PS", "Cross", "Circle", "Square", "Triangle", "Nintendo" };
            foreach (var d in DrivingActionCatalog.All)
                foreach (var p in d.Gamepad)
                {
                    string l = DrivingActionCatalog.GamepadControlLabel(p);
                    Assert.IsFalse(l.StartsWith("<"), "translated: " + p);
                    foreach (var b in banned) StringAssert.DoesNotContain(b, l, p);
                    Assert.AreNotEqual("A", l); Assert.AreNotEqual("B", l); Assert.AreNotEqual("X", l); Assert.AreNotEqual("Y", l);
                }
            Assert.AreEqual("—", DrivingActionCatalog.GamepadControlLabel(""));
        }

        // ---------------------------------------------------------------- bindings file

        const string SampleOverrides = "{\"bindings\":[{\"action\":\"DrivingKeyboard/Throttle\",\"id\":\"1f2e\",\"path\":\"<Keyboard>/i\",\"interactions\":\"\",\"processors\":\"\"}]}";

        [Test]
        public void Store_RoundTrip_KeepsOverridesAndTuning()
        {
            var f = PadKeyboardFeel.Defaults();
            var s = InputBindingsStore.Defaults(f);
            s.OverridesJson = SampleOverrides + "\n\t\"ąż\\u00e9\"";
            s.Tuning.StickDeadZone = 0.2f; s.Tuning.StickExponent = 2.4f; s.Tuning.SpeedLimitScale = 1.5f; s.Tuning.KeySteerScale = 0.7f;
            var r = InputBindingsStore.FromJson(s.ToJson(), f);
            Assert.AreEqual(InputBindingsStore.CurrentSchema, r.Schema);
            Assert.AreEqual(s.OverridesJson, r.OverridesJson);
            Assert.AreEqual(0.2f, r.Tuning.StickDeadZone, 1e-6f);
            Assert.AreEqual(2.4f, r.Tuning.StickExponent, 1e-6f);
            Assert.AreEqual(1.5f, r.Tuning.SpeedLimitScale, 1e-6f);
            Assert.AreEqual(0.7f, r.Tuning.KeySteerScale, 1e-6f);
        }

        [Test]
        public void Store_MigratesV0_BareOverrides_AndRejectsCorrupt_AndClamps()
        {
            var f = PadKeyboardFeel.Defaults();
            var v0 = InputBindingsStore.FromJson(SampleOverrides, f);
            Assert.AreEqual(1, v0.Schema, "v0 -> v1");
            Assert.AreEqual(SampleOverrides, v0.OverridesJson, "overrides kept verbatim");
            Assert.AreEqual(f.stickDeadZone, v0.Tuning.StickDeadZone, "default tuning");

            foreach (var bad in new[] { "", "   ", "garbage", "{\"schema\":1,\"overrides\":\"unterminated", "{\"schema\":", "[1,2]", "{\"foo\":1}" })
            {
                var d = InputBindingsStore.FromJson(bad, f);
                Assert.AreEqual("", d.OverridesJson, "corrupt -> defaults: " + bad);
                Assert.AreEqual(f.stickExponent, d.Tuning.StickExponent);
            }

            var c = InputBindingsStore.FromJson("{\"schema\":1,\"stickDeadZone\":5,\"stickExponent\":-3,\"speedLimitScale\":1e9,\"keySteerScale\":0,\"overrides\":\"\"}", f);
            Assert.AreEqual(PadUserTuning.DeadZoneMax, c.Tuning.StickDeadZone);
            Assert.AreEqual(PadUserTuning.ExponentMin, c.Tuning.StickExponent);
            Assert.AreEqual(PadUserTuning.SpeedLimitMax, c.Tuning.SpeedLimitScale);
            Assert.AreEqual(PadUserTuning.KeySpeedMin, c.Tuning.KeySteerScale);

            var future = InputBindingsStore.FromJson("{\"schema\":7,\"newThing\":{\"a\":[1,\"]}\"]},\"stickExponent\":2,\"overrides\":\"x\"}", f);
            Assert.AreEqual(InputBindingsStore.CurrentSchema, future.Schema, "newer file: known fields kept");
            Assert.AreEqual(2f, future.Tuning.StickExponent, 1e-6f);
            Assert.AreEqual("x", future.OverridesJson);
        }

        [Test]
        public void Store_RenameActions_ExactQuotedMatchOnly()
        {
            var map = new[,] { { "DrivingKeyboard/Accelerate", "DrivingKeyboard/Throttle" } };
            string doc = "{\"bindings\":[{\"action\":\"DrivingKeyboard/Accelerate\"},{\"action\":\"DrivingKeyboard/AccelerateMore\"}]}";
            string r = InputBindingsStore.RenameActions(doc, map);
            StringAssert.Contains("\"action\":\"DrivingKeyboard/Throttle\"", r);
            StringAssert.Contains("\"action\":\"DrivingKeyboard/AccelerateMore\"", r, "prefix of another name untouched");
        }

        [Test]
        public void Store_File_AtomicRoundTrip_MissingFileGivesDefaults()
        {
            var f = PadKeyboardFeel.Defaults();
            string dir = Path.Combine(Path.GetTempPath(), "kamion-0264-" + Guid.NewGuid().ToString("N"));
            string path = Path.Combine(dir, InputBindingsStore.FileName);
            try
            {
                Assert.AreEqual("", InputBindingsStore.LoadFromFile(path, f).OverridesJson, "missing file");
                var s = InputBindingsStore.Defaults(f);
                s.OverridesJson = SampleOverrides;
                s.SaveToFile(path);
                s.Tuning.StickExponent = 2.2f;
                s.SaveToFile(path);   // replace an existing file
                Assert.IsFalse(File.Exists(path + ".tmp"), "temp file consumed");
                var r = InputBindingsStore.LoadFromFile(path, f);
                Assert.AreEqual(SampleOverrides, r.OverridesJson);
                Assert.AreEqual(2.2f, r.Tuning.StickExponent, 1e-6f);
            }
            finally { if (Directory.Exists(dir)) Directory.Delete(dir, true); }
        }

        // ---------------------------------------------------------------- Input System overrides round trip

#if UNITY_5_3_OR_NEWER   // needs the Unity runtime (profiler recorder / Resources / Input System)
        [Test]
        public void Actions_OverridesRoundTrip_ThroughStore_AndReset()
        {
            var f = PadKeyboardFeel.Defaults();
            var a = new DrivingActions();
            var b = new DrivingActions();
            try
            {
                const string K = DrivingActionCatalog.KeyboardMap, G = DrivingActionCatalog.GamepadMap;
                Assert.AreEqual("<Keyboard>/w", a.EffectivePath(K, DrivingActionCatalog.Throttle, 0));
                Assert.AreEqual("<Gamepad>/rightTrigger", a.EffectivePath(G, DrivingActionCatalog.Throttle, 0));
                Assert.AreEqual("", a.SaveOverrides(), "no overrides at start");

                a.SetOverride(K, DrivingActionCatalog.Throttle, 0, "<Keyboard>/i");
                a.SetOverride(G, DrivingActionCatalog.ShiftUp, 0, "<Gamepad>/buttonSouth");
                var store = InputBindingsStore.Defaults(f);
                store.OverridesJson = a.SaveOverrides();
                var loaded = InputBindingsStore.FromJson(store.ToJson(), f);

                Assert.IsTrue(b.LoadOverrides(loaded.OverridesJson));
                Assert.AreEqual("<Keyboard>/i", b.EffectivePath(K, DrivingActionCatalog.Throttle, 0));
                Assert.AreEqual("<Gamepad>/buttonSouth", b.EffectivePath(G, DrivingActionCatalog.ShiftUp, 0));
                Assert.AreEqual("<Keyboard>/upArrow", b.EffectivePath(K, DrivingActionCatalog.Throttle, 1), "other bindings untouched");

                b.ResetToDefaults();
                Assert.AreEqual("<Keyboard>/w", b.EffectivePath(K, DrivingActionCatalog.Throttle, 0));
                Assert.IsFalse(b.LoadOverrides("{not json"), "bad document ignored");
                Assert.AreEqual("<Keyboard>/w", b.EffectivePath(K, DrivingActionCatalog.Throttle, 0), "defaults kept");
            }
            finally { a.Dispose(); b.Dispose(); }
        }
#endif

    }
}
