using Game.UI.CabDisplays;
using Game.UI.Driving;
using Game.UI.Navigation;
using Game.Vehicle.Runtime;
using Game.World;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Wires the GPS (ADR 0150) into a driving session: <see cref="NavigationService"/> for the scene's region (same
    /// region id and frame as the cab screens, <see cref="CabScreensInstaller"/>), the HUD minimap with the guidance
    /// banner, the full map (opened by a tap on the minimap) and the live route on the cab navigation screen.
    /// No region in the scene (DrivingLab) = no GPS widgets.
    /// </summary>
    public static class NavigationInstaller
    {
        public static NavigationService Install(DrivingHud hud, VehicleBody vehicle, GameObject host)
        {
            if (hud == null || vehicle == null || host == null) return null;
            var region = Object.FindAnyObjectByType<WorldRegionRoot>();
            if (region == null || string.IsNullOrEmpty(region.regionId)) return null;
            var route = Object.FindAnyObjectByType<WorldRoute>();
            Transform frame = route != null ? route.transform : null;   // same frame as the cab screens
            var nav = NavigationService.Install(host, vehicle.transform, vehicle.GetComponent<Rigidbody>(), frame, region.regionId);
            if (!nav.Ready) return nav;
            var screens = vehicle.GetComponent<CabScreens>();
            if (screens != null)
            {
                screens.NavLayout.Live = nav;
                nav.NightSource = () => screens.State.Night;
            }
            var full = FullMapView.Create(nav);
            full.transform.SetParent(host.transform, false);
            var mini = MiniMapView.Create(hud, nav);
            mini.OnOpenMap = full.Open;
            return nav;
        }
    }
}
