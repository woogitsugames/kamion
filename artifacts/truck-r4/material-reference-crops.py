from pathlib import Path
from PIL import Image
import hashlib,json
root=Path('artifacts/truck-r4'); src=Path('C:/Users/matma/Documents/Claude/kamion/Data/photos/nowe')
rows=[]
for name,out,box in [('cab_2022_DAF_XG_530.jpg','glass-reflection-crop.jpg',(325,230,890,510)),('cab_6-365_Volvo_FH.jpg','paint-door-crop.jpg',(800,800,930,950))]:
 p=src/name
 with Image.open(p) as im:
  q=im.convert('RGB').crop(box); q.save(root/'references'/out,quality=95)
 rows.append({'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'output':'references/'+out,'crop':box,'method':'crop only, no color or aspect adjustment'})
(root/'material-reference-crops.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
print('Saved two original-color reference crops')
