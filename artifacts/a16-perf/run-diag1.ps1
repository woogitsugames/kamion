# ADR 0136 diag1: A/B sweep of s10->s12 candidates on G3-B (uncapped, fixed scale), A16 only.
param([string]$Apk, [string]$Only = '', [string]$Segment = 'B', [string]$OutTag = 'diag1')
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
  ab_mirrors = 'mirrors'
  ab_envcap = 'envcap'
  ab_shadows = 'shadows'
  ab_hlodedge = 'hlodedge'
  ab_hlodcanopy = 'hlodcanopy'
  ab_impostor = 'impostor'
  # ADR 0136 r2: props per prototype prefix (pp: not drawn, ps: no shadow, vc: vehicle cull m)
  ab_veh    = 'pp:car_/van_/tractor_/trailer_/bus_/contact_'
  ab_vcar   = 'pp:car_/van_/contact_'
  ab_vtruck = 'pp:tractor_/trailer_/bus_'
  ab_lamp   = 'pp:lamp_'
  ab_signs  = 'pp:sign_/plate_/board_/signal_/gantry_'
  ab_fabp   = 'pp:fab_/propcontact_'
  ab_lmk    = 'pp:landmark_/facade_/gatehouse_'
  ab_misc   = 'pp:pallet/bin_/waste_/cone_/container_/skip_/barrier_/lift_/sliding_/power_/pylon_/bollard_/bench_'
  ab_pshadow = 'ps:all'
  ab_vshadow = 'ps:car_/van_/tractor_/trailer_/bus_'
  ab_vc150  = 'vc:150'
  ab_vc100  = 'vc:100'
  ab_contact = 'pp:contact_'
  ab_vl05   = 'vl:0.5'
  ab_vm     = 'vm'
  ab_mirrorlow = 'mirrorlow'
  ab_cc     = 'cc'
  ab_grime  = 'grime'
}
$sel = if ($Only) { $Only -split ',' } else { $runs.Keys }
$spec = ($sel | ForEach-Object { "$_=rq_ab=$($runs[$_]) $fix" }) -join ';'
$a = @('-NoProfile', '-File', "$d/phone-diag.ps1", '-OutTag', $OutTag, '-Segment', $Segment, '-Uncapped', '-Runs', $spec)
if ($Apk) { $a += @('-Apk', $Apk) }
pwsh @a
"DONE $OutTag" | Out-File "$d/$OutTag.done"
