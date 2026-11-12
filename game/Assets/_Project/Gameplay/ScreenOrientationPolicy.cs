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
    /// Settle-then-lock state machine (ADR 0135, review 0134-0135 P1). Pure logic, unit-tested.
    /// - A new screen configuration (first frame, fold / unfold, multi-window: the sorted window size changes) starts a
    ///   short settle: the allowed orientations (<see cref="ScreenOrientationPolicy.Decide"/>) rotate freely so the picture
    ///   turns to how the device is held at that moment. A rotation during the settle (width/height swap) restarts it.
    /// - After <see cref="SettleSeconds"/> the CURRENT concrete orientation is locked: tilting the phone while driving
    ///   never rotates the picture again (nor suspends gyro steering, which recalibrates on every orientation change).
    /// - Elongated screens (phones): landscape L/R keep rotating as before, unless gyro steering is on (then locked
    ///   too: the steering tilt is the very motion the orientation sensor reads). Near-square screens: always locked.
    /// </summary>
    public sealed class ScreenOrientationLock
    {
        /// <summary>Time for the OS to turn the picture to the held orientation after a configuration change [s]. WORKING_VALUE.</summary>
        public const float SettleSeconds = 1.2f;

        int m_ShortSide = -1, m_LongSide = -1, m_W, m_H;
        float m_SettleUntil;
        bool m_Settling, m_Locked, m_GyroLocked;

        public bool Settling => m_Settling;
        public bool Locked => m_Locked;
        public ScreenOrientationPolicy.Allowed Allowed { get; private set; }
        /// <summary>Orientation to lock to with <see cref="OrientationCommand.Lock"/>.</summary>
        public ScreenOrientation LockTo { get; private set; }
        /// <summary>Short reason for the last command (log).</summary>
        public string Reason { get; private set; } = "";

        static bool Concrete(ScreenOrientation o) => o == ScreenOrientation.Portrait || o == ScreenOrientation.PortraitUpsideDown
                                                    || o == ScreenOrientation.LandscapeLeft || o == ScreenOrientation.LandscapeRight;

        public OrientationCommand Step(float time, int width, int height, ScreenOrientation current, bool gyroActive)
        {
            int shortSide = Mathf.Min(width, height), longSide = Mathf.Max(width, height);
            if (shortSide != m_ShortSide || longSide != m_LongSide)
            {
                m_ShortSide = shortSide; m_LongSide = longSide; m_W = width; m_H = height;
                m_Settling = true; m_Locked = false; m_GyroLocked = false;
                m_SettleUntil = time + SettleSeconds;
                Allowed = ScreenOrientationPolicy.Decide(width, height);
                Reason = "new screen configuration: settle";
                return OrientationCommand.AllowAuto;
            }
            if (width != m_W || height != m_H) { m_W = width; m_H = height; if (m_Settling) m_SettleUntil = time + SettleSeconds; }
            bool nearSquare = ScreenOrientationPolicy.IsNearSquare(width, height);
            if (m_Settling)
            {
                if (time < m_SettleUntil || !Concrete(current)) return OrientationCommand.None;
                m_Settling = false;
                if (nearSquare || gyroActive)
                {
                    m_Locked = true; m_GyroLocked = !nearSquare; LockTo = current;
                    Reason = nearSquare ? "near-square: lock held orientation" : "gyro steering: lock held orientation";
                    return OrientationCommand.Lock;
                }
                return OrientationCommand.None;   // phone without gyro: landscape L/R keep rotating
            }
            if (!nearSquare)
            {
                if (gyroActive && !m_Locked && Concrete(current))
                {
                    m_Locked = true; m_GyroLocked = true; LockTo = current; Reason = "gyro steering on: lock";
                    return OrientationCommand.Lock;
                }
                if (!gyroActive && m_Locked && m_GyroLocked)
                {
                    m_Locked = false; m_GyroLocked = false; Allowed = ScreenOrientationPolicy.Decide(width, height); Reason = "gyro steering off: unlock";
                    return OrientationCommand.AllowAuto;
                }
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

        void Update()
        {
            var cmd = m_Lock.Step(Time.unscaledTime, Screen.width, Screen.height, Screen.orientation, GyroSteeringActive);
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
            else Screen.orientation = m_Lock.LockTo;   // equals the current one: no rotation, no gyro suspend
            DeviceDisplay.Invalidate();
            Log(cmd);
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
