using Game.Vehicle.Runtime;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Gameplay.Furniture
{
    /// <summary>Read-only bridge from the existing player's lamp state and authored sockets.
    /// No lights, camera replacement, vehicle changes or per-frame arrays. Missing sockets disable return.</summary>
    public static class FurnitureRetroSource
    {
        static readonly int Head0 = Shader.PropertyToID("_FurnitureRetroHead0");
        static readonly int Head1 = Shader.PropertyToID("_FurnitureRetroHead1");
        static readonly int Head2 = Shader.PropertyToID("_FurnitureRetroHead2");
        static readonly int Head3 = Shader.PropertyToID("_FurnitureRetroHead3");
        static readonly int Forward = Shader.PropertyToID("_FurnitureRetroForward");
        static readonly int Up = Shader.PropertyToID("_FurnitureRetroUp");
        static readonly int State = Shader.PropertyToID("_FurnitureRetroState");
        static TruckLights s_Lights;
        static Transform s_Left, s_Right, s_HighLeft, s_HighRight;
        static float s_NextFind;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void Initialize()
        {
            Uninstall();
            s_Lights = null;
            s_Left = s_Right = null;
            s_HighLeft = s_HighRight = null;
            s_NextFind = 0;
            Install();
        }

#if UNITY_EDITOR
        [UnityEditor.InitializeOnLoadMethod]
        static void EditorInitialize()
        {
            Install();
            UnityEditor.AssemblyReloadEvents.beforeAssemblyReload -= Uninstall;
            UnityEditor.AssemblyReloadEvents.beforeAssemblyReload += Uninstall;
        }
#endif

        static void Install()
        {
            RenderPipelineManager.beginCameraRendering -= BeginCamera;
            RenderPipelineManager.beginCameraRendering += BeginCamera;
            Shader.SetGlobalVector(State, Vector4.zero);
        }

        static void Uninstall()
        {
            RenderPipelineManager.beginCameraRendering -= BeginCamera;
            Shader.SetGlobalVector(State, Vector4.zero);
        }

        static void BeginCamera(ScriptableRenderContext context, Camera camera)
        {
            if ((s_Lights == null || !s_Lights.isActiveAndEnabled || s_Left == null || s_Right == null
                || s_HighLeft == null || s_HighRight == null)
                && Time.realtimeSinceStartup >= s_NextFind)
            {
                s_NextFind = Time.realtimeSinceStartup + 1f;
                s_Lights = Object.FindAnyObjectByType<TruckLights>();
                s_Left = s_Right = null;
                s_HighLeft = s_HighRight = null;
                if (s_Lights != null)
                {
                    var root = s_Lights.body != null ? s_Lights.body.transform : s_Lights.transform;
                    // One discovery allocation, at most once a second while the rig is unavailable.
                    foreach (var socket in root.GetComponentsInChildren<Transform>(true))
                    {
                        if (socket.name == "LIGHT_LowBeam_L") s_Left = socket;
                        else if (socket.name == "LIGHT_LowBeam_R") s_Right = socket;
                        else if (socket.name == "LIGHT_HighBeam_L") s_HighLeft = socket;
                        else if (socket.name == "LIGHT_HighBeam_R") s_HighRight = socket;
                    }
                }
            }
            Publish(s_Lights, s_Left, s_Right, s_HighLeft, s_HighRight);
        }

        /// <summary>Explicit source input also lets EditMode verify stale/off state without a fabricated live source.</summary>
        public static void Publish(TruckLights lights, Transform left, Transform right,
            Transform highLeft = null, Transform highRight = null)
        {
            bool low = lights != null && lights.isActiveAndEnabled && lights.LowBeamOn && left != null && right != null;
            bool high = lights != null && lights.isActiveAndEnabled && lights.highBeam && highLeft != null && highRight != null;
            if (!low && !high)
            {
                Shader.SetGlobalVector(State, Vector4.zero);
                return;
            }
            var root = lights.body != null ? lights.body.transform : lights.transform;
            SetHead(Head0, left, low ? 1f : 0f);
            SetHead(Head1, right, low ? 1f : 0f);
            SetHead(Head2, highLeft, high ? 1.6f : 0f); // intensity ratio WORKING_VALUE
            SetHead(Head3, highRight, high ? 1.6f : 0f);
            var f = root.forward;
            var u = root.up;
            Shader.SetGlobalVector(Forward, new Vector4(f.x, f.y, f.z, 0));
            Shader.SetGlobalVector(Up, new Vector4(u.x, u.y, u.z, 0));
            Shader.SetGlobalVector(State, new Vector4(1, high ? 1 : 0, 0, 0));
        }

        static void SetHead(int property, Transform socket, float strength)
        {
            var p = socket != null ? socket.position : Vector3.zero;
            Shader.SetGlobalVector(property, new Vector4(p.x, p.y, p.z, strength));
        }
    }
}
