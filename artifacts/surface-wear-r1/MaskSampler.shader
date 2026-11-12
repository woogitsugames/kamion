Shader "Hidden/SurfaceWearQA/MaskSampler"
{
    Properties { _MainTex("Mask",2D)="black"{} _QARepeat("Repeat",Float)=1 _QALod("LOD",Float)=0 }
    SubShader { Pass { ZTest Always Cull Off ZWrite Off
        CGPROGRAM
        #pragma vertex vert_img
        #pragma fragment frag
        #pragma target 3.5
        #include "UnityCG.cginc"
        sampler2D _MainTex; float _QARepeat,_QALod;
        float4 frag(v2f_img i):SV_Target { return tex2Dlod(_MainTex,float4(i.uv*_QARepeat,0,_QALod)); }
        ENDCG
    } }
}
