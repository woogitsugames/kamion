"""Temporarily select the five furniture modules for a reproducible base/current world A/B."""
import subprocess
import sys
from pathlib import Path

ref = '9e6e9fde' if sys.argv[1] == 'baseline' else 'HEAD'
for name in ('props', 'furniture', 'export', 'materials'):
    p = f'tools/worldgen/streetscape/{name}.py'
    Path(p).write_bytes(subprocess.check_output(['git', 'show', f'{ref}:{p}']))
