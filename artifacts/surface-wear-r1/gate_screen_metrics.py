"""Project the actual four added strips; report native matched-image contrast."""
import json
import numpy as np
from PIL import Image, ImageDraw
from bus_world_proof import ROOT, OUT, read


def main(stage='gate-pair-after',reference='gate-pair-before'):
    _, nodes = read(ROOT / 'Data/raw/derived/bialystok-industrial-c/world/chunk_6_6.glb')
    attrs = next(a for m, a in nodes['markings'] if m == 'decal_tyre')
    vertices = attrs['POSITION'][176:248].astype(float)
    indices = attrs['indices'].reshape(-1, 3)
    indices = indices[np.all((indices >= 176) & (indices < 248), axis=1)] - 176
    assert len(vertices) == 72 and len(indices) == 64
    specs = {c['id']: c for c in json.loads((OUT/'qa-gate-pair-cameras.json').read_text())['cameras']}
    results = []
    for condition in ['Low-clear', 'Low-overcast', 'High-clear', 'High-overcast']:
        packet = json.loads((OUT/stage/condition/'runtime-pose.json').read_text())
        old_packet = json.loads((OUT/reference/condition/'runtime-pose.json').read_text())
        for camera in packet['cameras']:
            name = camera['id']
            if name not in specs: continue
            old_camera = next(c for c in old_packet['cameras'] if c['id'] == name)
            for key in ['view', 'projection', 'width', 'height', 'fov']:
                assert camera[key] == old_camera[key], (condition, name, key)
            anchor = specs[name]['pos'][2] - camera['cameraPosition']['y']
            xyz = vertices.copy(); xyz[:, 0] *= -1; xyz[:, 1] -= anchor
            clip = np.array(camera['projection']).reshape(4,4) @ np.array(camera['view']).reshape(4,4) @ np.column_stack([xyz, np.ones(72)]).T
            ndc = (clip[:3] / clip[3]).T
            a = np.asarray(Image.open(OUT/reference/condition/(name+'.png')).convert('RGB'), float)
            image = Image.open(OUT/stage/condition/(name+'.png')).convert('RGB')
            # Low internal rendering dimensions differ from the saved upscaled PNG.
            points = np.column_stack([(ndc[:,0]+1)*image.width/2, (1-ndc[:,1])*image.height/2])
            b = np.asarray(image, float); delta = (b-a).mean(axis=2)
            union = np.zeros(delta.shape, bool); strips=[]
            overlay = image.copy(); painter = ImageDraw.Draw(overlay)
            # Source order: entry left/right, exit left/right. Each strip has 18 vertices.
            for s in range(4):
                triangles = indices[np.all((indices >= s*18) & (indices < (s+1)*18), axis=1)]
                assert len(triangles) == 16
                mask_image = Image.new('1', image.size); draw = ImageDraw.Draw(mask_image)
                for triangle in triangles: draw.polygon([tuple(points[i]) for i in triangle], fill=1)
                mask = np.asarray(mask_image, bool); union |= mask
                if not mask.any(): continue
                p = points[s*18:(s+1)*18]
                bbox = [int(p[:,0].min()), int(p[:,1].min()), int(p[:,0].max())+1, int(p[:,1].max())+1]
                strips.append(dict(strip=s, source_gate='entry' if s<2 else 'exit', native_bbox=bbox, pixels=int(mask.sum()),
                                   before_rgb=a[mask].mean(0).tolist(), after_rgb=b[mask].mean(0).tolist(),
                                   mean_darkening_lsb=float(-delta[mask].mean()), median_darkening_lsb=float(-np.median(delta[mask])),
                                   darkened_over3_lsb_fraction=float((delta[mask]<-3).mean()), darkening_p90_lsb=float(np.percentile(-delta[mask],90))))
                painter.rectangle(bbox, outline=(255,70,30), width=2); painter.text((bbox[0],bbox[1]), str(s), fill=(255,70,30))
            prefix=('gate' if stage=='gate-pair-after' else 'gate-r2')+('-vs-r1' if reference=='gate-pair-after' else '')
            overlay.thumbnail((960,960)); overlay.save(OUT/(f'{prefix}-mask-{condition}-{name}.jpg'),quality=90)
            results.append(dict(condition=condition,camera=name,strips=strips,
                                outside_strips_mean_abs_rgb_lsb=float(np.abs(b-a)[~union].mean()),
                                actual_runtime_matrices_identical=True))
    report=dict(stage=stage,reference=reference,note='Native screen RGB contrast over exact source triangles, not physical reflectance or visibility PASS. Before/after runtime matrices exact. Masks include decal edge fade and uncovered triangle pixels; original PNGs untouched.',
                strength_working=.9,source_strip_length_m=4.2,source_strip_width_m=.2,results=results)
    prefix=('gate' if stage=='gate-pair-after' else 'gate-r2')+('-vs-r1' if reference=='gate-pair-after' else '')
    (OUT/(prefix+'-screen-metrics.json')).write_text(json.dumps(report,indent=2)+'\n')
    for row in results:
        relevant=[s for s in row['strips'] if s['source_gate'] == row['camera'].removeprefix('d_gate_pair_')]
        print(row['condition'],row['camera'],[(s['strip'],round(s['mean_darkening_lsb'],3),round(s['darkened_over3_lsb_fraction'],3))for s in relevant])


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['gate-pair-after','gate-r2-after'],default='gate-pair-after')
    parser.add_argument('--reference',choices=['gate-pair-before','gate-pair-after'],default='gate-pair-before')
    args=parser.parse_args();main(args.stage,args.reference)
