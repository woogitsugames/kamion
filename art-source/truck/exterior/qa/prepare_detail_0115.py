"""Temporary close-up cameras for exterior QA; no prefab or scene asset is saved."""
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
runpy.run_path(str(HERE / 'prepare_round_0115.py'))
source = ROOT / 'game/Assets/_Generated/TruckQa0115/Editor/TruckRound0115.cs'
text = source.read_text(encoding='utf8')

def replace_once(old, new):
    global text
    if text.count(old) != 1:
        raise RuntimeError(f'Detail adapter source changed: {old[:90]}')
    text = text.replace(old, new, 1)

replace_once('public static class TruckRound0115', 'public static class TruckDetail0115')
replace_once('static bool noPane, noCoat;', '''static readonly List<GameObject> detailRoots = new List<GameObject>();
        static bool noPane, noCoat;''')
replace_once('static void OnScene(Scene scene, OpenSceneMode mode)\n        {', '''static void CreateDetailCameras(Scene scene)
        {
            if (!scene.IsValid() || !scene.path.StartsWith("Assets/_Generated/World/", StringComparison.Ordinal)) return;
            Game.Vehicle.Runtime.TruckVisualRig rig = null;
            foreach (var root in scene.GetRootGameObjects())
            {
                rig = root.GetComponentInChildren<Game.Vehicle.Runtime.TruckVisualRig>(true);
                if (rig != null) break;
            }
            if (rig == null) throw new InvalidOperationException("No live tractor rig for exterior detail cameras");
            var old = rig.transform.Find("ControlCameras_0115Detail");
            if (old != null) UnityEngine.Object.DestroyImmediate(old.gameObject);
            var parent = new GameObject("ControlCameras_0115Detail").transform;
            parent.SetParent(rig.transform, false);
            detailRoots.Add(parent.gameObject);
            void Q(string id, Vector3 position, Vector3 target, float fov)
            {
                var go = new GameObject("QA_" + id);
                go.transform.SetParent(parent, false);
                go.transform.localPosition = position;
                go.transform.localRotation = Quaternion.LookRotation(target - position, Vector3.up);
                var camera = go.AddComponent<Camera>();
                camera.fieldOfView = fov; camera.nearClipPlane = 0.03f; camera.farClipPlane = 1400f; camera.enabled = false;
                go.AddComponent<UnityEngine.Rendering.Universal.UniversalAdditionalCameraData>();
                var control = go.AddComponent<Game.Rendering.ControlCamera>();
                control.id = id; control.note = "ADR 0115: temporary exterior close-up; not a phone measurement.";
            }
            Q("truck-step-detail", new Vector3(-2.6f, 1.05f, 2.25f), new Vector3(-1.05f, 0.8f, 2.6f), 45f);
            Q("truck-mudguard-detail", new Vector3(-2.4f, 1.8f, -0.5f), new Vector3(-1.02f, 1.05f, -0.05f), 48f);
            Q("truck-wheel-detail", new Vector3(-2.5f, 0.8f, 3.82f), new Vector3(-1.02f, 0.57f, 3.8f), 50f);
        }
        static void OnScene(Scene scene, OpenSceneMode mode)
        {
            CreateDetailCameras(scene);''')
replace_once('public static void RunBatch()\n        {', '''public static void RunBatch()
        {
            detailRoots.Clear();''')
replace_once('EditorSceneManager.sceneOpened-=OnScene; QualityProfileApplier.Applied-=OnTier;', '''EditorSceneManager.sceneOpened-=OnScene; QualityProfileApplier.Applied-=OnTier;
                foreach (var root in detailRoots) if (root != null) UnityEngine.Object.DestroyImmediate(root);
                detailRoots.Clear();''')
target = source.with_name('TruckDetail0115.cs')
if not target.exists() or target.read_text(encoding='utf8') != text:
    target.write_text(text, encoding='utf8')
print(f'Prepared {target.relative_to(ROOT)}; three transient detail cameras, destroyed in finally.')
