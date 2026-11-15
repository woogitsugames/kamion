import re
from pathlib import Path
for p in sorted(Path('artifacts/knyszyn-rynek-0227/before').glob('*/stats.txt')):
 rows=[]
 for line in p.read_text(encoding='utf8').splitlines():
  m=re.match(r'^([^:]+): .*?drawsEst=(\d+).*?trisExact=(\d+)',line)
  if m: rows.append((m.group(1),int(m.group(2)),int(m.group(3))))
 if rows:
  a=max(rows,key=lambda r:r[1]); b=max(rows,key=lambda r:r[2]); print(f'{p.parent.name}: cameras={len(rows)}, max drawsEst={a[1]} ({a[0]}), max trisExact={b[2]} ({b[0]})')
