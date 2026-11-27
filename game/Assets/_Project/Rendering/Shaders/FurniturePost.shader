Shader "Kamion/Furniture Post"
{
    Properties
    {
        [MainTexture] _BaseMap("Albedo", 2D) = "white" {}
        [MainColor] _BaseColor("Color", Color) = (1,1,1,1)
        _Cutoff("Alpha Cutoff", Range(0.0, 1.0)) = 0.5
        _Smoothness("Smoothness", Range(0.0, 1.0)) = 0.5
        _SmoothnessTextureChannel("Smoothness texture channel", Float) = 0
        _Metallic("Metallic", Range(0.0, 1.0)) = 0.0
        _MetallicGlossMap("Metallic", 2D) = "white" {}
        _SpecColor("Specular", Color) = (0.2, 0.2, 0.2)
        _SpecGlossMap("Specular", 2D) = "white" {}
        [ToggleOff] _SpecularHighlights("Specular Highlights", Float) = 1.0
        [ToggleOff] _EnvironmentReflections("Environment Reflections", Float) = 1.0
        _BumpScale("Scale", Float) = 1.0
        _BumpMap("Normal Map", 2D) = "bump" {}
        _Parallax("Scale", Range(0.005, 0.08)) = 0.02
        _ParallaxMap("Height Map", 2D) = "black" {}
        _OcclusionStrength("Strength", Range(0.0, 1.0)) = 1.0
        _OcclusionMap("Occlusion", 2D) = "white" {}
        [HDR] _EmissionColor("Color", Color) = (0,0,0)
        _EmissionMap("Emission", 2D) = "white" {}
        _DetailMask("Detail Mask", 2D) = "white" {}
        _DetailAlbedoMapScale("Scale", Range(0.0, 2.0)) = 1.0
        _DetailAlbedoMap("Detail Albedo x2", 2D) = "linearGrey" {}
        _DetailNormalMapScale("Scale", Range(0.0, 2.0)) = 1.0
        [Normal] _DetailNormalMap("Normal Map", 2D) = "bump" {}
        [HideInInspector] _WorkflowMode("WorkflowMode", Float) = 1.0
        [HideInInspector] _Surface("__surface", Float) = 0.0
        [HideInInspector] _Blend("__blend", Float) = 0.0
        [HideInInspector] _Cull("__cull", Float) = 2.0
        [HideInInspector] _SrcBlend("__src", Float) = 1.0
        [HideInInspector] _DstBlend("__dst", Float) = 0.0
        [HideInInspector] _ZWrite("__zw", Float) = 1.0
        [HideInInspector] _KamionSignWear("Post Wear", Vector) = (0,0,0,0)
    }

    SubShader
    {
        Tags
        {
            "RenderType" = "Opaque"
            "RenderPipeline" = "UniversalPipeline"
            "IgnoreProjector" = "True"
        }
        LOD 100

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/Shaders/LitInput.hlsl"

        UNITY_INSTANCING_BUFFER_START(KamionSignProps)
            UNITY_DEFINE_INSTANCED_PROP(float4, _KamionSignWear)
        UNITY_INSTANCING_BUFFER_END(KamionSignProps)

        void ApplyFurniturePostProfile(inout float4 positionOS, inout float3 normalOS, out half2 postInfo)
        {
            float4 wear = UNITY_ACCESS_INSTANCED_PROP(KamionSignProps, _KamionSignWear);
            postInfo = half2((half)saturate(positionOS.y), 0.0h);
            if (wear.y <= 0.5) return;

            float r = length(positionOS.xz);
            if (r < 0.002) return;

            float ang = atan2(positionOS.z, positionOS.x);
            float cx = cos(ang);
            float sx = sin(ang);
            bool isCollar = (positionOS.y < 0.024 && r > 0.040);
            float halfW = isCollar ? 0.036 : 0.028;
            float frontZ = isCollar ? 0.022 : 0.016;
            float backZ = -0.016;

            float3 pOut = positionOS.xyz;
            float3 nOut = normalOS;
            if (sx >= 0.45)
            {
                pOut.x = clamp(cx * 1.18, -1.0, 1.0) * halfW;
                pOut.z = frontZ;
                nOut = float3(0.0, 0.0, 1.0);
            }
            else if (sx >= -0.60)
            {
                float sgnX = cx >= 0.0 ? 1.0 : -1.0;
                pOut.x = sgnX * halfW;
                pOut.z = lerp(backZ, frontZ * 0.45, saturate((sx + 0.60) / 1.05));
                nOut = float3(sgnX, 0.0, 0.0);
            }
            else
            {
                pOut.x = cx * (halfW * 1.4);
                pOut.z = frontZ - 0.005;
                nOut = float3(0.0, 0.0, -1.0);
                postInfo.y = 1.0h;
            }
            positionOS.xyz = pOut;
            normalOS = normalize(nOut);
        }
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Cull[_Cull]

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex FurniturePostVertex
            #pragma fragment FurniturePostFragment

            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS
            #pragma multi_compile _ EVALUATE_SH_MIXED EVALUATE_SH_VERTEX
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fog
            #pragma multi_compile_instancing

            #include "Packages/com.unity.render-pipelines.universal/Shaders/LitForwardPass.hlsl"

            struct PostVaryings
            {
                Varyings base;
                half2 postInfo : TEXCOORD10;
            };

            PostVaryings FurniturePostVertex(Attributes input)
            {
                UNITY_SETUP_INSTANCE_ID(input);
                half2 info;
                ApplyFurniturePostProfile(input.positionOS, input.normalOS, info);
                PostVaryings output;
                output.base = LitPassVertex(input);
                output.postInfo = info;
                return output;
            }

            half PostHash(float2 p)
            {
                return (half)frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
            }

            void FurniturePostFragment(
                PostVaryings wrapped,
                out half4 outColor : SV_Target0
            )
            {
                Varyings input = wrapped.base;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);

                SurfaceData surfaceData;
                InitializeStandardLitSurfaceData(input.uv, surfaceData);

                half4 wear = (half4)UNITY_ACCESS_INSTANCED_PROP(KamionSignProps, _KamionSignWear);
                half heightY = wrapped.postInfo.x;
                half recess = wrapped.postInfo.y;
                half seed = wear.w;
                half n = PostHash(floor(float2(input.uv.x * 16.0, heightY * 45.0) + float2(seed * 23.0, 5.1)));

                if (wear.x > 0.5h)
                {
                    // Painted grey-white municipal/county post
                    half3 paintBase = half3(0.45h, 0.465h, 0.445h) * (0.93h + 0.14h * seed);
                    surfaceData.albedo = lerp(paintBase, paintBase * 0.85h, n * 0.32h * wear.z);
                    surfaceData.metallic = 0.04h;
                    surfaceData.smoothness = lerp(0.28h, 0.16h, wear.z);
                    // Subtle collar/base corrosion on older posts
                    half collarRust = smoothstep(0.11h, 0.0h, heightY) * wear.z * smoothstep(0.42h, 0.75h, n);
                    surfaceData.albedo = lerp(surfaceData.albedo, half3(0.11h, 0.045h, 0.02h), collarRust);
                }
                else if (dot(wear, half4(1, 1, 1, 1)) > 0.001h)
                {
                    // Weathered hot-dip galvanized zinc post
                    half zincTone = lerp(0.96h, 0.84h, wear.z) * (0.92h + 0.16h * seed);
                    surfaceData.albedo *= zincTone * (0.94h + 0.12h * n);
                    surfaceData.metallic = lerp(0.62h, 0.38h, wear.z);
                    surfaceData.smoothness = lerp(0.40h, 0.22h, wear.z);
                }

                // Bottom road splash / dirt
                half baseDirt = smoothstep(0.14h, 0.0h, heightY) * (0.25h + 0.55h * wear.z) * (0.65h + 0.35h * n);
                surfaceData.albedo = lerp(surfaceData.albedo, half3(0.16h, 0.145h, 0.12h), saturate(baseDirt));

                // Open U-channel inner recess darkening (synthetic cavity AO)
                if (recess > 0.1h)
                {
                    surfaceData.albedo *= 0.62h;
                    surfaceData.occlusion *= 0.72h;
                }

                InputData inputData;
                InitializeInputData(input, surfaceData.normalTS, inputData);
                InitializeBakedGIData(input, inputData);
                half4 color = UniversalFragmentPBR(inputData, surfaceData);
                color.rgb = MixFog(color.rgb, inputData.fogCoord);
                color.a = OutputAlpha(color.a, IsSurfaceTypeTransparent(_Surface));
                outColor = color;
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode" = "ShadowCaster" }
            ZWrite On ZTest LEqual ColorMask 0 Cull[_Cull]

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex PostShadowVert
            #pragma fragment PostShadowFrag
            #pragma multi_compile_instancing
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"

            float3 _LightDirection;
            float3 _LightPosition;

            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct V { float4 positionCS : SV_POSITION; };

            V PostShadowVert(A v)
            {
                UNITY_SETUP_INSTANCE_ID(v);
                half2 dummy;
                ApplyFurniturePostProfile(v.positionOS, v.normalOS, dummy);
                V o;
                float3 pw = TransformObjectToWorld(v.positionOS.xyz);
                float3 nw = TransformObjectToWorldNormal(v.normalOS);
            #if _CASTING_PUNCTUAL_LIGHT_SHADOW
                float3 ld = normalize(_LightPosition - pw);
            #else
                float3 ld = _LightDirection;
            #endif
                float4 cs = TransformWorldToHClip(ApplyShadowBias(pw, nw, ld));
            #if UNITY_REVERSED_Z
                cs.z = min(cs.z, UNITY_NEAR_CLIP_VALUE);
            #else
                cs.z = max(cs.z, UNITY_NEAR_CLIP_VALUE);
            #endif
                o.positionCS = cs;
                return o;
            }
            half4 PostShadowFrag(V i) : SV_Target { return 0; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ZWrite On ColorMask R Cull[_Cull]

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex PostDepthVert
            #pragma fragment PostDepthFrag
            #pragma multi_compile_instancing

            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct V { float4 positionCS : SV_POSITION; };

            V PostDepthVert(A v)
            {
                UNITY_SETUP_INSTANCE_ID(v);
                half2 dummy;
                ApplyFurniturePostProfile(v.positionOS, v.normalOS, dummy);
                V o;
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                return o;
            }
            half PostDepthFrag(V i) : SV_Target { return i.positionCS.z; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode" = "DepthNormals" }
            ZWrite On Cull[_Cull]

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex PostDepthNormalsVertex
            #pragma fragment DepthNormalsFragment
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/Shaders/LitDepthNormalsPass.hlsl"

            Varyings PostDepthNormalsVertex(Attributes input)
            {
                UNITY_SETUP_INSTANCE_ID(input);
                half2 dummy;
                float3 n = input.normal;
                ApplyFurniturePostProfile(input.positionOS, n, dummy);
                input.normal = n;
                return DepthNormalsVertex(input);
            }
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
