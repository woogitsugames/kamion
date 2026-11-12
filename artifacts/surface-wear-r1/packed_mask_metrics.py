"""Actual four-camera mask-trial display metrics and untouched before/QA previews."""
import json
import numpy as np
from PIL import Image,ImageDraw
from bus_world_proof import OUT
from wear_probe_metrics import luminance
ROIS={
 'd_wear_lane_old':('old_asphalt',[470,280,610,400]),
 'd_wear_missing_uv_2':('missing_field_asphalt',[300,300,850,415]),
 'd_wear_newroad_negative':('fresh_asphalt_negative',[800,150,870,230]),
 'd_field_p8_turn':('paint_P8_context',[380,175,605,345]),
}
def main():
    dest=OUT/'packed-mask-pairs-960';dest.mkdir(exist_ok=True);rows=[]
    for cond in ['Low-clear','Low-overcast','High-clear','High-overcast']:
        for name,(label,box)in ROIS.items():
            before=OUT/'wear-probe-before'/cond/(name+'.png');after=OUT/'packed-mask-qa'/cond/(name+'.png')
            a=np.asarray(Image.open(before).convert('RGB'),float);b=np.asarray(Image.open(after).convert('RGB'),float)
            x0,y0,x1,y1=[round(v*a.shape[1]/960)for v in box]
            aa=a[y0:y1,x0:x1];bb=b[y0:y1,x0:x1];ya,yb=luminance(aa),luminance(bb);delta=yb-ya
            row=dict(condition=cond,camera=name,label=label,roi960=box,mean_RGB_delta=(bb-aa).mean((0,1)).tolist(),
                before_mean_luma=float(ya.mean()),after_mean_luma=float(yb.mean()),mean_luma_delta_lsb=float(delta.mean()),
                mean_abs_luma_lsb=float(abs(delta).mean()),p99_abs_luma_lsb=float(np.percentile(abs(delta),99)),max_abs_luma_lsb=float(abs(delta).max()),
                darkened_over1_fraction=float((delta<-1).mean()),darkened_over3_fraction=float((delta<-3).mean()),mean_within1_lsb=bool(abs(delta.mean())<=1),
                whole_frame_mean_abs_RGB_lsb=float(abs(b-a).mean()))
            if name=='d_field_p8_turn':
                threshold=float((np.percentile(ya,10)+np.percentile(ya,90))*.5);mask=ya>threshold
                row.update(fixed_paint_context_threshold=threshold,before_bright_fraction=float(mask.mean()),after_bright_fraction=float((yb>threshold).mean()),
                    original_bright_pixel_mean_abs_luma_lsb=float(abs(delta[mask]).mean()),paint_readability_requires_visual_review=True)
            rows.append(row)
            board=Image.new('RGB',(960,924),'#222');draw=ImageDraw.Draw(board)
            for i,(file,text)in enumerate([(before,'BEFORE selected shader'),(after,'QA packed mask, old road only')]):
                im=Image.open(file).convert('RGB');im.thumbnail((960,444));board.paste(im,(0,i*462+18));draw.text((8,i*462+3),name+' | '+cond+' | '+text,fill='white')
            board.save(dest/(cond+'-'+name+'.jpg'),quality=94)
    proof=dict(note='Native matched PNG measurements in inspected visible ROIs, display luma levels; not physical albedo. High tests GBA/compression drift and absence of double-crack response; Low tests the single existing mask sample. Mean alone is not a visibility PASS.',rows=rows)
    (OUT/'packed-mask16-image-metrics.json').write_text(json.dumps(proof,indent=2)+'\n')
    for r in rows:print(r['condition'],r['camera'],'mean',round(r['mean_luma_delta_lsb'],4),'abs',round(r['mean_abs_luma_lsb'],4),'dark>3',round(r['darkened_over3_fraction'],4))
if __name__=='__main__':main()
