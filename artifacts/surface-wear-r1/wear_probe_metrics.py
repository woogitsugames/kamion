"""Display-space paired metrics; visible ROI context is explicit, not physical albedo."""
import json
import numpy as np
from PIL import Image,ImageDraw
from bus_world_proof import OUT

ROIS={
 'd_wear_lane_old': [('asphalt',[470,280,610,400]),('longitudinal_line',[245,285,370,425])],
 'd_wear_newroad_negative':[('new_asphalt',[800,150,870,230])],
 'd_field_glyph_unknown':[('unknown_hatch',[430,220,540,315])],
 'd_field_glyph_supported':[('supported_hatch',[350,180,620,370])],
 'd_field_p8_turn':[('P8_readability',[380,175,605,345])],
 'd_wear_crossing':[('P10_readability',[200,180,750,400])],
}
def luminance(rgb):return rgb@np.array([.2126,.7152,.0722])
def main():
    rows=[];dest=OUT/'wear-probe-pairs-960';dest.mkdir(exist_ok=True)
    for cond in ['Low-clear','Low-overcast','High-clear','High-overcast']:
        for before in sorted((OUT/'wear-probe-before'/cond).glob('*.png')):
            after=OUT/'wear-probe-after'/cond/before.name
            a=np.asarray(Image.open(before).convert('RGB'),float);b=np.asarray(Image.open(after).convert('RGB'),float)
            ya,yb=luminance(a),luminance(b);delta=yb-ya
            row=dict(condition=cond,camera=before.stem,whole_frame_mean_rgb_delta=(b-a).mean((0,1)).tolist(),whole_frame_mean_abs_rgb_lsb=float(abs(b-a).mean()),rois=[])
            for label,box in ROIS.get(before.stem,[]):
                x0,y0,x1,y1=[round(v*a.shape[1]/960)for v in box]
                aa=ya[y0:y1,x0:x1];bb=yb[y0:y1,x0:x1]
                metric=dict(label=label,roi960=box,before_mean=float(aa.mean()),after_mean=float(bb.mean()),mean_luma_delta_lsb=float((bb-aa).mean()),before_p99=float(np.percentile(aa,99)),after_p99=float(np.percentile(bb,99)),mean_abs_luma_lsb=float(abs(bb-aa).mean()))
                if any(k in label for k in ['hatch','readability','line']):
                    threshold=float((np.percentile(aa,10)+np.percentile(aa,90))*.5)
                    metric.update(fixed_display_threshold=threshold,before_bright_fraction=float((aa>threshold).mean()),after_bright_fraction=float((bb>threshold).mean()),note='Fixed baseline-derived display threshold over visible marking context; not true paint area, glyph topology or independent readability acceptance.')
                row['rois'].append(metric)
            rows.append(row)
            board=Image.new('RGB',(960,924),'#222');draw=ImageDraw.Draw(board)
            for i,(file,label)in enumerate([(before,'BEFORE: gate R2, paint .425/.085'),(after,'AFTER: three wear blocks only')]):
                im=Image.open(file).convert('RGB');im.thumbnail((960,444));board.paste(im,(0,i*462+18));draw.text((8,i*462+3),cond+' | '+before.stem+' | '+label,fill='white')
            board.save(dest/(cond+'-'+before.stem+'.jpg'),quality=94)
    assert len(rows)==56
    report=dict(note='Actual matched source/camera pairs; RGB/luma display levels depend on exposure and weather. ROIs are visible context, not measured physical albedo. Human inspection decides wet ribbons and paint legibility. Signal lamp heads are outside the signal-oil closeup; no lamp ROI claim is made.',rows=rows)
    (OUT/'wear-probe-metrics.json').write_text(json.dumps(report,indent=2)+'\n')
    for row in rows:
        if row['rois']:print(row['condition'],row['camera'],[(r['label'],round(r['mean_luma_delta_lsb'],4))for r in row['rois']])
if __name__=='__main__':main()
