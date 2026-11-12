# ADR 0136 diag1: A/B sweep of s10->s12 candidates on G3-B (uncapped, fixed scale), A16 only.
param([string]$Apk, [string]$Only = '')
$d = $PSScriptRoot
$fix = 'rq_scale=0.75 rq_pacing=0'
$runs = [ordered]@{
  ab_asph   = 'vec:s.worldpbr:_asphaltwear:2:0+vec:s.worldpbr:_asphaltwear:3:0'
  ab_ground = 'vec:s.worldpbr:_groundwearexclude:2:0+vec:s.worldpbr:_kerbwear:3:0+vec:s.worldpbr:_patchseam:0:0'
  ab_truck  = 'truck'
  ab_props  = 'props'
  ab_trees  = 'trees'
  ab_fsign  = 'off:s.furnituresign'
  ab_plot   = 'off:s.plotkit'
  ab_far    = 'off:m.far_field+off:m.__far'
  ab_decal  = 'off:m.decal_+off:m.fab_round+off:m.fab_square+off:m.fab_drainage'
  ab_fab    = 'off:m.fab_'
  ab_bld    = 'off:m.plaster+off:m.brick+off:m.facade+off:m.hall_+off:m.panel_concrete'
  ab_hedge  = 'off:m.hedge'
  ab_noise  = 'off:m.noise_+off:m.gantry'
  ab_carfilm = 'vec:s.worldpbr:_carflake:3:0'
}
$sel = if ($Only) { $Only -split ',' } else { $runs.Keys }
$spec = ($sel | ForEach-Object { "$_=rq_ab=$($runs[$_]) $fix" }) -join ';'
$a = @('-NoProfile', '-File', "$d/phone-diag.ps1", '-OutTag', 'diag1', '-Segment', 'B', '-Uncapped', '-Runs', $spec)
if ($Apk) { $a += @('-Apk', $Apk) }
pwsh @a
"DIAG1 DONE" | Out-File "$d/diag1.done"
