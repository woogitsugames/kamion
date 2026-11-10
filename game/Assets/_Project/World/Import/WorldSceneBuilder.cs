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
        public static string SceneNameFor(string region, string tier = "Low")
        {
            string b = region == "bialystok-industrial-c" ? "WorldC" : "World_" + region;
            return tier == "High" ? b + "_High" : b;
        }

        /// <summary>Builds the scene of one content tier: "Low" (Low + Medium quality, WorldC) or "High" (WorldC_High).</summary>
        public static void Build(RegionImporter.Result r, string tier)
        {
            string scenePath = r.ScenePath(tier);
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
                BuildChunk(ch, rootGo.transform, r, tier, ref colliders);
                infos.Add(new WorldRegionRoot.ChunkInfo { id = ch.Id, minEN = ch.Min, maxEN = ch.Max, corridor = ch.Corridor, sha256 = ch.Sha256 });
            }
            root.chunks = infos.ToArray();
            // GPU-instanced props and trees (ADR 0012) - in region-root space, like the chunks.
            // Reload by path: NewScene(Single) unloads unreferenced assets, which turns the in-memory reference fake-null.
            var instances = AssetDatabase.LoadAssetAtPath<WorldInstanceSet>($"{r.Dir}/Instances.asset");
            if (instances != null) rootGo.AddComponent<WorldInstances>().set = instances;
            else Debug.LogWarning("[IMPORT] Instances.asset missing - no props or trees in " + scenePath);
            colliders += BuildPropColliders(r, rootGo.transform);
            BuildBarriers(r, rootGo.transform);
            Physics.SyncTransforms();
            // Region edge (ADR 0082): boundary data, apron to the horizon, road closures before the edge.
            WorldEdgeBuilder.Build(r, rootGo.transform, tier);
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
            // Track A7: the TRAKT art truck when it has been built (TruckAssetBuilder), else the graybox.
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(TruckAssetBuilder.PrefabPath) ??
                         AssetDatabase.LoadAssetAtPath<GameObject>(DrivingLabSceneBuilder.PrefabPath);
            // The art curtainsider when it has been built (TrailerAssetBuilder), else the graybox trailer (same physics root).
            var trailerPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(TrailerAssetBuilder.PrefabPath) ??
                                AssetDatabase.LoadAssetAtPath<GameObject>(DrivingLabSceneBuilder.TrailerPrefabPath);
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
            cam.fieldOfView = 55f; cam.nearClipPlane = 0.05f; cam.farClipPlane = 3500f;
            cam.clearFlags = CameraClearFlags.Skybox;
            camGo.AddComponent<UniversalAdditionalCameraData>();
            camGo.AddComponent<AudioListener>();
            camGo.transform.SetPositionAndRotation(spawnPos + spawn.rotation * dims.EyePointVehicle, spawn.rotation);
            var applier = camGo.AddComponent<QualityProfileApplier>();
            applier.targetCamera = cam;
            applier.volume = vol;
            // legacy detail textures + the generated PBR sets (ADR 0022): the tier sets their aniso and mip bias
            applier.worldTextures = WorldTextureGenerator.All.Select(AssetDatabase.LoadAssetAtPath<Texture>).Where(t => t != null)
                .Concat(WorldPbrMaterials.LoadAll(r.Dir)).ToArray();

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
                "Tractor + trailer at the Kwadrat Park spawn: wheels on the imported collision, shadows, scale against the road.");
            Vector3 eye = spawnPos + spawn.rotation * dims.EyePointVehicle;
            Qa(qa, "cab-gate", eye, eye + spawnFwd * 30f - Vector3.up * 2.2f, 55f, "Driver eye at the spawn, looking along the depot access road.");
            AddEdgeCameras(qa);

            TruckAssetBuilder.AddControlCameras(truck.transform);

            // Collision is cooked at load (no prebaked PhysX data in the APK): save the world MeshColliders disabled and let
            // WorldCollisionCooker bake them in parallel and enable them (ADR 0012 §6).
            var meshColliders = rootGo.GetComponentsInChildren<MeshCollider>(true);
            foreach (var mc in meshColliders) mc.enabled = false;
            rootGo.AddComponent<WorldCollisionCooker>().colliders = meshColliders;

            Directory.CreateDirectory(Path.Combine(Game.Editor.Build.EditorTools.ProjectRoot, Path.GetDirectoryName(scenePath)));
            EditorSceneManager.SaveScene(scene, scenePath);
            AssetDatabase.SaveAssets();
            Debug.Log($"[IMPORT] scene {scenePath} (tier {tier}): {r.Chunks.Count} chunks, {colliders} colliders, route {route.Length:F0} m, spawn {spawnPos}");
        }

        /// <summary>Automatic boom barriers of depot gates (MA-003): one kinematic boom with <see cref="DepotBarrier"/> each.</summary>
        static void BuildBarriers(RegionImporter.Result r, Transform parent)
        {
            if (r.PropColliders == null || r.PropColliders.Barriers.Count == 0) return;
            var root = new GameObject("Barriers").transform;
            root.SetParent(parent, false);
            int i = 0;
            foreach (var b in r.PropColliders.Barriers)
            {
                var go = new GameObject($"DepotBarrier_{i++}");
                go.layer = 2;   // Ignore Raycast: wheel rays (UnityGroundQuery) never stand on a boom, bodies still collide
                go.transform.SetParent(root, false);
                go.transform.localPosition = b.M.GetColumn(3);
                go.transform.localRotation = b.M.rotation;
                go.AddComponent<MeshFilter>().sharedMesh = b.Mesh;
                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterials = b.Materials;
                var bc = go.AddComponent<BoxCollider>();
                bc.center = new Vector3(b.Length * 0.5f, 0f, 0f);
                bc.size = new Vector3(b.Length, 0.10f, 0.10f);
                var rb = go.AddComponent<Rigidbody>();
                rb.isKinematic = true;
                rb.useGravity = false;
                rb.mass = 14f;
                var bar = go.AddComponent<DepotBarrier>();
                bar.boomLengthM = b.Length;
                bar.openAngleDeg = b.OpenDeg;
                bar.travelSign = b.Travel;
            }
            Debug.Log($"[IMPORT] barriers: {r.PropColliders.Barriers.Count} automatic booms (DepotBarrier)");
        }

        /// <summary>Box colliders of street props (lamps, poles, signal masts, gates...) in the start-route corridor.</summary>
        static int BuildPropColliders(RegionImporter.Result r, Transform parent)
        {
            if (r.PropColliders == null || r.PropColliders.Count == 0) return 0;
            var root = new GameObject("PropColliders").transform;
            root.SetParent(parent, false);
            Physics.SyncTransforms();
            int onRoad = 0;
            var report = new System.Text.StringBuilder();
            foreach (var (proto, m, local) in r.PropColliders.Items)
            {
                // A prop whose foot stands on a carriageway (asphalt road collision) is a generator placement error
                // (seen: lamp_12m at E 326.6 N -579.6 inside the Rondo Biezenstwa approach lane, which stopped the route
                // autopilot). It keeps its visual but gets no collider; listed for world-builder.
                Vector3 foot = parent.TransformPoint(m.GetColumn(3));
                if (Physics.Raycast(foot + Vector3.up * 1.0f, Vector3.down, out var hit, 1.6f) &&
                    hit.collider.GetComponent<GroundSurface>() is GroundSurface gs && gs.kind == SurfaceKind.DryAsphalt &&
                    hit.collider.name == "col_asphalt")
                {
                    onRoad++;
                    var lp = m.GetColumn(3);
                    report.AppendLine($"{proto} E {lp.x:F1} N {lp.z:F1}");
                    continue;
                }
                var go = new GameObject(proto);
                go.transform.SetParent(root, false);
                go.transform.localPosition = m.GetColumn(3);
                go.transform.localRotation = m.rotation;
                go.transform.localScale = m.lossyScale;
                var bc = go.AddComponent<BoxCollider>();
                bc.center = local.center;
                bc.size = Vector3.Max(local.size, new Vector3(0.05f, 0.05f, 0.05f));
                go.AddComponent<GroundSurface>().kind = SurfaceKind.Concrete;
                go.isStatic = true;
            }
            if (onRoad > 0)
            {
                Debug.LogWarning($"[IMPORT] {onRoad} props stand on a carriageway (no collider): see artifacts/world/{r.Region}-props-on-road.txt");
                string dir = Path.Combine(Game.Editor.Build.EditorTools.RepoRoot, "artifacts", "world");
                Directory.CreateDirectory(dir);
                File.WriteAllText(Path.Combine(dir, r.Region + "-props-on-road.txt"), report.ToString());
            }
            return r.PropColliders.Count - onRoad;
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

        // Layers per LOD (ADR 0012). Distances: manifest switch distances (camera to near chunk edge) + 0.7 chunk.
        static readonly string[][] k_LowLods =
        {
            new[] { "terrain_band", "road", "bridge", "markings", "paved", "buildings", "furniture", "wires" },
            new[] { "terrain_lod2", "road", "bridge", "markings", "paved", "buildings_lod1", "furniture", "wires" },
            new[] { "terrain_lod2", "road", "bridge", "paved", "buildings_lod1", "wires" },
            new[] { "terrain_lod3", "bridge", "buildings_lod1" },
        };
        static readonly string[][] k_HighLods =
        {
            new[] { "terrain_band", "road", "bridge", "markings", "paved", "buildings", "furniture", "wires" },
            new[] { "terrain_lod1", "road", "bridge", "markings", "paved", "buildings_lod1", "furniture", "wires" },
            new[] { "terrain_lod2", "road", "bridge", "paved", "buildings_lod1", "wires" },
            new[] { "terrain_lod3", "bridge", "buildings_lod1" },
        };
        static readonly HashSet<string> k_ShadowCasters = new HashSet<string> { "bridge", "buildings", "buildings_lod1", "furniture" };

        static void BuildChunk(RegionImporter.Chunk ch, Transform parent, RegionImporter.Result r, string tier, ref int colliders)
        {
            var go = new GameObject("Chunk_" + ch.Id);
            go.transform.SetParent(parent, false);
            var byNode = new Dictionary<string, Renderer>();
            foreach (var layer in ch.Layers[tier])
            {
                var child = new GameObject(layer.Node);
                child.transform.SetParent(go.transform, false);
                child.AddComponent<MeshFilter>().sharedMesh = layer.Mesh;
                var mr = child.AddComponent<MeshRenderer>();
                mr.sharedMaterials = layer.Materials;
                mr.shadowCastingMode = k_ShadowCasters.Contains(layer.Node) ? ShadowCastingMode.On : ShadowCastingMode.Off;
                mr.receiveShadows = true;
                mr.lightProbeUsage = LightProbeUsage.Off;
                mr.reflectionProbeUsage = ReflectionProbeUsage.Off;
                byNode[layer.Node] = mr;
            }

            // LODGroup: screen-relative height h = size / (2 d tan(fov/2)) for the switch distance d to the chunk centre.
            var lg = go.AddComponent<LODGroup>();
            float size = r.ChunkSize;
            float H(float d) => Mathf.Clamp(size / (2f * Mathf.Max(d, 1f) * Mathf.Tan(30f * Mathf.Deg2Rad)), 0.0005f, 1f);
            float half = size * 0.70f;
            var table = tier == "High" ? k_HighLods : k_LowLods;
            var lods = new LOD[table.Length];
            for (int i = 0; i < table.Length; i++)
            {
                // Without LOD0 buildings (Low content away from the route) LOD0 shows the LOD1 prisms.
                var names = table[i].Select(n => n == "buildings" && !byNode.ContainsKey("buildings") ? "buildings_lod1" : n);
                var rs = names.Where(byNode.ContainsKey).Select(n => byNode[n]).ToArray();
                float h = i + 1 < table.Length ? H(r.LodSwitchM[i + 1] + half) : 0.0005f;
                lods[i] = new LOD(h, rs);
            }
            lg.SetLODs(lods);
            lg.size = size;
            lg.localReferencePoint = new Vector3((ch.Min.x + ch.Max.x) * 0.5f, 140f, (ch.Min.y + ch.Max.y) * 0.5f);
            lg.fadeMode = LODFadeMode.None;

            // Collision (same in every tier): one MeshCollider per surface + terrain fallback.
            var col = new GameObject("Collision");
            col.transform.SetParent(go.transform, false);
            foreach (var (mesh, surface) in ch.Collision)
            {
                var c = new GameObject("col_" + surface);
                c.transform.SetParent(col.transform, false);
                // Kerbs: wheel rays only - the graybox body colliders (bumper 0.35 m) touched a 0.14 m roundabout kerb
                // under braking dive (40 t route, |dv| 1.62 m/s at s≈604 m); a real bumper sweeps over kerbs.
                if (surface.Contains("kerb"))
                {
                    int kl = LayerMask.NameToLayer(WorldCollisionCooker.KerbLayerName);
                    if (kl >= 0) c.layer = kl;
                    else Debug.LogWarning("[IMPORT] layer WorldKerb missing - run scripts/setup-project.ps1");
                }
                var mc = c.AddComponent<MeshCollider>();
                mc.sharedMesh = mesh;
                mc.cookingOptions = MeshColliderCookingOptions.CookForFasterSimulation | MeshColliderCookingOptions.EnableMeshCleaning | MeshColliderCookingOptions.WeldColocatedVertices | MeshColliderCookingOptions.UseFastMidphase;
                c.AddComponent<GroundSurface>().kind = RegionImporter.SurfaceKindOf(surface);
                colliders++;
            }
            if (ch.TerrainCollision != null)
            {
                var t = new GameObject("col_terrain");
                t.transform.SetParent(col.transform, false);
                var mc = t.AddComponent<MeshCollider>();
                mc.sharedMesh = ch.TerrainCollision;
                t.AddComponent<GroundSurface>().kind = SurfaceKind.Grass;
                colliders++;
            }
        }

        static void AddEdgeCameras(Transform qa)
        {
            var defs = new (string id, Vector2 posEN, Vector2 dirEN, string note)[]
            {
                ("edge-north", new Vector2(-837.9f, 936.7f), new Vector2(-0.21f, 0.98f),
                    "Driver eye 2.5 m on al. Tysiaclecia N (~937 m N), looking NNW past the U-20 closure over the northern forest/city edge (ADR 0085)."),
                ("edge-east", new Vector2(934.5f, -931.3f), new Vector2(0.88f, -0.48f),
                    "Driver eye 2.5 m on ul. Gen. W. Andersa E (~935 m E), looking ESE past the U-20 closure over the eastern horizon (ADR 0085)."),
                ("edge-west", new Vector2(-949.8f, 50.8f), new Vector2(-1.00f, -0.09f),
                    "Driver eye 2.5 m on ul. Gen. S. Maczka W (~-950 m E), looking W past the U-20 closure over the western horizon (ADR 0085)."),
                ("edge-south", new Vector2(-267.6f, -965.9f), new Vector2(0.46f, -0.89f),
                    "Driver eye 2.5 m on al. Tysiaclecia S (~-966 m N), looking SSE past the U-20 closure towards Bialostoczek and EC chimneys (ADR 0085)."),
            };
            foreach (var (id, posEN, dirEN, note) in defs)
            {
                if (qa.Find("QA_" + id) != null) continue;
                Vector2 d = dirEN.normalized;
                Vector3 g = Ground(new Vector3(posEN.x, 0f, posEN.y), float.NaN);
                Vector3 pos = g + Vector3.up * 2.5f;
                Vector3 look = new Vector3(posEN.x + d.x * 120f, g.y + 2.0f, posEN.y + d.y * 120f);
                Qa(qa, id, pos, look, 60f, note);
            }
        }

        static void Qa(Transform parent, string id, Vector3 pos, Vector3 lookAt, float fov, string note)
        {
            var go = new GameObject("QA_" + id);
            go.transform.SetParent(parent, false);
            go.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(lookAt - pos, Vector3.up));
            var cam = go.AddComponent<Camera>();
            cam.fieldOfView = fov; cam.nearClipPlane = 0.1f; cam.farClipPlane = 3500f;
            cam.enabled = false;
            go.AddComponent<UniversalAdditionalCameraData>();
            var qa = go.AddComponent<ControlCamera>();
            qa.id = id; qa.note = note;
        }
    }
}
