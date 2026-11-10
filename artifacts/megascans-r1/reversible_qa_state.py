"""Reversible local A/B state. Licensed backup stays inside ignored Fab output.
Run only while Unity and world generation for this worktree are stopped.
"""
from pathlib import Path
import sys,zipfile,shutil
ROOT=Path(__file__).resolve().parents[2]
ARCHIVE=ROOT/'art-source/world/megascans/_generated/qa-after-r3.zip'
PREFIXES=[ROOT/'game/Assets/_Generated/World/bialystok-industrial-c',ROOT/'Data/raw/derived/bialystok-industrial-c/world',ROOT/'Data/Regions/bialystok-industrial-c/generated']
def allowed(path):
 p=path.resolve()
 return any(p.is_relative_to(base.resolve()) for base in PREFIXES)
def unity_stopped():
 lock=ROOT/'game/Temp/UnityLockfile'
 if lock.exists():
  try:
   with lock.open('r+b'):pass
  except OSError as exc:raise RuntimeError('Unity still owns this project; wait before snapshot/restore') from exc

def save():
 unity_stopped()
 ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
 count=0
 with zipfile.ZipFile(ARCHIVE,'w',compression=zipfile.ZIP_STORED) as z:
  for base in PREFIXES:
   for path in sorted(base.rglob('*')):
    if path.is_file():
     assert allowed(path)
     z.write(path,path.relative_to(ROOT).as_posix());count+=1
 print(f'Saved {count} local generated files; licensed archive remains ignored')
def restore():
 unity_stopped()
 count=0
 with zipfile.ZipFile(ARCHIVE) as z:
  for member in z.infolist():
   if member.is_dir():continue
   path=ROOT/member.filename
   if not allowed(path):raise ValueError('Backup member outside explicit generated roots')
   path.parent.mkdir(parents=True,exist_ok=True)
   with z.open(member) as source,path.open('wb') as target:shutil.copyfileobj(source,target,1<<20)
   count+=1
 print(f'Restored {count} local generated files')
if __name__=='__main__':
 if sys.argv[1]=='save':save()
 elif sys.argv[1]=='restore':restore()
 else:raise ValueError('Expected save or restore')
