using System.Diagnostics;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using UnityEngine;

namespace Game.UI.CabDisplays
{
    /// <summary>
    /// Live cab screens of the TRAKT (review r4 C-N1/C-N2/L3): the 12.3" cluster, the navigation screen and the DIN unit
    /// faces are drawn into render textures from the solver state and bound to the existing display renderers
    /// (DISPLAY_Cluster_*, DISPLAY_Infotainment_*, DISPLAY_Tachograph_* / DISPLAY_Radio_* / DISPLAY_BunkPanel_*) with a
    /// material property block on <c>_BaseMap</c>: Kamion/Cab Display stays the material (emission, exposure, readability
    /// floor and cap unchanged), the prefab and the material assets are not modified.
    /// - Refresh: cluster 30 Hz (Low 20 Hz), navigation 10 Hz (Low 5 Hz), DIN 1 Hz; render-texture resolution by tier
    ///   (Low 0.5, Medium 0.75, High/Ultra 1.0 of the design size; mip-mapped, trilinear, aniso 4).
    /// - Zero GC per refresh (PlayMode test). CPU cost of the last / average refresh in <see cref="LastCpuMs"/> /
    ///   <see cref="AverageCpuMs"/>.
    /// - Day / night: night mode with the automatic dipped beam (TruckLights light sensor); the panel brightness itself
    ///   follows the exposure in Kamion/Cab Display.
    /// </summary>
    [DefaultExecutionOrder(100)]
    public sealed class CabScreens : MonoBehaviour
    {
        public static readonly int BaseMapId = Shader.PropertyToID("_BaseMap");
        public const string ClusterPrefix = "DISPLAY_Cluster_", NavPrefix = "DISPLAY_Infotainment_";
        static readonly string[] s_DinPrefixes = { "DISPLAY_Tachograph_", "DISPLAY_Radio_", "DISPLAY_BunkPanel_" };

        public VehicleBody vehicle;
        public TruckLights lights;
        [Tooltip("Region root (region-local frame of the navigation data); null = world frame")]
        public Transform regionFrame;
        [Tooltip("Region id of the navigation data (Resources/CabDisplay/Nav/<id>.bytes); empty = no map")]
        public string regionId = "";
        [Tooltip("-1 = from the quality tier")] public float clusterHz = -1f;
        [Tooltip("-1 = from the quality tier")] public float navHz = -1f;
        public float dinHz = 1f;
        [Tooltip("Render-texture size / design size; -1 = from the quality tier (Low 0.5, Medium 0.75, High 1)")]
        public float resolutionScale = -1f;

        public readonly CabDisplaySource Source = new CabDisplaySource();
        public CabDisplayState State;

        Renderer[] m_ClusterR, m_NavR, m_DinR;
        DisplayCanvas m_Cluster, m_Nav, m_Din;
        readonly ClusterLayout m_ClusterLayout = new ClusterLayout();
        readonly NavLayout m_NavLayout = new NavLayout();
        readonly DinLayout m_DinLayout = new DinLayout();
        MaterialPropertyBlock m_Mpb;
        float m_ClusterT, m_NavT, m_DinT, m_NavDt;
        float m_Rpm;
        VehicleModel m_Probe;
        int m_Refreshes;
        double m_CpuMsSum;
        bool m_Bound;

        public DisplayCanvas Cluster => m_Cluster;
        public DisplayCanvas Nav => m_Nav;
        public DisplayCanvas Din => m_Din;
        public NavLayout NavLayout => m_NavLayout;
        public float Scale { get; private set; }
        public double LastCpuMs { get; private set; }
        public double AverageCpuMs => m_Refreshes > 0 ? m_CpuMsSum / m_Refreshes : 0;
        public int RefreshCount => m_Refreshes;
        public bool HasScreens => m_ClusterR != null && m_ClusterR.Length > 0;

        /// <summary>Adds (or returns) the screens on a truck that has display renderers; null for the graybox.</summary>
        public static CabScreens Install(VehicleBody vehicle, Transform regionFrame, string regionId)
        {
            if (vehicle == null) return null;
            if (!HasDisplayRenderers(vehicle.transform)) return null;
            if (!vehicle.TryGetComponent(out CabScreens d)) d = vehicle.gameObject.AddComponent<CabScreens>();
            d.vehicle = vehicle;
            d.lights = vehicle.GetComponent<TruckLights>();
            d.regionFrame = regionFrame;
            d.regionId = regionId ?? "";
            d.Init();
            return d;
        }

        static bool HasDisplayRenderers(Transform root)
        {
            foreach (var r in root.GetComponentsInChildren<Renderer>(true))
                if (r.name.StartsWith(ClusterPrefix, System.StringComparison.Ordinal)) return true;
            return false;
        }

        void OnEnable() { if (vehicle != null && m_Cluster == null) Init(); }

        void OnDisable() => Release();

        void OnDestroy() => Release();

        void Release()
        {
            Unbind();
            m_NavLayout.ReleaseStatic();
            m_Cluster?.Dispose(); m_Nav?.Dispose(); m_Din?.Dispose();
            m_Cluster = m_Nav = m_Din = null;
            Font.textureRebuilt -= OnFontRebuilt;
        }

        public void Init()
        {
            Release();
            var root = vehicle != null ? vehicle.transform : transform;
            m_ClusterR = Find(root, ClusterPrefix, null);
            m_NavR = Find(root, NavPrefix, null);
            m_DinR = Find(root, null, s_DinPrefixes);
            int level = Mathf.Clamp(QualitySettings.GetQualityLevel(), 0, 3);
            Scale = resolutionScale > 0f ? resolutionScale : level == 0 ? 0.5f : level == 1 ? 0.75f : 1f;
            var font = UiFonts.Default;
            // Coverage gamma: light-on-dark cluster/DIN (sRGB-like stroke weight as the PIL reference), the day map is mixed.
            m_Cluster = new DisplayCanvas("Cluster", ClusterLayout.Width, ClusterLayout.Height, Scale, 3000, font, 1.5f);
            m_Nav = new DisplayCanvas("Nav", NavLayout.Width, NavLayout.Height, Scale, 6000, font, 1.0f);
            m_Din = new DisplayCanvas("Din", DinLayout.Width, DinLayout.Height, Mathf.Max(0.5f, Scale), 400, font, 1.5f);
            m_NavLayout.Map = NavMapData.Load(regionId);
            m_Mpb ??= new MaterialPropertyBlock();
            Font.textureRebuilt += OnFontRebuilt;
            RequestGlyphs();
            Bind();
            m_ClusterT = m_NavT = m_DinT = float.MaxValue;   // first LateUpdate draws everything
        }

        static Renderer[] Find(Transform root, string prefix, string[] prefixes)
        {
            var list = new System.Collections.Generic.List<Renderer>();
            foreach (var r in root.GetComponentsInChildren<Renderer>(true))
            {
                string n = r.name;
                if (prefix != null && n.StartsWith(prefix, System.StringComparison.Ordinal)) list.Add(r);
                else if (prefixes != null)
                    foreach (var p in prefixes) if (n.StartsWith(p, System.StringComparison.Ordinal)) { list.Add(r); break; }
            }
            return list.ToArray();
        }

        void Bind()
        {
            Bind(m_ClusterR, m_Cluster.Texture);
            Bind(m_NavR, m_Nav.Texture);
            Bind(m_DinR, m_Din.Texture);
            m_Bound = true;
        }

        void Bind(Renderer[] rs, Texture tex)
        {
            if (rs == null) return;
            foreach (var r in rs)
            {
                if (r == null) continue;
                r.GetPropertyBlock(m_Mpb);
                m_Mpb.SetTexture(BaseMapId, tex);
                r.SetPropertyBlock(m_Mpb);
            }
        }

        void Unbind()
        {
            if (!m_Bound) return;
            m_Bound = false;
            foreach (var rs in new[] { m_ClusterR, m_NavR, m_DinR })
                if (rs != null) foreach (var r in rs) if (r != null) r.SetPropertyBlock(null);
        }

        void OnFontRebuilt(Font f)
        {
            // Another text user grew the shared atlas: glyph UVs changed, redraw everything with the new atlas.
            if (m_Cluster == null || f != m_Cluster.Font) return;
            m_ClusterT = m_NavT = m_DinT = float.MaxValue;
            m_NeedGlyphs = true;
        }

        bool m_NeedGlyphs = true;

        void RequestGlyphs()
        {
            // An atlas rebuild during the requests (callback is synchronous) may drop glyphs requested before it: repeat.
            for (int tries = 0; tries < 3; tries++)
            {
                m_NeedGlyphs = false;
                ClusterLayout.RequestGlyphs(m_Cluster);
                NavLayout.RequestGlyphs(m_Nav);
                DinLayout.RequestGlyphs(m_Din);
                if (!m_NeedGlyphs) break;
            }
        }

        float ClusterHz => clusterHz > 0f ? clusterHz : Scale <= 0.5f ? 20f : 30f;
        float NavHz => navHz > 0f ? navHz : Scale <= 0.5f ? 5f : 10f;

        void LateUpdate()
        {
            if (m_Cluster == null) return;
            float dt = Time.unscaledDeltaTime;
            m_ClusterT += dt; m_NavT += dt; m_DinT += dt; m_NavDt += dt;
            bool c = m_ClusterT >= 1f / ClusterHz, n = m_NavT >= 1f / NavHz, d = m_DinT >= 1f / dinHz;
            if (!c && !n && !d) return;
            float needleDt = m_ClusterT < 1f ? m_ClusterT : 0f, navDt = m_NavDt < 2f ? m_NavDt : 0f;
            if (c) m_ClusterT = 0f;
            if (n) { m_NavT = 0f; m_NavDt = 0f; }
            if (d) m_DinT = 0f;
            Refresh(c, n, d, needleDt, navDt);
        }

        /// <summary>One refresh of the selected screens (the loop body of LateUpdate; public for the zero-GC test).</summary>
        public void Refresh(bool cluster, bool nav, bool din, float needleDt, float navDt)
        {
            long t0 = Stopwatch.GetTimestamp();
            Sample(needleDt);
            if (m_NeedGlyphs) RequestGlyphs();
            if (cluster) m_ClusterLayout.Draw(m_Cluster, State);
            if (nav) m_NavLayout.Draw(m_Nav, State, navDt);
            if (din) m_DinLayout.Draw(m_Din, State);
            Account(t0);
        }

        /// <summary>Samples and draws all screens now (visual QA in edit mode, tests). Without a running solver the
        /// truck is shown parked with the engine idling (a model built from the vehicle data, never stepped).</summary>
        public void RenderNow()
        {
            if (m_Cluster == null) Init();
            long t0 = Stopwatch.GetTimestamp();
            Sample(0f);
            RequestGlyphs();
            m_ClusterLayout.Draw(m_Cluster, State);
            m_NavLayout.Draw(m_Nav, State, 0f);
            m_DinLayout.Draw(m_Din, State);
            Bind();
            Account(t0);
        }

        void Account(long t0)
        {
            LastCpuMs = (Stopwatch.GetTimestamp() - t0) * 1000.0 / Stopwatch.Frequency;
            m_CpuMsSum += LastCpuMs;
            m_Refreshes++;
        }

        void Sample(float dt)
        {
            VehicleModel model = vehicle != null ? vehicle.Model : null;
            DriverInput input = vehicle != null && model != null ? vehicle.Input : new DriverInput { ParkingBrake = true, Selector = GearSelector.Drive };
            if (model == null && vehicle != null && vehicle.Data != null)
            {
                if (m_Probe == null) { m_Probe = vehicle.Data.CreateModel(); m_Probe.InitParking(true); }
                model = m_Probe;
            }
            var trailer = vehicle != null && vehicle.Trailer != null ? vehicle.Trailer.Model : null;
            double time = vehicle != null && vehicle.Model != null ? vehicle.SimTime : Time.realtimeSinceStartupAsDouble;
            Source.Sample(model, trailer, vehicle != null && vehicle.Coupled, lights, vehicle != null ? vehicle.transform : transform,
                regionFrame, time, ref State);
            CabDisplaySource.SampleInput(input, ref State);
            if (model == m_Probe) State.ParkingBrake = true;
            if (model != null) EcoBand(model.Engine.Def, ref State);
            // Needle damping (a real stepper needle follows with ~0.1 s lag; the 100 Hz solver rpm is noisy at shifts).
            m_Rpm = dt > 0f ? Mathf.Lerp(m_Rpm, State.EngineRpm, 1f - Mathf.Exp(-dt / 0.08f)) : State.EngineRpm;
            State.EngineRpm = m_Rpm;
        }

        float m_EcoLow = -1f, m_EcoHigh;
        EngineDefinition m_EcoDef;

        /// <summary>Green band = speed range where the full-load torque is within 3 % of its maximum (the torque plateau).</summary>
        void EcoBand(EngineDefinition def, ref CabDisplayState s)
        {
            if (def != m_EcoDef)
            {
                m_EcoDef = def;
                EcoBandOf(def, out m_EcoLow, out m_EcoHigh);
            }
            s.EcoLowRpm = m_EcoLow; s.EcoHighRpm = m_EcoHigh;
        }

        public static void EcoBandOf(EngineDefinition def, out float low, out float high)
        {
            double max = 0;
            foreach (var t in def.torqueCurveNm) max = System.Math.Max(max, t);
            low = high = 0f;
            bool found = false;
            double a = def.torqueCurveRpm[0], b = def.torqueCurveRpm[def.torqueCurveRpm.Length - 1];
            for (double rpm = a; rpm <= b; rpm += 10)
            {
                if (Lut(def.torqueCurveRpm, def.torqueCurveNm, rpm) < 0.97 * max) continue;
                if (!found) { low = (float)rpm; found = true; }
                high = (float)rpm;
            }
        }

        static double Lut(double[] x, double[] y, double v)
        {
            if (v <= x[0]) return y[0];
            for (int i = 1; i < x.Length; i++)
                if (v <= x[i]) return y[i - 1] + (y[i] - y[i - 1]) * (v - x[i - 1]) / (x[i] - x[i - 1]);
            return y[y.Length - 1];
        }
    }
}
