using Game.Vehicle.Physics;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// double (physics core) &lt;-&gt; float (Unity) conversions. The core uses Unity's component layout
    /// (X right, Y up, Z forward), so the mapping is 1:1. Conversion happens only in the adapter.
    /// </summary>
    public static class UnityConvert
    {
        public static Vector3 ToUnity(this Vec3 v) => new Vector3((float)v.x, (float)v.y, (float)v.z);
        public static Vec3 ToCore(this Vector3 v) => new Vec3(v.x, v.y, v.z);
        public static Quaternion ToUnity(this Quat q) => new Quaternion((float)q.x, (float)q.y, (float)q.z, (float)q.w);
        public static Quat ToCore(this Quaternion q) => new Quat(q.x, q.y, q.z, q.w);
    }
}
