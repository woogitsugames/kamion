# env.ps1 - single source of truth for tool paths. Dot-source from other scripts.
$RepoRoot     = (Resolve-Path "$PSScriptRoot/..").Path
$UnityVersion = (Get-Content "$RepoRoot/game/ProjectSettings/ProjectVersion.txt" -ErrorAction SilentlyContinue | Select-String 'm_EditorVersion:' | ForEach-Object { ($_ -split ':\s*')[1].Trim() })
if (-not $UnityVersion) { $UnityVersion = '6000.3.28f1' }
$UnityRoot    = if ($env:UNITY_EDITOR_ROOT) { $env:UNITY_EDITOR_ROOT } else { "C:\Program Files\Unity\Hub\Editor\$UnityVersion" }
$UnityExe     = Join-Path $UnityRoot 'Editor\Unity.exe'
# One documented Android SDK path: the one shipped with the Unity editor module.
$AndroidSdk   = Join-Path $UnityRoot 'Editor\Data\PlaybackEngines\AndroidPlayer\SDK'
$Adb          = Join-Path $AndroidSdk 'platform-tools\adb.exe'
$ProjectPath  = Join-Path $RepoRoot 'game'
$ArtifactsDir = Join-Path $RepoRoot 'artifacts'
