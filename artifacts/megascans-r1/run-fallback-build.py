"""Record the actual Python process exit for the no-Fab world build."""
import json,os,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[2]
env=os.environ.copy();env['KAMION_DISABLE_FAB']='1';env['PYTHONUNBUFFERED']='1'
command=[sys.executable,str(root/'tools/worldgen/roads/build_world.py'),'--region','bialystok-industrial-c']
t=time.monotonic()
with (root/'artifacts/megascans-r1/fallback-build.log').open('wb') as output:
 result=subprocess.run(command,cwd=root,env=env,stdout=output,stderr=subprocess.STDOUT)
record={'returncode':result.returncode,'seconds':round(time.monotonic()-t,3),'disabled_fab':True,'same_worldgen_python':True}
(root/'artifacts/megascans-r1/fallback-build-exit.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record));sys.exit(result.returncode)
