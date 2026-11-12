# ADR 0136 final: impostor trim before/after on the A16 (Low, 30 FPS cap like gate3), interleaved, plus uncapped A/B on G3-B.
# Usage: pwsh artifacts/a16-perf/run-final.ps1 -Before <s12 apk> -After <trim apk> [-Tag final1]
param([Parameter(Mandatory)][string]$Before, [Parameter(Mandatory)][string]$After, [string]$Tag = 'final1')
$d = $PSScriptRoot
$pd = "$d/phone-diag.ps1"
pwsh -NoProfile -File $pd -Apk $After -OutTag $Tag -Segment B -Uncapped -Runs "abB_impostor_trim=rq_ab=impostor rq_scale=0.75 rq_pacing=0;abB_trees_trim=rq_ab=trees rq_scale=0.75 rq_pacing=0"
pwsh -NoProfile -File $pd -Apk $Before -OutTag $Tag -Segment A -Runs "A_before="
pwsh -NoProfile -File $pd -Apk $After -OutTag $Tag -Segment A -Runs "A_after="
pwsh -NoProfile -File $pd -OutTag $Tag -Segment B -Runs "B_after="
pwsh -NoProfile -File $pd -Apk $Before -OutTag $Tag -Segment B -Runs "B_before="
"FINAL DONE $Tag" | Out-File "$d/$Tag.done"
