from PIL import Image, ImageDraw
import sys
def pair(name,tier,box=None,out=None,scale=1.0):
    a=Image.open(f'before/{tier}-clear/{name}.png'); b=Image.open(f'after/{tier}-clear/{name}.png')
    if box: a=a.crop(box); b=b.crop(box)
    w,h=a.size; s=Image.new('RGB',(w,h*2+8),'white'); s.paste(a,(0,0)); s.paste(b,(0,h+8))
    d=ImageDraw.Draw(s); d.text((8,8),f'BEFORE {tier} {name}',fill='yellow'); d.text((8,h+16),f'AFTER (0155) {tier}',fill='yellow')
    if scale!=1: s=s.resize((int(s.width*scale),int(s.height*scale)))
    s.save(out or f'sheets/{tier}-{name}.jpg',quality=88)
for t in ('Low','High'):
    pair('putry-island-near',t,(0,450,2340,1080))
    pair('sbs-g3-a-3970163613102941',t,None,scale=0.6)
    pair('sbs-g3-a-500263111404933',t,None,scale=0.6)
    pair('rv-andersa-deck-grazing',t,(0,500,2340,1080),scale=0.7)
    pair('g3a_rondo_bie_above',t,None,scale=0.6)
    pair('rv-island-underdeck-low',t,None,scale=0.6)
