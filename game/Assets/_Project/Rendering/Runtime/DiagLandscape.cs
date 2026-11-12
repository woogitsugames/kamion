using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// ADR 0136 r2 (device measurements only): with the launch argument <c>rq_landscape=1</c> the screen is turned to
    /// landscape left once, 1.5 s after start. On 2026-11-12 the A16 lying flat on the desk stayed in portrait
    /// (1080x2340) under the ADR 0135 AutoRotation policy, so G3 runs measured a narrower view than the game shows;
    /// the gate numbers must be taken in landscape. No effect without the argument.
    /// </summary>
    public sealed class DiagLandscape : MonoBehaviour
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Install()
        {
            if (!Application.isMobilePlatform) return;
            var go = new GameObject("DiagLandscape");
            DontDestroyOnLoad(go);
            go.AddComponent<DiagLandscape>();
        }

        void Update()
        {
            if (Time.unscaledTime < 1.5f) return;
            if (RenderOverrides.Landscape && Screen.width < Screen.height)
            {
                Screen.orientation = ScreenOrientation.LandscapeLeft;
                Debug.Log("[SCREEN] rq_landscape: forced LandscapeLeft (ADR 0136 r2)");
                enabled = false;
            }
            else if (Time.unscaledTime > 30f) enabled = false;
        }
    }
}
