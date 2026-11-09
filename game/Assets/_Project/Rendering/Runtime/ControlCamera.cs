using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// Marks a camera as a fixed visual-QA control camera. The editor visual-QA runner
    /// (Game.Editor.VisualQA.VisualQaRunner) renders every ControlCamera in a scene to
    /// artifacts/visual-qa/&lt;scene&gt;/&lt;id&gt;.png. Control cameras other than the main camera
    /// stay disabled at runtime.
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public sealed class ControlCamera : MonoBehaviour
    {
        [Tooltip("Stable id used as the PNG file name (kebab-case).")]
        public string id = "camera";

        [Tooltip("Render the diagnostics overlay on top (for UI legibility checks).")]
        public bool includeDiagnosticsOverlay;

        [TextArea] public string note;
    }
}
