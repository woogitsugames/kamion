from pathlib import Path
import json,re
root=Path(__file__).resolve().parent
out=[]
for cond in ['Low-overcast','Low-clear','High-overcast','High-clear']:
 before=(root/'before'/cond/'stats.txt').read_text().splitlines()
 after=(root/'after-final'/cond/'stats.txt').read_text().splitlines()
 diffs=[{'before':x,'after':y} for x,y in zip(before,after) if x!=y]
 out.append({'condition':cond,'rows_before':len(before),'rows_after':len(after),'stats_byte_identical':before==after,'changed_rows':diffs,'fixture_note':'after-final canonical Truck/Trailer refreshed; this diagnostic is not isolated material-cost evidence. Matched before/after-calibrated cost proof remains final-budget-proof.json.'})
(root/'canonical-fixture-budget-diagnostic.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
