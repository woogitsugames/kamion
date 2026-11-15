"""Small CC BY-SA Commons candidate thumbnails; no retries after HTTP errors."""
import io
import json
import time
from pathlib import Path
import requests
from PIL import Image

base = Path(__file__).resolve().parents[1]
pages = json.loads((base / 'data/candidates-imageinfo.json').read_text(encoding='utf-8-sig'))['query']['pages']
targets = {
    'File:Dom pogrzebowy w Knyszynie.jpg': '03R2-001.jpg',
    'File:Knyszyn Kościelna 2.jpg': '03R2-002.jpg',
    'File:Knyszyn Kościelna 42.jpg': '03R2-003.jpg',
}
(base / 'files').mkdir(exist_ok=True)
log = []
for page in pages.values():
    info = page['imageinfo'][0]
    licence = info['extmetadata']['LicenseShortName']['value']
    if licence not in ('CC0', 'CC BY 3.0', 'CC BY 4.0', 'CC BY-SA 3.0', 'CC BY-SA 4.0'):
        raise RuntimeError('Unexpected licence: ' + licence)
    response = requests.get(info['thumburl'], headers={'User-Agent': 'research-client/1.0 (generic)'}, timeout=40)
    response.raise_for_status()
    picture = Image.open(io.BytesIO(response.content)).convert('RGB')
    picture.thumbnail((800, 800), Image.Resampling.LANCZOS)
    destination = base / 'files' / targets[page['title']]
    picture.save(destination, quality=90)
    log.append({'title': page['title'], 'source_thumbnail': info['thumburl'], 'file': str(destination.relative_to(base)), 'size_px': list(picture.size), 'bytes_received': len(response.content), 'licence': licence})
    print(page['title'], picture.size)
    time.sleep(1)
(base / 'data/download-log.json').write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
