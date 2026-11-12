"""Draft for vegetation.py; baseline does not import it."""
from streetscape import plots as PLT


def garden_canopies(trees, rp, report):
    """ADR0154: broader existing High garden crowns, no added instances.

    Width multipliers are WORKING_VALUE from typology P07/P08/P12:
    maple/linden1.35, birch1.20, pine unchanged. Tree positions/radii source
    remains the original orthophoto extraction; species are existing rules.
    """
    lookup={f"plot:{p['id']}":p for p in rp.get('plots',[])}
    widths={'tree_maple':1.35,'tree_linden':1.35,'tree_birch':1.20}
    rows=[];result=[]
    for tree in trees:
        plot=lookup.get(tree.get('src','').rsplit(':',1)[0])
        width=widths.get(tree.get('p'))
        if tree.get('tier')!='high' or plot is None or width is None:
            result.append(tree);continue
        changed=dict(tree);changed['garden_canopy_width']=width
        species=tree['p'].removeprefix('tree_')
        # Height relation is a working typology, not an ortho height measurement.
        required=float(plot.get('house_h') or 6.)+3.5
        changed['h']=round(min(PLT.INST_H_M[species][1],max(float(tree['h']),required)),1)
        result.append(changed)
        rows.append({'src':tree['src'],'species':species,'height_before_m':tree['h'],'height_after_m':changed['h'],'width_multiplier':width,'position':[tree['e'],tree['n']]})
    report['garden_canopies']={'source':'WORKING_VALUE width/height; P07/P08/P12 typology; original ortho positions retained','modified':len(rows),'added_instances':0,'high_only':True,'list':rows}
    return result
