// Kamion/World Water - river / pond surface of the generator layer "water" (ADR 0210).
// Opaque sheet at the measured water level (no depth / opaque texture, no SSR, no planar reflection: mobile).
// Vertex data from the generator: UV0 = local metres (E, N); COLOR_0 = (shore distance / 8 m, depth / 1.5 m,
// flow E, flow N as 0.5 + 0.5 x unit vector; 0.5 / 0.5 = still water).
//   body      : lerp(_ShallowColor, _BaseColor, shore) lit by the sky (SH) and a little sun (turbid water scatters)
//   reflection: Fresnel (water F0 0.02) x environment
//       Low  (no _KAMION_WORLD_DETAIL): flat normal, blurred probe (one fetch) x _ReflectLow (dimmed gloss), dim sheen
//       High (_KAMION_WORLD_DETAIL)   : two procedural ripple octaves advected along the flow, reflection probe,
//                                       sun glint (Blinn-Phong) shadowed by the main-light shadow map
//   sky visibility: the baked world GI (ADR 0064) dims the sky reflection under the bridge deck / along tree lines.
// All constants WORKING_VALUE (ADR 0210), tuned on the dk65-02 control frames against the 2024 orthophoto.
Shader "Kamion/World Water"
{
    Properties
    {
        _BaseColor ("Deep body albedo (linear)", Color) = (0.016, 0.020, 0.014, 1)
        _ShallowColor ("Shore body albedo (linear)", Color) = (0.040, 0.042, 0.026, 1)
        _Reflect ("Reflection strength High", Range(0, 1)) = 0.85
        _ReflectLow ("Reflection strength Low", Range(0, 1)) = 0.55
        _FlowSpeed ("Surface drift along the flow (m/s)", Float) = 0.25
        _FlowCycle ("Flow-map cycle (s)", Float) = 6.0
        _RippleScale ("Ripple wavelength (m)", Float) = 2.4
        _RippleStrength ("Ripple slope", Range(0, 0.5)) = 0.05
        _Smoothness ("Smoothness of the sun glint", Range(0.5, 1)) = 0.93
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry+10" }
        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            ZWrite On
            Cull Back

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _KAMION_WORLD_DETAIL
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Assets/_Project/Rendering/Shaders/KamionWorldGI.hlsl"
            #include "Assets/_Project/Rendering/Shaders/KamionAtmosphere.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float4 _BaseColor, _ShallowColor;
                float _Reflect, _ReflectLow, _FlowSpeed, _FlowCycle, _RippleScale, _RippleStrength, _Smoothness;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                half4 color : COLOR;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float2 uv : TEXCOORD1;
                half4 data : TEXCOORD2;      // shore, depth, flow (signed)
                half fogFactor : TEXCOORD3;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings vert(Attributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                float3 pw = TransformObjectToWorld(v.positionOS.xyz);
                o.positionWS = pw;
                o.positionCS = TransformWorldToHClip(pw);
                o.uv = v.uv;
                o.data = half4(v.color.r, v.color.g, v.color.b * 2.0h - 1.0h, v.color.a * 2.0h - 1.0h);
                o.fogFactor = KamionFogTau(pw, o.positionCS.w);
                return o;
            }

            #if defined(_KAMION_WORLD_DETAIL)
            // gradient of a smooth value noise (quintic), returns d noise / d p
            float2 Hash2(float2 p)
            {
                p = float2(dot(p, float2(127.1, 311.7)), dot(p, float2(269.5, 183.3)));
                return frac(sin(p) * 43758.5453);
            }
            float2 NoiseGrad(float2 p)
            {
                float2 i = floor(p), f = frac(p);
                float2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
                float2 du = 30.0 * f * f * (f * (f - 2.0) + 1.0);
                float a = Hash2(i).x, b = Hash2(i + float2(1, 0)).x, c = Hash2(i + float2(0, 1)).x, d = Hash2(i + float2(1, 1)).x;
                return du * float2(b - a + (a - b - c + d) * u.y, c - a + (a - b - c + d) * u.x);
            }
            #endif

            half4 frag(Varyings i) : SV_Target
            {
                float3 pw = i.positionWS;
                half shore = i.data.x;
                half2 flow = i.data.zw;
                half3 n = half3(0, 1, 0);
                float3 V = normalize(GetCameraPositionWS() - pw);
                half giK, giSun;
                KamionWorldGI(pw, half3(0, 1, 0), giK, giSun);
            #if defined(_MAIN_LIGHT_SHADOWS) || defined(_MAIN_LIGHT_SHADOWS_CASCADE) || defined(_MAIN_LIGHT_SHADOWS_SCREEN)
                float4 shadowCoord = TransformWorldToShadowCoord(pw);
            #else
                float4 shadowCoord = float4(0, 0, 0, 0);
            #endif
                Light L = GetMainLight(shadowCoord, pw, half4(1, 1, 1, 1));
                half sh = KamionFarShadow(L.shadowAttenuation, giSun, pw);

            #if defined(_KAMION_WORLD_DETAIL)
                // ripples: two octaves advected along the flow with the two-phase flow-map scheme (offsets stay
                // bounded, so a flow field that turns at a confluence does not shear the pattern into seams); still
                // water drifts slowly. Faded with distance (no shimmer below a pixel) and towards the shore.
                float t = _Time.y / _FlowCycle;
                float ph0 = frac(t), ph1 = frac(t + 0.5);
                half w0 = 1.0h - abs(1.0h - 2.0h * (half)ph0);
                float2 fl = length(flow) > 0.1 ? (float2)flow : float2(0.35, 0.2);
                float2 off = fl * (_FlowSpeed * _FlowCycle);
                float2 p = i.uv / _RippleScale;
                float2 g0 = NoiseGrad(p - off * ph0 / _RippleScale) + 0.5 * NoiseGrad(p * 2.37 + float2(17.3, 5.1) - off * ph0 * (1.4 / _RippleScale));
                float2 g1 = NoiseGrad(p - off * ph1 / _RippleScale + float2(0.43, 0.71)) + 0.5 * NoiseGrad(p * 2.37 + float2(3.7, 11.9) - off * ph1 * (1.4 / _RippleScale));
                float2 g = g0 * w0 + g1 * (1.0h - w0);
                float dist = length(GetCameraPositionWS() - pw);
                half amp = _RippleStrength * (1.0 - smoothstep(25.0, 140.0, dist)) * lerp(0.45, 1.0, saturate(shore * 2.0));
                n = normalize(half3(-g.x * amp, 1.0, -g.y * amp));    // world XZ = (E, N)
            #endif
                half NdotV = saturate(dot(n, V));
                half fres = 0.02h + 0.98h * pow(1.0h - NdotV, 5.0h);
                float3 R = reflect(-V, n);
                R.y = abs(R.y);                                          // never reflect the ground below the horizon
            #if defined(_KAMION_WORLD_DETAIL)
                half3 env = GlossyEnvironmentReflection(R, 0.06h, 1.0h) * _Reflect;
            #else
                half3 env = GlossyEnvironmentReflection(R, 0.30h, 1.0h) * _ReflectLow;   // one blurred probe fetch
            #endif
                env *= lerp(0.25h, 1.0h, giK);                           // sky hidden by the deck / trees

                // turbid body: sky from above + a little sun scattered in the water column
                half3 body = lerp(_ShallowColor.rgb, _BaseColor.rgb, saturate(shore));
                half3 amb = SampleSH(half3(0, 1, 0)) * giK;
                half3 col = body * (amb + L.color * (0.35h * saturate(L.direction.y) * sh));
                col = lerp(col, env, fres);

                // sun on the water
                half3 H = normalize(L.direction + V);
            #if defined(_KAMION_WORLD_DETAIL)
                half sp = exp2(_Smoothness * 11.0h + 1.0h);
                half spec = pow(saturate(dot(n, H)), sp) * (sp + 8.0h) / 25.0h;
                col += L.color * spec * fres * sh * 4.0h;
            #else
                half spec = pow(saturate(dot(n, H)), 96.0h);
                col += L.color * spec * fres * sh * 1.5h;               // broad dimmed sheen (flat normal)
            #endif
                col = KamionMixFog(col, i.fogFactor);
                return half4(col, 1.0h);
            }
            ENDHLSL
        }
        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ZWrite On
            ColorMask R
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex DepthVert
            #pragma fragment DepthFrag
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            struct A { float4 positionOS : POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Vv { float4 positionCS : SV_POSITION; UNITY_VERTEX_OUTPUT_STEREO };
            Vv DepthVert(A v)
            {
                Vv o = (Vv)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                return o;
            }
            half DepthFrag(Vv i) : SV_Target { return 0; }
            ENDHLSL
        }
    }
    Fallback Off
}
