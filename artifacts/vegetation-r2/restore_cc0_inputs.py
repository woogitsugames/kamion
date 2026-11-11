"""Restore two pinned CC0 inputs from this ignored evidence packet, after B merge.
No download or source edit. Refuse conflicting files and any resolved path outside repo.
"""
import argparse,hashlib,json,shutil
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);args=parser.parse_args()
    root=args.root.resolve()
    if not (root/'.git').exists():raise ValueError('Target must be a Git checkout/worktree')
    packet=Path(__file__).resolve().parent/'inputs/cc0/pine_tree_01'
    pin=json.loads((packet/'pine_needles_manifest.json').read_text(encoding='utf-8'))
    target_manifest=root/'art-source/world/cc0/pine_needles_manifest.json'
    if not target_manifest.exists():raise ValueError('Merge B source manifest before restoring inputs')
    if json.loads(target_manifest.read_text(encoding='utf-8'))!=pin:raise ValueError('Target manifest differs from evidence packet')
    actions=[]
    for entry in pin['files']:
        source=packet/entry['file'];expected=entry['sha256'];dest=(root/pin['raw_dir']/entry['file']).resolve()
        if not dest.is_relative_to(root):raise ValueError('Target resolved outside selected checkout')
        if hashlib.sha256(source.read_bytes()).hexdigest()!=expected:raise ValueError('Packet hash mismatch: '+entry['file'])
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()!=expected:raise ValueError('Refusing to replace conflicting input: '+str(dest))
        actions.append((source,dest,expected))
    result=[]
    for source,dest,expected in actions:
        existed=dest.exists();dest.parent.mkdir(parents=True,exist_ok=True)
        if not existed:shutil.copy2(source,dest)
        if hashlib.sha256(dest.read_bytes()).hexdigest()!=expected:raise ValueError('Restored input hash mismatch')
        result.append({'file':str(dest),'sha256':expected,'copied':not existed})
    print(json.dumps({'status':'PINNED_CC0_INPUTS_READY','inputs':result},indent=2))
if __name__=='__main__':main()
