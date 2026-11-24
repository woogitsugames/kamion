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

        /// <summary>Roundabout-name clip in the nominative (B15 "Rondo Putry.", ADR 0329 addendum), said after B07 "Na rondzie zjedź ..."
        /// without a second "na rondzie"; (0,0) when the ring is not one of the named roundabouts of the region.</summary>
        public static VoiceClip RoundaboutNominativeClip(string ringName)
        {
            if (ringName != null && ringName.StartsWith("Rondo Krzysztofa Jakuba Putry", System.StringComparison.Ordinal)) return new VoiceClip(15, 1);
            if (ringName != null && ringName.StartsWith("Rondo Pamięci Bieżeństwa", System.StringComparison.Ordinal)) return new VoiceClip(15, 2);
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
        public static int Plan(RouteGraph g, RoutePath p, ref NavGuidance gd, float speedMs, VoiceClip[] buf) =>
            PlanBand(g, p, ref gd, BandFor(gd.NextM, speedMs), buf);

        /// <summary>Name of the ring of roundabout manoeuvre <paramref name="man"/>: the first non-empty segment name along
        /// the ring itself (<c>ManPoint[man] .. ManEndPoint[man] - 1</c>; never scanning onto the incoming or exit road).
        /// null when the ring is unnamed. No allocation.</summary>
        public static string RingName(RouteGraph g, RoutePath p, int man)
        {
            int from = p.ManPoint[man];
            int end = p.ManEndPoint[man];
            int to = end > from ? end - 1 : from;
            for (int i = from; i <= to && i < p.Count; i++)
            {
                int ni = p.Name[i];
                if (ni >= g.Names.Length) continue;   // a path from another graph (trip vs region names) must never throw
                string n = g.Names[ni];
                if (!string.IsNullOrEmpty(n)) return n;
            }
            return null;
        }

        /// <summary>As <see cref="Plan"/>, with the distance band chosen by the caller (<see cref="NavVoiceDriver"/> tiers;
        /// -1 = no distance sentence). No allocation.</summary>
        public static int PlanBand(RouteGraph g, RoutePath p, ref NavGuidance gd, int band, VoiceClip[] buf)
        {
            int n = 0;
            if (buf == null || buf.Length == 0 || g == null || p == null || gd.Next < 0 || gd.Next >= p.ManCount) return 0;
            Maneuver m = p.ManType[gd.Next];
            // Arrival (ADR 0329): the pack has no "za X metrow cel" sentence, so "Jestes u celu" is said only AT the destination
            // (the now band) - never in a far / near announcement (it used to be said 500 m before the end) - and alone: a street
            // suffix, "a nastepnie" or lane guidance after it make no sense.
            if (m == Maneuver.Arrive)
            {
                if (band != NowBand) return 0;
                buf[0] = new VoiceClip(10, 11);
                return 1;
            }
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
                if (m == Maneuver.Continue) { buf[n++] = new VoiceClip(10, 5); }
                else if (idx > 0) buf[n++] = new VoiceClip(blk, (byte)idx);
                if (m == Maneuver.Roundabout && n < buf.Length)
                {
                    buf[n++] = RoundaboutExitClip(p.ManTurn[gd.Next], gd.NextExit);
                    // The ring name goes in the nominative (B15 "Rondo Putry."), a separate sentence after B07 "Na rondzie zjedz ...":
                    // B14 "na rondzie Putry." would say "na rondzie" twice (ADR 0329). Only in the manoeuvre bands where B07 is spoken.
                    if (n < buf.Length)
                    {
                        VoiceClip rc = RoundaboutNominativeClip(RingName(g, p, gd.Next));
                        if (rc.Block != 0) buf[n++] = rc;
                    }
                }
            }
            if (n < buf.Length)
            {
                int si = p.ManName[gd.Next];
                VoiceClip sc = StreetClip(si < g.Names.Length ? g.Names[si] : null);
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
    /// Drives <see cref="NavVoice.PlanBand"/> along a route (ADR 0168): at most THREE announcements per manoeuvre -
    /// far (2 km / 1 km / 500 m), near (300 / 200 / 100 m) and now - each said at most once. A tier is said when the distance
    /// first falls below its trigger; only the closest due tier is said (a route that starts 150 m before a turn says
    /// "near" only, never far + near together). Tiers are monotone per manoeuvre: distance drift back over a trigger
    /// (projection jitter, stopping, slowing down) never repeats a sentence, and the guidance flipping back to an already
    /// passed manoeuvre is ignored. A new route (version / reference) or <see cref="Reset"/> starts over.
    /// Triggers depend on the speed (WORKING_VALUES): far = 2000/1000/500 m band at or below v * <see cref="FarLeadS"/>
    /// (min 500 m), near = 300/200/100 m band at or below v * <see cref="NearLeadS"/> (min 100 m), now = max(reaction +
    /// braking distance, <see cref="NowMinM"/>). No allocation in the update loop.
    /// </summary>
    public sealed class NavVoiceDriver
    {
        public const int TierNone = 0, TierFar = 1, TierNear = 2, TierNow = 3;
        /// <summary>Lead times [s] of the far / near announcement and the minimum "now" distance [m]. WORKING_VALUES (ADR 0168):
        /// 45 s gives 500 m at 50 km/h and 1 km at 80 km/h; 15 s gives 200 m at 50 km/h and 300 m at 80 km/h.</summary>
        public const float FarLeadS = 45f, NearLeadS = 15f, NowMinM = 30f;
        /// <summary>Near is skipped when its trigger is closer than this to the "now" trigger [m] (two sentences back to back).</summary>
        public const float MinTierGapM = 40f;

        readonly VoiceClip[] m_Buf = new VoiceClip[6];
        RoutePath m_Path;
        int m_Version = int.MinValue;
        int m_Man = -1;
        int m_Said = TierNone;

        /// <summary>Tier said last for the current manoeuvre (TierNone..TierNow) and how many announcements were made for it.</summary>
        public int LastTier => m_Said;
        public int CurrentManeuver => m_Man;

        public void Reset() { m_Path = null; m_Version = int.MinValue; m_Man = -1; m_Said = TierNone; }

        /// <summary>Far trigger [m] at this speed: 2000 / 1000 / 500.</summary>
        public static float FarM(float speedMs)
        {
            float d = speedMs * FarLeadS;
            return d >= 2000f ? 2000f : d >= 1000f ? 1000f : 500f;
        }

        /// <summary>Near trigger [m] at this speed: 300 / 200 / 100; 0 = no near tier (too close to "now").</summary>
        public static float NearM(float speedMs)
        {
            float d = speedMs * NearLeadS;
            float near = d >= 300f ? 300f : d >= 200f ? 200f : 100f;
            return near - NowM(speedMs) >= MinTierGapM ? near : 0f;
        }

        /// <summary>"Now" trigger [m]: reaction + braking distance of the laden truck, at least <see cref="NowMinM"/>.</summary>
        public static float NowM(float speedMs) => Mathf.Max(NavVoice.SafeAnnounceM(speedMs), NowMinM);

        /// <summary>The closest tier due at distance <paramref name="distM"/> (TierNone when farther than the far trigger).</summary>
        public static int TierFor(float distM, float speedMs)
        {
            if (distM <= NowM(speedMs)) return TierNow;
            float near = NearM(speedMs);
            if (near > 0f && distM <= near) return TierNear;
            if (distM <= FarM(speedMs)) return TierFar;
            return TierNone;
        }

        /// <summary>Distance band spoken for a tier: the smallest band of the tier that contains the distance.</summary>
        public static int BandForTier(int tier, float distM)
        {
            switch (tier)
            {
                case TierFar: return distM <= 500f ? 2 : distM <= 1000f ? 1 : 0;
                case TierNear: return distM <= 100f ? 5 : distM <= 200f ? 4 : 3;
                case TierNow: return NavVoice.NowBand;
                default: return -1;
            }
        }

        /// <summary>Plans the sentences for the current guidance state; returns how many clips were enqueued.</summary>
        public int Update(RouteGraph g, RoutePath p, ref NavGuidance gd, float speedMs, NavVoiceQueue q)
        {
            if (p == null || gd.Next < 0 || gd.Next >= p.ManCount) return 0;
            if (!ReferenceEquals(p, m_Path) || p.Version != m_Version) { m_Path = p; m_Version = p.Version; m_Man = -1; m_Said = TierNone; }
            if (gd.Next < m_Man) return 0;                                  // flip back to a passed manoeuvre: ignore
            if (gd.Next > m_Man) { m_Man = gd.Next; m_Said = TierNone; }
            int tier = TierFor(gd.NextM, speedMs);
            if (tier <= m_Said) return 0;                                   // already said (or farther tier): no repeats
            m_Said = tier;
            int n = NavVoice.PlanBand(g, p, ref gd, BandForTier(tier, gd.NextM), m_Buf);
            int enq = 0;
            for (int i = 0; i < n; i++) if (q.Enqueue(m_Buf[i])) enq++;
            return enq;
        }
    }
    /// <summary>
    /// Announcement hub of the GPS voice: <see cref="NavVoiceDriver"/> + <see cref="NavVoiceQueue"/> + evidence log. Every
    /// ordered announcement (rare: at most 3 per manoeuvre) is drained from the queue and, when <see cref="LogEnabled"/>
    /// (launch argument <c>-nav_log &lt;s&gt;</c>, off by default), written as ONE line
    /// <c>NAVVOICE t=123.4 band=300 clips=B07#2,B14#1 man=Roundabout ring="Rondo ..."</c> to <see cref="Sink"/> (Debug.Log), so a
    /// verification drive of a build can confirm what the voice said. <see cref="Spoken"/> is the hook for the future audio
    /// player. Strings are built only at announcement time; the per-frame path allocates nothing.
    /// </summary>
    public sealed class NavVoiceAnnouncer
    {
        public bool LogEnabled;
        /// <summary>Receives the log line; defaults to Debug.Log (tests replace it).</summary>
        public System.Action<string> Sink = Debug.Log;
        /// <summary>Called once per announcement with the clips in order (the buffer is reused - copy if kept).</summary>
        public System.Action<VoiceClip[], int> Spoken;
        public int Announcements { get; private set; }

        readonly NavVoiceDriver m_Driver = new NavVoiceDriver();
        readonly NavVoiceQueue m_Queue = new NavVoiceQueue();
        readonly VoiceClip[] m_Out = new VoiceClip[NavVoiceQueue.Capacity];

        public bool Active => LogEnabled || Spoken != null;
        public void Reset() { m_Driver.Reset(); m_Queue.Clear(); }

        /// <summary>Per-frame step; <paramref name="timeS"/> only goes into the log line.</summary>
        public void Update(RouteGraph g, RoutePath p, ref NavGuidance gd, float speedMs, float timeS)
        {
            if (!Active || g == null || p == null) return;
            if (m_Driver.Update(g, p, ref gd, speedMs, m_Queue) == 0) return;
            int n = 0;
            while (n < m_Out.Length && m_Queue.TryDequeue(out VoiceClip c)) m_Out[n++] = c;
            if (n == 0) return;
            Announcements++;
            Spoken?.Invoke(m_Out, n);
            if (LogEnabled && Sink != null) Sink(Format(g, p, ref gd, timeS, m_Driver.LastTier, m_Out, n));
        }

        /// <summary>The log line of one announcement (allocates - only called when logging).</summary>
        public static string Format(RouteGraph g, RoutePath p, ref NavGuidance gd, float timeS, int tier, VoiceClip[] clips, int n)
        {
            var sb = new System.Text.StringBuilder(96);
            sb.Append("NAVVOICE t=").Append(timeS.ToString("0.0", System.Globalization.CultureInfo.InvariantCulture));
            int band = NavVoiceDriver.BandForTier(tier, gd.NextM);
            sb.Append(" band=");
            if (band < 0) sb.Append('-');
            else if (band >= NavVoice.BandM.Length) sb.Append("now");
            else sb.Append((int)NavVoice.BandM[band]);
            sb.Append(" clips=");
            for (int i = 0; i < n; i++)
            {
                if (i > 0) sb.Append(',');
                sb.Append('B').Append(clips[i].Block.ToString("00")).Append('#').Append(clips[i].Index);
            }
            if (gd.Next >= 0 && gd.Next < p.ManCount)
            {
                sb.Append(" man=").Append(p.ManType[gd.Next]);
                if (p.ManType[gd.Next] == Maneuver.Roundabout)
                {
                    string ring = NavVoice.RingName(g, p, gd.Next);
                    if (!string.IsNullOrEmpty(ring)) sb.Append(" ring=\"").Append(ring).Append('"');
                }
                int si = p.ManName[gd.Next];
                string street = si < g.Names.Length ? g.Names[si] : null;
                if (!string.IsNullOrEmpty(street)) sb.Append(" street=\"").Append(street).Append('"');
            }
            return sb.ToString();
        }
    }
}
