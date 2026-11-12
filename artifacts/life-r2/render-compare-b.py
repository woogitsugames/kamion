"""Explicit arguments without PowerShell -File array-parameter ambiguity."""
import runpy
import sys
from pathlib import Path

sys.argv = ['compare.py', '--before', 'before-exact', '--after', 'after-b-exact', '--tag', 'b', '--exact']
runpy.run_path(str(Path(__file__).with_name('compare.py')), run_name='__main__')
