using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Editor.Setup;
using Game.Gameplay;
using Game.Rendering;
using Game.Rendering.Editor;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using static Game.World.Import.MiniJson;

namespace Game.World.Import
{
    /// <summary>
    /// Builds the drivable scene of an imported region (WorldC for bialystok-industrial-c): region root at
    /// y = −anchor height (Unity origin = region anchor, ADR 0003), chunks with LODGroups (terrain LOD0–3 by the
    /// manifest's switch distances, roads, markings, bridges), MeshColliders from the separate collision meshes tagged
    /// with <see cref="GroundSurface"/>, a terrain fallback collider (LOD1) in the route corridor, environment lighting
    /// (clear / overcast presets), the world volume, the DrivingLab tractor + trailer at the depot gate with the
    /// DrivingLab bootstrap, the start route, and the visual-QA control cameras.
    /// The scene is generated into Assets/_Generated (gitignored) - regenerate with scripts/import-region.ps1.
    /// </summary>
    public static class WorldSceneBuilder
    {
        public static string SceneNameFor(string region) => region == "bialystok-industrial-c" ? "WorldC" : "World_" + region;

        public static void Build(RegionImporter.Result r)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            // ---------------- lighting ----------------
            var sunGo = new GameObject("Sun");
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.shadows = LightShadows.Soft;
            sun.shadowBias = 0.05f; sun.shadowNormalBias = 0.4f;
            sunGo.AddComponent<UniversalAdditionalLightData>();
            var envGo = new GameObject("EnvironmentLighting");
            var env = envGo.AddComponent<EnvironmentLighting>();
            env.presets = LookDevAssets.Presets();
            env.sun = sun;
            env.skyMaterial = AssetDatabase.LoadAssetAtPath<Material>(LookDevAssets.SkyMaterial);
            env.Apply();
            var volGo = new GameObject("WorldVolume");
            var vol = volGo.AddComponent<Volume>();
            vol.isGlobal = true;
            vol.sharedProfile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(LookDevAssets.WorldVolumeProfile);

            // ---------------- region ----------------
            var rootGo = new GameObject("Region_" + r.Region);
            var root = rootGo.AddComponent<WorldRegionRoot>();
            root.regionId = r.Region; root.anchorX = r.AnchorX; root.anchorY = r.AnchorY; root.anchorZ = r.AnchorZ;
            root.chunkSizeM = r.ChunkSize;
            rootGo.transform.position = new Vector3(0f, (float)-r.AnchorZ, 0f);
            var infos = new List<WorldRegionRoot.ChunkInfo>();
            int colliders = 0;
            foreach (var ch in r.Chunks)
            {
                BuildChunk(ch, rootGo.transform, r, ref colliders);
                infos.Add(new WorldRegionRoot.ChunkInfo { id = ch.Id, minEN = ch.Min, maxEN = ch.Max, corridor = ch.Corridor, sha256 = ch.Sha256 });
            }
            root.chunks = infos.ToArray();
            Physics.SyncTransforms();

            // ---------------- route (heights from the collision) ----------------
            var routeGo = new GameObject("Route_start");
            var route = routeGo.AddComponent<WorldRoute>();
            var pts = new Vector3[r.RouteEN.Length];
            float prevY = float.NaN;
            for (int i = 0; i < pts.Length; i++) { pts[i] = Ground(new Vector3(r.RouteEN[i].x, 0f, r.RouteEN[i].y), prevY); prevY = pts[i].y; }
            route.points = pts;
            route.distances = new float[pts.Length];
            for (int i = 1; i < pts.Length; i++)
            {
                Vector3 d = pts[i] - pts[i - 1]; d.y = 0f;
                route.distances[i] = route.distances[i - 1] + d.magnitude;
            }
            route.speedLimitsKmh = r.RouteLimits.Length == pts.Length ? r.RouteLimits : new float[pts.Length];

            // ---------------- vehicle, camera, bootstrap ----------------
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(DrivingLabSceneBuilder.PrefabPath);
            var trailerPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(DrivingLabSceneBuilder.TrailerPrefabPath);
            if (prefab == null || trailerPrefab == null) throw new FileNotFoundException("DrivingLab prefabs missing: run Kamion/Setup/Rebuild DrivingLab first");
            const float spawnS = 12f;
            Vector3 spawnPos = route.points.Length > 1 ? route.PointAt(spawnS) : Vector3.zero;
            Vector3 spawnFwd = route.points.Length > 1 ? route.TangentAt(spawnS) : Vector3.forward;
            var spawn = new GameObject("Spawn_KwadratParkGate").transform;
            spawn.SetPositionAndRotation(spawnPos, Quaternion.LookRotation(spawnFwd, Vector3.up));

            var truck = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            truck.transform.SetPositionAndRotation(spawnPos, spawn.rotation);
            var trailerGo = (GameObject)PrefabUtility.InstantiatePrefab(trailerPrefab);
            {
                var data = truck.GetComponent<VehicleBody>().Data;
                var tractorModel = data.CreateModel();
                var trailerModel = data.CreateTrailer();
                _ = new CombinationModel(tractorModel, trailerModel, true);
                CombinationPlacement.Coupled(tractorModel, spawnPos, spawn.rotation, trailerModel, 0f, out Vector3 tp, out Quaternion tq);
                trailerGo.transform.SetPositionAndRotation(tp, tq);
            }
            var dims = DrivingLabSceneBuilder.ReadAndCheckDims();
            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            var cam = camGo.AddComponent<Camera>();
            cam.fieldOfView = 55f; cam.nearClipPlane = 0.05f; cam.farClipPlane = 1400f;
            cam.clearFlags = CameraClearFlags.Skybox;
            camGo.AddComponent<UniversalAdditionalCameraData>();
            camGo.AddComponent<AudioListener>();
            camGo.transform.SetPositionAndRotation(spawnPos + spawn.rotation * dims.EyePointVehicle, spawn.rotation);
            var applier = camGo.AddComponent<QualityProfileApplier>();
            applier.targetCamera = cam;
            applier.volume = vol;
            applier.worldTextures = WorldTextureGenerator.All.Select(AssetDatabase.LoadAssetAtPath<Texture>).Where(t => t != null).ToArray();

            var boot = new GameObject("DrivingLabBootstrap").AddComponent<DrivingLabBootstrap>();
            boot.vehicle = truck.GetComponent<VehicleBody>();
            boot.trailer = trailerGo.GetComponent<TrailerBody>();
            boot.mainCamera = cam;
            boot.spawnPoint = spawn;
            boot.route = route;

            // ---------------- control cameras ----------------
            var qa = new GameObject("ControlCameras").transform;
            float az = (float)r.AnchorZ;
            foreach (var co in r.ControlCameras)
            {
                var c = Obj(co);
                if (Str(c.Get("type")) != "persp") continue;
                var p = Arr(c.Get("pos")); var l = Arr(c.Get("look_at"));
                var pos = new Vector3((float)Num(p[0]), (float)Num(p[2]) - az, (float)Num(p[1]));
                var look = new Vector3((float)Num(l[0]), (float)Num(l[2]) - az, (float)Num(l[1]));
                Qa(qa, Str(c.Get("id")).Replace('_', '-'), pos, look, (float)Num(c.Get("fov_deg")), Str(c.Get("note")));
            }
            // The tractor at the gate (truck on the imported ground, contact shadows) and the cab view down the access road.
            Vector3 side = Vector3.Cross(Vector3.up, spawnFwd);
            Qa(qa, "truck-at-gate", spawnPos + spawnFwd * 11f + side * 7f + Vector3.up * 2.6f, spawnPos + Vector3.up * 1.6f - spawnFwd * 3f, 50f,
                "Graybox tractor + trailer at the Kwadrat Park spawn: wheels on the imported collision, shadows, scale against the road.");
            Vector3 eye = spawnPos + spawn.rotation * dims.EyePointVehicle;
            Qa(qa, "cab-gate", eye, eye + spawnFwd * 30f - Vector3.up * 2.2f, 55f, "Driver eye at the spawn, looking along the depot access road.");

            Directory.CreateDirectory(Path.Combine(Game.Editor.Build.EditorTools.ProjectRoot, Path.GetDirectoryName(r.ScenePath)));
            EditorSceneManager.SaveScene(scene, r.ScenePath);
            BuildScenes.Apply();
            AssetDatabase.SaveAssets();
            Debug.Log($"[IMPORT] scene {r.ScenePath}: {r.Chunks.Count} chunks, {colliders} colliders, route {route.Length:F0} m, spawn {spawnPos}");
        }

        /// <summary>Ground under a route point; under viaducts the hit closest to the previous point's height wins.</summary>
        static Vector3 Ground(Vector3 p, float prevY)
        {
            var hits = Physics.RaycastAll(new Vector3(p.x, 400f, p.z), Vector3.down, 800f);
            if (hits.Length == 0) return new Vector3(p.x, float.IsNaN(prevY) ? 0f : prevY, p.z);
            RaycastHit best = hits[0];
            foreach (var h in hits)
            {
                bool better = float.IsNaN(prevY) ? h.point.y > best.point.y : Mathf.Abs(h.point.y - prevY) < Mathf.Abs(best.point.y - prevY);
                if (better) best = h;
            }
            return best.point;
        }

        static void BuildChunk(RegionImporter.Chunk ch, Transform parent, RegionImporter.Result r, ref int colliders)
        {
            var go = new GameObject("Chunk_" + ch.Id);
            go.transform.SetParent(parent, false);
            var byNode = new Dictionary<string, List<Renderer>>();
            Mesh terrainLod1 = null;
            foreach (var (node, mesh, mats) in ch.Visual)
            {
                if (node == "road_collision") continue;
                if (node == "terrain_lod1") terrainLod1 = mesh;
                bool far = !ch.Corridor;
                // Outside the route corridor: no LOD0/LOD1 terrain, no markings (memory, ADR 0011 §corridor).
                if (far && (node == "terrain_lod0" || node == "terrain_lod1" || node == "markings")) continue;
                var child = new GameObject(node);
                child.transform.SetParent(go.transform, false);
                child.AddComponent<MeshFilter>().sharedMesh = mesh;
                var mr = child.AddComponent<MeshRenderer>();
                mr.sharedMaterials = mats;
                bool castsShadows = node == "bridge";
                mr.shadowCastingMode = castsShadows ? ShadowCastingMode.On : ShadowCastingMode.Off;
                mr.receiveShadows = true;
                mr.lightProbeUsage = LightProbeUsage.Off;
                mr.reflectionProbeUsage = ReflectionProbeUsage.Off;
                if (!byNode.TryGetValue(node, out var list)) byNode[node] = list = new List<Renderer>();
                list.Add(mr);
            }

            // LODGroup: screen-relative height h = size / (2 d tan(fov/2)) for the switch distance d measured to the
            // chunk centre (manifest distances are from the camera to the near chunk edge, so add half a chunk).
            var lg = go.AddComponent<LODGroup>();
            float size = r.ChunkSize;
            float H(float d) => Mathf.Clamp(size / (2f * Mathf.Max(d, 1f) * Mathf.Tan(30f * Mathf.Deg2Rad)), 0.0005f, 1f);
            float half = size * 0.70f;
            var get = (System.Func<string, Renderer[]>)(n => byNode.TryGetValue(n, out var l) ? l.ToArray() : new Renderer[0]);
            var road = get("road").Concat(get("bridge")).ToArray();
            LOD[] lods;
            if (ch.Corridor)
            {
                lods = new[]
                {
                    new LOD(H(r.LodSwitchM[1] + half), get("terrain_lod0").Concat(road).Concat(get("markings")).ToArray()),
                    new LOD(H(r.LodSwitchM[2] + half), get("terrain_lod1").Concat(road).Concat(get("markings")).ToArray()),
                    new LOD(H(r.LodSwitchM[3] + half), get("terrain_lod2").Concat(road).ToArray()),
                    new LOD(0.0005f, get("terrain_lod3").Concat(get("bridge")).ToArray()),
                };
            }
            else
            {
                lods = new[]
                {
                    new LOD(H(r.LodSwitchM[3] + half), get("terrain_lod2").Concat(road).ToArray()),
                    new LOD(0.0005f, get("terrain_lod3").Concat(get("bridge")).ToArray()),
                };
            }
            lg.SetLODs(lods);
            lg.size = size;
            lg.localReferencePoint = new Vector3((ch.Min.x + ch.Max.x) * 0.5f, 140f, (ch.Min.y + ch.Max.y) * 0.5f);
            lg.fadeMode = LODFadeMode.None;

            // Collision: one MeshCollider per surface + terrain fallback in the corridor.
            if (!ch.Corridor) return;
            var col = new GameObject("Collision");
            col.transform.SetParent(go.transform, false);
            foreach (var (mesh, surface) in ch.Collision)
            {
                var c = new GameObject("col_" + surface);
                c.transform.SetParent(col.transform, false);
                var mc = c.AddComponent<MeshCollider>();
                mc.sharedMesh = mesh;
                mc.cookingOptions = MeshColliderCookingOptions.CookForFasterSimulation | MeshColliderCookingOptions.EnableMeshCleaning | MeshColliderCookingOptions.WeldColocatedVertices | MeshColliderCookingOptions.UseFastMidphase;
                c.AddComponent<GroundSurface>().kind = RegionImporter.SurfaceKindOf(surface);
                colliders++;
            }
            if (terrainLod1 != null)
            {
                var t = new GameObject("col_terrain");
                t.transform.SetParent(col.transform, false);
                var mc = t.AddComponent<MeshCollider>();
                mc.sharedMesh = terrainLod1;
                t.AddComponent<GroundSurface>().kind = SurfaceKind.Grass;
                colliders++;
            }
        }

        static void Qa(Transform parent, string id, Vector3 pos, Vector3 lookAt, float fov, string note)
        {
            var go = new GameObject("QA_" + id);
            go.transform.SetParent(parent, false);
            go.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(lookAt - pos, Vector3.up));
            var cam = go.AddComponent<Camera>();
            cam.fieldOfView = fov; cam.nearClipPlane = 0.1f; cam.farClipPlane = 1400f;
            cam.enabled = false;
            go.AddComponent<UniversalAdditionalCameraData>();
            var qa = go.AddComponent<ControlCamera>();
            qa.id = id; qa.note = note;
        }
    }
}
