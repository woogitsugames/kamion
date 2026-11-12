using Game.Controls;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Which screen orientations the game allows for a window size (ADR 0135). Pure function, unit-tested.
    /// - Elongated screens (phones, a foldable's cover screen, 16:10 and 4:3 tablets): landscape left/right only, as in
    ///   Player Settings (the game is a landscape game, docs/01).
    /// - Near-square screens (a foldable's inner screen, ~1.1:1): every orientation, following how the device is held
    ///   (OS "user" rotation, i.e. the rotation lock is respected). Locking such a screen to landscape makes Android
    ///   turn the picture 90 deg against the way the opened phone is held ("obraca obraz", owner, Fold, 2026-11-12):
    ///   the inner screen's natural orientation is portrait-ish, so "landscape" means a quarter-turned picture.
    ///   Either orientation of a near-square screen is equally usable (HUD solver: ADR 0079, both orientations tested).
    /// The decision uses max/min of the window size, so it is the same in both orientations (no flip-flop).
    /// </summary>
    public static class ScreenOrientationPolicy
    {
        /// <summary>Longer / shorter window side up to which a screen counts as near-square. Fold inner screens
        /// ~1.1-1.2 (e.g. 2184x1968 = 1.11); 4:3 tablets 1.33 and every phone (>= 1.78) stay landscape-only. WORKING_VALUE.</summary>
        public const float NearSquareMaxAspect = 1.25f;

        public struct Allowed
        {
            public bool Portrait, PortraitUpsideDown, LandscapeLeft, LandscapeRight;
            public bool Equals(Allowed o) => Portrait == o.Portrait && PortraitUpsideDown == o.PortraitUpsideDown && LandscapeLeft == o.LandscapeLeft && LandscapeRight == o.LandscapeRight;
            public override string ToString() => (Portrait ? "P" : "-") + (PortraitUpsideDown ? "U" : "-") + (LandscapeLeft ? "L" : "-") + (LandscapeRight ? "R" : "-");
        }

        public static float Aspect(int width, int height)
        {
            if (width <= 0 || height <= 0) return 0f;
            return Mathf.Max(width, height) / (float)Mathf.Min(width, height);
        }

        public static bool IsNearSquare(int width, int height)
        {
            float a = Aspect(width, height);
            return a > 0f && a <= NearSquareMaxAspect;
        }

        /// <summary>Allowed orientations for a window of this size (0 x 0 = unknown: landscape only).</summary>
        public static Allowed Decide(int width, int height)
        {
            bool any = IsNearSquare(width, height);
            return new Allowed { Portrait = any, PortraitUpsideDown = any, LandscapeLeft = true, LandscapeRight = true };
        }
    }

    /// <summary>What <see cref="ScreenOrientationLock"/> asks the screen to do this frame.</summary>
    public enum OrientationCommand { None, AllowAuto, Lock }

    /// <summary>
    /// Orientation state machine (ADR 0135 r3). Pure logic, unit-tested.
    /// Owner, Fold, r2: "dalej obraca obraz" - the r2 settle (rotate freely 1.2 s, then lock) itself turned the picture:
    /// the activity started in landscape and then rotated to the held portrait. r3: the game NEVER asks for a rotation on
    /// a near-square screen. Player Settings allow all four orientations (activity launches in the orientation the
    /// display already has, no launch rotation), and on a near-square window the current concrete orientation is locked
    /// at once - at start and after every fold / unfold (a new sorted window size).
    /// Elongated windows (phones, cover screen): landscape L/R only (a phone held upright turns to landscape once, as
    /// in every landscape game); with gyro steering the current landscape is locked after a short settle (the steering
    /// tilt is the motion the orientation sensor reads), unlocked again when gyro is switched off.
    /// ADR 0147: an elongated window that is portrait (phone flat on a table at launch, fold to the cover screen held
    /// upright) is first locked to a concrete landscape - AutoRotation alone left the A16 in portrait - and L/R
    /// auto-rotation is allowed once the window is landscape.
    /// </summary>
    public sealed class ScreenOrientationLock
    {
        /// <summary>Elongated screen with gyro: time for the OS to finish turning to landscape before the lock [s]. WORKING_VALUE.</summary>
        public const float SettleSeconds = 1.2f;

        int m_ShortSide = -1, m_LongSide = -1, m_W, m_H;
        float m_SettleUntil;
        bool m_Pending, m_Locked, m_GyroLocked;

        public bool Locked => m_Locked;
        public ScreenOrientationPolicy.Allowed Allowed { get; private set; }
        /// <summary>Orientation to lock to with <see cref="OrientationCommand.Lock"/>.</summary>
        public ScreenOrientation LockTo { get; private set; }
        /// <summary>Short reason for the last command (log).</summary>
        public string Reason { get; private set; } = "";

        public static bool Concrete(ScreenOrientation o) => o == ScreenOrientation.Portrait || o == ScreenOrientation.PortraitUpsideDown
                                                           || o == ScreenOrientation.LandscapeLeft || o == ScreenOrientation.LandscapeRight;

        static bool IsLandscape(ScreenOrientation o) => o == ScreenOrientation.LandscapeLeft || o == ScreenOrientation.LandscapeRight;

        /// <summary>
        /// Concrete landscape to force an elongated portrait window into (ADR 0147): the one the device is held in, if
        /// the sensor knows it; otherwise (flat on a table: FaceUp/FaceDown/Unknown, or held upright) LandscapeLeft,
        /// the standard landscape (top of the phone to the left). Unity's DeviceOrientation and ScreenOrientation
        /// landscape names describe the same physical pose.
        /// </summary>
        public static ScreenOrientation ForcedLandscape(DeviceOrientation device)
            => device == DeviceOrientation.LandscapeRight ? ScreenOrientation.LandscapeRight : ScreenOrientation.LandscapeLeft;

        /// <summary>True while an elongated window is being forced out of portrait (ADR 0147).</summary>
        public bool Forcing => m_Forcing;
        bool m_Forcing;

        public OrientationCommand Step(float time, int width, int height, ScreenOrientation current, bool gyroActive)
            => Step(time, width, height, current, gyroActive, DeviceOrientation.Unknown);

        public OrientationCommand Step(float time, int width, int height, ScreenOrientation current, bool gyroActive, DeviceOrientation device)
        {
            int shortSide = Mathf.Min(width, height), longSide = Mathf.Max(width, height);
            bool nearSquare = ScreenOrientationPolicy.IsNearSquare(width, height);
            if (shortSide != m_ShortSide || longSide != m_LongSide)
            {
                m_ShortSide = shortSide; m_LongSide = longSide; m_W = width; m_H = height;
                m_Locked = false; m_GyroLocked = false; m_Pending = true; m_Forcing = false;
                m_SettleUntil = time + SettleSeconds;
                Allowed = ScreenOrientationPolicy.Decide(width, height);
                if (!nearSquare)
                {
                    // ADR 0147: with the manifest fullUser (ADR 0135 r3) a phone lying flat launches in its natural
                    // portrait, and AutoRotation restricted to L/R does NOT move it out (A16 logcat: AllowAuto
                    // allowed=--LR orientation=Portrait, no rotation followed). A concrete landscape request rotates
                    // at once, sensor or not; L/R auto-rotation is allowed once the window is landscape.
                    if (height > width)
                    {
                        m_Forcing = true; m_Locked = true; LockTo = ForcedLandscape(device);
                        Reason = "elongated portrait window: force landscape";
                        return OrientationCommand.Lock;
                    }
                    Reason = "elongated: landscape only"; return OrientationCommand.AllowAuto;
                }
            }
            if (width != m_W || height != m_H) { m_W = width; m_H = height; m_SettleUntil = time + SettleSeconds; }
            if (m_Forcing)
            {
                // Wait for the OS to deliver the landscape window (no repeated requests, no loop if it never comes,
                // e.g. a freeform window that ignores orientation requests).
                if (height > width) return OrientationCommand.None;
                m_Forcing = false; m_Locked = false;
                Reason = "landscape reached: allow L/R";
                return OrientationCommand.AllowAuto;
            }
            if (nearSquare)
            {
                if (m_Pending && Concrete(current))
                {
                    m_Pending = false; m_Locked = true; LockTo = current; Reason = "near-square: keep current orientation";
                    return OrientationCommand.Lock;
                }
                return OrientationCommand.None;
            }
            if (m_Pending)
            {
                if (time < m_SettleUntil || !IsLandscape(current)) return OrientationCommand.None;
                m_Pending = false;
            }
            if (gyroActive && !m_Locked && IsLandscape(current))
            {
                m_Locked = true; m_GyroLocked = true; LockTo = current; Reason = "gyro steering: lock current landscape";
                return OrientationCommand.Lock;
            }
            if (!gyroActive && m_Locked && m_GyroLocked)
            {
                m_Locked = false; m_GyroLocked = false; Allowed = ScreenOrientationPolicy.Decide(width, height); Reason = "gyro steering off: unlock";
                return OrientationCommand.AllowAuto;
            }
            return OrientationCommand.None;
        }
    }

    /// <summary>
    /// Applies <see cref="ScreenOrientationLock"/> on the device for the whole process (all scenes). The activity declares
    /// every configChanges flag (Unity default), so a fold is a size change inside the running game, not a restart.
    /// Logs one <c>[SCREEN]</c> line per command: window, aspect, orientation, device orientation, natural panel
    /// orientation, DPI (reported / panel / used), safe area. Allocation-free per frame (strings only on a command).
    /// </summary>
    public sealed class ScreenOrientationGuard : MonoBehaviour
    {
        /// <summary>Set by the driving scene while gyro steering is selected (locks the orientation on phones too).</summary>
        public static bool GyroSteeringActive;

        readonly ScreenOrientationLock m_Lock = new ScreenOrientationLock();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Install()
        {
            if (!Application.isMobilePlatform) return;   // editor / desktop: the window is resized freely, nothing to lock
            var go = new GameObject("ScreenOrientationGuard");
            DontDestroyOnLoad(go);
            go.AddComponent<ScreenOrientationGuard>();
        }

        ScreenOrientation m_LastOrientation = ScreenOrientation.AutoRotation;
        bool m_RollLogged;

        void Update()
        {
            Diagnostics();
            var cmd = m_Lock.Step(Time.unscaledTime, Screen.width, Screen.height, Screen.orientation, GyroSteeringActive, Input.deviceOrientation);
            if (cmd == OrientationCommand.None) return;
            if (cmd == OrientationCommand.AllowAuto)
            {
                var a = m_Lock.Allowed;
                // Allow first, then AutoRotation: Unity re-requests the orientation from these flags.
                Screen.autorotateToLandscapeLeft = a.LandscapeLeft;
                Screen.autorotateToLandscapeRight = a.LandscapeRight;
                Screen.autorotateToPortrait = a.Portrait;
                Screen.autorotateToPortraitUpsideDown = a.PortraitUpsideDown;
                Screen.orientation = ScreenOrientation.AutoRotation;
            }
            else Screen.orientation = m_Lock.LockTo;   // near-square / gyro: the current one (no rotation); elongated portrait: forced landscape (ADR 0147)
            DeviceDisplay.Invalidate();
            Log(cmd);
        }

        /// <summary>
        /// Owner r2 "dalej obraca obraz o 45°": logs every actual orientation change (who rotated: the OS) and a camera
        /// roll over 10 deg (cab roll / head motion), once per episode. Strings only on such an edge.
        /// </summary>
        void Diagnostics()
        {
            var o = Screen.orientation;
            if (o != m_LastOrientation)
            {
                if (m_LastOrientation != ScreenOrientation.AutoRotation)
                {
                    DeviceDisplay.Invalidate();
                    Debug.Log("[SCREEN] orientation changed " + m_LastOrientation + " -> " + o + " window=" + Screen.width + "x" + Screen.height
                              + " rotation=" + DeviceDisplay.Rotation + " device=" + Input.deviceOrientation + " locked=" + m_Lock.Locked
                              + " gyro=" + (GyroSteeringActive ? "on" : "off") + " t=" + Time.unscaledTime.ToString("F1", System.Globalization.CultureInfo.InvariantCulture));
                }
                m_LastOrientation = o;
            }
            var cam = Camera.main;
            if (cam == null) return;
            float roll = Mathf.DeltaAngle(0f, cam.transform.eulerAngles.z);
            if (!m_RollLogged && Mathf.Abs(roll) > 10f)
            {
                m_RollLogged = true;
                Debug.Log("[SCREEN] camera roll " + roll.ToString("F1", System.Globalization.CultureInfo.InvariantCulture) + " deg (" + cam.name + ") gyro=" + (GyroSteeringActive ? "on" : "off"));
            }
            else if (m_RollLogged && Mathf.Abs(roll) < 5f) m_RollLogged = false;
        }

        void Log(OrientationCommand cmd)
        {
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            int w = Screen.width, h = Screen.height;
            var sa = Screen.safeArea;
            Debug.Log("[SCREEN] " + cmd + " (" + m_Lock.Reason + ") window=" + w + "x" + h
                      + " aspect=" + ScreenOrientationPolicy.Aspect(w, h).ToString("F2", ci)
                      + " allowed=" + m_Lock.Allowed + (cmd == OrientationCommand.Lock ? " lockTo=" + m_Lock.LockTo : "")
                      + " orientation=" + Screen.orientation + " device=" + Input.deviceOrientation
                      + " rotation=" + DeviceDisplay.Rotation + " natural=" + DeviceDisplay.NaturalOrientation(w, h, DeviceDisplay.Rotation)
                      + " dpi=" + DeviceDisplay.ReportedDpi.ToString("F0", ci) + "/" + DeviceDisplay.PanelXDpi.ToString("F0", ci) + "/" + DeviceDisplay.Dpi.ToString("F0", ci)
                      + " safe=" + sa.x.ToString("F0", ci) + "," + sa.y.ToString("F0", ci) + "," + sa.width.ToString("F0", ci) + "x" + sa.height.ToString("F0", ci)
                      + " gyro=" + (GyroSteeringActive ? "on" : "off") + " (ADR 0135)");
        }
    }
}
