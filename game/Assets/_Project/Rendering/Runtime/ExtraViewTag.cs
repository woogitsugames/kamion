using Game.Core;
using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// Marks a camera created at run time as an extra view (ADR 0068): reflection-capture faces, other off-screen views.
    /// Gives it a LOD-bias multiplier (Game.Core.ExtraViewLod) and lets the pass-cost monitor attribute its time.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class ExtraViewTag : MonoBehaviour, IExtraViewCamera
    {
        public ExtraViewKind kind = ExtraViewKind.Capture;
        [Tooltip("Multiplier on the tier LOD bias while this camera renders (1 = main-view LOD)")]
        public float lodScale = 1f;

        public ExtraViewKind Kind => kind;
        public float LodScale => lodScale;

        void OnEnable() => ExtraViewLod.Hook();
    }
}
