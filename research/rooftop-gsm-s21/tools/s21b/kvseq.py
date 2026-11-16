import json, sys, urllib.request, time, math
UA = {'User-Agent': 'research-client/1.0 (generic)'}
seq = sys.argv[1]
out = sys.argv[2]
allp = []
page = 1
while True:
    url = f'https://api.kartaview.org/2.0/photo/?sequenceId={seq}&itemsPerPage=100&page={page}'
    j = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read())
    d = j['result']['data']
    allp += [{k: p.get(k) for k in ('id', 'lat', 'lng', 'heading', 'shotDate', 'sequenceIndex', 'fileurlProc', 'fileurlLTh', 'imageProcUrl', 'width', 'height', 'fieldOfView', 'projection')} for p in d]
    sys.stderr.write(f'{page} {len(d)} {len(allp)}\n')
    if not j['result'].get('hasMoreData') or not d:
        break
    page += 1
    time.sleep(1)
json.dump(allp, open(out, 'w'))
