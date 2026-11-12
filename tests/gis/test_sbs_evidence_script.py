"""PowerShell orchestration checks with isolated fake leases and a recording composer."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest

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
    for name,data in [('sbs_cameras.json',{'cameras':[]}),('sbs_references.json',{'references':[]}),
                      ('world_manifest.json',{'world':'captured'}),('materials_spec.json',{'materials':'captured'})]:
        write(snapshot/name,data)
    capture={'status':'OK','git_sha':'a'*40,'main_sha':'b'*40,'cameras':[],
             'tier':'Low','width':1280,'height':960,'render_sha256':{}}
    for name,key in [('sbs_cameras.json','cameras_sha256'),('sbs_references.json','references_sha256'),
                     ('world_manifest.json','world_manifest_sha256'),('materials_spec.json','materials_spec_sha256')]:
        capture[key]=hashlib.sha256((snapshot/name).read_bytes()).hexdigest()
    for state in states:
        row={**capture,'lighting':state}
        write(root/f'out/renders/Low-{state}/capture-4x3.json',row)
        write(root/f'out/sheets/Low-{state}/metrics.json',{'landmarks_sha256':None,'photometry_sha256':None,'render_captures':[row]})
    region=root/'Data/Regions/bialystok-industrial-c'
    write(region/'sbs_references.json',{'references':[]})
    write(region/'sbs_cameras.json',{'cameras':[]})
    write(region/'generated/world_manifest.json',{'world':'dirty newer live state'})
    write(root/'art-source/world/materials/materials_spec.json',{'materials':'dirty live'})
    env={**os.environ,'PATH':str(bin_dir)+os.pathsep+os.environ['PATH'],'SBS_TEST_ROOT':str(root)}
    return root,env


def invoke(root,env,states=('overcast',),borrow=False):
    quote=lambda value:"'"+str(value).replace("'","''")+"'"
    lights=','.join(quote(state) for state in states)
    command=f"$ErrorActionPreference='Stop'\n& {quote(root/'scripts/sbs-gate3.ps1')} -ComposeOnly -OutputRoot out -Tiers @('Low') -Lighting @({lights})"
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
