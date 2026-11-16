namespace Game.Controls
{
    /// <summary>Menu commands (ADR 0283). Stored nowhere; the order is the help-line order.</summary>
    public enum MenuCommand
    {
        Up, Down, Left, Right, Submit, Back, NextTab, PrevTab, ScrollUp, ScrollDown,
    }

    /// <summary>One physical control of a menu command (Input System control path).</summary>
    public readonly struct MenuBinding
    {
        public readonly MenuCommand Command;
        public readonly string Path;
        public MenuBinding(MenuCommand c, string path) { Command = c; Path = path; }
        public bool IsKeyboard => Path.StartsWith("<Keyboard>");
        public bool IsGamepad => Path.StartsWith("<Gamepad>");
        public bool IsMouse => Path.StartsWith("<Mouse>");
    }

    /// <summary>
    /// The fixed menu layout of keyboard, mouse and pad (ADR 0265 P2-3: menus are not rebindable, like a truck display).
    /// Navigation / submit / back are the Input System UI module's default actions; the settings tabs add
    /// <see cref="MenuCommand.NextTab"/> / <see cref="MenuCommand.PrevTab"/> (pad bumpers, keyboard E / Q - also the
    /// gear keys in driving: safe only because the driving scene gates every PC driving source while a menu owns the
    /// focus, <c>DriverInputMixer.MenuOpen</c> = <c>UiFocus.HasModal</c>, review #131 P1-1; see <see cref="SharedWithDriving"/>).
    /// Pure table, tested in EditMode.
    /// </summary>
    public static class MenuCommandMap
    {
        public static readonly MenuBinding[] All =
        {
            new MenuBinding(MenuCommand.Up, "<Keyboard>/upArrow"), new MenuBinding(MenuCommand.Up, "<Gamepad>/dpad/up"), new MenuBinding(MenuCommand.Up, "<Gamepad>/leftStick/up"),
            new MenuBinding(MenuCommand.Down, "<Keyboard>/downArrow"), new MenuBinding(MenuCommand.Down, "<Gamepad>/dpad/down"), new MenuBinding(MenuCommand.Down, "<Gamepad>/leftStick/down"),
            new MenuBinding(MenuCommand.Left, "<Keyboard>/leftArrow"), new MenuBinding(MenuCommand.Left, "<Gamepad>/dpad/left"), new MenuBinding(MenuCommand.Left, "<Gamepad>/leftStick/left"),
            new MenuBinding(MenuCommand.Right, "<Keyboard>/rightArrow"), new MenuBinding(MenuCommand.Right, "<Gamepad>/dpad/right"), new MenuBinding(MenuCommand.Right, "<Gamepad>/leftStick/right"),
            new MenuBinding(MenuCommand.Submit, "<Keyboard>/enter"), new MenuBinding(MenuCommand.Submit, "<Keyboard>/numpadEnter"), new MenuBinding(MenuCommand.Submit, "<Gamepad>/buttonSouth"),
            new MenuBinding(MenuCommand.Submit, "<Mouse>/leftButton"),
            new MenuBinding(MenuCommand.Back, "<Keyboard>/escape"), new MenuBinding(MenuCommand.Back, "<Gamepad>/buttonEast"), new MenuBinding(MenuCommand.Back, "<Mouse>/rightButton"),
            new MenuBinding(MenuCommand.NextTab, "<Keyboard>/e"), new MenuBinding(MenuCommand.NextTab, "<Gamepad>/rightShoulder"),
            new MenuBinding(MenuCommand.PrevTab, "<Keyboard>/q"), new MenuBinding(MenuCommand.PrevTab, "<Gamepad>/leftShoulder"),
            new MenuBinding(MenuCommand.ScrollUp, "<Keyboard>/pageUp"), new MenuBinding(MenuCommand.ScrollUp, "<Gamepad>/rightStick/up"), new MenuBinding(MenuCommand.ScrollUp, "<Mouse>/scroll/up"),
            new MenuBinding(MenuCommand.ScrollDown, "<Keyboard>/pageDown"), new MenuBinding(MenuCommand.ScrollDown, "<Gamepad>/rightStick/down"), new MenuBinding(MenuCommand.ScrollDown, "<Mouse>/scroll/down"),
        };

        /// <summary>Number of commands (enum size).</summary>
        public const int CommandCount = 10;

        /// <summary>True when <paramref name="path"/> is bound to <paramref name="c"/>.</summary>
        public static bool Has(MenuCommand c, string path)
        {
            for (int i = 0; i < All.Length; i++) if (All[i].Command == c && All[i].Path == path) return true;
            return false;
        }

        /// <summary>
        /// True when a menu control is also a default driving control (<see cref="DrivingActionCatalog.All"/>, incl. the
        /// keyboard steering pairs). Every such control is safe only behind the driving gate (review #131 P1-1).
        /// </summary>
        public static bool SharedWithDriving(string path)
        {
            foreach (var def in DrivingActionCatalog.All)
            {
                foreach (var p in def.Keyboard) if (p == path) return true;
                foreach (var p in def.Gamepad) if (p == path || SameStick(p, path)) return true;
            }
            foreach (var pair in DrivingActionCatalog.KeyboardSteerPairs) foreach (var p in pair) if (p == path) return true;
            return false;
        }

        /// <summary>Both paths on the same analogue stick (any direction / axis of it).</summary>
        static bool SameStick(string a, string b)
        {
            const string l = "<Gamepad>/leftStick", r = "<Gamepad>/rightStick";
            return (a.StartsWith(l) && b.StartsWith(l)) || (a.StartsWith(r) && b.StartsWith(r));
        }

        /// <summary>Next / previous tab with wrap-around.</summary>
        public static int StepTab(int index, int delta, int count)
        {
            if (count <= 0) return 0;
            return ((index + delta) % count + count) % count;
        }
    }
}
