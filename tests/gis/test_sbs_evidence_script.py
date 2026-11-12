"""PowerShell orchestration checks with isolated fake leases and a recording composer."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
PWSH=shutil.which('pwsh')
pytestmark=pytest.mark.skipif(not PWSH,reason='PowerShell 7 required')


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf-8')


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line] if path.exists() else []


def fixture_repo(tmp_path,states=('overcast',)):
    root=tmp_path/'repo';scripts=root/'scripts';scripts.mkdir(parents=True)
    subprocess.run(['git','init','-q','-b','gpt-sbs-test',str(root)],check=True,capture_output=True)
    for directory in ('game/Assets/_Project/Rendering/Settings','game/ProjectSettings'):
        path=root/directory/'fixture.txt';path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
    subprocess.run(['git','-C',str(root),'add','--','game'],check=True,capture_output=True)
    subprocess.run(['git','-C',str(root),'-c','user.name=SBS Test','-c','user.email=sbs-test@example.invalid',
                    '-c','commit.gpgsign=false','-c',f'core.hooksPath={root/"no-hooks"}',
                    'commit','-q','-m','isolated fixture'],check=True,capture_output=True)
    subprocess.run(['git','-C',str(root),'branch','main'],check=True,capture_output=True)
    shutil.copy2(ROOT/'scripts/sbs-gate3.ps1',scripts/'sbs-gate3.ps1')
    (scripts/'unity-slot.ps1').write_text(r"""
param([switch]$Acquire,[switch]$Release,[string]$Owner,[string]$Pool='unity',[int]$PollSeconds,[double]$StaleHours)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$dir=Join-Path $root ('artifacts/locks/'+$Pool+'-slots')
New-Item -ItemType Directory -Force $dir | Out-Null
$slot=Join-Path $dir ($Owner+'.slot')
$operation=if($Acquire){'Acquire'}else{'Release'}
@{operation=$operation;owner=$Owner;pool=$Pool} | ConvertTo-Json -Compress | Add-Content (Join-Path $root 'slot-calls.jsonl')
if($Acquire){($Owner+' original-lease') | Set-Content $slot}
if($Release){Remove-Item -LiteralPath $slot -ErrorAction Stop}
if($Release -and $Pool -eq 'heavy' -and $env:SBS_TEST_QUEUE_AFTER_RELEASE -eq '1'){
    $queue=Join-Path $dir 'queue';New-Item -ItemType Directory -Force $queue | Out-Null
    'queued-job-original-ticket' | Set-Content (Join-Path $queue ($Owner+'.wait'))
}
if($Release -and $Pool -eq 'unity'){
    $capture=Join-Path $root 'out/renders/Low-overcast/capture-4x3.json'
    switch($env:SBS_TEST_CAPTURE_TAMPER){
        'raw' {[IO.File]::AppendAllText((Join-Path $root 'out/renders/Low-overcast/sbs-test.png'),'changed')}
        'state' {$c=Get-Content $capture -Raw | ConvertFrom-Json;$c.lighting='clear';$c | ConvertTo-Json -Depth 8 | Set-Content $capture}
        'duplicate' {Copy-Item $capture (Join-Path (Split-Path $capture -Parent) 'capture-extra.json')}
        'missing' {Remove-Item -LiteralPath $capture}
        'roster' {$c=Get-Content $capture -Raw | ConvertFrom-Json;$c.cameras=@('sbs-test','sbs-test');$c | ConvertTo-Json -Depth 8 | Set-Content $capture}
        'dimensions' {
            $raw=Join-Path $root 'out/renders/Low-overcast/sbs-test.png'
            Copy-Item (Join-Path $root 'different-size.png') $raw -Force
            $c=Get-Content $capture -Raw | ConvertFrom-Json
            $c.render_sha256.'sbs-test'=(Get-FileHash $raw).Hash.ToLower()
            $c | ConvertTo-Json -Depth 8 | Set-Content $capture
        }
    }
    if($env:SBS_TEST_OTHER_HEAVY_DURING_UNITY){
        $heavy=Join-Path $root 'artifacts/locks/heavy-slots'
        New-Item -ItemType Directory -Force $heavy | Out-Null
        if($env:SBS_TEST_OTHER_HEAVY_DURING_UNITY -eq 'slot'){
            'other-job-original-lease' | Set-Content (Join-Path $heavy 'gpt-sbs-test.slot')
        }else{
            $queue=Join-Path $heavy 'queue';New-Item -ItemType Directory -Force $queue | Out-Null
            'queued-job-original-ticket' | Set-Content (Join-Path $queue 'gpt-sbs-test.wait')
        }
    }
}
exit 0
""",encoding='utf-8')
    Image.new('RGB',(1280,960),'gray').save(root/'template.png')
    Image.new('RGB',(1280,720),'gray').save(root/'different-size.png')
    (scripts/'visual-qa.ps1').write_text(r"""
param([string]$Scene,[string]$Tier,[string]$Lighting,[int]$Width,[int]$Height,[string]$Gate3,[string]$Cameras,[string]$OutputDir)
$root=Split-Path $PSScriptRoot -Parent
New-Item -ItemType Directory -Force $OutputDir | Out-Null
foreach($camera in ($Cameras -split ',')){Copy-Item (Join-Path $root 'template.png') (Join-Path $OutputDir ($camera+'.png')) -Force}
'fixture stats' | Set-Content (Join-Path $OutputDir 'stats.txt')
exit 0
""",encoding='utf-8')
    bin_dir=root/'bin';bin_dir.mkdir()
    (bin_dir/'uv.ps1').write_text(r"""
$args | ConvertTo-Json -Compress | Add-Content (Join-Path $env:SBS_TEST_ROOT 'uv-calls.jsonl')
if($env:SBS_TEST_REPLACE_LEASE -eq '1'){
    'gpt-sbs-test replacement-lease' | Set-Content (Join-Path $env:SBS_TEST_ROOT 'artifacts/locks/heavy-slots/gpt-sbs-test.slot')
}
$global:LASTEXITCODE=0
""",encoding='utf-8')
    snapshot=root/'out/inputs'
    cameras={'cameras':[{'id':'sbs-test','pos':[0,0,2],'look_at':[0,40,2],'fov_deg':60}]}
    refs={'references':[{'camera':'sbs-test','width':40,'height':30}]}
    for name,data in [('sbs_cameras.json',cameras),('sbs_references.json',refs),
                      ('world_manifest.json',{'world':'captured'}),('materials_spec.json',{'materials':'captured'})]:
        write(snapshot/name,data)
    capture={'status':'OK','git_sha':'a'*40,'main_sha':'b'*40,'cameras':['sbs-test'],
             'tier':'Low','width':1280,'height':960,
             'render_sha256':{'sbs-test':hashlib.sha256((root/'template.png').read_bytes()).hexdigest()}}
    for name,key in [('sbs_cameras.json','cameras_sha256'),('sbs_references.json','references_sha256'),
                     ('world_manifest.json','world_manifest_sha256'),('materials_spec.json','materials_spec_sha256')]:
        capture[key]=hashlib.sha256((snapshot/name).read_bytes()).hexdigest()
    for state in states:
        row={**capture,'lighting':state}
        write(root/f'out/renders/Low-{state}/capture-4x3.json',row)
        shutil.copy2(root/'template.png',root/f'out/renders/Low-{state}/sbs-test.png')
        write(root/f'out/sheets/Low-{state}/metrics.json',{'landmarks_sha256':None,'photometry_sha256':None,'render_captures':[row]})
    region=root/'Data/Regions/bialystok-industrial-c'
    write(region/'sbs_references.json',refs)
    write(region/'sbs_cameras.json',cameras)
    write(region/'generated/world_manifest.json',{'world':'dirty newer live state'})
    write(root/'art-source/world/materials/materials_spec.json',{'materials':'dirty live'})
    env={**os.environ,'PATH':str(bin_dir)+os.pathsep+os.environ['PATH'],'SBS_TEST_ROOT':str(root)}
    return root,env


def invoke(root,env,states=('overcast',),borrow=False,render_only=False,output='out',combined=False):
    quote=lambda value:"'"+str(value).replace("'","''")+"'"
    lights=','.join(quote(state) for state in states)
    mode='' if combined else ('-RenderOnly' if render_only else '-ComposeOnly')
    command=f"$ErrorActionPreference='Stop'\n& {quote(root/'scripts/sbs-gate3.ps1')} {mode} -OutputRoot {quote(output)} -Tiers @('Low') -Lighting @({lights})"
    if borrow:command+=' -HeavyLeaseOwner gpt-sbs-test'
    command+="\nif($LASTEXITCODE -ne 0){exit $LASTEXITCODE}\n"
    script=root/'invoke.ps1';script.write_text(command,encoding='utf-8')
    return subprocess.run([PWSH,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(script)],env=env,
                          cwd=root,capture_output=True,text=True,timeout=25)


def held_lease(root):
    path=root/'artifacts/locks/heavy-slots/gpt-sbs-test.slot'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('gpt-sbs-test original-lease',encoding='utf-8')
    return path


def queued_lease(root):
    path=root/'artifacts/locks/heavy-slots/queue/gpt-sbs-test.wait'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('queued-job-original-ticket',encoding='utf-8')
    return path


def test_existing_queued_owner_cannot_start_second_composition(tmp_path):
    root,env=fixture_repo(tmp_path);ticket=queued_lease(root);original=ticket.read_bytes()
    result=invoke(root,env)
    assert result.returncode!=0 and 'already queued' in result.stderr
    assert ticket.read_bytes()==original
    assert not lines(root/'slot-calls.jsonl') and not lines(root/'uv-calls.jsonl')


@pytest.mark.parametrize('kind',['slot','queue'])
def test_combined_render_rechecks_other_heavy_job_before_acquire(tmp_path,kind):
    root,env=fixture_repo(tmp_path);env['SBS_TEST_OTHER_HEAVY_DURING_UNITY']=kind
    result=invoke(root,env,combined=True)
    assert result.returncode!=0 and ('already held' if kind=='slot' else 'already queued') in result.stderr
    path=root/'artifacts/locks/heavy-slots'/('gpt-sbs-test.slot' if kind=='slot' else 'queue/gpt-sbs-test.wait')
    assert ('other-job-original-lease' if kind=='slot' else 'queued-job-original-ticket') in path.read_text(encoding='utf-8-sig')
    assert [(r['operation'],r['pool']) for r in lines(root/'slot-calls.jsonl')]==[('Acquire','unity'),('Release','unity')]
    assert not lines(root/'uv-calls.jsonl')


def test_ticket_appearing_between_states_is_preserved_without_second_acquire(tmp_path):
    root,env=fixture_repo(tmp_path,('overcast','clear'));env['SBS_TEST_QUEUE_AFTER_RELEASE']='1'
    result=invoke(root,env,('overcast','clear'))
    assert result.returncode!=0 and 'already queued' in result.stderr
    ticket=root/'artifacts/locks/heavy-slots/queue/gpt-sbs-test.wait'
    assert 'queued-job-original-ticket' in ticket.read_text(encoding='utf-8-sig')
    assert [r['operation'] for r in lines(root/'slot-calls.jsonl')]==['Acquire','Release']
    assert len(lines(root/'uv-calls.jsonl'))==1


def test_render_only_does_not_touch_existing_heavy_ticket(tmp_path):
    root,env=fixture_repo(tmp_path);ticket=queued_lease(root);original=ticket.read_bytes()
    result=invoke(root,env,render_only=True)
    assert result.returncode==0,result.stdout+result.stderr
    assert ticket.read_bytes()==original
    assert [(r['operation'],r['pool']) for r in lines(root/'slot-calls.jsonl')]==[('Acquire','unity'),('Release','unity')]
    assert not lines(root/'uv-calls.jsonl')


def test_compose_uses_snapshot_and_releases_between_states(tmp_path):
    root,env=fixture_repo(tmp_path,('overcast','clear'))
    captured=(root/'out/inputs/world_manifest.json').read_bytes()
    result=invoke(root,env,('overcast','clear'))
    assert result.returncode==0,result.stdout+result.stderr
    assert [r['operation'] for r in lines(root/'slot-calls.jsonl')]==['Acquire','Release','Acquire','Release']
    assert not (root/'artifacts/locks/heavy-slots/gpt-sbs-test.slot').exists()
    calls=lines(root/'uv-calls.jsonl')
    assert len(calls)==2
    assert all('--inputs' in args and '--historical' not in args for args in calls)
    assert (root/'out/inputs/world_manifest.json').read_bytes()==captured
    with zipfile.ZipFile(root/'out/inputs.zip') as archive:
        assert archive.read('world_manifest.json')==captured
    assert len(list((root/'out/inputs-history').iterdir()))==1


def test_implicit_nested_lease_fails_without_releasing_caller(tmp_path):
    root,env=fixture_repo(tmp_path);lease=held_lease(root);original=lease.read_bytes()
    result=invoke(root,env)
    assert result.returncode!=0 and 'already held' in result.stderr
    assert lease.read_bytes()==original
    assert not lines(root/'slot-calls.jsonl') and not lines(root/'uv-calls.jsonl')


def test_explicit_borrow_preserves_caller_lease(tmp_path):
    root,env=fixture_repo(tmp_path);lease=held_lease(root);original=lease.read_bytes()
    result=invoke(root,env,borrow=True)
    assert result.returncode==0,result.stdout+result.stderr
    assert lease.read_bytes()==original and not lines(root/'slot-calls.jsonl')
    assert len(lines(root/'uv-calls.jsonl'))==1


def test_borrow_rejects_same_owner_reacquisition_without_releasing_it(tmp_path):
    root,env=fixture_repo(tmp_path);lease=held_lease(root)
    env['SBS_TEST_REPLACE_LEASE']='1'
    result=invoke(root,env,borrow=True)
    assert result.returncode!=0 and 'was replaced' in result.stderr
    assert 'replacement-lease' in lease.read_text(encoding='utf-8-sig')
    assert not lines(root/'slot-calls.jsonl')


def test_borrow_cannot_cover_multiple_states(tmp_path):
    root,env=fixture_repo(tmp_path,('overcast','clear'));lease=held_lease(root);original=lease.read_bytes()
    result=invoke(root,env,('overcast','clear'),borrow=True)
    assert result.returncode!=0 and 'exactly one render state' in result.stderr
    assert lease.read_bytes()==original
    assert not lines(root/'slot-calls.jsonl') and not lines(root/'uv-calls.jsonl')


def test_incomplete_snapshot_never_falls_back_to_live_world(tmp_path):
    root,env=fixture_repo(tmp_path)
    (root/'out/inputs/world_manifest.json').unlink()
    result=invoke(root,env)
    assert result.returncode!=0 and 'Incomplete captured inputs: world_manifest.json' in result.stderr
    assert not lines(root/'slot-calls.jsonl') and not lines(root/'uv-calls.jsonl')


def test_missing_snapshot_directory_never_falls_back_to_live_world(tmp_path):
    root,env=fixture_repo(tmp_path)
    result=invoke(root,env,output='uncaptured-output')
    assert result.returncode!=0 and 'Captured input directory required' in result.stderr
    assert not lines(root/'slot-calls.jsonl') and not lines(root/'uv-calls.jsonl')


def test_render_only_seals_complete_raw_without_existing_metrics(tmp_path):
    root,env=fixture_repo(tmp_path)
    metrics=root/'out/sheets/Low-overcast/metrics.json';metrics.unlink()
    result=invoke(root,env,render_only=True)
    assert result.returncode==0,result.stdout+result.stderr
    assert not metrics.exists() and not lines(root/'uv-calls.jsonl')
    capture=json.loads((root/'out/renders/Low-overcast/capture-4x3.json').read_text(encoding='utf-8-sig'))
    assert capture['status']=='OK' and capture['cameras']==['sbs-test']
    assert (root/'out/inputs/world_manifest.json').read_bytes()==(root/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_bytes()
    calls=lines(root/'slot-calls.jsonl')
    assert [(r['operation'],r['pool']) for r in calls]==[('Acquire','unity'),('Release','unity')]


@pytest.mark.parametrize('tamper,error',[
    ('raw','Captured raw hash differs'),('state','Capture status or render state differs'),
    ('duplicate','Incomplete aspect capture roster'),('missing','Cannot snapshot evidence without render captures'),
    ('roster','Incomplete or duplicate capture cameras'),('dimensions','Raw dimensions differ from capture')])
def test_render_only_rejects_incomplete_or_changed_capture_before_sealing(tmp_path,tamper,error):
    root,env=fixture_repo(tmp_path)
    original=(root/'out/inputs/world_manifest.json').read_bytes()
    (root/'out/sheets/Low-overcast/metrics.json').unlink()
    env['SBS_TEST_CAPTURE_TAMPER']=tamper
    result=invoke(root,env,render_only=True)
    assert result.returncode!=0 and error in result.stderr
    assert (root/'out/inputs/world_manifest.json').read_bytes()==original
    assert not (root/'artifacts/locks/unity-slots/gpt-sbs.slot').exists()
    assert not lines(root/'uv-calls.jsonl')


def test_snapshot_cannot_publish_mixed_main_bases_between_states(tmp_path):
    root,env=fixture_repo(tmp_path,('overcast','clear'))
    original=(root/'out/inputs/world_manifest.json').read_bytes()
    path=root/'out/renders/Low-clear/capture-4x3.json'
    capture=json.loads(path.read_text());capture['main_sha']='c'*40;write(path,capture)
    result=invoke(root,env,('overcast','clear'))
    assert result.returncode!=0 and 'Cannot snapshot mixed main bases' in result.stderr
    assert (root/'out/inputs/world_manifest.json').read_bytes()==original
    assert not (root/'artifacts/locks/heavy-slots/gpt-sbs-test.slot').exists()
