using System;

namespace Game.Controls
{
    /// <summary>Gameplay actions a wheel button can carry (ADR 0263). Names are stable: they are stored in profiles.</summary>
    public enum WheelAction : byte
    {
        None = 0,
        ParkingBrake, RetarderMore, RetarderLess, SignalLeft, SignalRight, Hazard,
        Drive, Neutral, Reverse, ToggleManual, BrakeCruise, ReverseCamera, Coupling, LandingGear,
        ShiftUp, ShiftDown, RangeToggle,
    }

    /// <summary>One analogue control of a wheel/pedal device: an Input System control path relative to the device + calibration.</summary>
    [Serializable]
    public sealed class WheelAxisBinding
    {
        /// <summary>Control path relative to the device (e.g. "stick/x", "z", "rz"); empty = not present.</summary>
        public string control = "";
        public AxisCalibration calibration = new AxisCalibration();
        /// <summary>false = <see cref="calibration"/> is a guess: pedals use <see cref="AutoPedal"/> (rest = first reading),
        /// the wheel uses the first reading as centre, until the wizard stores a calibration.</summary>
        public bool calibrated;
        /// <summary>Smallest plausible raw span of the full travel for the uncalibrated fallback (Unity reports normalised
        /// HID axes as 0..1 or -1..1 depending on the descriptor → 1 is the safe minimum). UNVERIFIED per device.</summary>
        public float expectedSpan = 1f;
        public bool Present => !string.IsNullOrEmpty(control);
    }

    /// <summary>A button → action mapping (control path relative to the device).</summary>
    [Serializable]
    public sealed class WheelButtonBinding
    {
        public string action = "";
        public string control = "";

        /// <summary>Parsed <see cref="action"/> (load time only; unknown names give <see cref="WheelAction.None"/>).</summary>
        public WheelAction Parse() => Enum.TryParse(action, true, out WheelAction a) ? a : WheelAction.None;
    }

    /// <summary>
    /// Device profile as data (ADR 0263; <c>Resources/Controls/wheel_profiles.json</c>). Vendor/product ids and product
    /// names are only used for matching and live here and in docs/compat/wheels.md — never in the UI (no third-party
    /// brands in the game). Every control path is UNVERIFIED until checked on the device (status field) — the
    /// calibration wizard (<see cref="AxisAutoDetect"/>) and player overrides fix a wrong guess without a new build.
    /// </summary>
    [Serializable]
    public sealed class WheelDeviceProfile
    {
        public string id = "generic";
        /// <summary>Documentation only (what the profile is for); never shown in the UI.</summary>
        public string note = "";
        /// <summary>Source / verification status: UNVERIFIED, SOURCED (ids from a cited source), VERIFIED (checked on the device).</summary>
        public string status = "UNVERIFIED";
        /// <summary>USB vendor id (0 = any).</summary>
        public int vendorId;
        /// <summary>USB product ids accepted (empty = any product of the vendor).</summary>
        public int[] productIds = new int[0];
        /// <summary>Case-insensitive substring of the HID product string (fallback match when ids are unknown).</summary>
        public string productContains = "";
        /// <summary>Lock-to-lock rotation the steering axis spans in the driver's current mode [deg]. WORKING_VALUE until read
        /// from the device (some drivers let the user lower it; the player setting must then match).</summary>
        public float deviceRangeDeg = 900f;
        /// <summary>Default in-game rotation range [deg] (270-900).</summary>
        public float defaultRangeDeg = 540f;

        public WheelAxisBinding steer = new WheelAxisBinding();
        public WheelAxisBinding throttle = new WheelAxisBinding();
        public WheelAxisBinding brake = new WheelAxisBinding();
        public WheelAxisBinding clutch = new WheelAxisBinding();
        /// <summary>Throttle and brake on one axis (legacy driver modes); uses <see cref="combined"/> instead of throttle/brake.</summary>
        public bool combinedPedals;
        public WheelAxisBinding combined = new WheelAxisBinding();

        /// <summary>H-shifter forward gates in order (1, 2, 3 ...); empty = no shifter.</summary>
        public string[] shifterGates = new string[0];
        public string shifterReverse = "";
        /// <summary>Range (low/high) switch held = high range; empty = use the <see cref="WheelAction.RangeToggle"/> button.</summary>
        public string shifterRange = "";
        public string paddleUp = "";
        public string paddleDown = "";
        public WheelButtonBinding[] buttons = new WheelButtonBinding[0];

        /// <summary>The device has a force-feedback motor (backend availability is decided at runtime).</summary>
        public bool forceFeedback;

        public bool MatchesIds(int vid, int pid)
        {
            if (vendorId == 0 || vid != vendorId) return false;
            if (productIds == null || productIds.Length == 0) return true;
            for (int i = 0; i < productIds.Length; i++) if (productIds[i] == pid) return true;
            return false;
        }

        public bool MatchesName(string product)
            => !string.IsNullOrEmpty(productContains) && !string.IsNullOrEmpty(product)
               && product.IndexOf(productContains, StringComparison.OrdinalIgnoreCase) >= 0;
    }

    /// <summary>All shipped profiles (JSON root).</summary>
    [Serializable]
    public sealed class WheelProfileSet
    {
        public const int CurrentSchema = 1;
        public int schema = CurrentSchema;
        public WheelDeviceProfile[] profiles = new WheelDeviceProfile[0];

        /// <summary>
        /// Best profile for a device (connect time only): vendor+product id, then product-name substring (with a matching
        /// vendor if both are known), then the profile with id "generic", else null.
        /// </summary>
        public WheelDeviceProfile Find(int vendorId, int productId, string product)
        {
            if (profiles == null) return null;
            for (int i = 0; i < profiles.Length; i++)
                if (profiles[i] != null && profiles[i].productIds != null && profiles[i].productIds.Length > 0 && profiles[i].MatchesIds(vendorId, productId)) return profiles[i];
            for (int i = 0; i < profiles.Length; i++)
            {
                var p = profiles[i];
                if (p == null || !p.MatchesName(product)) continue;
                if (p.vendorId == 0 || vendorId == 0 || p.vendorId == vendorId) return p;
            }
            for (int i = 0; i < profiles.Length; i++)
            {
                var p = profiles[i];   // vendor-only profile: no product ids and no product name
                if (p != null && string.IsNullOrEmpty(p.productContains) && (p.productIds == null || p.productIds.Length == 0) && p.MatchesIds(vendorId, productId)) return p;
            }
            return ById("generic");
        }

        public WheelDeviceProfile ById(string id)
        {
            if (profiles == null || string.IsNullOrEmpty(id)) return null;
            for (int i = 0; i < profiles.Length; i++)
                if (profiles[i] != null && string.Equals(profiles[i].id, id, StringComparison.OrdinalIgnoreCase)) return profiles[i];
            return null;
        }

        /// <summary>Clamps every calibration (corrupt or hand-edited data).</summary>
        public void Sanitize()
        {
            if (profiles == null) { profiles = new WheelDeviceProfile[0]; return; }
            for (int i = 0; i < profiles.Length; i++)
            {
                var p = profiles[i];
                if (p == null) continue;
                p.deviceRangeDeg = WheelAxisMath.Clamp(float.IsNaN(p.deviceRangeDeg) ? 900f : p.deviceRangeDeg, 90f, 2520f);
                p.defaultRangeDeg = WheelSteeringMap.ClampRange(p.defaultRangeDeg, p.deviceRangeDeg);
                Fix(p.steer); Fix(p.throttle); Fix(p.brake); Fix(p.clutch); Fix(p.combined);
                if (p.shifterGates == null) p.shifterGates = new string[0];
                if (p.buttons == null) p.buttons = new WheelButtonBinding[0];
                if (p.productIds == null) p.productIds = new int[0];
            }
        }

        static void Fix(WheelAxisBinding b)
        {
            if (b == null) return;
            if (b.calibration == null) b.calibration = new AxisCalibration();
            b.calibration.Sanitize();
        }
    }

    /// <summary>
    /// Calibration wizard helper: which of several axes the player moved (largest change from a baseline). Pure,
    /// allocation-free; the caller owns the arrays.
    /// </summary>
    public static class AxisAutoDetect
    {
        /// <summary>Index of the axis with the largest |current - baseline| above <paramref name="minChange"/>, else -1.</summary>
        public static int MostMoved(float[] baseline, float[] current, int count, float minChange)
        {
            if (baseline == null || current == null) return -1;
            int n = Math.Min(count, Math.Min(baseline.Length, current.Length));
            int best = -1; float bestD = minChange;
            for (int i = 0; i < n; i++)
            {
                float d = Math.Abs(current[i] - baseline[i]);
                if (d > bestD) { bestD = d; best = i; }
            }
            return best;
        }
    }
}
