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

path = root / 'tools/worldgen/streetscape/furniture_textures.py'
text = path.read_text(encoding='utf-8')
old = 'rgb = np.repeat((245 * (1 + 0.3 * (ratio - 1)))[..., None], 3, axis=2)'
assert old in text
text = text.replace(old, '''# ADR0120: retain concrete scan relief instead of compressing it to nearly white.
    level, grain = (228, 1.05) if concrete else (245, 0.3)
    rgb = np.repeat((level * (1 + grain * (ratio - 1)))[..., None], 3, axis=2)''')
text = text.replace('(0.22 if concrete else 0.30)', '(0.65 if concrete else 0.30)')
old = '    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")'
assert old in text
text = text.replace(old, '''    if concrete:
        # Dirt runs below the two steel arm collars; no uniform all-over noise.
        metres = z * height
        runoff = np.zeros((h, w))
        for collar, sector in ((7.6, 0.22), (8.3, 0.73)):
            below = collar - metres
            streak = np.exp(-((u-sector) / 0.055) ** 2)
            streak = streak * np.clip(below / 0.12, 0, 1) * np.clip(1-below / 2.6, 0, 1)
            runoff = np.maximum(runoff, streak * 0.28)
        rgb = rgb * (1-runoff[..., None]) + np.array([125, 117, 99]) * runoff[..., None]
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")''')
path.write_text(text, encoding='utf-8')

path = root / 'tools/worldgen/streetscape/signs.py'
text = path.read_text(encoding='utf-8')
start = text.index('def plate_back(')
end = text.index('\ndef digits_atlas(', start)
body = text[start:end]
old = '    a = np.full((n, n, 1), 255.0)'
assert old in body
body = body.replace(old, '''    # ADR0120: aluminium oxidises; brown runoff comes only from steel fasteners.
    # Clamp heights match props.plate; marks stay local instead of rusting the whole disc.
    xx = np.linspace(0, 1, n)[None, :]
    runoff = np.zeros((n, n))
    for mount in (0.28, 0.78):
        below = yy - mount
        for bolt in (0.40, 0.60):
            width = 0.009 + 0.014 * np.clip(below / 0.2, 0, 1)
            mark = np.exp(-((xx-bolt) / width) ** 2)
            mark *= np.clip(below / 0.012, 0, 1) * np.clip(1-below / 0.22, 0, 1)
            runoff = np.maximum(runoff, mark * 0.68)
    img = img * (1-runoff[..., None]) + np.array([116, 78, 47]) * runoff[..., None]
    a = np.full((n, n, 1), 255.0)''')
path.write_text(text[:start] + body + text[end:], encoding='utf-8')
print('Applied fence, concrete pole and localised furniture/sign wear; no shader changes.')
