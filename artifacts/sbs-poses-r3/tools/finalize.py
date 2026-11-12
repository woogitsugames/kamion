"""ADR 0143: write chosen probe overrides as explicit authored overrides + formula-identical sbs_cameras.json /
sbs_references.json entries. usage: finalize.py r1 [r2 ...] [--write]; choices in choice.json
{camera_id: {probe, anchors, how}}."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P
CHOICE = json.loads((Path(__file__).parent / 'choice.json').read_text(encoding='utf-8'))


def build(rounds):
    probes, plan = {}, {}
    for rnd in rounds:
        base = Path(__file__).resolve().parents[1] / rnd
        probes.update({c['id']: c for c in json.loads((base / 'cameras.json').read_text(encoding='utf-8'))['cameras']})
        plan.update({p['probe']: p for p in json.loads((base / 'plan.json').read_text(encoding='utf-8'))})
    R, O = P.refs(), P.overrides()
    out = {}
    for cid, ch in CHOICE.items():
        pl = plan[ch['probe']]
        assert pl['base'] == cid, (cid, pl['base'])
        ov = dict(O.get(cid, {}))
        ov.update(pl['override'])
        if pl.get('rectified_horizon') is not None:
            ov['rectified_horizon_y_fraction'] = pl['rectified_horizon']
        if not ov.get('heading_delta_deg'):
            ov.pop('heading_delta_deg', None)
        ov['pose_status'] = 'WORKING_VALUE'
        ov['pose_confidence'] = ch.get('confidence', 'B')
        ov['pose_reason'] = f"ADR 0143 (s14): probe {ch['probe']}; anchors: {ch['anchors']}"
        old = ov.get('note', '').split(' ADR 0143:')[0]
        ov['note'] = old + f" ADR 0143: {ch['how']} WORKING_VALUE, not surveyed."
        cam, inf = P.camera(R[cid], ov)
        pc = probes[ch['probe']]
        d = max(abs(a - b) for a, b in zip(cam['pos'] + cam['look_at'] + [cam['fov_deg']], pc['pos'] + pc['look_at'] + [pc['fov_deg']]))
        if d > 2e-3:
            raise SystemExit(f'{cid}: production camera differs from rendered probe by {d}')
        out[cid] = (ov, cam, inf)
    return out


if __name__ == '__main__':
    res = build([a for a in sys.argv[1:] if not a.startswith('--')])
    reg = P.REGION
    od = P.S.read(reg / 'sbs_authored_overrides.json')
    cd = P.S.read(reg / 'sbs_cameras.json')
    rd = P.S.read(reg / 'sbs_references.json')
    for cid, (ov, cam, inf) in res.items():
        od['authored_overrides'][cid] = ov
        for i, c in enumerate(cd['cameras']):
            if c['id'] == cid:
                cd['cameras'][i] = cam
        for r in rd['references']:
            if r['camera'] == cid:
                r['heading_grid_deg'] = inf['heading']; r['horizon_y_fraction'] = inf['horizon_rect']
                r['pose_status'] = ov['pose_status']; r['pose_confidence'] = ov['pose_confidence']; r['pose_reason'] = ov['pose_reason']
                r['authored_overrides'] = ov
        print(cid, cam['pos'], round(inf['heading'], 3), round(inf['horizon_rect'], 3))
    if '--write' in sys.argv:
        for name, data in (('sbs_authored_overrides.json', od), ('sbs_cameras.json', cd), ('sbs_references.json', rd)):
            P.S.write(reg / name, data)
        print('written; mismatches:', P.verify_all())
