using Game.Core;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.World
{
    /// <summary>
    /// ADR 0124 (review 0114 P1-r8-h): the house plots (chunk nodes <c>plots</c> = fences, gates, garden plants and
    /// <c>plot_ground</c> = lawn, driveway) are drawn with the chunk's LOD0 / LOD1, i.e. to ~300 m x LOD bias. An extra
    /// view (vehicle mirror, reversing camera, reflection capture: <see cref="IExtraViewCamera"/>) shows a fence at 100 m
    /// as a few texels, so while such a camera renders, the plot nodes whose bounds lie further than
    /// <see cref="extraViewRangeM"/> from it are switched off (<c>forceRenderingOff</c>, restored when the camera is done).
    /// Granularity is the chunk (256 m): the plots of the chunk the truck drives through stay in the mirrors.
    /// One component on the region root (WorldSceneBuilder); no allocation per frame.
    /// </summary>
    [ExecuteAlways]
    public sealed class PlotViewCull : MonoBehaviour
    {
        [Tooltip("plots / plot_ground renderers of every chunk (filled by the scene builder).")]
        public Renderer[] renderers = new Renderer[0];
        [Tooltip("Range of the house plots in extra views (mirrors, reversing camera), metres to the node bounds. WORKING_VALUE.")]
        public float extraViewRangeM = 70f;

        /// <summary>Editor / profiler switch: false = plots drawn in extra views as in the main view (ADR 0114 behaviour).</summary>
        public static bool Enabled = true;

        static PlotViewCull s_Active;
        bool[] m_Off = new bool[0];
        bool m_Dirty;

        void OnEnable()
        {
            s_Active = this;
            if (m_Off.Length != renderers.Length) m_Off = new bool[renderers.Length];
            RenderPipelineManager.beginCameraRendering += OnBegin;
            RenderPipelineManager.endCameraRendering += OnEnd;
        }

        void OnDisable()
        {
            RenderPipelineManager.beginCameraRendering -= OnBegin;
            RenderPipelineManager.endCameraRendering -= OnEnd;
            Restore();
            if (s_Active == this) s_Active = null;
        }

        /// <summary>True when <paramref name="r"/> is a plot node this component hides for <paramref name="cam"/> (also used
        /// by the editor's draw estimate, which does not render).</summary>
        public static bool HiddenFor(Camera cam, Renderer r)
        {
            var a = s_Active != null ? s_Active : FindAnyObjectByType<PlotViewCull>();
            if (!Enabled || a == null || cam == null || r == null || !cam.TryGetComponent(out IExtraViewCamera _)) return false;
            if (System.Array.IndexOf(a.renderers, r) < 0) return false;
            float range = a.extraViewRangeM;
            return r.bounds.SqrDistance(cam.transform.position) > range * range;
        }

        void OnBegin(ScriptableRenderContext ctx, Camera cam)
        {
            if (m_Dirty) Restore();
            if (!Enabled || !cam.TryGetComponent(out IExtraViewCamera _)) return;
            Vector3 p = cam.transform.position;
            float r2 = extraViewRangeM * extraViewRangeM;
            for (int i = 0; i < renderers.Length; i++)
            {
                var r = renderers[i];
                if (r == null || r.forceRenderingOff) continue;
                if (r.bounds.SqrDistance(p) > r2) { r.forceRenderingOff = true; m_Off[i] = true; m_Dirty = true; }
            }
        }

        void OnEnd(ScriptableRenderContext ctx, Camera cam)
        {
            if (m_Dirty) Restore();
        }

        void Restore()
        {
            for (int i = 0; i < m_Off.Length && i < renderers.Length; i++)
                if (m_Off[i]) { if (renderers[i] != null) renderers[i].forceRenderingOff = false; m_Off[i] = false; }
            m_Dirty = false;
        }
    }
}
