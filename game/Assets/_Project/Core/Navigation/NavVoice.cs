using UnityEngine;

namespace Game.Core.Navigation
{
    /// <summary>One recorded sentence of the GPS voice pack (docs/owner/ELEVENLABS-GPS-VOICE.md): block GPS_Bxx, 1-based index in it.</summary>
    public readonly struct VoiceClip : System.IEquatable<VoiceClip>
    {
        public readonly byte Block, Index;
        public VoiceClip(byte block, byte index) { Block = block; Index = index; }
        public bool Equals(VoiceClip o) => Block == o.Block && Index == o.Index;
        public override bool Equals(object o) => o is VoiceClip c && Equals(c);
        public override int GetHashCode() => Block * 31 + Index;
        public static bool operator ==(VoiceClip a, VoiceClip b) => a.Equals(b);
        public static bool operator !=(VoiceClip a, VoiceClip b) => !a.Equals(b);
        public override string ToString() => "GPS_B" + Block.ToString("00") + " #" + Index;
    }

    /// <summary>
    /// Choice of the GPS voice sentences (docs/owner/ELEVENLABS-GPS-VOICE.md) - pure functions, no audio files, no allocation
    /// (clips are written into a caller buffer). Distance bands depend on the speed: a manoeuvre is announced no closer than
    /// the reaction + braking distance of the laden truck - WORKING_VALUE rachunek: t_react 1.5 s, a_brake 3.0 m/s^2 (dry asphalt),
    /// d(v) = v*1.5 + v^2/6; at 80 km/h = 116 m, at 50 km/h = 53 m, so at the motorway limit "za sto metrów" is never said.
    /// </summary>
    public static class NavVoice
    {
        /// <summary>Reaction time [s] (WORKING_VALUE) and braking deceleration [m/s^2] (WORKING_VALUE, laden 40 t, dry asphalt).</summary>
        public const float ReactS = 1.5f, BrakeDecelMs2 = 3.0f;
        /// <summary>Reaction + braking distance [m] - the smallest distance at which a band may be announced at this speed.</summary>
        public static float SafeAnnounceM(float speedMs) => speedMs * ReactS + speedMs * speedMs / (2f * BrakeDecelMs2);

        // Bands: 2000 / 1000 / 500 / 300 / 200 / 100 m, then "now". Block per band: B06 (km variants), B06, B05, B04, B03, B02, B01.
        public static readonly float[] BandM = { 2000f, 1000f, 500f, 300f, 200f, 100f };
        public static readonly byte[] BandBlock = { 6, 6, 5, 4, 3, 2, 1 };
        public const int NowBand = 6;

        /// <summary>Band index (0 = 2000 m .. 5 = 100 m, 6 = "now") for a manoeuvre at <paramref name="distM"/> at <paramref name="speedMs"/>; -1 = too far.
        /// The band is the smallest one that still contains the distance (450 m -> "500 m"); "now" when the band or the distance
        /// is below the reaction + braking distance.</summary>
        public static int BandFor(float distM, float speedMs)
        {
            float safe = SafeAnnounceM(speedMs);
            int b = -1;
            for (int i = BandM.Length - 1; i >= 0; i--) if (distM <= BandM[i]) { b = i; break; }
            if (b < 0) return -1;
            if (BandM[b] < safe || distM < safe) return NowBand;
            return b;
        }

        /// <summary>Index of the manoeuvre sentence inside blocks B01..B05 (1 right, 2 left, 3 keep right, 4 keep left, 5 sharp right,
        /// 6 sharp left, 7 U-turn, 8 enter roundabout); 0 = no variant (Continue / Arrive).</summary>
        public static int ManIndex(Maneuver m)
        {
            switch (m)
            {
                case Maneuver.Right: return 1;
                case Maneuver.Left: return 2;
                case Maneuver.SlightRight: return 3;
                case Maneuver.SlightLeft: return 4;
                case Maneuver.SharpRight: return 5;
                case Maneuver.SharpLeft: return 6;
                case Maneuver.UTurn: return 7;
                case Maneuver.Roundabout: return 8;
                default: return 0;
            }
        }

        /// <summary>Index inside B06 for the 1 km (1..5) / 2 km (6..10) variants (right, left, keep right, keep left, roundabout); 0 = no km variant.</summary>
        public static int ManIndexKm(Maneuver m, bool twoKm)
        {
            int i = m == Maneuver.Right ? 1 : m == Maneuver.Left ? 2 : m == Maneuver.SlightRight ? 3 : m == Maneuver.SlightLeft ? 4 : m == Maneuver.Roundabout ? 5 : 0;
            return i == 0 ? 0 : i + (twoKm ? 5 : 0);
        }

        /// <summary>Street-name suffix clip (B12/B13 of the pack) for a graph name; (0,0) when the street is not in the pack.</summary>
        public static VoiceClip StreetClip(string name)
        {
            switch (name)
            {
                case "Generała Władysława Andersa": return new VoiceClip(12, 1);
                case "Generała Stanisława Maczka": return new VoiceClip(12, 2);
                case "Aleja Tysiąclecia Państwa Polskiego": return new VoiceClip(12, 3);
                case "Bitwy Białostockiej": return new VoiceClip(12, 4);
                case "Białostoczek": return new VoiceClip(12, 5);
                case "Kombatantów": return new VoiceClip(12, 6);
                case "Michała Motoszko": return new VoiceClip(12, 7);
                case "Stefana Batorego": return new VoiceClip(12, 8);
                case "Władysława Bełzy": return new VoiceClip(12, 9);
                case "Wileńska": return new VoiceClip(12, 10);
                case "Sokólska": return new VoiceClip(12, 11);
                case "Grodzieńska": return new VoiceClip(12, 12);
                case "Brzeska": return new VoiceClip(13, 1);
                case "Buska": return new VoiceClip(13, 2);
                case "Kowieńska": return new VoiceClip(13, 3);
                case "Lidzka": return new VoiceClip(13, 4);
                case "Olsztyńska": return new VoiceClip(13, 5);
                case "Racławicka": return new VoiceClip(13, 6);
                case "Sitarska": return new VoiceClip(13, 7);
                case "Skidelska": return new VoiceClip(13, 8);
                case "Wołkowyska": return new VoiceClip(13, 9);
                case "Łańcucka": return new VoiceClip(13, 10);
                case "Świsłocka": return new VoiceClip(13, 11);
                default: return new VoiceClip(0, 0);
            }
        }

        /// <summary>Roundabout-name clip (B14) when the ring is one of the named roundabouts of the region; (0,0) otherwise.</summary>
        public static VoiceClip RoundaboutNameClip(string ringName)
        {
            if (ringName != null && ringName.StartsWith("Rondo Krzysztofa Jakuba Putry", System.StringComparison.Ordinal)) return new VoiceClip(14, 1);
            if (ringName != null && ringName.StartsWith("Rondo Pamięci Bieżeństwa", System.StringComparison.Ordinal)) return new VoiceClip(14, 2);
            return new VoiceClip(0, 0);
        }

        /// <summary>B07 clip for a roundabout manoeuvre: #1..#5 = N-th exit, #6 = turn round on the roundabout, #7 = straight through.</summary>
        public static VoiceClip RoundaboutExitClip(float turnDeg, byte exit)
        {
            if (Mathf.Abs(turnDeg) > 150f) return new VoiceClip(7, 6);
            if (exit >= 1 && exit <= 5) return new VoiceClip(7, exit);
            return new VoiceClip(7, 7);
        }

        /// <summary>B08 "a następnie" clip for the manoeuvre after the next; (0,0) for none.</summary>
        public static VoiceClip ThenClip(Maneuver then)
        {
            switch (then)
            {
                case Maneuver.Right: return new VoiceClip(8, 1);
                case Maneuver.Left: return new VoiceClip(8, 2);
                case Maneuver.SlightRight: return new VoiceClip(8, 3);
                case Maneuver.SlightLeft: return new VoiceClip(8, 4);
                case Maneuver.Roundabout: return new VoiceClip(8, 5);
                case Maneuver.UTurn: return new VoiceClip(8, 6);
                case Maneuver.Arrive: return new VoiceClip(8, 7);
                default: return new VoiceClip(0, 0);
            }
        }

        /// <summary>B09 lane clip from the recommended-lane mask (bit i = lane i, leftmost = bit 0); (0,0) = no guidance.</summary>
        public static VoiceClip LaneClip(byte laneCount, uint recMask)
        {
            if (laneCount < 2 || recMask == 0u) return new VoiceClip(0, 0);
            if (recMask == (1u << (laneCount - 1))) return new VoiceClip(9, 1);          // rightmost lane
            if (recMask == 1u) return new VoiceClip(9, 2);                                  // leftmost lane
            if (laneCount == 3 && recMask == 2u) return new VoiceClip(9, 3);                // middle lane
            if (laneCount >= 2 && recMask == (3u << (laneCount - 2))) return new VoiceClip(9, 4);   // two right lanes
            if (laneCount >= 2 && recMask == 3u) return new VoiceClip(9, 5);                // two left lanes
            return new VoiceClip(0, 0);
        }

        /// <summary>
        /// Pure function: the sentences for one guidance snapshot. Writes up to <paramref name="buf"/> and returns the count:
        /// the manoeuvre at its distance band (speed-dependent, "now" when closer than the reaction + braking distance),
        /// the street-name suffix, the roundabout exit / name, the "then" manoeuvre and the lane guidance. No allocation.
        /// </summary>
        public static int Plan(RouteGraph g, RoutePath p, ref NavGuidance gd, float speedMs, VoiceClip[] buf)
        {
            int n = 0;
            if (buf == null || buf.Length == 0 || g == null || p == null || gd.Next < 0 || gd.Next >= p.ManCount) return 0;
            Maneuver m = p.ManType[gd.Next];
            int band = BandFor(gd.NextM, speedMs);
            if (band >= 0 && n < buf.Length)
            {
                byte blk = BandBlock[band];
                int idx;
                if (blk == 6)
                {
                    idx = ManIndexKm(m, band == 0);
                    if (idx == 0) { blk = 5; idx = ManIndex(m); }   // no km variant (sharp / U-turn): fall back to the 500 m block
                }
                else idx = ManIndex(m);
                if (m == Maneuver.Arrive) { buf[n++] = new VoiceClip(10, 11); }
                else if (m == Maneuver.Continue) { buf[n++] = new VoiceClip(10, 5); }
                else if (idx > 0) buf[n++] = new VoiceClip(blk, (byte)idx);
                if (m == Maneuver.Roundabout && n < buf.Length)
                {
                    buf[n++] = RoundaboutExitClip(p.ManTurn[gd.Next], gd.NextExit);
                    // ManName of a roundabout manoeuvre is the exit street; the ring's name is on the path segment that
                    // starts at the manoeuvre point (the first ring edge).
                    string ring = g.Names[p.Name[p.ManPoint[gd.Next]]];
                    VoiceClip rc = RoundaboutNameClip(ring);
                    if (rc.Block != 0 && n < buf.Length) buf[n++] = rc;
                }
            }
            if (n < buf.Length)
            {
                VoiceClip sc = StreetClip(g.Names[p.ManName[gd.Next]]);
                if (sc.Block != 0) buf[n++] = sc;
            }
            if (gd.Then >= 0 && gd.Then < p.ManCount && n < buf.Length)
            {
                VoiceClip tc = ThenClip(p.ManType[gd.Then]);
                if (tc.Block != 0) buf[n++] = tc;
            }
            if (n < buf.Length)
            {
                VoiceClip lc = LaneClip(gd.NextLaneCount, gd.NextLanesRec);
                if (lc.Block != 0) buf[n++] = lc;
            }
            return n;
        }
    }

    /// <summary>
    /// Voice queue without repeats: fixed capacity, enqueueing a clip equal to any of the last <see cref="NoRepeatWindow"/>
    /// is dropped. No allocation (the clip array is allocated once).
    /// </summary>
    public sealed class NavVoiceQueue
    {
        public const int Capacity = 8, NoRepeatWindow = 3;
        readonly VoiceClip[] m_Items = new VoiceClip[Capacity];
        int m_Head, m_Count;

        public int Count => m_Count;
        public void Clear() { m_Head = 0; m_Count = 0; }

        public bool Enqueue(VoiceClip c)
        {
            int window = System.Math.Min(m_Count, NoRepeatWindow);
            for (int i = 0; i < window; i++)
                if (m_Items[(m_Head + m_Count - 1 - i + Capacity) % Capacity] == c) return false;
            if (m_Count >= Capacity) return false;
            m_Items[(m_Head + m_Count) % Capacity] = c;
            m_Count++;
            return true;
        }

        public bool TryDequeue(out VoiceClip c)
        {
            if (m_Count == 0) { c = default; return false; }
            c = m_Items[m_Head];
            m_Head = (m_Head + 1) % Capacity;
            m_Count--;
            return true;
        }
    }

    /// <summary>
    /// Drives <see cref="NavVoice.Plan"/> along a route: announces each manoeuvre once per distance band (a closer band
    /// re-announces), clips go into a <see cref="NavVoiceQueue"/> without repeats. No allocation in the update loop.
    /// </summary>
    public sealed class NavVoiceDriver
    {
        readonly VoiceClip[] m_Buf = new VoiceClip[6];
        int m_LastMan = -1;
        int m_LastBand = -1;

        public void Reset() { m_LastMan = -1; m_LastBand = -1; }

        /// <summary>Plans the sentences for the current guidance state; returns how many were enqueued.</summary>
        public int Update(RouteGraph g, RoutePath p, ref NavGuidance gd, float speedMs, NavVoiceQueue q)
        {
            int enq = 0;
            if (p != null && gd.Next >= 0 && gd.Next < p.ManCount)
            {
                int band = NavVoice.BandFor(gd.NextM, speedMs);
                if (band >= 0 && (gd.Next != m_LastMan || band > m_LastBand))
                {
                    m_LastMan = gd.Next; m_LastBand = band;
                    int n = NavVoice.Plan(g, p, ref gd, speedMs, m_Buf);
                    for (int i = 0; i < n; i++) if (q.Enqueue(m_Buf[i])) enq++;
                }
            }
            return enq;
        }
    }
}
