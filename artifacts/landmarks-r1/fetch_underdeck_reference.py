"""Small network-only reference fetch, no world generation or shader build."""
from pathlib import Path
import hashlib
import io
import json
import urllib.request
from PIL import Image

ROOT=Path(__file__).resolve().parent
url='https://upload.wikimedia.org/wikipedia/commons/8/8c/7204_May_2021_in_Bia%C5%82ystok.jpg'
target=ROOT/'reference7204-original.jpg'
data=target.read_bytes() if target.exists() else urllib.request.urlopen(
    urllib.request.Request(url,headers={'User-Agent':'kamion-reference-audit/1.0 (CC0 source verification)'}),timeout=30).read()
assert len(data)==10468810
assert hashlib.sha1(data).hexdigest()=='61364bef59ec622ecf0a89e5a4c6e9cf6678504a'
im=Image.open(io.BytesIO(data))
assert im.size==(5520,3680)
if not target.exists(): target.write_bytes(data)
(ROOT/'reference7204-original-source.json').write_text(json.dumps({
    'title':'7204 May 2021 in Białystok.jpg','author':'Rakoon','license':'CC0 1.0 Universal',
    'page':'https://commons.wikimedia.org/wiki/File:7204_May_2021_in_Bia%C5%82ystok.jpg',
    'url':url,'size':im.size,'bytes':len(data),'sha1_commons':hashlib.sha1(data).hexdigest(),
    'sha256':hashlib.sha256(data).hexdigest(),'capture_date_commons':'2021-05-03 12:34:33',
    'purpose':'native reference details and ROI analysis; reference junction untouched'
},indent=2,ensure_ascii=False),encoding='utf-8')
print('Verified original:',im.size,len(data),'bytes')
