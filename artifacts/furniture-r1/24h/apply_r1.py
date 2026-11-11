"""Apply furniture-only changes after the baseline generator has exited."""
from pathlib import Path

root = Path.cwd()
path = root / 'tools/worldgen/streetscape/furniture.py'
text = path.read_text(encoding='utf-8')
start = text.index('def panel_fence(')
end = text.index('\ndef fences(', start)
candidate = Path(__file__).with_name('panel_candidate.py').read_text(encoding='utf-8')
candidate = candidate[candidate.index('def panel_fence('):]
path.write_text(text[:start] + candidate.rstrip() + '\n\n' + text[end:], encoding='utf-8')

path = root / 'tools/worldgen/streetscape/props.py'
text = path.read_text(encoding='utf-8')
start = text.index('def lamp_old(')
end = text.index('\ndef lamp_arc(', start)
body = text[start:end]
body = body.replace('0.24 -> 0.14 m', '0.30 -> 0.14 m')
body = body.replace('0.12, 0.12, seg, cap=False)', '0.15, 0.15, seg, cap=False)')
body = body.replace('[0, 0, h], 0.12, 0.07, seg)', '[0, 0, h], 0.15, 0.07, seg)')
body = body.replace('rr = 0.12 - 0.05 * zb / h + 0.004', 'rr = 0.15 - 0.08 * zb / h + 0.004')
body = body.replace('col.tube("collision_steel", [0, 0, 0], [0, 0, h], 0.13, 0.13, 6)',
                    'col.tube("collision_steel", [0, 0, 0], [0, 0, h],\n'
                    '             0.16 if kind == "concrete" else 0.13, 0.08 if kind == "concrete" else 0.13, 6)')
assert body != text[start:end]
path.write_text(text[:start] + body + text[end:], encoding='utf-8')
print('Applied fence candidate and concrete-pole silhouette; textures are separate changes.')
