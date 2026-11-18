using System.IO;
using Game.Editor.Build;
using NUnit.Framework;
using UnityEngine;
using Json = Game.Editor.Setup.TruckAssetBuilder.Json;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0296 (D84): the cab control cameras live in the generated DrivingLab scene (cab renders without a world), and
    /// the legend backlight cap stays in the band measured as legible at night without clipping.
    /// </summary>
    public class CabD84Polish0296Tests
    {
        [Test]
        public void DrivingLabScene_HasTheCabControlCameras()
        {
            string scene = File.ReadAllText(Path.Combine(Application.dataPath, "_Project/World/Scenes/DrivingLab.unity")).Replace("\r\n", "\n");
            foreach (string id in new[] { "cab-driver", "cab-dash", "cab-hub", "cab-switches", "cab-trays", "cab-seat", "cab-materials", "cab-apillar" })
                StringAssert.Contains("  id: " + id + "\n", scene, "control camera missing in DrivingLab.unity (pwsh scripts/build-lab.ps1 -SkipAudio -BuildTarget Win64)");
        }

        [Test]
        public void LegendBacklightCap_IsInTheMeasuredLegibleBand()
        {
            var data = Json.Obj(Json.Parse(File.ReadAllText(Path.Combine(EditorTools.RepoRoot, "art-source/truck/interior/cab_backlight.json"))));
            double cap = Json.Num(data["max_exposed_linear"]);
            // Measured in cab-switches at night (High, 1080p): cap 0.09 -> legend peak sRGB 106 (reads as dim grey print),
            // 0.30 -> 146, 0.45 -> 158-172, 0.60 -> 201; none clips. At night luminance x exposure always exceeds the cap.
            Assert.That(cap, Is.InRange(0.30, 0.60));
        }
    }
}
