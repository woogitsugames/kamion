"""Commons API zwraca HTTP 429 (2026-11-15) — odczyt stron kategorii HTML „<Miesiąc> <Rok> in Białystok”,
wybór plików z czasem w nazwie (YYYYMMDD HHMMSS), wysokość Słońca dla środka miasta (czas z nazwy = lokalny).
Zapis kandydatów (sun < -6) do JSON."""
import sys, re, json, time, html, urllib.parse, datetime
sys.path.insert(0, sys.argv[1])
from httpc import get  # noqa
import sun  # noqa
out = sys.argv[2]
years = range(2019, 2027)
months = ['January', 'February', 'March', 'October', 'November', 'December']
cands = {}
for y in years:
    for m in months:
        cat = 'Category:%s %d in Białystok' % (m, y)
        url = 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(cat.replace(' ', '_'))
        frm = None
        for page in range(6):
            u = url + ('?filefrom=' + urllib.parse.quote(frm) if frm else '')
            try:
                s = get(u, tries=1).decode('utf-8', 'replace')
            except Exception as e:  # noqa
                print('fail', cat, e, file=sys.stderr)
                break
            names = set(html.unescape(urllib.parse.unquote(x)) for x in re.findall(r'href="/wiki/(File:[^"#?]+)"', s))
            for n in names:
                mm = re.search(r'(20\d\d)(\d\d)(\d\d)[ _](\d\d)(\d\d)(\d\d)', n)
                if not mm:
                    continue
                try:
                    loc = datetime.datetime(*map(int, mm.groups()))
                    el = sun.elevation_local(loc)[0]
                except Exception:  # noqa
                    continue
                if el < -6:
                    cands[n.replace('_', ' ')] = {'title': n.replace('_', ' '), 'cat': cat, 'local': loc.isoformat(), 'sun_el': round(el, 1)}
            nxt = re.search(r'filefrom=([^"&#]+)[^"]*"[^>]*>next page', s)
            if not nxt:
                break
            frm = html.unescape(urllib.parse.unquote(nxt.group(1)))
            time.sleep(1)
        print(cat, len(cands), file=sys.stderr)
        time.sleep(1)
json.dump(sorted(cands.values(), key=lambda c: c['title']), open(out, 'w'), ensure_ascii=False, indent=0)
print(len(cands))
