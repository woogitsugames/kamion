"""960 px comparisons of the whole vehicle after repacking the atlas."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw

root=Path(__file__).resolve().parent
stage=sys.argv[1]
tier=sys.argv[2] if len(sys.argv)>2 else 'Low'
if tier not in ('Low','High'): raise ValueError('Unknown tier')
cameras=('truck-34','truck-34r','truck-front','truck-side','truck-rear34','cab-driver','chase')
out=root/(stage+'-pairs')
out.mkdir(exist_ok=True)
for condition in (tier+'-overcast',tier+'-clear'):
    if not (root/stage/condition/'complete.ok').exists():
        raise ValueError('Unfinished capture')
    contact=Image.new('RGB',(960,592),(24,24,24))
    for i,camera in enumerate(cameras):
        sheet=Image.new('RGB',(960,256),(24,24,24))
        draw=ImageDraw.Draw(sheet)
        for x,phase,label in ((0,'before','PRZED'),(480,stage,'KANDYDAT')):
            with Image.open(root/phase/condition/f'{camera}.png') as picture:
                if picture.size!=(2340,1080):
                    raise ValueError('Unexpected native dimensions')
                sheet.paste(picture.convert('RGB').resize((480,222),Image.Resampling.LANCZOS),(x,34))
            draw.text((x+8,8),f'{label} | {condition}',fill='white')
        sheet.save(out/f'{condition}-{camera}.jpg',quality=94)
        x,y=(i%2)*480,(i//2)*148
        ImageDraw.Draw(contact).text((x+6,y+3),f'{condition} | {camera}',fill='white')
        contact.paste(sheet.resize((480,128),Image.Resampling.LANCZOS),(x,y+20))
    contact.save(out/f'{condition}-contact.jpg',quality=94)
print(out)

