namespace Game.Gameplay
{
    /// <summary>
    /// Player texts of the start safety net (ADR 0277), Polish. One table per feature, as
    /// <c>Game.UI.Settings.PcSettingsTexts</c>: the project has no localisation package yet; when it gets one these
    /// constants become its PL table entries (same keys = the field names).
    /// </summary>
    public static class StartSafetyTexts
    {
        /// <summary>Scene the player returns to when a start fails (the start menu).</summary>
        public const string MenuScene = "Boot";

        /// <summary>Start menu notice after a start that found no free place (shown once, amber line under the title).</summary>
        public const string NoSpaceMessage =
            "Nie udało się ustawić zestawu na starcie: na drodze w tym regionie nie ma wolnego miejsca. " +
            "Ciężarówka nie została postawiona. Wybierz inny region lub inny start.";

        /// <summary>HUD line when a respawn on the route (route_s, tests) found no free place: the combination stays where it is.</summary>
        public const string NoSpaceRespawn = "Brak wolnego miejsca na trasie: zestaw zostaje na miejscu.";
    }
}
