using System;
using System.Linq;
using Game.World;
using UnityEditor;
using UnityEngine;

namespace Game.Editor.Furniture
{
    /// <summary>Keep the authored furniture variant on its existing family's visibility policy.
    /// Runs while generated instance assets are saved, with no runtime callback or foreign policy edits.</summary>
    public sealed class FurnitureShelterPolicySave : AssetModificationProcessor
    {
        public const string Variant = "bus_shelter_red_0120";

        public static bool Inherit(WorldInstanceSet set)
        {
            var variant = set.prototypes.FirstOrDefault(p => p.name == Variant);
            if (variant == null) return false;
            var source = set.prototypes.FirstOrDefault(p => p.name == "bus_shelter");
            if (source == null || source.lodEndM.Length != variant.lods.Length)
                throw new InvalidOperationException("Furniture shelter variant requires the matching bus_shelter LOD policy");
            if (variant.lodEndM.SequenceEqual(source.lodEndM) && variant.shadowLodMask == source.shadowLodMask)
                return false;
            variant.lodEndM = (float[])source.lodEndM.Clone();
            variant.shadowLodMask = source.shadowLodMask;
            return true;
        }

        static string[] OnWillSaveAssets(string[] paths)
        {
            foreach (var path in paths)
            {
                if (!path.StartsWith("Assets/_Generated/World/", StringComparison.Ordinal) ||
                    !path.EndsWith("/Instances.asset", StringComparison.Ordinal)) continue;
                var set = AssetDatabase.LoadAssetAtPath<WorldInstanceSet>(path);
                if (set == null || !Inherit(set)) continue;
                EditorUtility.SetDirty(set);
                Debug.Log($"FURNITURE_SHELTER_POLICY: inherited bus_shelter policy for {Variant} in {path}");
            }
            return paths;
        }
    }
}
