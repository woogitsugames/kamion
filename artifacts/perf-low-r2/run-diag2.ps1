# ADR 0113 diag2: cell sort A/B (release, uncapped G3-B and G3-A), then dev APK: PSO trace G3-A/G3-B, spike probe G3-A.
param([string]$Apk, [string]$DevApk)
$d = $PSScriptRoot
$dev = 'RFGL34SJYDZ'
pwsh -NoProfile -File "$d/phone-diag.ps1" -Apk $Apk -OutTag diag2 -Segment B -Uncapped -Runs "ab_sortB=rq_ab=cellsort"
pwsh -NoProfile -File "$d/phone-diag.ps1" -OutTag diag2 -Segment A -Uncapped -Runs "ab_sortA=rq_ab=cellsort"
pwsh -NoProfile -File "$d/phone-diag.ps1" -Apk $DevApk -OutTag diag2 -Segment A -Runs "devtraceA=pso_trace=90 pso_tag=g3a spike_probe=1"
pwsh -NoProfile -File "$d/phone-diag.ps1" -OutTag diag2 -Segment B -Runs "devtraceB=pso_trace=95 pso_tag=g3b"
. (Join-Path (Split-Path (Split-Path $d)) 'scripts/env.ps1')
New-Item -ItemType Directory -Force "$d/pso2" | Out-Null
& $Adb -s $dev shell ls -l /sdcard/Android/data/com.woogitsugames.kamion/files/ | Out-File "$d/pso2/ls.txt"
foreach ($f in 'pso_Vulkan_Low_g3a.graphicsstate', 'pso_Vulkan_Low_g3b.graphicsstate') { & $Adb -s $dev pull "/sdcard/Android/data/com.woogitsugames.kamion/files/$f" "$d/pso2/" }
"DIAG2 DONE" | Out-File "$d/diag2.done"
