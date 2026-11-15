"""Fetch imageinfo (url, thumb 1600, extmetadata, sha1) for Commons titles listed in a text file.
Usage: commons_info.py titles.txt out.json"""
import json, sys, subprocess, time, urllib.parse
UA = 'research-client/1.0 (generic)'
titles = [l.strip() for l in open(sys.argv[1]) if l.strip()]
out = {}
try:
    out = json.load(open(sys.argv[2]))
except Exception:
    pass
todo = [t for t in titles if t not in out]
for i in range(0, len(todo), 20):
    batch = todo[i:i + 20]
    q = urllib.parse.urlencode({'action': 'query', 'format': 'json', 'prop': 'imageinfo|coordinates',
                                'iiprop': 'url|sha1|size|extmetadata|timestamp', 'iiurlwidth': '1600',
                                'colimit': 'max', 'coprop': 'type|dim', 'coprimary': 'all',
                                'titles': '|'.join(batch)})
    for k in range(8):
        r = subprocess.run(['curl', '-sS', '-m', '90', '-A', UA, 'https://commons.wikimedia.org/w/api.php?' + q],
                           capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
            d['query']
            break
        except Exception:
            print('retry', r.stdout[:60], file=sys.stderr)
            time.sleep(20 * (k + 1))
    for p in d['query']['pages'].values():
        out[p['title']] = p
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    time.sleep(6)
print(len(out))
