using Game.UI.CabDisplays;
using Game.Vehicle.Runtime;
using Game.World;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Puts the live cab screens (<see cref="CabScreens"/>) on the art truck of a scene: region id and frame of the
    /// navigation data from the scene's <see cref="WorldRegionRoot"/> (none in the DrivingLab: the navigation shows
    /// "no map"). Used by <see cref="DrivingLabBootstrap"/> at play and by the visual-QA runner in edit mode.
    /// </summary>
    public static class CabScreensInstaller
    {
        public static CabScreens Install(VehicleBody vehicle)
        {
            if (vehicle == null) return null;
            var region = Object.FindAnyObjectByType<WorldRegionRoot>();
            var route = Object.FindAnyObjectByType<WorldRoute>();
            // Route points are region-local (x east, z north) relative to the route object (ADR 0003 frame).
            Transform frame = route != null ? route.transform : null;
            return CabScreens.Install(vehicle, frame, region != null ? region.regionId : "");
        }
    }
}
