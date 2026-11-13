using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// ADR 0191: photometry of the analytic street-lamp pools - the C# mirror of KamionLampIntensity in
    /// Rendering/Shaders/KamionLampPools.hlsl (keep both in step) and the luminaire geometry read from the lamp prototypes.
    /// The intensity is defined through its ground footprint in mounting heights h: over a level road E = I0 / h² · F with
    /// F = (1 - ρ²)², ρ² = (along / RA)² + (across / RC)², RC = RS on the carriageway side of the arm and RH behind the
    /// column; a luminaire without an arm (post-top) is symmetric (RSym). The equivalent intensity table is
    /// I(γ, C) = I0 · F · (d / h)³ - a road-luminaire bat-wing with its peak (~2.2 I0) at ~54° along the road, a short
    /// throw behind the column and nothing above ~67° (full cutoff). Shape typical of EN 13201 street lighting; radii
    /// WORKING_VALUE, no product's photometry copied.
    /// </summary>
    public static class StreetLampOptics
    {
        /// <summary>Footprint half-length along the road, in mounting heights (WORKING_VALUE).</summary>
        public const float AlongRadiusH = 2.4f;
        /// <summary>Footprint reach across, on the carriageway side of the arm (WORKING_VALUE).</summary>
        public const float StreetSideRadiusH = 1.5f;
        /// <summary>Footprint reach across, behind the column (house side; WORKING_VALUE).</summary>
        public const float HouseSideRadiusH = 0.7f;
        /// <summary>Footprint radius of a luminaire without an arm (post-top, symmetric; WORKING_VALUE).</summary>
        public const float SymmetricRadiusH = 1.8f;
        /// <summary>A glass quad whose centre lies closer than this to the column axis (m) is not on an arm.</summary>
        public const float MinArmReachM = 0.3f;
        /// <summary>A glass submesh spanning more than this across the column (m) holds two back-to-back luminaires.</summary>
        public const float DoubleSpanM = 1.0f;
        /// <summary>Distance from the outer end of a glass quad to its centre (props.py: 0.04-0.66 m along the arm).</summary>
        public const float GlassOuterToCentreM = 0.29f;

        /// <summary>
        /// Relative intensity I / I0 of a luminaire at <paramref name="lamp"/> towards <paramref name="p"/>.
        /// <paramref name="arm"/> = horizontal unit direction from the column to the luminaire (x, z); <paramref name="road"/>
        /// = asymmetric road optic (false = symmetric post-top).
        /// </summary>
        public static float RelativeIntensity(Vector3 lamp, Vector2 arm, bool road, Vector3 p)
        {
            Vector3 dv = lamp - p;
            float h = dv.y;
            if (h <= 0.05f) return 0f;
            float d = Mathf.Sqrt(Mathf.Max(dv.sqrMagnitude, 0.25f));
            float gx = -dv.x / h, gz = -dv.z / h;
            float across = gx * arm.x + gz * arm.y;
            float along = gx * arm.y - gz * arm.x;
            float rc = road ? (across > 0f ? StreetSideRadiusH : HouseSideRadiusH) : SymmetricRadiusH;
            float ra = road ? AlongRadiusH : SymmetricRadiusH;
            float qa = along / ra, qc = across / rc;
            float f = Mathf.Clamp01(1f - qa * qa - qc * qc);
            float dh = d / h;
            return f * f * dh * dh * dh;
        }

        /// <summary>Horizontal illuminance (lx) at <paramref name="p"/> (level ground) for a nadir intensity <paramref name="i0Cd"/>.</summary>
        public static float GroundLux(Vector3 lamp, Vector2 arm, bool road, Vector3 p, float i0Cd)
        {
            Vector3 dv = lamp - p;
            float d2 = Mathf.Max(dv.sqrMagnitude, 0.25f);
            float cos = Mathf.Clamp01(dv.y / Mathf.Sqrt(d2));
            return i0Cd * RelativeIntensity(lamp, arm, road, p) * cos / d2;
        }

        /// <summary>Downward luminous flux of the footprint model (lm): I0 · π · RA · (RS + RH) / 2 / 3 (road optic).</summary>
        public static float DownwardFluxLm(float i0Cd, bool road) =>
            road ? i0Cd * Mathf.PI * AlongRadiusH * (StreetSideRadiusH + HouseSideRadiusH) * 0.5f / 3f
                 : i0Cd * Mathf.PI * SymmetricRadiusH * SymmetricRadiusH / 3f;

        /// <summary>
        /// Luminaires of a lamp prototype from the bounds of its lamp-glass submesh (mesh space, Y up). Returns 0–2 and
        /// writes the luminaire centres and their arm directions (x, z of the horizontal unit vector from the column).
        /// One glass quad off the axis = one luminaire on an arm; a glass submesh spanning the column = two back-to-back
        /// luminaires at its ends (lamp_double_*, lamp_y); glass on the axis = post-top (arm = zero, symmetric optic).
        /// </summary>
        public static int LuminairesFromGlass(Bounds glass, Vector3[] pos, Vector2[] arm)
        {
            Vector2 c = new Vector2(glass.center.x, glass.center.z);
            float y = glass.center.y;
            if (c.magnitude >= MinArmReachM)
            {
                pos[0] = new Vector3(c.x, y, c.y);
                arm[0] = c.normalized;
                return 1;
            }
            float ex = glass.extents.x, ez = glass.extents.z;
            if (2f * Mathf.Max(ex, ez) >= DoubleSpanM)
            {
                Vector2 axis = ex >= ez ? Vector2.right : Vector2.up;
                float reach = Mathf.Max(ex, ez) - GlassOuterToCentreM;
                for (int s = 0; s < 2; s++)
                {
                    Vector2 a = s == 0 ? axis : -axis;
                    pos[s] = new Vector3(c.x + a.x * reach, y, c.y + a.y * reach);
                    arm[s] = a;
                }
                return 2;
            }
            pos[0] = new Vector3(c.x, y, c.y);
            arm[0] = Vector2.zero;
            return 1;
        }
    }
}
