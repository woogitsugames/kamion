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

    /// <summary>
    /// Applies <see cref="ScreenOrientationPolicy"/> on the device at start and whenever the window size changes (fold /
    /// unfold, multi-window): the activity declares every configChanges flag (Unity default), so a fold is a resolution
    /// change inside the running game, not a restart. Lives for the whole process (all scenes). Allocation-free per frame.
    /// </summary>
    public sealed class ScreenOrientationGuard : MonoBehaviour
    {
        int m_W = -1, m_H = -1;
        bool m_HasApplied;
        ScreenOrientationPolicy.Allowed m_Applied;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Install()
        {
            if (!Application.isMobilePlatform) return;   // editor / desktop: the window is resized freely, nothing to lock
            var go = new GameObject("ScreenOrientationGuard");
            DontDestroyOnLoad(go);
            go.AddComponent<ScreenOrientationGuard>();
        }

        void Start() => Check();

        void Update() => Check();

        void Check()
        {
            int w = Screen.width, h = Screen.height;
            if (w == m_W && h == m_H) return;
            m_W = w; m_H = h;
            var a = ScreenOrientationPolicy.Decide(w, h);
            if (m_HasApplied && a.Equals(m_Applied)) return;
            m_HasApplied = true; m_Applied = a;
            // Allow first, then (only if needed) forbid: Unity re-requests the orientation from these flags while
            // Screen.orientation is AutoRotation, and an orientation that is currently shown stays valid in between.
            Screen.autorotateToLandscapeLeft = a.LandscapeLeft;
            Screen.autorotateToLandscapeRight = a.LandscapeRight;
            Screen.autorotateToPortrait = a.Portrait;
            Screen.autorotateToPortraitUpsideDown = a.PortraitUpsideDown;
            if (Screen.orientation != ScreenOrientation.AutoRotation) Screen.orientation = ScreenOrientation.AutoRotation;
            Debug.Log("[SCREEN] " + w + "x" + h + " aspect " + ScreenOrientationPolicy.Aspect(w, h).ToString("F2", System.Globalization.CultureInfo.InvariantCulture)
                      + " -> orientations " + a + " (ADR 0135)");
        }
    }
}
