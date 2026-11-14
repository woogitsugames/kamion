using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using Game.Gameplay;
using Game.Rendering;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using L = Game.Gameplay.DrivingLabLayout;
using EditorTools = Game.Editor.Build.EditorTools;

namespace Game.Editor.Setup
{
    /// <summary>
    /// Generates the Stage 1 driving lab from code (regenerate, never hand-edit):
    /// - Resources/VehicleData_Tractor4x2.asset (references the physics JSON definitions),
    /// - graybox tractor prefab at the true dimensions (art-source/truck/dims.json is re-read and checked),
    /// - procedural textures/materials/meshes under Environment/DrivingLab,
    /// - DrivingLab.unity: 400×400 m asphalt pad with an acceleration lane and distance markers, R25/R50 circles,
    ///   figure-eight, 6 % and 12 % ramps, 8/15 cm platforms and side curbs, speed bump, ruts, surface patches
    ///   (wet asphalt, concrete, cobbles, gravel, grass) tagged with <see cref="GroundSurface"/>, signs, lighting,
    ///   the truck at the spawn, camera, bootstrap and visual-QA control cameras.
    /// - Stage 2: graybox curtainsider trailer prefab (coupled behind the truck at the spawn), coupling bay, loading
    ///   dock with bumpers, 7 % hill road (600 m) with a turning plateau, wet skid pad with an R100 circle.
    /// Entry point: Kamion/Setup/Rebuild DrivingLab, or batchmode -executeMethod Game.Editor.Setup.DrivingLabSceneBuilder.BuildBatch
    /// </summary>
    public static class DrivingLabSceneBuilder
    {
        public const string ScenePath = "Assets/_Project/World/Scenes/DrivingLab.unity";
        const string EnvDir = "Assets/_Project/Environment/DrivingLab";
        const string TexDir = EnvDir + "/Textures";
        const string MeshAssetPath = EnvDir + "/DrivingLab_Meshes.asset";
        const string VehicleDataPath = "Assets/_Project/Vehicle/Runtime/Resources/" + VehicleDataAsset.DefaultResourcePath + ".asset";
        const string PrefabDir = "Assets/_Project/Vehicle/Runtime/Prefabs";
        public const string PrefabPath = PrefabDir + "/" + GrayboxTractorBuilder.RootName + ".prefab";
        public const string TrailerPrefabPath = PrefabDir + "/" + GrayboxTrailerBuilder.RootName + ".prefab";
        const string DefDir = "Assets/_Project/Vehicle/Physics/Definitions/Data";

        static readonly List<Mesh> s_Meshes = new List<Mesh>();
        static Material s_Paint, s_Asphalt, s_Sign, s_Post, s_Text;
        static Font s_Font;

        public static void BuildBatch()
        {
            int exit = 0;
            try { Build(); Debug.Log("DRIVINGLAB_RESULT: OK"); }
            catch (Exception e) { Debug.LogException(e); Debug.Log("DRIVINGLAB_RESULT: FAILED"); exit = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/Setup/Rebuild DrivingLab")]
        public static void Build()
        {
            foreach (var d in new[] { EnvDir, TexDir, PrefabDir, Path.GetDirectoryName(ScenePath), Path.GetDirectoryName(VehicleDataPath) })
                Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, d));
            AssetDatabase.Refresh();

            var data = CreateVehicleData();
            var dims = ReadAndCheckDims();
            var gbMats = CreateGrayboxMaterials();
            var prefab = CreateTractorPrefab(data, dims, gbMats);
            var trailerPrefab = CreateTrailerPrefab(data, gbMats);

            // ---- materials ----
            var asphaltTex = Tex("T_Asphalt", 512, AsphaltPixel);
            var concreteTex = Tex("T_Concrete", 512, ConcretePixel);
            var cobbleTex = Tex("T_Cobbles", 512, CobblePixel);
            var gravelTex = Tex("T_Gravel", 512, GravelPixel);
            var grassTex = Tex("T_Grass", 512, GrassPixel);
            s_Asphalt = Lit("M_Asphalt_Dry", Color.white, 0.18f, asphaltTex);
            var wet = Lit("M_Asphalt_Wet", new Color(0.80f, 0.82f, 0.85f), 0.62f, asphaltTex);
            var concrete = Lit("M_Concrete", Color.white, 0.2f, concreteTex);
            var cobbles = Lit("M_Cobbles", Color.white, 0.22f, cobbleTex);
            var gravel = Lit("M_Gravel", Color.white, 0.08f, gravelTex);
            var grass = Lit("M_Grass", Color.white, 0.10f, grassTex);
            s_Paint = Lit("M_Paint_White", new Color(0.86f, 0.86f, 0.83f), 0.25f);
            var paintYellow = Lit("M_Paint_Yellow", new Color(0.86f, 0.70f, 0.18f), 0.25f);
            var curb = Lit("M_Curb_Concrete", new Color(0.70f, 0.69f, 0.66f), 0.15f);
            var ramp = Lit("M_Ramp_Concrete", Color.white, 0.2f, concreteTex);
            s_Sign = Lit("M_Sign_Board", new Color(0.90f, 0.90f, 0.87f), 0.2f);
            s_Post = Lit("M_Sign_Post", new Color(0.35f, 0.36f, 0.37f), 0.4f);
            var cone = Lit("M_Ref_Orange", new Color(0.86f, 0.40f, 0.10f), 0.3f);
            var sky = Skybox();
            s_Font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            s_Text = TextMaterial(s_Font);

            s_Meshes.Clear();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            SetupLighting(sky);

            var world = new GameObject("DrivingLab").transform;
            var ground = Group(world, "Ground");
            var marks = Group(world, "Markings");
            var obst = Group(world, "Obstacles");
            var signs = Group(world, "Signs");

            // ---- ground ----
            float pad = L.PadHalfSize * 2f;
            Solid(ground, "Pad_Asphalt_400m", MeshGen.Slab(new Vector3(pad, 1f, pad), 4f, "Pad"), new Vector3(0, -0.5f, 0), s_Asphalt, SurfaceKind.DryAsphalt);
            Solid(ground, "Surround_Grass_8km", MeshGen.Slab(new Vector3(8000f, 1f, 8000f), 8f, "Surround"), new Vector3(0, -0.51f, 0), grass, SurfaceKind.Grass);

            // ---- acceleration lane: edge lines, transverse lines every 10 m, signs every 50 m ----
            float laneLen = L.LaneEndZ - L.Spawn.z + 10f;
            float laneMidZ = (L.LaneEndZ + L.Spawn.z - 10f) * 0.5f;
            Paint(marks, "LaneEdge_W", new Vector3(-L.LaneHalfWidth, 0, laneMidZ), new Vector3(0.15f, 0, laneLen), s_Paint);
            Paint(marks, "LaneEdge_E", new Vector3(L.LaneHalfWidth, 0, laneMidZ), new Vector3(0.15f, 0, laneLen), s_Paint);
            for (int d = 0; L.Spawn.z + d <= L.LaneEndZ; d += 10)
            {
                bool major = d % 50 == 0;
                float z = L.Spawn.z + d;
                Paint(marks, $"Dist_{d}m", new Vector3(0, 0, z), new Vector3(L.LaneHalfWidth * 2f, 0, major ? 0.40f : 0.12f), s_Paint);
                if (major) Sign(signs, $"{d} m", new Vector3(L.LaneHalfWidth + 2.2f, 0, z), 0f, 1.6f);
            }
            Sign(signs, "START — przyspieszanie / hamowanie", new Vector3(-L.LaneHalfWidth - 3.5f, 0, L.Spawn.z + 6f), 0f, 4.2f);

            // ---- circles and figure-eight ----
            Ring(marks, "Circle_R50", L.CircleR50Center, L.CircleR50, 0.25f);
            Ring(marks, "Circle_R50_inner", L.CircleR50Center, 0.6f, 0.25f);
            Ring(marks, "Circle_R25", L.CircleR25Center, L.CircleR25, 0.25f);
            Ring(marks, "Circle_R25_inner", L.CircleR25Center, 0.6f, 0.25f);
            Sign(signs, "OKRĄG R = 50 m", L.CircleR50Center + new Vector3(0, 0, -L.CircleR50 - 6f), 0f, 3.2f);
            Sign(signs, "OKRĄG R = 25 m", L.CircleR25Center + new Vector3(0, 0, -L.CircleR25 - 6f), 0f, 3.2f);
            Ring(marks, "Eight_S", L.FigureEightCenter + new Vector3(0, 0, -L.FigureEightR), L.FigureEightR, 0.25f);
            Ring(marks, "Eight_N", L.FigureEightCenter + new Vector3(0, 0, L.FigureEightR), L.FigureEightR, 0.25f);
            Sign(signs, "ÓSEMKA 2 × R 20 m", L.FigureEightCenter + new Vector3(L.FigureEightR + 6f, 0, -2f * L.FigureEightR - 4f), 0f, 3.4f);

            // ---- ramps 6 % and 12 % ----
            RampAt(obst, signs, "Ramp_6pct", L.Ramp6X, 0.06f, ramp);
            RampAt(obst, signs, "Ramp_12pct", L.Ramp12X, 0.12f, ramp);

            // ---- obstacle lane: platforms 8/15 cm, speed bump, ruts ----
            float ow = L.ObstacleHalfWidth * 2f;
            Solid(obst, "Platform_8cm", MeshGen.Slab(new Vector3(ow, 0.08f, L.PlatformLength), 4f, "Platform8"), new Vector3(L.ObstacleX, 0.04f, L.Curb8Z + L.PlatformLength * 0.5f), curb, SurfaceKind.Concrete);
            Solid(obst, "Platform_15cm", MeshGen.Slab(new Vector3(ow, 0.15f, L.PlatformLength), 4f, "Platform15"), new Vector3(L.ObstacleX, 0.075f, L.Curb15Z + L.PlatformLength * 0.5f), curb, SurfaceKind.Concrete);
            Sign(signs, "KRAWĘŻNIK 8 cm", new Vector3(L.ObstacleX - L.ObstacleHalfWidth - 2.5f, 0, L.Curb8Z - 3f), 0f, 3.0f);
            Sign(signs, "KRAWĘŻNIK 15 cm", new Vector3(L.ObstacleX - L.ObstacleHalfWidth - 2.5f, 0, L.Curb15Z - 3f), 0f, 3.0f);
            // Speed bump: 8 cm high, 1.0 m long, half-sine profile (WORKING_VALUE geometry).
            var bump = new Vector2[11];
            for (int i = 0; i <= 10; i++) bump[i] = new Vector2(i * 0.1f, 0.08f * Mathf.Sin(Mathf.PI * i / 10f));
            Solid(obst, "SpeedBump_8cm", MeshGen.Prism(bump, ow, 1f, "Bump"), new Vector3(L.ObstacleX, 0, L.BumpZ), paintYellow, SurfaceKind.DryAsphalt, true);
            Sign(signs, "PRÓG 8 cm", new Vector3(L.ObstacleX - L.ObstacleHalfWidth - 2.5f, 0, L.BumpZ - 3f), 0f, 2.4f);
            // Ruts 4 cm deep, 0.6 m wide at x = ±1.0 m from the lane centre: raised strips with ramps at both ends.
            float[] edges = { L.ObstacleX - L.ObstacleHalfWidth, L.ObstacleX - 1.3f, L.ObstacleX - 0.7f, L.ObstacleX + 0.7f, L.ObstacleX + 1.3f, L.ObstacleX + L.ObstacleHalfWidth };
            var rutProfile = new[] { new Vector2(0, 0), new Vector2(0.6f, 0.04f), new Vector2(L.RutsLength - 0.6f, 0.04f), new Vector2(L.RutsLength, 0) };
            for (int i = 0; i < edges.Length; i += 2)
            {
                float w = edges[i + 1] - edges[i];
                Solid(obst, $"RutStrip_{i / 2}", MeshGen.Prism(rutProfile, w, 4f, "RutStrip" + i), new Vector3((edges[i] + edges[i + 1]) * 0.5f, 0, L.RutsStartZ), s_Asphalt, SurfaceKind.DryAsphalt, true);
            }
            Sign(signs, "KOLEINY 4 cm", new Vector3(L.ObstacleX - L.ObstacleHalfWidth - 2.5f, 0, L.RutsStartZ - 3f), 0f, 2.8f);
            // Long side curbs (mount with one side).
            Solid(obst, "SideCurb_8cm", MeshGen.Slab(new Vector3(0.3f, 0.08f, 40f), 2f, "SideCurb8"), new Vector3(L.SideCurb8X, 0.04f, -130f), curb, SurfaceKind.Concrete);
            Solid(obst, "SideCurb_15cm", MeshGen.Slab(new Vector3(0.3f, 0.15f, 40f), 2f, "SideCurb15"), new Vector3(L.SideCurb15X, 0.075f, -130f), curb, SurfaceKind.Concrete);
            Sign(signs, "KRAWĘŻNIK BOCZNY 8 cm", new Vector3(L.SideCurb8X - 3f, 0, -153f), 0f, 3.6f);
            Sign(signs, "KRAWĘŻNIK BOCZNY 15 cm", new Vector3(L.SideCurb15X + 3f, 0, -153f), 0f, 3.8f);

            // ---- surface patches ----
            var kinds = new[] { SurfaceKind.DryAsphalt, SurfaceKind.WetAsphalt, SurfaceKind.Concrete, SurfaceKind.Cobbles, SurfaceKind.Gravel, SurfaceKind.Grass };
            var mats = new[] { s_Asphalt, wet, concrete, cobbles, gravel, grass };
            var names = new[] { "ASFALT SUCHY", "ASFALT MOKRY", "BETON", "KOSTKA", "ŻWIR", "TRAWA" };
            for (int i = 0; i < kinds.Length; i++)
            {
                float x = L.PatchX0 + L.PatchWidth * (i + 0.5f);
                float len = L.PatchZ1 - L.PatchZ0;
                if (i > 0)
                    Solid(ground, "Patch_" + kinds[i], MeshGen.Slab(new Vector3(L.PatchWidth, 0.05f, len), kinds[i] == SurfaceKind.Cobbles || kinds[i] == SurfaceKind.Gravel ? 2f : 4f, "Patch" + i),
                        new Vector3(x, -0.02f, (L.PatchZ0 + L.PatchZ1) * 0.5f), mats[i], kinds[i]);
                Sign(signs, names[i], new Vector3(x, 0, L.PatchZ0 - 4f), 0f, 2.6f);
                Paint(marks, "PatchEdge_" + i, new Vector3(L.PatchX0 + L.PatchWidth * i, 0, (L.PatchZ0 + L.PatchZ1) * 0.5f), new Vector3(0.12f, 0, L.PatchZ1 - L.PatchZ0), s_Paint, 0.04f);
            }

            // ---- scale references: cones every 5 m along the west lane edge for the first 50 m ----
            for (int d = 0; d <= 50; d += 5)
            {
                var c = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                c.name = $"Cone_{d}m";
                c.transform.SetParent(obst, false);
                c.transform.localPosition = new Vector3(-L.LaneHalfWidth - 1f, 0.375f, L.Spawn.z + d);
                c.transform.localScale = new Vector3(0.3f, 0.375f, 0.3f);
                c.GetComponent<MeshRenderer>().sharedMaterial = cone;
                UnityEngine.Object.DestroyImmediate(c.GetComponent<Collider>());
                c.isStatic = true;
            }

            // ---- Stage 2: coupling bay, loading dock, hill road, wet skid pad ----
            var dockMats = new DockMaterials
            {
                wall = Lit("M_Dock_Wall", new Color(0.66f, 0.66f, 0.63f), 0.15f, concreteTex),
                door = Lit("M_Dock_Door", new Color(0.36f, 0.42f, 0.48f), 0.3f),
                rubber = Lit("M_Dock_Rubber", new Color(0.05f, 0.05f, 0.05f), 0.1f),
                yellow = paintYellow, barrier = curb,
            };
            BuildCouplingBay(marks, signs);
            BuildDock(world, marks, signs, dockMats);
            BuildHill(world, signs, s_Asphalt, ramp, curb);
            BuildWetPad(ground, marks, signs, wet);
            BuildStraight(ground, marks, signs);

            SaveMeshes();

            // ---- truck + trailer, camera, bootstrap ----
            var truck = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            truck.transform.SetPositionAndRotation(L.Spawn, Quaternion.identity);
            var eye = L.Spawn + dims.EyePointVehicle;
            var trailerGo = (GameObject)PrefabUtility.InstantiatePrefab(trailerPrefab);
            {
                // Coupled at static equilibrium behind the truck (the bootstrap respawns per the lab preset at run time).
                var tractorModel = data.CreateModel();
                var trailerModel = data.CreateTrailer();
                _ = new CombinationModel(tractorModel, trailerModel, true);
                CombinationPlacement.Coupled(tractorModel, L.Spawn, Quaternion.identity, trailerModel, 0f, out Vector3 tp, out Quaternion tq);
                trailerGo.transform.SetPositionAndRotation(tp, tq);
            }

            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            var cam = camGo.AddComponent<Camera>();
            cam.fieldOfView = 55f; cam.nearClipPlane = 0.05f; cam.farClipPlane = 5000f;
            cam.clearFlags = CameraClearFlags.Skybox;
            camGo.AddComponent<UniversalAdditionalCameraData>();
            camGo.AddComponent<AudioListener>();
            camGo.transform.SetPositionAndRotation(eye, Quaternion.identity);

            var boot = new GameObject("DrivingLabBootstrap").AddComponent<DrivingLabBootstrap>();
            boot.vehicle = truck.GetComponent<VehicleBody>();
            boot.trailer = trailerGo.GetComponent<TrailerBody>();
            boot.mainCamera = cam;

            // ---- visual-QA control cameras ----
            var qa = new GameObject("ControlCameras").transform;
            Vector3 s0 = L.Spawn;
            Qa(qa, "lab-overview", new Vector3(-215f, 120f, -275f), new Vector3(0f, 0f, -10f), 45f, "Whole pad from the south-west: layout legibility, markings, zones.");
            Qa(qa, "lab-truck-34", s0 + new Vector3(6.5f, 2.8f, 11.5f), s0 + new Vector3(0f, 1.7f, 2.2f), 50f, "Graybox tractor 3/4 front: proportions, wheels on the ground, cab, mirrors.");
            Qa(qa, "lab-truck-side", s0 + new Vector3(13f, 1.6f, 2.2f), s0 + new Vector3(0f, 1.6f, 2.2f), 40f, "Side elevation: wheelbase 3.70 m, overhangs, cab height 3.75 m against the 1 m cones.");
            Qa(qa, "lab-cab-eye", eye, eye + Quaternion.Euler(7f, 0f, 0f) * Vector3.forward * 10f, 55f, "Driver eye point with the driving HUD: windscreen view, mirror insets, steering wheel, safe area.", hud: true, mirrorInsets: true);
            Qa(qa, "lab-chase-hud", s0 + new Vector3(0f, 7.5f, -26f), s0 + new Vector3(0f, 2f, 3f), 50f, "Chase camera (combination framing) with HUD and telemetry panel.", hud: true, telemetry: true);
            Qa(qa, "lab-combo-34", s0 + new Vector3(10f, 3.6f, 9f), s0 + new Vector3(0f, 1.9f, -4.5f), 50f, "Tractor + 13.6 m curtainsider 3/4 front: kingpin over the fifth wheel, tridem, landing gear, proportions.");
            Qa(qa, "lab-combo-side", s0 + new Vector3(30f, 2.0f, -3.8f), s0 + new Vector3(0f, 2.0f, -3.8f), 40f, "Combination side elevation: 16.6 m overall, trailer 13.6 × 4.0 m against the 1 m cones.");
            Qa(qa, "lab-trailer-rear", s0 + new Vector3(-5f, 2.2f, -24f), s0 + new Vector3(0f, 1.4f, -12.5f), 50f, "Trailer rear: doors, lamps, underrun bar, tridem, reversing camera mount.");
            Qa(qa, "lab-cab-mirror", eye, eye + Quaternion.Euler(6f, -42f, 0f) * Vector3.forward * 10f, 55f, "Cab view turned to the left mirror: render-texture mirror shows the trailer side.", hud: true);
            Qa(qa, "lab-reverse-hud", s0 + new Vector3(0f, 7.5f, -26f), s0 + new Vector3(0f, 2f, 3f), 50f, "HUD while reversing: reversing-camera view from the trailer rear.", hud: true, reverseCam: true);
            Qa(qa, "lab-dock", new Vector3(L.DockBay0X + 8f, 9f, L.DockFaceZ - 48f), new Vector3(L.DockBay0X + 8f, 1.5f, L.DockFaceZ), 50f, "Loading dock: 5 bays, 1.20 m dock height, bumpers, guide lines.");
            Qa(qa, "lab-coupling-bay", L.CouplingKingpin + new Vector3(-14f, 7f, -22f), L.CouplingKingpin + new Vector3(0f, 0f, 0f), 50f, "Coupling bay markings (trailer parked here in the Solo preset).");
            Qa(qa, "lab-hill", new Vector3(L.HillStartX - 40f, 22f, L.HillZ - 60f), new Vector3(L.HillStartX + 300f, 15f, L.HillZ), 50f, "7 % hill road (600 m, 42 m high), barriers, turning plateau.");
            Qa(qa, "lab-straight", new Vector3(L.StraightStartX - 25f, 9f, L.StraightZ - 18f), new Vector3(L.StraightStartX + 120f, 0f, L.StraightZ), 50f, "Measurement straight (1300 m, ADR 0195): start line, edge lines, 50 m marks, distance signs.");
            Qa(qa, "lab-wet", new Vector3(L.WetX0 - 10f, 30f, L.WetZ0 - 30f), L.WetCircleCenter, 55f, "Wet skid pad with the R100 circle (jackknife demo).");
            Qa(qa, "lab-obstacles", new Vector3(L.ObstacleX - 20f, 12f, L.Curb8Z - 22f), new Vector3(L.ObstacleX, 0f, L.RutsStartZ), 50f, "Obstacle lane: 8/15 cm platforms, speed bump, ruts, side curbs.");
            Qa(qa, "lab-ramps", new Vector3(20f, 6f, L.RampStartZ - 18f), new Vector3((L.Ramp6X + L.Ramp12X) * 0.5f, 1f, L.RampStartZ + 30f), 50f, "6 % and 12 % ramps with plateau.");
            Qa(qa, "lab-surfaces", new Vector3(L.PatchX0 + 60f, 14f, L.PatchZ0 - 26f), new Vector3(L.PatchX0 + 60f, 0f, L.PatchZ0 + 20f), 55f, "Surface patches: dry/wet asphalt, concrete, cobbles, gravel, grass + labels.");
            Qa(qa, "lab-circles", new Vector3(-110f, 70f, -215f), new Vector3(-110f, 0f, -40f), 50f, "R50 / R25 circles and figure-eight markings.");

            EditorSceneManager.SaveScene(scene, ScenePath);
            BuildScenes.Apply();
            AssetDatabase.SaveAssets();
            Debug.Log($"[SETUP] DrivingLab written: {ScenePath}, prefab {PrefabPath}");
        }

        // ------------------------------------------------------------------ vehicle

        static VehicleDataAsset CreateVehicleData()
        {
            var a = AssetDatabase.LoadAssetAtPath<VehicleDataAsset>(VehicleDataPath);
            if (a == null) { a = ScriptableObject.CreateInstance<VehicleDataAsset>(); AssetDatabase.CreateAsset(a, VehicleDataPath); }
            a.vehicle = AssetDatabase.LoadAssetAtPath<TextAsset>($"{DefDir}/tractor_4x2_generic.vehicle.json");
            a.engine = AssetDatabase.LoadAssetAtPath<TextAsset>($"{DefDir}/diesel_r6_13l_368kw.engine.json");
            a.gearbox = AssetDatabase.LoadAssetAtPath<TextAsset>($"{DefDir}/amt12_od_traxon_class.gearbox.json");
            var tires = new List<TextAsset>();
            foreach (var guid in AssetDatabase.FindAssets("t:TextAsset", new[] { DefDir }))
            {
                var p = AssetDatabase.GUIDToAssetPath(guid);
                if (p.EndsWith(".tire.json")) tires.Add(AssetDatabase.LoadAssetAtPath<TextAsset>(p));
            }
            a.tires = tires.ToArray();
            a.trailer = AssetDatabase.LoadAssetAtPath<TextAsset>($"{DefDir}/curtainsider_tridem_13_6.trailer.json");
            if (a.vehicle == null || a.engine == null || a.gearbox == null || a.tires.Length == 0)
                throw new FileNotFoundException("vehicle definitions missing in " + DefDir);
            EditorUtility.SetDirty(a);
            AssetDatabase.SaveAssets();
            a.CreateModel(); // parse + validate now
            if (a.trailer == null) throw new FileNotFoundException("trailer definition missing in " + DefDir);
            a.CreateTrailer();
            return a;
        }

        /// <summary>Reads art-source/truck/dims.json and fails if the runtime defaults differ (single source of truth).</summary>
        public static TractorDimensions ReadAndCheckDims()
        {
            var d = new TractorDimensions();
            string path = Path.Combine(EditorTools.RepoRoot, "art-source", "truck", "dims.json");
            if (!File.Exists(path)) { Debug.LogWarning("[SETUP] dims.json not found, using TractorDimensions defaults"); return d; }
            string json = File.ReadAllText(path);
            var errors = new List<string>();
            void Check(string key, float expected)
            {
                var m = Regex.Match(json, "\"" + key + "\"\\s*:\\s*\\{\\s*\"value\"\\s*:\\s*(-?[0-9.]+)");
                if (!m.Success) { errors.Add(key + " missing"); return; }
                float v = float.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture);
                if (Mathf.Abs(v - expected) > 1e-4f) errors.Add($"{key}: dims.json {v} != TractorDimensions {expected}");
            }
            Check("wheelbase_m", d.wheelbase); Check("front_overhang_m", d.frontOverhang); Check("rear_overhang_m", d.rearOverhang);
            Check("cab_width_m", d.cabWidth); Check("overall_height_m", d.overallHeight); Check("cab_back_behind_front_axle_m", d.cabBackBehindFrontAxle);
            Check("cab_body_bottom_m", d.cabBodyBottom); Check("cab_interior_floor_m", d.cabInteriorFloor); Check("frame_width_outer_m", d.frameWidthOuter);
            Check("frame_top_height_m", d.frameTopHeight); Check("fifth_wheel_height_m", d.fifthWheelHeight); Check("fifth_wheel_lead_m", d.fifthWheelLead);
            Check("dual_spacing_m", d.dualSpacing); Check("tyre_section_width_m", d.tyreSectionWidth); Check("rim_flange_diameter_m", d.rimFlangeDiameter);
            Check("mirror_head_outer_m", d.mirrorHeadOuter);
            var eye = Regex.Match(json, "\"driver_eye_point_m\"\\s*:\\s*\\{\\s*\"value\"\\s*:\\s*\\[\\s*(-?[0-9.]+)\\s*,\\s*(-?[0-9.]+)\\s*,\\s*(-?[0-9.]+)");
            if (!eye.Success) errors.Add("driver_eye_point_m missing");
            else
            {
                var e = new Vector3(float.Parse(eye.Groups[1].Value, CultureInfo.InvariantCulture), float.Parse(eye.Groups[2].Value, CultureInfo.InvariantCulture), float.Parse(eye.Groups[3].Value, CultureInfo.InvariantCulture));
                if ((e - d.driverEyePointDims).sqrMagnitude > 1e-8f) errors.Add($"driver_eye_point_m {e} != {d.driverEyePointDims}");
            }
            Check("driver_eye_above_h_point_m", d.driverEyeAboveHPoint);
            var hp = Regex.Match(json, "\"driver_h_point_m\"\\s*:\\s*\\{\\s*\"value\"\\s*:\\s*\\[\\s*(-?[0-9.]+)\\s*,\\s*(-?[0-9.]+)\\s*,\\s*(-?[0-9.]+)");
            if (!hp.Success) errors.Add("driver_h_point_m missing");
            else
            {
                var h = new Vector3(float.Parse(hp.Groups[1].Value, CultureInfo.InvariantCulture), float.Parse(hp.Groups[2].Value, CultureInfo.InvariantCulture), float.Parse(hp.Groups[3].Value, CultureInfo.InvariantCulture));
                if ((h - d.driverHPointDims).sqrMagnitude > 1e-8f) errors.Add($"driver_h_point_m {h} != {d.driverHPointDims}");
            }
            if (errors.Count > 0) throw new InvalidDataException("TractorDimensions out of sync with art-source/truck/dims.json: " + string.Join("; ", errors));
            return d;
        }

        static GrayboxMaterials CreateGrayboxMaterials()
        {
            var c = GrayboxMaterials.DefaultColors;
            return new GrayboxMaterials
            {
                paint = Lit("M_GB_Paint", c[0], 0.45f, null, PrefabDir), chassis = Lit("M_GB_Chassis", c[1], 0.25f, null, PrefabDir),
                tire = Lit("M_GB_Tire", c[2], 0.15f, null, PrefabDir), rim = Lit("M_GB_Rim", c[3], 0.4f, null, PrefabDir),
                interior = Lit("M_GB_Interior", c[4], 0.2f, null, PrefabDir), dark = Lit("M_GB_Dark", c[5], 0.3f, null, PrefabDir),
                marker = Lit("M_GB_Marker", c[6], 0.3f, null, PrefabDir),
                curtain = Lit("M_GB_Curtain", c[7], 0.2f, null, PrefabDir), trailerPanel = Lit("M_GB_TrailerPanel", c[8], 0.35f, null, PrefabDir),
                lamp = Lit("M_GB_Lamp", c[9], 0.5f, null, PrefabDir), mirror = Unlit("M_GB_MirrorGlass", GrayboxMaterials.MirrorIdleColor, PrefabDir),
            };
        }

        static GameObject CreateTractorPrefab(VehicleDataAsset data, TractorDimensions dims, GrayboxMaterials mats)
        {
            var body = GrayboxTractorBuilder.Build(data, dims, mats);
            var prefab = PrefabUtility.SaveAsPrefabAsset(body.gameObject, PrefabPath);
            UnityEngine.Object.DestroyImmediate(body.gameObject);
            return prefab;
        }

        static GameObject CreateTrailerPrefab(VehicleDataAsset data, GrayboxMaterials mats)
        {
            var body = GrayboxTrailerBuilder.Build(data, new TrailerDimensions(), mats);
            var prefab = PrefabUtility.SaveAsPrefabAsset(body.gameObject, TrailerPrefabPath);
            UnityEngine.Object.DestroyImmediate(body.gameObject);
            return prefab;
        }

        // ------------------------------------------------------------------ Stage 2 lab areas

        sealed class DockMaterials { public Material wall, door, rubber, yellow, barrier; }

        /// <summary>Painted outline of the parked-trailer spot and the tractor approach lane (trailer parked here in the Solo preset).</summary>
        static void BuildCouplingBay(Transform marks, Transform signs)
        {
            Vector3 k = L.CouplingKingpin;
            const float hw = 1.6f;
            float rear = k.z - 12.2f, front = k.z + 14f;
            Paint(marks, "CouplingBay_W", new Vector3(k.x - hw, 0, (rear + front) * 0.5f), new Vector3(0.12f, 0, front - rear), s_Paint);
            Paint(marks, "CouplingBay_E", new Vector3(k.x + hw, 0, (rear + front) * 0.5f), new Vector3(0.12f, 0, front - rear), s_Paint);
            Paint(marks, "CouplingBay_Rear", new Vector3(k.x, 0, rear), new Vector3(2 * hw, 0, 0.12f), s_Paint);
            Paint(marks, "CouplingBay_Kingpin", new Vector3(k.x, 0, k.z), new Vector3(0.6f, 0, 0.06f), s_Paint);
            Sign(signs, "PLAC NACZEP — sprzęganie (Zestaw → Solo)", new Vector3(k.x - hw - 3.5f, 0, rear - 3f), 0f, 4.6f);
        }

        /// <summary>
        /// Loading dock on the north edge: a warehouse block, 5 bays with sectional doors at the 1.20 m dock floor,
        /// two rubber bumpers per bay (box colliders the trailer rear touches), yellow guide lines and stop marks.
        /// </summary>
        static void BuildDock(Transform world, Transform marks, Transform signs, DockMaterials m)
        {
            var dock = Group(world, "LoadingDock");
            float x0 = L.DockBay0X - 6f, x1 = L.DockBay0X + (L.DockBays - 1) * L.DockBayPitch + 6f;
            float depth = L.PadHalfSize - L.DockFaceZ;
            var wall = Solid(dock, "Warehouse", MeshGen.Slab(new Vector3(x1 - x0, 9f, depth), 4f, "Warehouse"), new Vector3((x0 + x1) * 0.5f, 4.5f, L.DockFaceZ + depth * 0.5f), m.wall, SurfaceKind.Concrete);
            wall.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.On;
            for (int i = 0; i < L.DockBays; i++)
            {
                float x = L.DockBay0X + i * L.DockBayPitch;
                Deco(dock, $"Door_{i + 1}", new Vector3(x, L.DockHeight + 1.6f, L.DockFaceZ - 0.02f), new Vector3(3.0f, 3.2f, 0.04f), m.door);
                Deco(dock, $"DoorSeal_{i + 1}", new Vector3(x, L.DockHeight + 1.65f, L.DockFaceZ - 0.01f), new Vector3(3.5f, 3.4f, 0.02f), m.rubber);
                Deco(dock, $"Leveller_{i + 1}", new Vector3(x, L.DockHeight - 0.03f, L.DockFaceZ - 0.04f), new Vector3(2.2f, 0.06f, 0.08f), m.barrier);
                for (int sgn = -1; sgn <= 1; sgn += 2)
                {
                    // Rubber bumper 0.25 × 0.40 m, 0.12 m proud of the dock face, top 0.15 m above the dock floor (WORKING_VALUE).
                    var b = Solid(dock, $"Bumper_{i + 1}{(sgn < 0 ? "L" : "R")}", MeshGen.Slab(new Vector3(0.25f, 0.40f, 0.12f), 1f, "Bumper"),
                        new Vector3(x + sgn * 0.85f, L.DockHeight - 0.05f, L.DockFaceZ - 0.06f), m.rubber, SurfaceKind.Concrete);
                    b.isStatic = true;
                    Paint(marks, $"DockGuide_{i + 1}{(sgn < 0 ? "L" : "R")}", new Vector3(x + sgn * 1.65f, 0, L.DockFaceZ - L.DockGuideLength * 0.5f - 0.5f),
                        new Vector3(0.15f, 0, L.DockGuideLength), m.yellow);
                }
                Paint(marks, $"DockStop_{i + 1}", new Vector3(x, 0, L.DockFaceZ - 1.2f), new Vector3(3.3f, 0, 0.15f), m.yellow);
                WallText(dock, (i + 1).ToString(CultureInfo.InvariantCulture), new Vector3(x, L.DockHeight + 3.6f, L.DockFaceZ - 0.03f), 0.09f);
            }
            Sign(signs, "RAMPA ZAŁADUNKOWA — cofanie (wys. 1,20 m)", new Vector3(x0 - 4f, 0, L.DockFaceZ - L.DockGuideLength - 4f), 0f, 5.2f);
        }

        /// <summary>7 % ramp (600 m, rising east), turning plateau 120 × 120 m on top, concrete barriers along both edges.</summary>
        /// <summary>Measurement straight north of the pad (ADR 0195): asphalt slab, edge lines, distance marks every 50 m, signs every 100 m.</summary>
        static void BuildStraight(Transform ground, Transform marks, Transform signs)
        {
            float len = L.StraightX1 - L.StraightX0, midX = (L.StraightX0 + L.StraightX1) * 0.5f, w = L.StraightHalfWidth * 2f + 2f;
            Solid(ground, "Straight_Asphalt_1300m", MeshGen.Slab(new Vector3(len, 1f, w), 4f, "Straight"), new Vector3(midX, -0.5f, L.StraightZ), s_Asphalt, SurfaceKind.DryAsphalt);
            Paint(marks, "Straight_Edge_N", new Vector3(midX, 0, L.StraightZ + L.StraightHalfWidth), new Vector3(len, 0, 0.15f), s_Paint);
            Paint(marks, "Straight_Edge_S", new Vector3(midX, 0, L.StraightZ - L.StraightHalfWidth), new Vector3(len, 0, 0.15f), s_Paint);
            for (int d = 0; L.StraightStartX + d <= L.StraightX1 - 10f; d += 50)
            {
                bool major = d % 100 == 0;
                float x = L.StraightStartX + d;
                Paint(marks, $"Straight_{d}m", new Vector3(x, 0, L.StraightZ), new Vector3(major ? 0.40f : 0.12f, 0, L.StraightHalfWidth * 2f), s_Paint);
                if (major) Sign(signs, $"{d} m", new Vector3(x, 0, L.StraightZ - L.StraightHalfWidth - 2.2f), 90f, 1.6f);
            }
            Sign(signs, "PROSTA POMIAROWA 0–80–0 km/h", new Vector3(L.StraightStartX - 6f, 0, L.StraightZ + L.StraightHalfWidth + 3.5f), 90f, 4.6f);
        }

        static void BuildHill(Transform world, Transform signs, Material asphalt, Material concrete, Material barrier)
        {
            var hill = Group(world, "HillRoad_7pct");
            float L0 = L.HillLength, H = L.HillTopHeight, W = L.HillRoadWidth, P = L.HillPlateau;
            var prof = new[] { new Vector2(0, 0), new Vector2(L0, H), new Vector2(L0, 0) };
            var ramp = Solid(hill, "Ramp_7pct", MeshGen.Prism(prof, W, 4f, "HillRamp"), new Vector3(L.HillStartX, 0, L.HillZ), asphalt, SurfaceKind.DryAsphalt, true);
            ramp.transform.localRotation = Quaternion.Euler(0f, 90f, 0f); // profile +Z → world +X (east)
            Solid(hill, "Plateau", MeshGen.Slab(new Vector3(P, H, P), 4f, "HillPlateau"), new Vector3(L.HillStartX + L0 + P * 0.5f, H * 0.5f, L.HillZ), concrete, SurfaceKind.Concrete);
            // Barriers (0.5 × 0.9 m) along the ramp edges, following the slope.
            float slopeLen = Mathf.Sqrt(L0 * L0 + H * H);
            float pitch = Mathf.Atan2(H, L0) * Mathf.Rad2Deg;
            for (int sgn = -1; sgn <= 1; sgn += 2)
            {
                var b = Solid(hill, sgn < 0 ? "Barrier_S" : "Barrier_N", MeshGen.Slab(new Vector3(slopeLen, 0.9f, 0.5f), 2f, "HillBarrier" + sgn),
                    new Vector3(L.HillStartX + L0 * 0.5f, H * 0.5f + 0.45f, L.HillZ + sgn * (W * 0.5f + 0.25f)), barrier, SurfaceKind.Concrete);
                b.transform.localRotation = Quaternion.Euler(0f, 0f, pitch);
            }
            // Plateau edges: east, north, south full length; west in two pieces around the road.
            float px0 = L.HillStartX + L0, px1 = px0 + P, pz0 = L.HillZ - P * 0.5f, pz1 = L.HillZ + P * 0.5f;
            void Edge(string n, Vector3 c, Vector3 size) => Solid(hill, n, MeshGen.Slab(size, 2f, n), c, barrier, SurfaceKind.Concrete);
            Edge("PlateauEdge_E", new Vector3(px1 - 0.25f, H + 0.45f, L.HillZ), new Vector3(0.5f, 0.9f, P));
            Edge("PlateauEdge_N", new Vector3((px0 + px1) * 0.5f, H + 0.45f, pz1 - 0.25f), new Vector3(P, 0.9f, 0.5f));
            Edge("PlateauEdge_S", new Vector3((px0 + px1) * 0.5f, H + 0.45f, pz0 + 0.25f), new Vector3(P, 0.9f, 0.5f));
            float gap0 = L.HillZ - W * 0.5f - 0.5f, gap1 = L.HillZ + W * 0.5f + 0.5f;
            Edge("PlateauEdge_WS", new Vector3(px0 + 0.25f, H + 0.45f, (pz0 + gap0) * 0.5f), new Vector3(0.5f, 0.9f, gap0 - pz0));
            Edge("PlateauEdge_WN", new Vector3(px0 + 0.25f, H + 0.45f, (gap1 + pz1) * 0.5f), new Vector3(0.5f, 0.9f, pz1 - gap1));
            // Centre-line dashes (3 m every 12 m) following the slope.
            var dashMesh = MeshGen.Slab(new Vector3(3f, 0.002f, 0.15f), 1f, "HillDash");
            s_Meshes.Add(dashMesh);
            for (float d = 6f; d < L0 - 3f; d += 12f)
            {
                var go = new GameObject("Dash");
                go.transform.SetParent(hill, false);
                go.transform.localPosition = new Vector3(L.HillStartX + d, d * L.HillGrade + 0.012f, L.HillZ);
                go.transform.localRotation = Quaternion.Euler(0f, 0f, pitch);
                go.AddComponent<MeshFilter>().sharedMesh = dashMesh;
                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterial = s_Paint;
                mr.shadowCastingMode = ShadowCastingMode.Off;
                go.isStatic = true;
            }
            Sign(signs, "PODJAZD / ZJAZD 7 % · 600 m", new Vector3(L.HillStartX - 6f, 0, L.HillZ - W * 0.5f - 3f), 90f, 4.2f);
            var top = new Vector3(px0 + 8f, H, L.HillZ + W * 0.5f + 3f);
            Sign(signs, "ZJAZD 7 % — retarder / hamulec silnikowy / stała prędkość", top, -90f, 6.0f);
        }

        /// <summary>Wet asphalt skid pad (jackknife demo with the ABS fault) and its R100 guide circle.</summary>
        static void BuildWetPad(Transform ground, Transform marks, Transform signs, Material wet)
        {
            float w = L.WetX1 - L.WetX0, d = L.WetZ1 - L.WetZ0;
            Solid(ground, "WetPad", MeshGen.Slab(new Vector3(w, 0.05f, d), 4f, "WetPad"), new Vector3((L.WetX0 + L.WetX1) * 0.5f, -0.02f, (L.WetZ0 + L.WetZ1) * 0.5f), wet, SurfaceKind.WetAsphalt);
            Ring(marks, "WetCircle_R100", L.WetCircleCenter + new Vector3(0f, 0.005f, 0f), L.WetCircleR, 0.25f);
            Sign(signs, "PŁYTA MOKRA · R 100 m · scyzoryk: Zestaw → ABS: USTERKA", new Vector3(L.WetX0 - 4f, 0, L.WetZ1 - 14f), 90f, 6.4f);
        }

        /// <summary>Visual-only box (no collider).</summary>
        static void Deco(Transform parent, string name, Vector3 pos, Vector3 size, Material mat)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localScale = size;
            go.GetComponent<MeshRenderer>().sharedMaterial = mat;
            UnityEngine.Object.DestroyImmediate(go.GetComponent<Collider>());
            go.isStatic = true;
        }

        static void WallText(Transform parent, string text, Vector3 pos, float charSize)
        {
            var tgo = new GameObject("Text_" + text);
            tgo.transform.SetParent(parent, false);
            tgo.transform.localPosition = pos;
            var tm = tgo.AddComponent<TextMesh>();
            tm.font = s_Font; tm.text = text; tm.fontSize = 96; tm.characterSize = charSize;
            tm.anchor = TextAnchor.MiddleCenter; tm.alignment = TextAlignment.Center;
            tm.color = new Color(0.9f, 0.9f, 0.85f);
            tgo.GetComponent<MeshRenderer>().sharedMaterial = s_Text;
        }

        static Material Unlit(string name, Color color, string dir)
        {
            string path = $"{dir}/{name}.mat";
            var shader = Shader.Find("Universal Render Pipeline/Unlit");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = shader;
            mat.SetColor("_BaseColor", color);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        // ------------------------------------------------------------------ scene helpers

        static Transform Group(Transform parent, string name)
        {
            var t = new GameObject(name).transform;
            t.SetParent(parent, false);
            return t;
        }

        static GameObject Solid(Transform parent, string name, Mesh mesh, Vector3 pos, Material mat, SurfaceKind kind, bool meshCollider = false)
        {
            s_Meshes.Add(mesh);
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            go.AddComponent<MeshRenderer>().sharedMaterial = mat;
            if (meshCollider) go.AddComponent<MeshCollider>().sharedMesh = mesh;
            else go.AddComponent<BoxCollider>(); // size from mesh bounds
            go.AddComponent<GroundSurface>().kind = kind;
            go.isStatic = true;
            return go;
        }

        /// <summary>Painted flat mark (visual only, no collider), lifted 1.2 cm above the surface below.</summary>
        static void Paint(Transform parent, string name, Vector3 pos, Vector3 size, Material mat, float lift = 0.012f)
        {
            var mesh = MeshGen.Slab(new Vector3(size.x, 0.002f, size.z), 1f, name);
            s_Meshes.Add(mesh);
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos + new Vector3(0, lift, 0);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = mat;
            mr.shadowCastingMode = ShadowCastingMode.Off;
            go.isStatic = true;
        }

        static void Ring(Transform parent, string name, Vector3 center, float r, float width)
        {
            var mesh = MeshGen.Ring(r, width, Mathf.Clamp(Mathf.RoundToInt(r * 8f), 24, 512), name);
            s_Meshes.Add(mesh);
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = center + new Vector3(0, 0.012f, 0);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = s_Paint;
            mr.shadowCastingMode = ShadowCastingMode.Off;
            go.isStatic = true;
        }

        static void RampAt(Transform parent, Transform signs, string name, float x, float grade, Material mat)
        {
            float len = L.RampHeight / grade;
            var prof = new[] { new Vector2(0, 0), new Vector2(len, L.RampHeight), new Vector2(len + L.RampPlateau, L.RampHeight), new Vector2(2 * len + L.RampPlateau, 0) };
            Solid(parent, name, MeshGen.Prism(prof, L.RampWidth, 4f, name), new Vector3(x, 0, L.RampStartZ), mat, SurfaceKind.Concrete, true);
            Paint(parent, name + "_Foot", new Vector3(x, 0, L.RampStartZ - 0.3f), new Vector3(L.RampWidth, 0, 0.3f), s_Paint);
            Sign(signs, $"PODJAZD {grade * 100f:F0} %  ({L.RampHeight:F1} m)", new Vector3(x - L.RampWidth * 0.5f - 3f, 0, L.RampStartZ - 4f), 0f, 3.8f);
        }

        /// <summary>Sign on a post facing south (readable when driving north).</summary>
        static void Sign(Transform parent, string text, Vector3 basePos, float yaw, float width)
        {
            width = Mathf.Max(width, 0.4f + text.Length * 0.105f); // legacy font at this size: ≈ 0.1 m per character
            var root = new GameObject("Sign_" + text).transform;
            root.SetParent(parent, false);
            root.localPosition = basePos;
            root.localRotation = Quaternion.Euler(0, yaw, 0);
            var post = GameObject.CreatePrimitive(PrimitiveType.Cube);
            post.name = "Post"; post.transform.SetParent(root, false);
            post.transform.localPosition = new Vector3(0, 1.0f, 0.05f); post.transform.localScale = new Vector3(0.08f, 2.0f, 0.08f);
            post.GetComponent<MeshRenderer>().sharedMaterial = s_Post;
            UnityEngine.Object.DestroyImmediate(post.GetComponent<Collider>());
            var board = GameObject.CreatePrimitive(PrimitiveType.Cube);
            board.name = "Board"; board.transform.SetParent(root, false);
            board.transform.localPosition = new Vector3(0, 2.2f, 0); board.transform.localScale = new Vector3(width, 0.8f, 0.05f);
            board.GetComponent<MeshRenderer>().sharedMaterial = s_Sign;
            UnityEngine.Object.DestroyImmediate(board.GetComponent<Collider>());
            var tgo = new GameObject("Text");
            tgo.transform.SetParent(root, false);
            tgo.transform.localPosition = new Vector3(0, 2.2f, -0.035f);
            var tm = tgo.AddComponent<TextMesh>();
            tm.font = s_Font; tm.text = text; tm.fontSize = 96; tm.characterSize = 0.035f;
            tm.anchor = TextAnchor.MiddleCenter; tm.alignment = TextAlignment.Center;
            tm.color = new Color(0.08f, 0.08f, 0.09f);
            tgo.GetComponent<MeshRenderer>().sharedMaterial = s_Text;
            root.gameObject.isStatic = false;
        }

        static void Qa(Transform parent, string id, Vector3 pos, Vector3 lookAt, float fov, string note, bool hud = false, bool telemetry = false, bool reverseCam = false, bool mirrorInsets = false)
        {
            var go = new GameObject("QA_" + id);
            go.transform.SetParent(parent, false);
            go.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(lookAt - pos, Vector3.up));
            var cam = go.AddComponent<Camera>();
            cam.fieldOfView = fov; cam.nearClipPlane = hud ? 0.05f : 0.2f; cam.farClipPlane = 5000f;
            cam.enabled = false;
            go.AddComponent<UniversalAdditionalCameraData>();
            var qa = go.AddComponent<ControlCamera>();
            qa.id = id; qa.note = note; qa.includeDrivingHud = hud; qa.drivingHudTelemetry = telemetry; qa.drivingHudReverseCamera = reverseCam; qa.drivingHudMirrorInsets = mirrorInsets;
        }

        static void SaveMeshes()
        {
            AssetDatabase.DeleteAsset(MeshAssetPath);
            var container = new Mesh { name = "DrivingLab_Meshes" };
            AssetDatabase.CreateAsset(container, MeshAssetPath);
            var used = new HashSet<string>();
            foreach (var m in s_Meshes)
            {
                string n = m.name; int k = 1;
                while (!used.Add(n)) n = m.name + "_" + (k++);
                m.name = n;
                AssetDatabase.AddObjectToAsset(m, container);
            }
            AssetDatabase.SaveAssets();
        }

        static void SetupLighting(Material sky)
        {
            RenderSettings.skybox = sky;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.52f, 0.62f, 0.78f);
            RenderSettings.ambientEquatorColor = new Color(0.45f, 0.47f, 0.48f);
            RenderSettings.ambientGroundColor = new Color(0.20f, 0.19f, 0.17f);
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Custom;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogStartDistance = 350f;
            RenderSettings.fogEndDistance = 1800f;
            RenderSettings.fogColor = new Color(0.68f, 0.73f, 0.79f);
            var sunGo = new GameObject("Sun");
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.956f, 0.89f);
            sun.intensity = 1.6f;
            sun.shadows = LightShadows.Hard;
            sunGo.transform.rotation = Quaternion.Euler(45f, -35f, 0f);
            sunGo.AddComponent<UniversalAdditionalLightData>();
            RenderSettings.sun = sun;
        }

        // ------------------------------------------------------------------ materials / textures

        static Material Lit(string name, Color color, float smoothness, Texture2D tex = null, string dir = EnvDir)
        {
            string path = $"{dir}/{name}.mat";
            var shader = Shader.Find("Universal Render Pipeline/Lit");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = shader;
            mat.SetColor("_BaseColor", color);
            mat.SetFloat("_Smoothness", smoothness);
            mat.SetFloat("_Metallic", 0f);
            mat.SetTexture("_BaseMap", tex);
            mat.enableInstancing = true;
            EditorUtility.SetDirty(mat);
            return mat;
        }

        /// <summary>
        /// Sign text: URP Unlit with the legacy font atlas, alpha-clipped, back faces culled and depth-tested
        /// (the font's own GUI/Text shader ignores depth, so text showed through the boards and the cab).
        /// </summary>
        static Material TextMaterial(Font font)
        {
            string path = $"{EnvDir}/M_Sign_Text.mat";
            var shader = Shader.Find("Universal Render Pipeline/Unlit");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = shader;
            mat.SetTexture("_BaseMap", font.material.mainTexture);
            mat.SetColor("_BaseColor", new Color(0.06f, 0.06f, 0.07f, 1f));
            mat.SetFloat("_AlphaClip", 1f);
            mat.SetFloat("_Cutoff", 0.5f);
            mat.EnableKeyword("_ALPHATEST_ON");
            mat.SetFloat("_Cull", 2f);
            mat.renderQueue = (int)RenderQueue.AlphaTest;
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static Material Skybox()
        {
            string path = $"{EnvDir}/M_Sky_Procedural.mat";
            var shader = Shader.Find("Skybox/Procedural");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.SetFloat("_SunSize", 0.035f);
            mat.SetFloat("_AtmosphereThickness", 0.9f);
            mat.SetColor("_SkyTint", new Color(0.5f, 0.5f, 0.5f));
            mat.SetColor("_GroundColor", new Color(0.37f, 0.35f, 0.32f));
            mat.SetFloat("_Exposure", 1.2f);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        delegate Color32 PixelFn(int x, int y, int size);

        static Texture2D Tex(string name, int size, PixelFn fn)
        {
            string path = $"{TexDir}/{name}.png";
            var tex = new Texture2D(size, size, TextureFormat.RGB24, false);
            var px = new Color32[size * size];
            for (int y = 0; y < size; y++) for (int x = 0; x < size; x++) px[y * size + x] = fn(x, y, size);
            tex.SetPixels32(px);
            File.WriteAllBytes(Path.Combine(EditorTools.ProjectRoot, path), tex.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(tex);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            var imp = (TextureImporter)AssetImporter.GetAtPath(path);
            imp.sRGBTexture = true; imp.mipmapEnabled = true; imp.wrapMode = TextureWrapMode.Repeat;
            imp.filterMode = FilterMode.Trilinear; imp.anisoLevel = 4; imp.maxTextureSize = 512;
            imp.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        // Deterministic hash noise (tileable at the given period).
        static float Hash(int x, int y, int seed)
        {
            unchecked
            {
                uint h = (uint)(x * 374761393 + y * 668265263 + seed * 1442695041);
                h = (h ^ (h >> 13)) * 1274126177u;
                return ((h ^ (h >> 16)) & 0xFFFFFF) / 16777215f;
            }
        }

        static float Value(float x, float y, int period, int seed)
        {
            int x0 = Mathf.FloorToInt(x), y0 = Mathf.FloorToInt(y);
            float fx = x - x0, fy = y - y0;
            fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy);
            int Wx(int v) => ((v % period) + period) % period;
            float a = Hash(Wx(x0), Wx(y0), seed), b = Hash(Wx(x0 + 1), Wx(y0), seed), c = Hash(Wx(x0), Wx(y0 + 1), seed), d = Hash(Wx(x0 + 1), Wx(y0 + 1), seed);
            return Mathf.Lerp(Mathf.Lerp(a, b, fx), Mathf.Lerp(c, d, fx), fy);
        }

        static Color32 Grey(float v, float r = 1f, float g = 1f, float b = 1f)
        {
            byte C(float f) => (byte)Mathf.Clamp(Mathf.RoundToInt(f * 255f), 0, 255);
            return new Color32(C(v * r), C(v * g), C(v * b), 255);
        }

        static Color32 AsphaltPixel(int x, int y, int n)
        {
            float u = (float)x / n, v = (float)y / n;
            float low = Value(u * 4, v * 4, 4, 1) * 0.6f + Value(u * 16, v * 16, 16, 2) * 0.4f;
            float grain = Hash(x, y, 3);
            float s = 0.27f + (low - 0.5f) * 0.05f + (grain - 0.5f) * 0.09f;
            if (grain > 0.985f) s += 0.12f; // light aggregate
            return Grey(s, 1f, 1f, 0.98f);
        }

        static Color32 ConcretePixel(int x, int y, int n)
        {
            float u = (float)x / n, v = (float)y / n;
            float s = 0.55f + (Value(u * 8, v * 8, 8, 4) - 0.5f) * 0.07f + (Hash(x, y, 5) - 0.5f) * 0.05f;
            if (x < 3 || y < 3) s = 0.33f; // slab joints every tile (4 m)
            return Grey(s, 1f, 0.99f, 0.95f);
        }

        static Color32 CobblePixel(int x, int y, int n)
        {
            const int cells = 10; // 2 m tile → 0.2 m stones
            float cs = (float)n / cells;
            int row = Mathf.FloorToInt(y / cs);
            float off = (row % 2) * cs * 0.5f;
            float fx = (x + off) % cs, fy = y % cs;
            int col = Mathf.FloorToInt(((x + off) % n) / cs);
            float dx = Mathf.Min(fx, cs - fx), dy = Mathf.Min(fy, cs - fy);
            float edge = Mathf.Min(dx, dy) / (cs * 0.5f);
            float tint = 0.36f + (Hash(col, row, 6) - 0.5f) * 0.12f + (Hash(x, y, 7) - 0.5f) * 0.04f;
            float s = edge < 0.12f ? 0.16f : tint * Mathf.Lerp(0.85f, 1f, Mathf.Clamp01((edge - 0.12f) * 4f));
            return Grey(s, 1f, 0.97f, 0.93f);
        }

        static Color32 GravelPixel(int x, int y, int n)
        {
            float u = (float)x / n, v = (float)y / n;
            float stones = Value(u * 96, v * 96, 96, 8);
            float s = 0.42f + (stones - 0.5f) * 0.22f + (Hash(x, y, 9) - 0.5f) * 0.10f;
            return Grey(s, 1f, 0.95f, 0.84f);
        }

        static Color32 GrassPixel(int x, int y, int n)
        {
            float u = (float)x / n, v = (float)y / n;
            float low = Value(u * 6, v * 6, 6, 10);
            float blade = Hash(x, y, 11);
            float s = 0.30f + (low - 0.5f) * 0.10f + (blade - 0.5f) * 0.10f;
            return Grey(s, 0.62f, 1.0f, 0.38f);
        }
    }
}
