"""Lista i pobranie załączników postępowania z miastobialystok.ezamawiajacy.pl (publiczne, bez logowania).
Użycie: ezam.py <tools_dir> <notice_id> <outdir> [substring_nazwy ...]"""
import sys, re, os, html, http.cookiejar, urllib.request, hashlib
UA = 'research-client/1.0 (generic)'
nid, outdir = sys.argv[2], sys.argv[3]
pats = [p.lower() for p in sys.argv[4:]]
os.makedirs(outdir, exist_ok=True)
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', UA)]
base = 'https://miastobialystok.ezamawiajacy.pl'
s = op.open(base + '/pn/miastobialystok/demand/notice/public/%s/details' % nid, timeout=120).read().decode('utf-8', 'replace')
open(os.path.join(outdir, 'details.html'), 'w').write(s)
for r in re.split(r'<tr', s):
    m = re.search(r"downloadPostUrl: '(/repository/download/[0-9A-Za-z]+)'", r)
    if not m:
        continue
    t = re.sub(r'<script.*?</script>', '', r, flags=re.S)
    t = html.unescape(re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', t))).strip()
    t = t.split('>', 1)[-1].strip()
    print(m.group(1), t[:120])
    if pats and any(p in t.lower() for p in pats):
        name = re.split(r' \d{4}-\d\d-\d\d ', t)[0].strip()
        fn = os.path.join(outdir, re.sub(r'[^\w.\- ]', '_', name))
        b = op.open(urllib.request.Request(base + m.group(1), data=b'', method='POST'), timeout=180).read()
        open(fn, 'wb').write(b)
        print('  -> saved', fn, len(b), hashlib.sha256(b).hexdigest())
