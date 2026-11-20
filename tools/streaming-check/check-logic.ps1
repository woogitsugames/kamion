param([switch]$Before, [string]$BeforeRef = 'f08172268')
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$files = @(
 'game/Assets/_Project/World/Runtime/Streaming/TileGraph.cs',
 'game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs',
 'game/Assets/_Project/Gameplay/DesktopAutoShot.cs',
 'game/Assets/_Project/Tests/EditMode/StreamingWorkSchedulingTests.cs'
)
# In-memory C# logic check only: no Unity Editor/player/build process. Unity calls are deliberately unavailable.
# The tiny NUnit surface below executes the SAME new EditMode test bodies, but is not a Unity/NUnit runner.
$shim = @"
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using Game.Gameplay;
using Game.World.Streaming;
using NUnit.Framework;
using UnityEngine;
namespace UnityEngine {
 public class MonoBehaviour { protected static void DontDestroyOnLoad(object o) {} }
 public class GameObject { public GameObject(string s) {} public T AddComponent<T>() where T:new() => new T(); }
 public static class Application { public static bool runInBackground; public static void Quit(int c) {} }
 public static class Time { public static float realtimeSinceStartup => throw new NotSupportedException(); }
 public static class Screen { public static int width => 0; public static int height => 0; }
 public static class ScreenCapture { public static void CaptureScreenshot(string s) => throw new NotSupportedException(); }
 public static class Debug { public static void Log(object o) {} public static void LogWarning(object o) {} }
 public static class Mathf { public static int RoundToInt(float f) => (int)Math.Round(f); }
 public class TextAsset { public string text => throw new NotSupportedException(); }
 public static class Resources { public static T Load<T>(string s) => throw new NotSupportedException(); }
 public static class JsonUtility { public static T FromJson<T>(string s) => throw new NotSupportedException(); }
}
namespace UnityEngine.SceneManagement {
 public struct Scene { public string name => "test"; }
 public static class SceneManager { public static Scene GetActiveScene() => new Scene(); }
}
namespace Game.World { public static class RegionScenes { public const string HighTier = "High"; } }
namespace NUnit.Framework {
 [AttributeUsage(AttributeTargets.Method)] public class TestAttribute : Attribute {}
 public static class Assert {
  public static void AreEqual(object a, object b, string message = "") { if (!object.Equals(a,b)) throw new Exception(message + " expected=" + a + " actual=" + b); }
  public static void AreNotEqual(object a, object b, string message = "") { if (object.Equals(a,b)) throw new Exception(message + " unexpectedly equal=" + a); }
  public static void IsTrue(bool b, string message = "") { AreEqual(true,b,message); }
  public static void IsFalse(bool b, string message = "") { AreEqual(false,b,message); }
 }
}
"@
$code = $shim
foreach ($file in $files) {
 if ($Before -and $file -like '*StreamingPolicy.cs') {
  $src = (git -C $repo show "${BeforeRef}:$file") -join "`n"
 } else { $src = Get-Content (Join-Path $repo $file) -Raw }
 if ($Before -and $file -like '*DesktopAutoShot.cs') { $src = $src.Replace('nextAt = now + every;', 'nextAt += every;') }
 $code += "`n" + [regex]::Replace($src, '(?m)^using [^\r\n]+;\r?\n', '')
}
Add-Type -TypeDefinition $code
$instance = [Game.Tests.StreamingWorkSchedulingTests]::new()
$failed = 0
foreach ($method in $instance.GetType().GetMethods()) {
 if ($method.GetCustomAttributes([NUnit.Framework.TestAttribute], $true).Length -eq 0) { continue }
 try { $method.Invoke($instance, @()) | Out-Null; Write-Output "PASS $($method.Name)" }
 catch { $failed++; Write-Output "FAIL $($method.Name): $($_.Exception.InnerException.Message)" }
}
if ($failed) { exit 1 }
