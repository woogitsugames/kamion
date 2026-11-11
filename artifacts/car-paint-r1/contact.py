"""Every native QA PNG is included once in labelled <=960px contact pages."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent
def main():
    tag=sys.argv[1]
    for folder in sorted((ROOT/tag).iterdir()):
        if not folder.is_dir():continue
        files=sorted(p for p in folder.glob('*.png') if not p.stem.endswith(('_mask','_envcube')))
        out=ROOT/'contacts'/tag/folder.name;out.mkdir(parents=True,exist_ok=True)
        for start in range(0,len(files),12):
            page=Image.new('RGB',(960,720),(33,33,33));d=ImageDraw.Draw(page)
            for j,p in enumerate(files[start:start+12]):
                image=Image.open(p).convert('RGB');image.thumbnail((320,148))
                x=(j%3)*320;y=(j//3)*180
                page.paste(image,(x+(320-image.width)//2,y+24))
                d.text((x+5,y+5),p.stem,fill='white')
            page.save(out/f'{start//12:02d}.jpg',quality=90)
        print(tag,folder.name,len(files),'native frames',len(list(out.glob('*.jpg'))),'pages')

if __name__=='__main__':main()
