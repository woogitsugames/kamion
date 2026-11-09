#if UNITY_ANDROID && !UNITY_EDITOR
using System;
using UnityEngine;

namespace Game.Platform
{
    /// <summary>Android implementation via JNI. Only compiled into Android players.</summary>
    sealed class AndroidPlatformServices : IPlatformServices
    {
        readonly AndroidJavaObject m_Activity;
        readonly AndroidJavaObject m_Context;
        readonly AndroidJavaObject m_PowerManager;
        readonly AndroidJavaObject m_BatteryFilter;
        readonly IntPtr m_RegisterReceiver;
        readonly int m_SdkInt;

        public AndroidPlatformServices()
        {
            using (var player = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
                m_Activity = player.GetStatic<AndroidJavaObject>("currentActivity");
            m_Context = m_Activity.Call<AndroidJavaObject>("getApplicationContext");
            using (var version = new AndroidJavaClass("android.os.Build$VERSION"))
                m_SdkInt = version.GetStatic<int>("SDK_INT");
            m_PowerManager = m_Context.Call<AndroidJavaObject>("getSystemService", "power");
            m_BatteryFilter = new AndroidJavaObject("android.content.IntentFilter", "android.intent.action.BATTERY_CHANGED");

            // registerReceiver(null, filter) returns the sticky battery intent; a null receiver
            // cannot be expressed through AndroidJavaObject.Call signature inference, so use raw JNI.
            IntPtr contextClass = AndroidJNI.GetObjectClass(m_Context.GetRawObject());
            m_RegisterReceiver = AndroidJNI.GetMethodID(contextClass, "registerReceiver",
                "(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;)Landroid/content/Intent;");
            AndroidJNI.DeleteLocalRef(contextClass);
        }

        public string Name => "android-" + m_SdkInt;

        public float? GetBatteryTemperatureC()
        {
            try
            {
                var args = new jvalue[2];
                args[0].l = IntPtr.Zero;
                args[1].l = m_BatteryFilter.GetRawObject();
                IntPtr intentPtr = AndroidJNI.CallObjectMethod(m_Context.GetRawObject(), m_RegisterReceiver, args);
                if (intentPtr == IntPtr.Zero) return null;
                IntPtr intentClass = AndroidJNI.GetObjectClass(intentPtr);
                IntPtr getIntExtra = AndroidJNI.GetMethodID(intentClass, "getIntExtra", "(Ljava/lang/String;I)I");
                IntPtr key = AndroidJNI.NewStringUTF("temperature");
                var extraArgs = new jvalue[2];
                extraArgs[0].l = key;
                extraArgs[1].i = int.MinValue;
                int tenths = AndroidJNI.CallIntMethod(intentPtr, getIntExtra, extraArgs);
                AndroidJNI.DeleteLocalRef(key);
                AndroidJNI.DeleteLocalRef(intentClass);
                AndroidJNI.DeleteLocalRef(intentPtr);
                return tenths == int.MinValue ? (float?)null : tenths / 10f;
            }
            catch (Exception)
            {
                return null;
            }
        }

        public int? GetThermalStatus()
        {
            if (m_SdkInt < 29 || m_PowerManager == null) return null;
            try { return m_PowerManager.Call<int>("getCurrentThermalStatus"); }
            catch (Exception) { return null; }
        }

        public float? GetThermalHeadroom()
        {
            if (m_SdkInt < 30 || m_PowerManager == null) return null;
            try
            {
                float h = m_PowerManager.Call<float>("getThermalHeadroom", 10);
                return float.IsNaN(h) ? (float?)null : h;
            }
            catch (Exception) { return null; }
        }

        public long? GetProcessPssKb()
        {
            try
            {
                using (var debug = new AndroidJavaClass("android.os.Debug"))
                    return debug.CallStatic<long>("getPss");
            }
            catch (Exception) { return null; }
        }

        public string GetLaunchArgument(string key)
        {
            try
            {
                using (var intent = m_Activity.Call<AndroidJavaObject>("getIntent"))
                    return intent?.Call<string>("getStringExtra", key);
            }
            catch (Exception) { return null; }
        }
    }
}
#endif
