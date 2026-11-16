using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Game.UI.Settings
{
    /// <summary>Visible focus for pad / keyboard in <see cref="PcSettingsPanel"/>: a thin outline while the item is selected
    /// (no glow, no colour shift). Stop-gap until #131 (ADR 0265) <c>UiFocus.Decorate</c> is merged; then delete this file.</summary>
    public sealed class PcFocusOutline : MonoBehaviour, ISelectHandler, IDeselectHandler
    {
        Outline m_Outline;

        public void Init(Color color)
        {
            if (m_Outline == null) m_Outline = gameObject.AddComponent<Outline>();
            m_Outline.effectColor = color;
            m_Outline.effectDistance = new Vector2(3f, -3f);
            m_Outline.enabled = false;
        }

        /// <summary>True while the outline is shown (tests).</summary>
        public bool Shown => m_Outline != null && m_Outline.enabled;

        public void OnSelect(BaseEventData e) { if (m_Outline != null) m_Outline.enabled = true; }
        public void OnDeselect(BaseEventData e) { if (m_Outline != null) m_Outline.enabled = false; }
        void OnDisable() { if (m_Outline != null) m_Outline.enabled = false; }
    }
}
