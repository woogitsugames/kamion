"""ADR 0140: SBS review pairs (photo | render, <= 960 px) and a world-freshness preflight.

  preflight  - refuse to render when the Unity-imported world or the derived GLBs are stale against the committed
               world manifest (ADR 0140 found a worktree whose Data/raw/derived still had the pre-0127 16 m portal).
  pairs      - photo | render (or photo | before over photo | after) per SBS camera, attributed (CC BY-SA), <= 960 px.

Light work (PIL on ~42 images); no heavy slot needed. Renders come from scripts/sbs-gate3.ps1 -RenderOnly."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
REGION = 'bialystok-industrial-c'
MAX_W = 960


def _sha(path: Path, normalise_eol: bool = False) -> str:
    data = path.read_bytes()
    if normalise_eol:
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


def preflight(root: Path = ROOT, region: str = REGION) -> list[str]:
    """Return a list of problems (empty = world on disk matches the committed manifest and the Unity import)."""
    problems = []
    manifest_path = root / f'Data/Regions/{region}/generated/world_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    newest = 0.0
    for chunk in manifest['chunks']:
        f = root / chunk['file']
        if not f.exists():
            problems.append(f'missing derived chunk {chunk["file"]}')
            continue
        if f.stat().st_size != chunk['bytes']:
            problems.append(f'derived chunk {f.name}: {f.stat().st_size} B on disk, manifest {chunk["bytes"]} B '
                            '(Data/raw/derived is from another build: run build_world or copy the matching derived world)')
        newest = max(newest, f.stat().st_mtime)
    for name, digest in manifest.get('sources_sha256', {}).items():
        if name == 'overrides.yaml':
            f = root / f'Data/Regions/{region}/overrides.yaml'
            if f.exists() and digest not in (_sha(f), _sha(f, True)):
                problems.append('overrides.yaml changed after the committed world build (world_manifest sources_sha256)')
    instances = root / f'game/Assets/_Generated/World/{region}/Instances.asset'
    if not instances.exists():
        problems.append(f'no Unity import: {instances.relative_to(root)} (run scripts/import-region.ps1)')
    elif newest and instances.stat().st_mtime + 1 < newest:
        problems.append('Unity import older than the derived chunks (run scripts/import-region.ps1 -SkipCopy)')
    return problems


def _font(size: int):
    for name in ('arial.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _label(im: Image.Image, text: str, font) -> None:
    d = ImageDraw.Draw(im, 'RGBA')
    box = d.textbbox((4, 3), text, font=font)
    d.rectangle((box[0] - 3, box[1] - 2, box[2] + 3, box[3] + 2), fill=(0, 0, 0, 160))
    d.text((4, 3), text, fill=(255, 255, 255, 255), font=font)


def _fit(path: Path, w: int, h: int) -> Image.Image:
    return Image.open(path).convert('RGB').resize((w, h), Image.LANCZOS)


def compose_pairs(renders: Path, out: Path, before: Path | None = None, segment: str | None = None,
                  cameras: list[str] | None = None, label: str = 'render', before_label: str = 'before',
                  width: int = MAX_W, root: Path = ROOT, region: str = REGION) -> list[Path]:
    if width > MAX_W:
        raise ValueError(f'pair width {width} > {MAX_W}')
    refs = json.loads((root / f'Data/Regions/{region}/sbs_references.json').read_text(encoding='utf-8'))['references']
    font = _font(13)
    out.mkdir(parents=True, exist_ok=True)
    half = width // 2
    written, missing = [], []
    for r in refs:
        cam = r['camera']
        if segment and r.get('segment') != segment:
            continue
        if cameras and not any(c in cam for c in cameras):
            continue
        photo = root / (r.get('comparison_photo') or r['photo'])
        after = renders / f'{cam}.png'
        prior = before / f'{cam}.png' if before else None
        if not photo.exists() or not after.exists() or (prior is not None and not prior.exists()):
            missing.append(cam)
            continue
        h = round(half * r['height'] / r['width'])
        credit = f"{r.get('author', '?')} {r.get('captured_at', '')} {r.get('license', '')} ({r.get('source_id', '')})"
        p = _fit(photo, half, h); _label(p, 'photo ' + credit, font)
        a = _fit(after, half, h); _label(a, f'{label} {cam}', font)
        rows = [(p, a)]
        if prior is not None:
            b = _fit(prior, half, h); _label(b, f'{before_label} {cam}', font)
            p2 = _fit(photo, half, h)
            rows = [(p, b), (p2, a)]
        sheet = Image.new('RGB', (width, h * len(rows)))
        for i, (left, right) in enumerate(rows):
            sheet.paste(left, (0, i * h)); sheet.paste(right, (half, i * h))
        dest = out / f'{cam}.jpg'
        sheet.save(dest, quality=88)
        written.append(dest)
    if missing:
        print(f'pairs: {len(missing)} cameras without photo/render: {", ".join(missing)}', file=sys.stderr)
    return written


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('preflight')
    p = sub.add_parser('pairs')
    p.add_argument('--renders', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--before', type=Path)
    p.add_argument('--segment')
    p.add_argument('--cameras', help='comma-separated id substrings')
    p.add_argument('--label', default='render')
    p.add_argument('--before-label', default='before')
    p.add_argument('--require-all', action='store_true', help='exit 1 if any reference has no pair')
    a = ap.parse_args(argv)
    if a.cmd == 'preflight':
        problems = preflight()
        for line in problems:
            print('STALE:', line)
        print('preflight', 'FAIL' if problems else 'OK')
        return 1 if problems else 0
    cams = a.cameras.split(',') if a.cameras else None
    written = compose_pairs(a.renders, a.output, a.before, a.segment, cams, a.label, a.before_label)
    print(f'{len(written)} pairs -> {a.output}')
    if a.require_all and not a.segment and not cams:
        n = len(json.loads((ROOT / f'Data/Regions/{REGION}/sbs_references.json').read_text(encoding='utf-8'))['references'])
        if len(written) != n:
            return 1
    return 0 if written else 1


if __name__ == '__main__':
    sys.exit(main())
