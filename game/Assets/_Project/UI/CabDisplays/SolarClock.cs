using System;

namespace Game.UI.CabDisplays
{
    /// <summary>
    /// Wall-clock time consistent with the scene sun (there is no game clock yet): from the sun elevation and azimuth at
    /// Białystok the solar declination (season) and hour angle follow, hence local solar time; the clock adds the zone
    /// (CET, or CEST when the declination is positive - spring/summer half of the year, an approximation of the EU DST
    /// dates) and the longitude offset. Equation of time ignored (|EoT| &lt;= 16 min). A dusk preset therefore reads
    /// "20:04" instead of a fixed "14:32" (review r4 C-N1).
    /// </summary>
    public static class SolarClock
    {
        /// <summary>Białystok city centre (WGS84), the reference of the world regions.</summary>
        public const double LatitudeDeg = 53.13, LongitudeDeg = 23.16;

        /// <summary>Minutes of the local day (0..1439) for a sun at <paramref name="elevationDeg"/> / <paramref name="azimuthDeg"/> (0 = north, clockwise).</summary>
        public static int LocalMinutes(double elevationDeg, double azimuthDeg, double latitudeDeg = LatitudeDeg, double longitudeDeg = LongitudeDeg)
        {
            const double D = Math.PI / 180.0;
            double phi = latitudeDeg * D, e = elevationDeg * D, a = azimuthDeg * D;
            double sinDec = Math.Sin(phi) * Math.Sin(e) + Math.Cos(phi) * Math.Cos(e) * Math.Cos(a);
            sinDec = Math.Max(Math.Sin(-23.44 * D), Math.Min(Math.Sin(23.44 * D), sinDec));
            double dec = Math.Asin(sinDec);
            double cosH = (Math.Sin(e) - Math.Sin(phi) * sinDec) / Math.Max(1e-6, Math.Cos(phi) * Math.Cos(dec));
            double h = Math.Acos(Math.Max(-1.0, Math.Min(1.0, cosH))) / D;   // 0..180, afternoon when the sun is west
            double az = ((azimuthDeg % 360.0) + 360.0) % 360.0;
            if (az < 180.0) h = -h;
            double solarHours = 12.0 + h / 15.0;
            double zone = dec > 0 ? 2.0 : 1.0;
            double clock = solarHours - longitudeDeg / 15.0 + zone;
            int minutes = (int)Math.Round(clock * 60.0);
            return ((minutes % 1440) + 1440) % 1440;
        }
    }
}
