namespace Game.Controls
{
    /// <summary>What kind of value an action carries (Input System action type + expected control).</summary>
    public enum DrivingActionKind : byte { Axis = 0, Button = 1, Stick = 2 }

    /// <summary>One driving action: stable name, value kind, Polish label and the default bindings per device.</summary>
    public sealed class DrivingActionDef
    {
        public readonly string Name;
        public readonly DrivingActionKind Kind;
        /// <summary>Label on the settings screen (PL; the localisation table of this screen).</summary>
        public readonly string LabelPl;
        /// <summary>Default keyboard control paths; empty = unbound (still one empty slot so the player can assign one).</summary>
        public readonly string[] Keyboard;
        /// <summary>Default gamepad control paths (generic &lt;Gamepad&gt; layout: any Xbox- or PlayStation-style pad).</summary>
        public readonly string[] Gamepad;
        /// <summary>false = reserved name, no consumer yet (not shown on the settings screen).</summary>
        public readonly bool Visible;

        public DrivingActionDef(string name, DrivingActionKind kind, string labelPl, string[] keyboard, string[] gamepad, bool visible = true)
        {
            Name = name; Kind = kind; LabelPl = labelPl; Keyboard = keyboard ?? new string[0]; Gamepad = gamepad ?? new string[0]; Visible = visible;
        }
    }

    /// <summary>
    /// Stable action names and default bindings of the driving controls (ADR 0264). The names are the contract shared
    /// by the keyboard, gamepad and (ADR 0263) wheel sources and by saved binding overrides: renaming one needs an
    /// entry in <see cref="InputBindingsStore.ActionRenames"/>. Two action maps carry the same names, one per device
    /// family, so each source reads only its device and shapes it its own way (ramp for keys, curve for sticks).
    /// Pure data (no Input System types): testable without the player.
    /// </summary>
    public static class DrivingActionCatalog
    {
        public const string KeyboardMap = "DrivingKeyboard";
        public const string GamepadMap = "DrivingGamepad";

        public const string Steer = "Steer", Throttle = "Throttle", Brake = "Brake", Clutch = "Clutch";
        public const string ShiftUp = "ShiftUp", ShiftDown = "ShiftDown";
        public const string SelectDrive = "SelectDrive", SelectNeutral = "SelectNeutral", SelectReverse = "SelectReverse";
        public const string ToggleManual = "ToggleManual", ParkingBrake = "ParkingBrake";
        public const string RetarderMore = "RetarderMore", RetarderLess = "RetarderLess";
        public const string Couple = "Couple", LandingGear = "LandingGear", BrakeCruise = "BrakeCruise", ReverseCamera = "ReverseCamera";
        public const string IndicatorLeft = "IndicatorLeft", IndicatorRight = "IndicatorRight", Hazard = "Hazard";
        public const string Horn = "Horn", CycleCamera = "CycleCamera", MirrorInsets = "MirrorInsets", Look = "Look";
        /// <summary>ADR 0283: monitor HUD minimal / extended (default I; rebindable, no pad default).</summary>
        public const string HudDetail = "HudDetail";

        /// <summary>Keyboard steering: 1D-axis composites (negative = left, positive = right), one per pair.</summary>
        public static readonly string[][] KeyboardSteerPairs =
        {
            new[] { "<Keyboard>/a", "<Keyboard>/d" },
            new[] { "<Keyboard>/leftArrow", "<Keyboard>/rightArrow" },
        };

        static string[] K(params string[] p) => p;
        static readonly string[] None = new string[0];

        /// <summary>
        /// All actions in settings-screen order. Defaults = the fixed mapping of ADR 0261 already on main (one documented
        /// layout for the owner): keyboard as KeyboardDriverInput with C (and Tab) = camera, T = couple, L = mirror insets.
        /// Pad: triggers = pedals, left stick = wheel, bumpers = gears, bottom face button = parking brake, left / right
        /// face = D / N, select = R, top face = camera, d-pad left / right = indicators, up = hazard, down / left-stick
        /// press = retarder more / less, right-stick press = horn, right stick = look. Start is left to the menu
        /// (bootstrap, ADR 0261 / 0265).
        /// </summary>
        public static readonly DrivingActionDef[] All =
        {
            new DrivingActionDef(Steer, DrivingActionKind.Axis, "Kierownica", None, K("<Gamepad>/leftStick/x")),
            new DrivingActionDef(Throttle, DrivingActionKind.Axis, "Gaz", K("<Keyboard>/w", "<Keyboard>/upArrow"), K("<Gamepad>/rightTrigger")),
            new DrivingActionDef(Brake, DrivingActionKind.Axis, "Hamulec", K("<Keyboard>/s", "<Keyboard>/downArrow"), K("<Gamepad>/leftTrigger")),
            new DrivingActionDef(Clutch, DrivingActionKind.Axis, "Sprzęgło", None, None, visible: false),   // reserved: AMT has no pedal; wheel sets (ADR 0263)
            new DrivingActionDef(ShiftUp, DrivingActionKind.Button, "Bieg w górę", K("<Keyboard>/e"), K("<Gamepad>/rightShoulder")),
            new DrivingActionDef(ShiftDown, DrivingActionKind.Button, "Bieg w dół", K("<Keyboard>/q"), K("<Gamepad>/leftShoulder")),
            new DrivingActionDef(SelectDrive, DrivingActionKind.Button, "Jazda (D)", K("<Keyboard>/1"), K("<Gamepad>/buttonWest")),
            new DrivingActionDef(SelectNeutral, DrivingActionKind.Button, "Luz (N)", K("<Keyboard>/2"), K("<Gamepad>/buttonEast")),
            new DrivingActionDef(SelectReverse, DrivingActionKind.Button, "Wsteczny (R)", K("<Keyboard>/3"), K("<Gamepad>/select")),
            new DrivingActionDef(ToggleManual, DrivingActionKind.Button, "Tryb ręczny / automat", K("<Keyboard>/m"), None),
            new DrivingActionDef(ParkingBrake, DrivingActionKind.Button, "Hamulec postojowy", K("<Keyboard>/space"), K("<Gamepad>/buttonSouth")),
            new DrivingActionDef(RetarderMore, DrivingActionKind.Button, "Retarder: mocniej", K("<Keyboard>/x"), K("<Gamepad>/dpad/down")),
            new DrivingActionDef(RetarderLess, DrivingActionKind.Button, "Retarder: słabiej", K("<Keyboard>/z"), K("<Gamepad>/leftStickPress")),
            new DrivingActionDef(IndicatorLeft, DrivingActionKind.Button, "Kierunkowskaz w lewo", K("<Keyboard>/comma"), K("<Gamepad>/dpad/left")),
            new DrivingActionDef(IndicatorRight, DrivingActionKind.Button, "Kierunkowskaz w prawo", K("<Keyboard>/period"), K("<Gamepad>/dpad/right")),
            new DrivingActionDef(Hazard, DrivingActionKind.Button, "Światła awaryjne", K("<Keyboard>/h"), K("<Gamepad>/dpad/up")),
            new DrivingActionDef(Horn, DrivingActionKind.Button, "Klakson", K("<Keyboard>/k"), K("<Gamepad>/rightStickPress")),
            new DrivingActionDef(CycleCamera, DrivingActionKind.Button, "Zmiana kamery", K("<Keyboard>/c", "<Keyboard>/tab"), K("<Gamepad>/buttonNorth")),
            new DrivingActionDef(MirrorInsets, DrivingActionKind.Button, "Lusterka w oknach", K("<Keyboard>/l"), None),
            new DrivingActionDef(HudDetail, DrivingActionKind.Button, "HUD: tryb rozszerzony", K("<Keyboard>/i"), None),
            new DrivingActionDef(ReverseCamera, DrivingActionKind.Button, "Kamera cofania", K("<Keyboard>/v"), None),
            new DrivingActionDef(BrakeCruise, DrivingActionKind.Button, "Tempomat zjazdu", K("<Keyboard>/b"), None),
            new DrivingActionDef(Couple, DrivingActionKind.Button, "Sprzęg naczepy", K("<Keyboard>/t"), None),
            new DrivingActionDef(LandingGear, DrivingActionKind.Button, "Podpory naczepy", K("<Keyboard>/g"), None),
            new DrivingActionDef(Look, DrivingActionKind.Stick, "Rozglądanie", None, K("<Gamepad>/rightStick")),
        };

        // ------------------------------------------------------------------ asset JSON

        /// <summary>
        /// Deterministic GUID of a map / action / binding: MD5 of <c>"kamion.driving/" + key</c>. Binding overrides
        /// are matched by binding id when loaded, so the ids must be the same in every run and build; they depend only
        /// on map name, action name and the binding's index in that action (part of the ADR 0264 contract).
        /// </summary>
        public static string StableId(string key)
        {
            using (var md5 = System.Security.Cryptography.MD5.Create())
            {
                var bytes = md5.ComputeHash(System.Text.Encoding.UTF8.GetBytes("kamion.driving/" + key));
                return new System.Guid(bytes).ToString();
            }
        }

        /// <summary>
        /// The Input System action-asset JSON (same format as an <c>.inputactions</c> file) of both driving maps with the
        /// default bindings and stable ids. Unbound visible actions get one empty binding slot (assignable in settings).
        /// </summary>
        public static string BuildAssetJson()
        {
            var sb = new System.Text.StringBuilder(16384);
            sb.Append("{\"name\":\"DrivingActions\",\"maps\":[");
            AppendMap(sb, KeyboardMap, keyboard: true);
            sb.Append(',');
            AppendMap(sb, GamepadMap, keyboard: false);
            sb.Append("],\"controlSchemes\":[]}");
            return sb.ToString();
        }

        static void AppendMap(System.Text.StringBuilder sb, string map, bool keyboard)
        {
            sb.Append("{\"name\":\"").Append(map).Append("\",\"id\":\"").Append(StableId(map)).Append("\",\"actions\":[");
            for (int i = 0; i < All.Length; i++)
            {
                var d = All[i];
                if (i > 0) sb.Append(',');
                string type = d.Kind == DrivingActionKind.Button ? "Button" : "Value";
                string ctl = d.Kind == DrivingActionKind.Axis ? "Axis" : d.Kind == DrivingActionKind.Stick ? "Vector2" : "Button";
                sb.Append("{\"name\":\"").Append(d.Name).Append("\",\"type\":\"").Append(type)
                  .Append("\",\"id\":\"").Append(StableId(map + "/" + d.Name))
                  .Append("\",\"expectedControlType\":\"").Append(ctl)
                  .Append("\",\"processors\":\"\",\"interactions\":\"\",\"initialStateCheck\":").Append(d.Kind == DrivingActionKind.Button ? "false" : "true").Append('}');
            }
            sb.Append("],\"bindings\":[");
            bool first = true;
            foreach (var d in All)
            {
                int index = 0;
                string prefix = map + "/" + d.Name + "/";
                if (keyboard && d.Name == Steer)
                {
                    foreach (var pair in KeyboardSteerPairs)
                    {
                        Binding(sb, ref first, prefix + index++, "1D Axis", "1DAxis", d.Name, composite: true, part: false);
                        Binding(sb, ref first, prefix + index++, "negative", pair[0], d.Name, composite: false, part: true);
                        Binding(sb, ref first, prefix + index++, "positive", pair[1], d.Name, composite: false, part: true);
                    }
                    continue;
                }
                var paths = keyboard ? d.Keyboard : d.Gamepad;
                if (paths.Length == 0)
                {
                    if (d.Visible) Binding(sb, ref first, prefix + index, "", "", d.Name, false, false);
                    continue;
                }
                foreach (var p in paths) Binding(sb, ref first, prefix + index++, "", p, d.Name, false, false);
            }
            sb.Append("]}");
        }

        static void Binding(System.Text.StringBuilder sb, ref bool first, string idKey, string name, string path, string action, bool composite, bool part)
        {
            if (!first) sb.Append(',');
            first = false;
            sb.Append("{\"name\":\"").Append(name).Append("\",\"id\":\"").Append(StableId(idKey))
              .Append("\",\"path\":\"").Append(path).Append("\",\"interactions\":\"\",\"processors\":\"\",\"groups\":\"\",\"action\":\"").Append(action)
              .Append("\",\"isComposite\":").Append(composite ? "true" : "false")
              .Append(",\"isPartOfComposite\":").Append(part ? "true" : "false").Append('}');
        }

        /// <summary>Definition by name, or null.</summary>
        public static DrivingActionDef Find(string name)
        {
            for (int i = 0; i < All.Length; i++) if (All[i].Name == name) return All[i];
            return null;
        }

        /// <summary>
        /// Generic Polish name of a gamepad control (no maker's button glyphs or letters: positions only, so the same
        /// text fits Xbox- and PlayStation-style pads). Unknown paths are returned without the layout prefix.
        /// </summary>
        public static string GamepadControlLabel(string path)
        {
            if (string.IsNullOrEmpty(path)) return "—";
            int slash = path.IndexOf('/');
            string c = slash >= 0 ? path.Substring(slash + 1) : path;
            switch (c)
            {
                case "buttonSouth": return "przycisk dolny";
                case "buttonEast": return "przycisk prawy";
                case "buttonWest": return "przycisk lewy";
                case "buttonNorth": return "przycisk górny";
                case "leftShoulder": return "lewy bumper";
                case "rightShoulder": return "prawy bumper";
                case "leftTrigger": return "lewy spust";
                case "rightTrigger": return "prawy spust";
                case "dpad/up": return "krzyżak w górę";
                case "dpad/down": return "krzyżak w dół";
                case "dpad/left": return "krzyżak w lewo";
                case "dpad/right": return "krzyżak w prawo";
                case "leftStick": return "lewa gałka";
                case "rightStick": return "prawa gałka";
                case "leftStick/x": return "lewa gałka (poziomo)";
                case "leftStick/y": return "lewa gałka (pionowo)";
                case "rightStick/x": return "prawa gałka (poziomo)";
                case "rightStick/y": return "prawa gałka (pionowo)";
                case "leftStickPress": return "wciśnięcie lewej gałki";
                case "rightStickPress": return "wciśnięcie prawej gałki";
                case "select": return "środkowy lewy przycisk";
                case "start": return "środkowy prawy przycisk";
                default: return c;
            }
        }
    }
}
