#!/usr/bin/env python3
"""M65: sklada manifest.csv z inventory.json + crossings.json + data/* (odczyty wpisane recznie po ogledzinach).
Uruchom: python3 -I tools/build_manifest.py"""
import csv, json, math, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools')); sys.path.insert(0, os.path.join(HERE, 'data'))
sys.dont_write_bytecode = True
from geo import to2180
import observations as O
import frame_notes as FN
import documents as DOC

ACCESS = '2026-11-14'
ORTO_DATE = '2025-04-18 albo 2024-03-30 (oba naloty 5 cm RGB pokrywają punkt wg WFS Skorowidze; WMS nie podaje arkusza)'
ORTO_LIC = 'GUGiK — dane publiczne, bezpłatne (art. 40a ust. 2 pkt 1 PGiK); referencja, nie tekstura'
OSM_LIC = 'ODbL 1.0 (© autorzy OpenStreetMap)'
COLS = ['id', 'kategoria', 'region', 'way_id', 'tagi_osm', 'długość_m', 'szerokość', 'jednostka', 'lat', 'lon', 'kierunek_deg',
        'droga_równoległa_way_id', 'odległość_do_osi_jezdni_m', 'data_zdjęcia', 'sezon', 'pora_dnia', 'opis_co_widać', 'url_źródła',
        'licencja', 'autor', 'data_dostępu', 'status', 'uwagi', 'url_pliku', 'sha256']

def J(name):
    return json.load(open(os.path.join(HERE, name), encoding='utf-8'))

def fmt(v):
    return ('%.2f' % v).rstrip('0').rstrip('.').replace('.', ',') if isinstance(v, float) else str(v)

def main():
    inv = J('inventory.json'); ways = inv['ways']; osm_base = inv['osm_base']
    cross = J('crossings.json')
    tr = {}
    for t in J('data/ortho_transects.json'):
        tr.setdefault(t['way_id'], []).append(t)
    cc = {c['node_id']: c for c in J('data/ortho_crossings.json')}
    dw = {c['node_id']: c for c in J('data/ortho_driveways.json')}
    cl = {c['label']: c for c in J('data/ortho_clusters.json')}
    street = J('data/street_frames.json')
    commons = J('data/commons_frames.json') if os.path.exists(os.path.join(HERE, 'data/commons_frames.json')) else []
    raw = J('overpass-result.json')
    segs = []
    for w in raw['elements']:
        if w['type'] == 'way' and any(w['id'] == r['way_id'] for r in ways):
            xy = [to2180(g['lat'], g['lon']) for g in w['geometry']]
            segs += [(w['id'], xy[i], xy[i + 1]) for i in range(len(xy) - 1)]

    def nearest_way(lat, lon):
        p = to2180(lat, lon); best = (1e9, None)
        for wid, a, b in segs:
            dx, dy = b[0] - a[0], b[1] - a[1]; l2 = dx * dx + dy * dy
            t = 0 if l2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
            d = math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
            if d < best[0]:
                best = (d, wid)
        return best

    rows = []
    def add(**k):
        r = {c: '' for c in COLS}; r.update(k); r['id'] = 'C65-%03d' % (len(rows) + 1); r['data_dostępu'] = ACCESS
        rows.append(r); return r

    # kadry uliczne -> przypisanie do odcinkow (do zaznaczenia "na zdjeciu")
    on_photo = {}
    frames = []
    for f in street + commons:
        d, wid = nearest_way(f['lat'], f['lon'])
        f['_d'] = d; f['_way'] = wid; frames.append(f)
        if d <= 25:
            on_photo.setdefault(wid, []).append(f['key'])
    for k, wid in (('P11-001', 212811563), ('P11-056', 538810153)):
        if k not in on_photo.get(wid, []):
            on_photo.setdefault(wid, []).append(k + ' (wg pozycji z manifestu p11)')

    # 1. odcinki
    way_row = {}
    for w in ways:
        t = w['tags']; o = O.W.get(w['way_id']); par = w['parallel'] or {}
        ts = tr.get(w['way_id'], [])
        missing = [k for k in ('surface', 'colour', 'width', 'segregated', 'oneway', 'lit', 'smoothness') if k not in t]
        uw = ['koniec A: %.7f, %.7f; koniec B: %.7f, %.7f' % (w['start'][0], w['start'][1], w['end'][0], w['end'][1]),
              'długość w kaflu regionu: %s m' % fmt(w['length_in_tile_m']),
              'brak tagu: ' + ', '.join(missing) if missing else 'komplet tagów kontrolnych']
        if par:
            uw.append('jezdnia równoległa: %s %s (way %d), odległość osi DDR–oś najbliższej jezdni: mediana %s m (min %s, max %s), udział próbek %s'
                      % (par['highway'], par['name'] or '(bez nazwy)', par['way_id'], fmt(par['dist_median_m']), fmt(par['dist_min_m']), fmt(par['dist_max_m']), fmt(par['share'])))
        else:
            uw.append('brak jezdni równoległej w 40 m (±30°)')
        if w['way_id'] in on_photo:
            uw.append('NA ZDJĘCIU: ' + ', '.join(on_photo[w['way_id']]))
        if o:
            lab, kol, sz, ch, zi, ukl, note = o
            opis = 'Ortofotomapa (przekrój %s): nawierzchnia — %s.' % (lab, kol)
            if sz is not None: opis += ' Szerokość DDR/ciągu ok. %s m.' % fmt(sz)
            if ch is not None: opis += ' Chodnik obok ok. %s m.' % fmt(ch)
            if zi is not None: opis += ' Pas zieleni przy jezdni ok. %s m.' % fmt(zi) if zi > 0 else ' Bez pasa zieleni przy jezdni.'
            opis += ' Układ: %s.' % ukl
            if note: opis += ' ' + note[0].upper() + note[1:] + '.'
            red = kol in (O.CB, O.CK) or 'czerwon' in kol and 'przejazd' not in kol
            if red:
                uw.append('ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=%s)' % t.get('surface', 'brak tagu'))
            if kol == O.SZ and t.get('surface') in ('paved', None):
                uw.append('OSM surface=%s — orto pokazuje asfalt' % t.get('surface', 'brak tagu'))
            szer = fmt(sz) if sz is not None else 'brak tagu width; z orto nieczytelne'
            status = 'SOURCED (OSM %s); szerokość i kolor ESTIMATED (orto 5 cm, linijka 1 m, ±0,3 m)' % osm_base[:10] if sz is not None else 'SOURCED (OSM %s); szerokość UNVERIFIED' % osm_base[:10]
        else:
            opis = 'Odcinek nieoglądany na ortofotomapie (krótki łącznik) — tylko dane OSM.'
            szer = 'brak tagu width; nie mierzono'; status = 'SOURCED (OSM %s); szerokość i kolor UNVERIFIED' % osm_base[:10]
        r = add(kategoria='odcinek', region=w['region'], way_id=w['way_id'], tagi_osm=json.dumps(t, ensure_ascii=False, sort_keys=True),
                długość_m=fmt(w['length_m']), szerokość=szer, jednostka='m', lat='%.6f' % w['start'][0], lon='%.6f' % w['start'][1],
                kierunek_deg='nie dotyczy', droga_równoległa_way_id=par.get('way_id', ''), odległość_do_osi_jezdni_m=fmt(par['dist_median_m']) if par else '',
                data_zdjęcia=ORTO_DATE if ts else '', sezon='wiosna' if ts else '', pora_dnia='dzień' if ts else '', opis_co_widać=opis,
                url_źródła='https://www.openstreetmap.org/way/%d' % w['way_id'], licencja=OSM_LIC + ('; wycinek: ' + ORTO_LIC if ts else ''),
                autor='autorzy OpenStreetMap' + ('; GUGiK' if ts else ''), status=status, uwagi='; '.join(uw),
                url_pliku=ts[0]['url'] if ts else '', sha256=ts[0]['sha256'] if ts else '')
        way_row[w['way_id']] = r['id']
        for extra in ts[1:]:
            add(kategoria='kadr', region=w['region'], way_id=w['way_id'], lat='%.6f' % extra['lat'], lon='%.6f' % extra['lon'],
                kierunek_deg='nadir (obraz z WMS: północ u góry)', data_zdjęcia=ORTO_DATE, sezon='wiosna', pora_dnia='dzień',
                opis_co_widać='Drugi przekrój odcinka %d (%s): %s' % (w['way_id'], extra['label'], o[5]),
                url_źródła='https://www.openstreetmap.org/way/%d' % w['way_id'], licencja=ORTO_LIC, autor='GUGiK',
                status='ESTIMATED (orto 5 cm)', uwagi='wycinek 44×44 m; patrz wiersz ' + r['id'], url_pliku=extra['url'], sha256=extra['sha256'])

    # 2. przejazdy przez jezdnie + 3. wjazdy
    for kind in ('jezdnia', 'wjazd'):
        for c in cross:
            if c['kind'] != kind:
                continue
            nid = c['node_id']; rd = c['roads'][0]; nt = c['node_tags']
            sig = {'traffic_signals': 'jest (OSM crossing=traffic_signals)', 'uncontrolled': 'brak (OSM crossing=uncontrolled)',
                   'unmarked': 'brak (OSM crossing=unmarked)', 'marked': 'brak (OSM crossing=marked)'}.get(nt.get('crossing'), 'brak tagu crossing w OSM')
            if nt.get('crossing:signals') == 'no': sig = 'brak (OSM crossing:signals=no)'
            uw = ['jezdnia: %s' % '; '.join('%s %s (way %d%s)' % (x['highway'], x['name'] or '(bez nazwy)', x['way_id'], ', lanes=' + x['lanes'] if x['lanes'] else '') for x in c['roads']),
                  'azymut osi jezdni w węźle: %d°' % c['road_bearing_deg'], 'DDR: ' + ', '.join('way %d' % x['way_id'] for x in c['cycle_ways']),
                  'sygnalizacja: ' + sig, 'tagi węzła: ' + (json.dumps(nt, ensure_ascii=False, sort_keys=True) if nt else 'brak tagów'),
                  'znaki pionowe (C-13/C-16, D-6b, D-6a): UNVERIFIED — z ortofotomapy nieczytelne']
            szer = ''; opis = ''; status = ''; url = ''; sha = ''; lic = OSM_LIC; aut = 'autorzy OpenStreetMap'; dz = ''
            if kind == 'jezdnia':
                if nid in O.X:
                    lab, red, s, zeb, wys, note = O.X[nid]; crop = cc[nid]
                    opis = 'Ortofotomapa (wycinek %s): %s. ' % (lab, {'tak': 'przejazd z CZERWONYM polem między liniami P-11', 'nie': 'przejazd wyznaczony TYLKO białymi liniami P-11 (kwadraty), bez czerwonej powierzchni',
                                                                         'brak oznakowania': 'BRAK oznakowania przejazdu dla rowerzystów'}[red])
                    if s is not None: opis += 'Szerokość przejazdu (między zewnętrznymi krawędziami linii P-11 / do krawędzi zebry) ok. %s m. ' % fmt(s)
                    if zeb is not None: opis += 'Przejście dla pieszych obok ok. %s m. ' % fmt(zeb)
                    opis += 'Wyspa/pas dzielący: %s. %s' % (wys, (note[0].upper() + note[1:] + '.') if note else '')
                    szer = fmt(s) if s is not None else 'nie dotyczy'
                    status = 'SOURCED (OSM %s: pozycja, tagi); czerwień/szerokość ESTIMATED (orto 5 cm; profil jasności ±0,15 m, przejazdy ukośne ±0,5 m)' % osm_base[:10]
                    url, sha, lic, aut, dz = crop['url'], crop['sha256'], OSM_LIC + '; wycinek: ' + ORTO_LIC, 'autorzy OpenStreetMap; GUGiK', ORTO_DATE
                    if red == 'tak' and nt:
                        uw.append('ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour)')
                    if red == 'brak oznakowania' and nt.get('bicycle') == 'yes':
                        uw.append('ROZBIEŻNOŚĆ OSM↔orto: bicycle=yes, a na ortofotomapie brak linii P-11')
                elif nid in O.XC:
                    lab, red, note = O.XC[nid]; crop = cl[lab]
                    opis = 'Ortofotomapa (wycinek zbiorczy skrzyżowania %s, bez pomiaru): %s. %s.' % (lab, {'tak': 'przejazd z CZERWONYM polem', 'nie': 'przejazd tylko z białych linii P-11, bez czerwieni', 'brak oznakowania': 'BRAK oznakowania przejazdu'}[red], note[0].upper() + note[1:])
                    szer = 'UNVERIFIED'; status = 'SOURCED (OSM %s); czerwień ESTIMATED (orto, wycinek zbiorczy — przypisanie do węzła z położenia)' % osm_base[:10]
                    url, sha, lic, aut, dz = crop['url'], crop['sha256'], OSM_LIC + '; wycinek: ' + ORTO_LIC, 'autorzy OpenStreetMap; GUGiK', ORTO_DATE
                else:
                    opis = 'Przecięcie DDR/ciągu z jezdnią wg wspólnego węzła OSM — nieoglądane na ortofotomapie.'
                    szer = 'UNVERIFIED'; status = 'SOURCED (OSM %s); oznakowanie UNVERIFIED' % osm_base[:10]
                if not c['through']:
                    uw.append('DDR kończy się w tym węźle (włączenie do jezdni, nie przejazd przelotowy)')
            else:
                if nid in O.D:
                    lab, note = O.D[nid]; crop = dw[nid]
                    opis = 'WJAZD (highway=service). Ortofotomapa (wycinek %s): %s.' % (lab, note)
                    status = 'SOURCED (OSM %s); ciągłość nawierzchni ESTIMATED (orto 5 cm)' % osm_base[:10]
                    url, sha, lic, aut, dz = crop['url'], crop['sha256'], OSM_LIC + '; wycinek: ' + ORTO_LIC, 'autorzy OpenStreetMap; GUGiK', ORTO_DATE
                else:
                    opis = 'WJAZD (highway=service%s) przecinający DDR/ciąg wg wspólnego węzła OSM — nieoglądany na ortofotomapie.' % (', service=' + rd['service'] if rd['service'] else '')
                    status = 'SOURCED (OSM %s); ciągłość nawierzchni UNVERIFIED' % osm_base[:10]
                szer = 'nie mierzono'
            add(kategoria='przejazd', region=c['region'], way_id=rd['way_id'], tagi_osm=json.dumps(nt, ensure_ascii=False, sort_keys=True) if nt else 'brak tagów',
                szerokość=szer, jednostka='m', lat='%.6f' % c['lat'], lon='%.6f' % c['lon'], kierunek_deg='nie dotyczy',
                droga_równoległa_way_id=c['cycle_ways'][0]['way_id'], data_zdjęcia=dz, sezon='wiosna' if dz else '', pora_dnia='dzień' if dz else '',
                opis_co_widać=opis, url_źródła='https://www.openstreetmap.org/node/%d' % nid, licencja=lic, autor=aut, status=status, uwagi='; '.join(uw),
                url_pliku=url, sha256=sha)

    # 4. nawierzchnia / wymiary z dokumentow i obserwacji
    for d in DOC.ROWS:
        add(kategoria='nawierzchnia', region=d['region'], szerokość=d.get('wartość', ''), jednostka=d.get('jednostka', ''), opis_co_widać=d['opis'],
            url_źródła=d['url'], licencja=d['licencja'], autor=d['autor'], status=d['status'], uwagi=d['uwagi'],
            url_pliku=d.get('url_pliku', ''), sha256=d.get('sha256', ''), way_id=d.get('way_id', ''))

    # 5. kadry uliczne (Commons dopisane po audycie -> na koncu, zeby nie zmieniac id wczesniejszych wierszy)
    def street_rows(fl):
      for f in fl:
          pd, sez, prz, opis = FN.STREET[f['key']]
          w = next(x for x in ways if x['way_id'] == f['_way'])
          uw = ['najbliższy odcinek DDR: way %d (%s), odległość kamery od osi %.1f m%s' % (f['_way'], way_row[f['_way']], f['_d'], '' if f['_d'] <= 25 else ' — POZA regułą 25 m, kadr kontekstowy'),
                'przejazd rowerowy w kadrze: ' + prz,
                'kierunek: ' + {'panoramax': 'view:azimuth z API Panoramax (geograficzny wg API; zgodny z układem estakady/jezdni w kadrze)',
                                'kartaview': 'pole heading z API KartaView (kurs GPS pojazdu)', 'commons': f.get('heading_method', 'UNVERIFIED')}[f['src']],
                'CC BY-SA — referencja, nie tekstura' if 'SA' in f['license'].upper() else 'licencja swobodna']
          if f.get('note'): uw.append(f['note'])
          add(kategoria='kadr', region=w['region'], way_id=f['_way'], tagi_osm=json.dumps(w['tags'], ensure_ascii=False, sort_keys=True),
              lat='%.6f' % f['lat'], lon='%.6f' % f['lon'], kierunek_deg=('%.0f' % f['heading']) if f.get('heading') is not None else 'UNVERIFIED',
              droga_równoległa_way_id=(w['parallel'] or {}).get('way_id', ''), odległość_do_osi_jezdni_m='',
              data_zdjęcia=f['datetime'][:10], sezon=sez, pora_dnia=pd, opis_co_widać=opis, url_źródła=f['page'], licencja=f['license'].replace('CC-BY-SA-4.0', 'CC BY-SA 4.0'),
              autor=f['author'], status='SOURCED (kadr obejrzany)', uwagi='; '.join(uw), url_pliku=f['url'], sha256=f['sha256'])

    street_rows([f for f in frames if f['src'] != 'commons'])

    # 6. kadry z ortofotomapy (wycinki zbiorcze skrzyzowan)
    for lab in sorted(FN.ORTHO):
        c = cl[lab]
        from geo import from2180
        lat, lon = from2180(c['cx'], c['cy'])
        add(kategoria='kadr', region=c['region'], lat='%.6f' % lat, lon='%.6f' % lon, kierunek_deg='nadir (północ u góry)', data_zdjęcia=ORTO_DATE,
            sezon='wiosna', pora_dnia='dzień', opis_co_widać='Ortofotomapa, wycinek %d×%d m (%s): %s' % (c['size'], c['size'], lab, FN.ORTHO[lab]),
            url_źródła='https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution', licencja=ORTO_LIC, autor='GUGiK',
            status='SOURCED (kadr obejrzany)', uwagi='węzły OSM przejazdów w kadrze: ' + ', '.join(str(n) for n in c['nodes']) + '; jezdnie: ' + ', '.join(c['roads'])
            + ''.join('; TEN SAM PLIK (sha256) co wiersz ' + r0['id'] for r0 in rows if r0['sha256'] == c['sha256']),
            url_pliku=c['url'], sha256=c['sha256'])

    street_rows([f for f in frames if f['src'] == 'commons'])

    with open(os.path.join(HERE, 'manifest.csv'), 'w', encoding='utf-8', newline='') as f:
        wr = csv.DictWriter(f, COLS); wr.writeheader(); wr.writerows(rows)
    from collections import Counter
    print(len(rows), Counter((r['kategoria'], r['region']) for r in rows))
    print('pliki:', len({r['url_pliku'] for r in rows if r['url_pliku']}))

if __name__ == '__main__':
    main()
