"""Preserve exact chunk mesh/transform evidence; material definitions and indirect instances are separate."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / 'artifacts/surface-wear-r1'))
from bus_world_proof import read


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--details', action='store_true', help='Optional local full ledger; keep outside Git.')
    args = parser.parse_args()
    world = ROOT / 'Data/raw/derived/bialystok-industrial-c/world'
    rows = []
    for file in sorted(world.glob('chunk_*.glb')):
        document, nodes = read(file)
        graph = [{key: node[key] for key in ('name', 'mesh', 'children', 'matrix', 'translation', 'rotation', 'scale') if key in node}
                 for node in document['nodes']]
        transforms = hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        primitives = []
        for node, parts in sorted(nodes.items()):
            for index, (material, attrs) in enumerate(parts):
                fields = {}
                for name, values in sorted(attrs.items()):
                    fields[name] = dict(shape=list(values.shape), dtype=values.dtype.str,
                                        sha256=hashlib.sha256(values.tobytes()).hexdigest())
                primitives.append(dict(node=node, primitive=index, material=material, fields=fields))
        rows.append(dict(file=file.name, scene_graph_sha256=transforms, primitives=primitives))
    if not rows:
        raise RuntimeError('No chunk GLBs; run the canonical world producer first.')
    report = dict(label=args.label, files=len(rows), rows=rows,
                  note='Exact accessor values/types/shapes and scene graph for every chunk GLB, both tiers. Material definitions, indirect instance files and GPU draw costs are not covered.')
    if args.details:
        (OUT / f'geometry-{args.label}.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    compact_rows = [dict(file=row['file'], primitives=len(row['primitives']),
                         scene_graph_sha256=row['scene_graph_sha256'],
                         record_sha256=hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':')).encode()).hexdigest())
                    for row in rows]
    compact = dict(label=args.label, files=len(rows), rows=compact_rows,
                   note='Per-file SHA-256 of the canonical full accessor/graph record: json sort_keys=True, separators=(comma,colon). '
                        'Every accessor shape/type/value hash and primitive material name participates. '
                        'Material definitions, indirect instances and GPU costs are separate. Full ledgers optional/local only.')
    (OUT / f'geometry-summary-{args.label}.json').write_text(json.dumps(compact, indent=2)+'\n', encoding='utf-8')
    summary = dict(label=args.label, files=len(rows), primitives=sum(len(row['primitives']) for row in rows))
    baseline_path = OUT / 'geometry-summary-baseline.json'
    if args.label != 'baseline' and baseline_path.exists():
        baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
        before = {row['file']: row for row in baseline['rows']}
        after = {row['file']: row for row in compact_rows}
        changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
        summary.update(exactly_equal=not changed, changed_files=changed)
        (OUT / f'geometry-comparison-{args.label}.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
        if changed:
            print(json.dumps(summary))
            raise SystemExit(1)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
