using System.Globalization;

namespace Game.World.Packs
{
    /// <summary>
    /// Polish menu texts for a region pack state (ADR 0234 §6) - the region picker of ADR 0229 (PR #104) puts
    /// <see cref="Detail"/> into its detail line and <see cref="Action"/> on its start button. Pure strings, no UI objects.
    /// </summary>
    public static class RegionPackLabels
    {
        public const string StartLabel = "Jedź w wybranym regionie";
        public const string DownloadLabel = "Pobierz paczkę regionu";
        public const string RetryLabel = "Pobierz paczkę ponownie";
        public const string UnavailableLabel = "Region niedostępny w tym APK";
        public const string IncompatibleLabel = "Paczka niezgodna z tym APK";
        public const string LoadingLabel = "Wczytywanie paczki…";

        /// <summary>"52,3 MB" (Polish decimal comma, 1 MB = 1 048 576 B like the build reports).</summary>
        public static string Megabytes(long bytes)
        {
            double mb = bytes / 1048576.0;
            return mb.ToString(mb < 10 ? "0.0" : "0", CultureInfo.InvariantCulture).Replace('.', ',') + " MB";
        }

        /// <summary>Detail line for the picker, e.g. "paczka pobrana · 52,3 MB".</summary>
        public static string Detail(in RegionPackInfo info, bool downloadEnabled)
        {
            switch (info.State)
            {
                case RegionPackState.InBase: return "w APK";
                case RegionPackState.Loaded: return "paczka wczytana";
                case RegionPackState.Installed: return "paczka pobrana · " + Megabytes(info.SizeBytes);
                case RegionPackState.Downloading:
                    return "pobieranie " + ((int)(info.Progress * 100f + 0.5f)).ToString(CultureInfo.InvariantCulture) + " % · " + Megabytes(info.SizeBytes);
                case RegionPackState.NotInstalled:
                    if (info.SizeBytes > 0 && downloadEnabled) return "do pobrania · " + Megabytes(info.SizeBytes);
                    return downloadEnabled ? "brak paczki w katalogu pobierania" : "brak paczki (wgraj przez adb)";
                case RegionPackState.MissingDependency:
                    return downloadEnabled ? "brak paczki wspólnej · do pobrania " + Megabytes(info.SizeBytes) : "brak paczki wspólnej (common)";
                case RegionPackState.Corrupt: return "paczka uszkodzona · pobierz ponownie";
                case RegionPackState.Incompatible: return "paczka z innej wersji gry · zaktualizuj paczki";
                default: return "";
            }
        }

        /// <summary>Text of the start button for a state (download offered only when a download URL is configured).</summary>
        public static string Action(in RegionPackInfo info, bool downloadEnabled)
        {
            switch (info.State)
            {
                case RegionPackState.InBase:
                case RegionPackState.Installed:
                case RegionPackState.Loaded: return StartLabel;
                case RegionPackState.Downloading: return LoadingLabel;
                case RegionPackState.Incompatible: return IncompatibleLabel;
                case RegionPackState.Corrupt: return downloadEnabled ? RetryLabel : UnavailableLabel;
                default: return downloadEnabled && info.SizeBytes > 0 ? DownloadLabel : UnavailableLabel;
            }
        }

        /// <summary>True when pressing the button should start a download instead of the drive.</summary>
        public static bool ActionDownloads(in RegionPackInfo info, bool downloadEnabled) =>
            downloadEnabled && info.SizeBytes > 0 &&
            (info.State == RegionPackState.NotInstalled || info.State == RegionPackState.MissingDependency || info.State == RegionPackState.Corrupt);
    }
}
