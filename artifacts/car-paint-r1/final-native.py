from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json
r=Path(__file__).resolve().parent;out=r/'r3-checks';out.mkdir(exist_ok=True)
boxes={'tyre_upper':(1125,401,1215,416),'rim_spoke':(1075,533,1110,543),'dark_dish':(1100,460,1115,485)};metrics={}
for c in ['Low-clear','Low-overcast','High-clear','High-overcast']:
 o=Image.new('RGB',(960,500));d=ImageDraw.Draw(o);metrics[c]={}
 for j,tag in enumerate(['before-wheel','r3']):
  im=Image.open(r/tag/c/'g_current_black_wheel_02.png').convert('RGB');a=np.asarray(im);metrics[c][tag]={k:a[y0:y1,x0:x1].mean(axis=(0,1)).tolist() for k,(x0,y0,x1,y1) in boxes.items()}
  o.paste(im.crop((930,300,1410,780)),(j*480,20));d.text((j*480+5,3),f'{tag} {c} native wheel ROI',fill='white')
 o.save(out/f'wheel-native-{c}.jpg',quality=94)
 o=Image.new('RGB',(960,440));d=ImageDraw.Draw(o)
 for j,tag in enumerate(['before','pearl-only','r3']):
  im=Image.open(r/tag/c/'r10b_black_05.png').convert('RGB');door=im.crop((980,590,1100,660));hood=im.crop((1450,560,1580,630));door=door.resize((300,175));hood=hood.resize((300,162));o.paste(door,(j*320,35));o.paste(hood,(j*320,260));d.text((j*320+6,8),f'{tag} {c} door',fill='white');d.text((j*320+6,235),'pure bonnet',fill='white')
 o.save(out/f'owner-native-{c}.jpg',quality=94)
(r/'final-native-wheel-metrics.json').write_text(json.dumps(dict(note='Same native wheel pixel ROIs, environmental lighting affects RGB. Geometry22vs14 changes sampled face interpolation, not calibrated reflectance.',boxes=boxes,conditions=metrics),indent=2)+'\n',encoding='utf-8')
