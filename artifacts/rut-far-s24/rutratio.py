"""after/before ratio of rut darkening on identical ground (off render shared): isolates the shader change.
Cells: mean rel darkening (%) per ground slice x camera shift (rg_S), plus q_far/q_far2 row bands (rutmeasure)."""
import sys
from rutdist import table, SHIFTS, SLICES
from rutmeasure import measure
from pathlib import Path
for lt in ('clear', 'overcast'):
    Ss, b = table('vqa/dist2-before', 'vqa/dist2-off', lt)
    _, a = table('vqa/after', 'vqa/dist2-off', lt)
    print(f'== {lt}: rg slices, mean darkening before -> after (%) [ratio]; peak before -> after')
    for g in SLICES:
        row = []
        for S in Ss:
            x, y = b[(g, S)], a[(g, S)]
            row.append(f'S={S}({S+g[0]}-{S+g[1]}m): ' + ('-' if not x or not y else f'{x[1]:.2f}->{y[1]:.2f} [{(y[1]/x[1]) if abs(x[1])>0.2 else float("nan"):.2f}] pk {x[0]:.1f}->{y[0]:.1f}'))
        print(f'  ground {g[0]}-{g[1]} m: ' + ' | '.join(row))
    for cam in ('q_far', 'q_far2'):
        p0 = lambda d: Path(f'vqa/{d}-{lt}/{cam}.png')
        mb = measure(p0('before'), p0('before-off')); ma = measure(p0('after'), p0('before-off'))
        print(f'  {cam} (h=2.5 row->dist, UNVERIFIED): rows | dist | peak before->after | mean before->after')
        for rb, ra in zip(mb, ma):
            if len(rb) > 3 and len(ra) > 3: print(f'    {rb[0]}-{rb[1]} ~{rb[2]} m  peak {rb[3]:.1f}->{ra[3]:.1f}  mean {rb[4]:.1f}->{ra[4]:.1f}')
