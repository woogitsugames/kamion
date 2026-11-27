using System;
using UnityEngine.InputSystem;

namespace Game.Controls
{
    /// <summary>Cached actions of one driving map (no lookups by name in the driving loop).</summary>
    public sealed class DrivingActionSet
    {
        public readonly InputActionMap Map;
        public readonly InputAction CycleWipers;
        public readonly InputAction Steer, Throttle, Brake, Clutch, ShiftUp, ShiftDown, SelectDrive, SelectNeutral, SelectReverse,
            ToggleManual, ParkingBrake, RetarderMore, RetarderLess, Couple, LandingGear, BrakeCruise, ReverseCamera,
            IndicatorLeft, IndicatorRight, Hazard, Horn, CycleCamera, MirrorInsets, HudDetail, Look;

        public DrivingActionSet(InputActionMap map)
        {
            Map = map;
            InputAction A(string n) => map.FindAction(n, throwIfNotFound: true);
            Steer = A(DrivingActionCatalog.Steer); Throttle = A(DrivingActionCatalog.Throttle); Brake = A(DrivingActionCatalog.Brake);
            Clutch = A(DrivingActionCatalog.Clutch);
            ShiftUp = A(DrivingActionCatalog.ShiftUp); ShiftDown = A(DrivingActionCatalog.ShiftDown);
            SelectDrive = A(DrivingActionCatalog.SelectDrive); SelectNeutral = A(DrivingActionCatalog.SelectNeutral); SelectReverse = A(DrivingActionCatalog.SelectReverse);
            ToggleManual = A(DrivingActionCatalog.ToggleManual); ParkingBrake = A(DrivingActionCatalog.ParkingBrake);
            RetarderMore = A(DrivingActionCatalog.RetarderMore); RetarderLess = A(DrivingActionCatalog.RetarderLess);
            Couple = A(DrivingActionCatalog.Couple); LandingGear = A(DrivingActionCatalog.LandingGear);
            BrakeCruise = A(DrivingActionCatalog.BrakeCruise); ReverseCamera = A(DrivingActionCatalog.ReverseCamera);
            IndicatorLeft = A(DrivingActionCatalog.IndicatorLeft); IndicatorRight = A(DrivingActionCatalog.IndicatorRight);
            Hazard = A(DrivingActionCatalog.Hazard); Horn = A(DrivingActionCatalog.Horn);
            CycleCamera = A(DrivingActionCatalog.CycleCamera); MirrorInsets = A(DrivingActionCatalog.MirrorInsets); Look = A(DrivingActionCatalog.Look);
            HudDetail = A(DrivingActionCatalog.HudDetail);
            CycleWipers = A(DrivingActionCatalog.CycleWipers);
        }

        /// <summary>One-shot commands common to every device (allocation-free; call once per rendered frame).</summary>
        public void ReadCommands(ref DriverIntent intent, ref ViewCommands view)
        {
            if (SelectDrive.WasPressedThisFrame()) intent.Selector = SelectorRequest.Drive;
            if (SelectNeutral.WasPressedThisFrame()) intent.Selector = SelectorRequest.Neutral;
            if (SelectReverse.WasPressedThisFrame()) intent.Selector = SelectorRequest.Reverse;
            if (ShiftUp.WasPressedThisFrame()) intent.ShiftDelta += 1;
            if (ShiftDown.WasPressedThisFrame()) intent.ShiftDelta -= 1;
            if (ParkingBrake.WasPressedThisFrame()) intent.ToggleParkingBrake = true;
            if (ToggleManual.WasPressedThisFrame()) intent.ToggleManual = true;
            if (RetarderMore.WasPressedThisFrame()) intent.RetarderDelta += 1;
            if (RetarderLess.WasPressedThisFrame()) intent.RetarderDelta -= 1;
            if (Couple.WasPressedThisFrame()) intent.ToggleCoupling = true;
            if (LandingGear.WasPressedThisFrame()) intent.ToggleLandingGear = true;
            if (BrakeCruise.WasPressedThisFrame()) intent.ToggleBrakeCruise = true;
            if (ReverseCamera.WasPressedThisFrame()) intent.ToggleReverseCamera = true;
            if (IndicatorLeft.WasPressedThisFrame()) intent.TurnSignal = TurnSignalRequest.Left;
            if (IndicatorRight.WasPressedThisFrame()) intent.TurnSignal = TurnSignalRequest.Right;
            if (Hazard.WasPressedThisFrame()) intent.TurnSignal = TurnSignalRequest.Hazard;
            view.Horn |= Horn.IsPressed();
            view.CycleCamera |= CycleCamera.WasPressedThisFrame();
            view.ToggleMirrorInsets |= MirrorInsets.WasPressedThisFrame();
            view.ToggleHudDetail |= HudDetail.WasPressedThisFrame();
            view.CycleWipers |= CycleWipers.WasPressedThisFrame();
        }
    }

    /// <summary>
    /// The driving action asset (ADR 0264), built in code from <see cref="DrivingActionCatalog"/> so it needs no
    /// imported asset and no edit of the template <c>InputSystem_Actions.inputactions</c>. Two maps with the same action
    /// names: <see cref="DrivingActionCatalog.KeyboardMap"/> and <see cref="DrivingActionCatalog.GamepadMap"/>.
    /// Binding overrides (rebinding) are kept as the Input System JSON and persisted by <see cref="InputBindingsStore"/>.
    /// The string-only methods let EditMode tests round-trip overrides without referencing Unity.InputSystem.
    /// </summary>
    public sealed class DrivingActions : IDisposable
    {
        public InputActionAsset Asset { get; private set; }
        public DrivingActionSet Keyboard { get; private set; }
        public DrivingActionSet Gamepad { get; private set; }

        public DrivingActions()
        {
            // From JSON (not AddAction/AddBinding) so every binding has the stable id of DrivingActionCatalog.StableId:
            // saved overrides are matched by binding id and must survive a restart (ADR 0264).
            Asset = InputActionAsset.FromJson(DrivingActionCatalog.BuildAssetJson());
            Asset.name = "DrivingActions";
            Keyboard = new DrivingActionSet(Asset.FindActionMap(DrivingActionCatalog.KeyboardMap, true));
            Gamepad = new DrivingActionSet(Asset.FindActionMap(DrivingActionCatalog.GamepadMap, true));
        }

        public void Enable() => Asset.Enable();
        public void Disable() => Asset.Disable();

        public void Dispose()
        {
            if (Asset == null) return;
            Asset.Disable();
            if (UnityEngine.Application.isPlaying) UnityEngine.Object.Destroy(Asset); else UnityEngine.Object.DestroyImmediate(Asset);
            Asset = null;
        }

        // ------------------------------------------------------------------ overrides (string API)

        /// <summary>Current overrides as the Input System JSON ("" when none).</summary>
        public string SaveOverrides() => HasOverrides() ? Asset.SaveBindingOverridesAsJson() : "";

        /// <summary>True when any binding has an override (an empty override = binding removed counts too).</summary>
        public bool HasOverrides()
        {
            foreach (var map in Asset.actionMaps)
            {
                var b = map.bindings;
                for (int i = 0; i < b.Count; i++) if (b[i].overridePath != null) return true;
            }
            return false;
        }

        /// <summary>Replaces all overrides by a saved document (empty = defaults). Bad documents are ignored (defaults kept).</summary>
        public bool LoadOverrides(string json)
        {
            Asset.RemoveAllBindingOverrides();
            if (string.IsNullOrWhiteSpace(json)) return true;
            try { Asset.LoadBindingOverridesFromJson(json); return true; }
            catch (Exception e)
            {
                UnityEngine.Debug.LogWarning("[CONTROLS] binding overrides ignored: " + e.Message);
                Asset.RemoveAllBindingOverrides();
                return false;
            }
        }

        public void ResetToDefaults() => Asset.RemoveAllBindingOverrides();

        /// <summary>Overrides one binding's path (tests and scripted setups; the settings screen uses interactive rebinding).</summary>
        public void SetOverride(string map, string action, int bindingIndex, string path)
        {
            var a = Asset.FindActionMap(map, true).FindAction(action, true);
            a.ApplyBindingOverride(bindingIndex, path);
        }

        /// <summary>Effective control path of one binding (override if any, else default).</summary>
        public string EffectivePath(string map, string action, int bindingIndex)
        {
            var a = Asset.FindActionMap(map, true).FindAction(action, true);
            return a.bindings[bindingIndex].effectivePath;
        }

        /// <summary>
        /// Name of another action in the same map already bound to <paramref name="path"/> (rebinding conflict
        /// warning), or null. Composite parent bindings are skipped.
        /// </summary>
        public static string FindConflict(InputActionMap map, string path, InputAction except, int exceptIndex)
        {
            if (string.IsNullOrEmpty(path)) return null;
            foreach (var a in map.actions)
            {
                var b = a.bindings;
                for (int i = 0; i < b.Count; i++)
                {
                    if (b[i].isComposite || (a == except && i == exceptIndex)) continue;
                    if (string.Equals(b[i].effectivePath, path, StringComparison.OrdinalIgnoreCase)) return a.name;
                }
            }
            return null;
        }

        /// <summary>
        /// Starts interactive rebinding of one binding (settings screen). The map is disabled while waiting. Escape is
        /// reserved for the menu and never bound; Backspace or the pad's start button cancel; 10 s without input cancels.
        /// The caller saves the overrides in <paramref name="done"/> (true = changed).
        /// </summary>
        public InputActionRebindingExtensions.RebindingOperation StartRebind(InputAction action, int bindingIndex, bool gamepad, Action<bool> done)
        {
            var map = action.actionMap;
            map.Disable();
            var op = action.PerformInteractiveRebinding(bindingIndex)
                .WithControlsExcluding("<Keyboard>/escape")
                .WithCancelingThrough(gamepad ? "<Gamepad>/start" : "<Keyboard>/backspace")
                .WithTimeout(10f)
                .OnMatchWaitForAnother(0.1f);
            op = op.WithControlsHavingToMatchPath(gamepad ? "<Gamepad>" : "<Keyboard>");   // keys also fit Axis actions (Key is a Button is an Axis)
            op.OnComplete(o => { o.Dispose(); map.Enable(); done?.Invoke(true); })
              .OnCancel(o => { o.Dispose(); map.Enable(); done?.Invoke(false); });
            return op.Start();
        }
    }
}
