from pathlib import Path
from PIL import Image, ImageDraw
root=Path(__file__).parent
cameras=['stretch-05-docks','r10_hall_3','r10_block_3']
for light in ['clear','lowsun']:
    sheet=Image.new('RGB',(960,704),'#202020')
    draw=ImageDraw.Draw(sheet)
    for row,name in enumerate(['before','bias','splits','combined']):
        directory=root/('before/High-'+light) if name=='before' else root/'shadow'/name/light
        for col,camera in enumerate(cameras):
            im=Image.open(directory/(camera+'.png')).convert('RGB').resize((320,148))
            sheet.paste(im,(col*320,row*176+20))
            draw.text((col*320+2,row*176+3),name+' '+camera,fill='white')
    sheet.save(root/'shadow'/('comparison-'+light+'.jpg'),quality=96)
for light in ['clear','lowsun']:
    sheet=Image.new('RGB',(960,528),'#202020')
    draw=ImageDraw.Draw(sheet)
    for row,name in enumerate(['before','bias','combined']):
        directory=root/'shadow'/('Medium-'+name)/light
        for col,camera in enumerate(cameras):
            im=Image.open(directory/(camera+'.png')).convert('RGB').resize((320,148))
            sheet.paste(im,(col*320,row*176+20))
            draw.text((col*320+2,row*176+3),name+' '+camera,fill='white')
    sheet.save(root/'shadow'/('Medium-comparison-'+light+'.jpg'),quality=96)
