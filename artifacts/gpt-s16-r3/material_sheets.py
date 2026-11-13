from pathlib import Path
from PIL import Image,ImageDraw
r=Path(__file__).resolve().parent;dest=r/'material-ablation-sheets';dest.mkdir(exist_ok=True)
for name in ['M_bridge_concrete','M_road_asphalt','deck-pair','all-pbr','M_bridge_kerb','deck-triple']:
 for camera in ['sbs-g3-a-2818555625124739','sbs-g3-a-3970163613102941','putry-island-1','putry-island-2','putry-island-near']:
  candidate=r/'material-ablations'/f'{name}-Low'/f'{camera}.png'
  if not candidate.exists():continue
  out=Image.new('RGB',(960,750),'white');d=ImageDraw.Draw(out)
  for i,(label,path) in enumerate([('baseline',r/'ablations/Low-baseline'/f'{camera}.png'),(name+' only',candidate),('global normal=0',r/'ablations/Low-zero-normal'/f'{camera}.png')]):
   im=Image.open(path).convert('RGB').crop((0,540,2340,1080));im.thumbnail((960,222));out.paste(im,(0,i*250+24));d.text((8,i*250+4),label+' | '+camera+' | native crop y540..1080',fill='black')
  out.save(dest/f'{name}-{camera}.jpg',quality=93)
print('Material isolation sheets updated')
