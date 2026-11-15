"""Generuje frames.json (wiersze kadrów do manifestu). Opisy = to, co widać na obejrzanym obrazie (≤ 960 px; wycinki tam, gdzie zaznaczono).
Odpowiedzi a–f: a) barwa, b) pula i ułamek jezdni, c) ciemne przerwy, d) halo, e) mokra nawierzchnia, f) osobne światło chodnika/DDR."""
import json, os, hashlib, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
pnx = json.load(open(os.path.join(HERE, 'pnx_meta.json')))
cm = json.load(open(os.path.join(HERE, 'commons_meta.json')))


def sha(fn):
    return hashlib.sha256(open(os.path.join(HERE, 'files', fn), 'rb').read()).hexdigest()


def local(dt):
    u = datetime.datetime.fromisoformat(dt).astimezone(datetime.timezone.utc)
    off = 1 if u.month in (1, 2, 3, 11, 12) or (u.month == 10 and u.day > 25) else 2  # CET/CEST (uproszczenie, daty kadrów poza tygodniami zmiany)
    return (u + datetime.timedelta(hours=off)).strftime('%Y-%m-%d %H:%M') + (' CET' if off == 1 else ' CEST')


out = []


def P(key, kat, ulica, way, el, par, val, opis, frac, halo, status, uw, sun=None):
    i = pnx[key]
    out.append(dict(kategoria=kat, ulica=ulica, way_id=way, element=el, parametr=par, wartość=val, jednostka='' if not sun else '° (wys. Słońca)',
                    lat='%.6f' % i['lat'], lon='%.6f' % i['lon'], kierunek_deg=str(i['azimuth']) + ' (view:azimuth API)',
                    data_godzina=local(i['datetime']) + ' (API: ' + i['datetime'] + ')', opis_co_widać=opis, ułamek_jezdni_oświetlony=frac, halo=halo,
                    url_źródła='https://api.panoramax.xyz/api/collections/%s/items/%s' % (i['collection'], i['id']), licencja='CC BY-SA 4.0 (referencja, nie tekstura)',
                    autor='Panoramax, konto: %s' % i['producer'], status=status, uwagi=uw, plik='files/pnx_%s.jpg' % key, url_pliku=i['hd'],
                    sha256_pliku=sha('pnx_%s.jpg' % key)))


def C(key, ulica, way, val, opis, frac, halo, status, uw):
    m = cm[key]
    t = m['title'][5:]
    dt = '%s-%s-%s %s:%s (czas z nazwy/EXIF, lokalny)' % (t[0:4], t[4:6], t[6:8], t[9:11], t[11:13])
    out.append(dict(kategoria='kadr', ulica=ulica, way_id=way, element='nocny kadr ulicy', parametr='wysokość Słońca (z czasu i środka miasta)', wartość=val,
                    jednostka='°', lat='%.6f' % m['lat'] if m['lat'] else 'UNVERIFIED', lon='%.6f' % m['lon'] if m['lon'] else 'UNVERIFIED',
                    kierunek_deg='UNVERIFIED (brak azymutu w opisie pliku)', data_godzina=dt, opis_co_widać=opis, ułamek_jezdni_oświetlony=frac, halo=halo,
                    url_źródła=m['page'], licencja='CC0', autor='Rakoon (Wikimedia Commons)', status=status, uwagi=uw, plik='files/%s.jpg' % key,
                    url_pliku='upload.wikimedia.org thumb 960px (ścieżka md5, tools/commons_thumbs.py)', sha256_pliku=sha('%s.jpg' % key)))


def F(key, page, author, lic, date, ulica, opis, frac, halo, status, uw, url):
    out.append(dict(kategoria='kadr', ulica=ulica, way_id='UNVERIFIED', element='nocny kadr (Openverse/Flickr)', parametr='wysokość Słońca', wartość='UNVERIFIED (brak godziny)',
                    lat='UNVERIFIED', lon='UNVERIFIED', kierunek_deg='UNVERIFIED', data_godzina=date + ' (Flickr „Taken on”, bez godziny)', opis_co_widać=opis,
                    ułamek_jezdni_oświetlony=frac, halo=halo, url_źródła=page, licencja=lic, autor=author, status=status, uwagi=uw, plik='files/ov_%s.jpg' % key,
                    url_pliku=url, sha256_pliku=sha('ov_%s.jpg' % key)))


# ---------------- nocne kadry ----------------
P('3e13253b', 'kadr', 'Swobodna (osiedle; numer 34 na budynku)', 'UNVERIFIED (poza bbox OSM)', 'zmierzchowy kadr osiedla', 'wysokość Słońca', '-4,4',
  'a) jedna oprawa przy lewej krawędzi (częściowo poza kadrem) świeci ciepło (żółtawo-biało); b) puli na jezdni nie widać — niebo jeszcze jasne, nawierzchnia oświetlona równo światłem nieba; c) nie dotyczy; d) słabe; e) sucho; f) brak osobnego światła chodnika w kadrze; zapalone ok. 1/3 okien bloku',
  'UNVERIFIED', 'słabe', 'VERIFIED_WIZJA', 'przy −4,4° latarnie już świecą (zgodne z C60: −3,1…−5,4°)', sun=True)
P('c1a5e40e', 'kadr', 'Swobodna (parking osiedlowy)', 'UNVERIFIED (poza bbox OSM)', 'latarnia parkowa post-top', 'wysokość Słońca', '-11,8',
  'a) neutralna/zimna biel; b) wokół podstawy słupa jasny krąg na trawie i asfalcie parkingu, jasność maleje płynnie do ok. 1–1,5 wysokości słupa; c) w głębi dwie kolejne lampy post-top (białe) z ciemniejszym pasem trawy pomiędzy; d) SILNE — duża poświata wokół klosza i różowo-zielone odblaski obiektywu nad lampą; e) sucho; f) to oprawa parkingu/chodnika (nie drogowa)',
  'nie dotyczy (parking)', 'silne (promień poświaty ok. 0,1–0,15 wys. słupa; odblaski obiektywu)', 'VERIFIED_WIZJA', 'typ T5 post-top; wys. słupa ok. 4–5 m ESTIMATED (proporcja do samochodu osobowego ~1,5 m wys. w tle — niska pewność)', sun=True)
P('f4ead989', 'kadr', 'Swobodna (zieleń osiedlowa)', 'UNVERIFIED (poza bbox OSM)', 'trawnik oświetlony latarnią', 'wysokość Słońca', '-11,2',
  'a) neutralna biel na trawie; b) oprawy w kadrze brak — trawnik jasny, ostry cień młodego drzewka (źródło punktowe z lewej-tyłu); c) nie da się ocenić; d) nie dotyczy; e) sucho; f) nie dotyczy',
  'UNVERIFIED', 'nie dotyczy', 'VERIFIED_WIZJA', 'kadr pomocniczy: barwa światła osiedlowego LED', sun=True)
P('c0c6954b', 'kadr', 'Swobodna (zieleń osiedlowa)', 'UNVERIFIED (poza bbox OSM)', 'trawnik przy słupie latarni', 'wysokość Słońca', '-10,9',
  'a) neutralna biel na trawie (okna w tle ciepłe żółte); b) szary stalowy słup z betonowym fundamentem w kadrze, oprawa poza kadrem; trawnik oświetlony równo w promieniu kilku m; c) brak; d) nie dotyczy; e) sucho; f) nie dotyczy',
  'UNVERIFIED', 'nie dotyczy', 'VERIFIED_WIZJA', 'kadr pomocniczy', sun=True)
P('a68677d0', 'kadr', 'Rondo J. Nowaka-Jeziorańskiego (pod estakadą)', '259439846 (5,3 m)', 'jezdnia ronda o zmierzchu', 'wysokość Słońca', '-15,9 (gdy datetime API = UTC); ok. −7,5 gdy to czas lokalny — sprzeczne, UNVERIFIED',
  'a) w tle dwuramienne latarnie drogowe świecą ciepło pomarańczowo (wygląd sodowy, 2020); pod estakadą ciepłe oprawy sufitowe; b) puli na pierwszym planie nie widać — jezdnia ciemnoszara z białymi liniami; c) nie da się ocenić; d) słabe; e) sucho; f) brak (słup na pierwszym planie to słup bez oprawy w kadrze)',
  '0 (pierwszy plan nieoświetlony przez widoczne oprawy)', 'słabe', 'VERIFIED_WIZJA', 'niebo granatowe z jasnym pasem — bardziej pasuje do −7…−9° niż −16°; godzina niepewna', sun=True)

F('10c97958', 'https://www.flickr.com/photos/28415052@N02/2653184103', 'piszczu (Flickr)', 'CC BY 2.0', '2006-12-30', 'Lipowa (widok z góry na zachód/wschód — kierunek UNVERIFIED)',
  'a) sodowa pomarańczowa (całość); b) jezdnia i chodniki oświetlone CIĄGLE — jaśniejsze miejsca pod oprawami, ale bez ciemnych przerw; c) brak wyraźnych przerw; d) silne — mgiełka, nad ulicą pomarańczowa łuna, oprawy z gwiazdkami; e) nawierzchnia wilgotna, odbicia słabe; f) chodniki oświetlone tymi samymi oprawami; po prawej jednoramienne łukowe oprawy przy krawędzi',
  '≈1 (cała szerokość)', 'silne (mgła)', 'VERIFIED_WIZJA', 'stan 2006 (przed LED); typ T2 po prawej', 'https://live.staticflickr.com/3044/2653184103_93795cd30a_b.jpg')
F('88e3040d', 'https://www.flickr.com/photos/37209452@N02/4372739745', 'Cezary Borysiuk (Flickr)', 'CC BY 2.0', '2010-02-19', 'skrzyżowanie w śródmieściu (nazwa UNVERIFIED)',
  'a) UNVERIFIED — zdjęcie czarno-białe; b) długi czas naświetlania: jasne łukowe pasy na jezdni w głębi to ŚLADY ŚWIATEŁ AUT (poprawka audytu), nie pule; na mokrej jezdni na pierwszym planie odbicia pod jednoramiennymi latarniami; c) mokra jezdnia między odbiciami ciemniejsza; d) „gwiazdy” dyfrakcyjne przysłony — efekt aparatu, nie oprawy; e) TAK, mokra jezdnia, odbicia wydłużone w stronę aparatu; f) chodniki pod śniegiem jasne od tych samych latarń',
  '≈0,5–1 (smugi odbić, nie pule)', 'nieocenialne (filtr/dyfrakcja)', 'VERIFIED_WIZJA', 'latarnie jednoramienne i dwuramienne na wysokich słupach; barwa nieznana', 'https://live.staticflickr.com/4011/4372739745_d4f8effaf9_b.jpg')
F('10510274', 'https://www.flickr.com/photos/28415052@N02/2653183441', 'piszczu (Flickr)', 'CC BY 2.0', '2006-12-26', 'ul. Kilińskiego przy bramie Pałacu Branickich (wg tytułu i obrazu; ulica UNVERIFIED)',
  'a) sodowa żółto-pomarańczowa; b) pojedyncza oprawa na smukłym słupie z krótkim wygiętym ramieniem; nawierzchni pod nią prawie nie widać (ciemny pierwszy plan) — UNVERIFIED; c) nie dotyczy; d) silne promienie (dyfrakcja przysłony) + mała poświata; e) sucho; f) brak',
  'UNVERIFIED', 'średnie (promienie aparatu)', 'VERIFIED_WIZJA', 'typ T2 (wariant krótki); budynek iluminowany', 'https://live.staticflickr.com/3025/2653183441_9c792387a9_b.jpg')
F('ef5f02ef', 'https://www.flickr.com/photos/28668451@N00/3357771560', 'access.denied (Flickr)', 'CC BY-SA 2.0 (referencja)', '2008-12-27', 'Rynek Kościuszki',
  'a) ciepła żółta (przesycona ekspozycja); b) plac oświetlony równo, bez kręgów; c) brak; d) średnie — kule opraw prześwietlone; e) sucho; f) plac pieszy — latarnie ozdobne kandelabrowe z 3–4 kulami na niskich słupach',
  '≈1 (plac)', 'średnie', 'VERIFIED_WIZJA', 'typ T4 (ozdobna wielokulowa)', 'https://live.staticflickr.com/3553/3357771560_aba8aa386e_b.jpg')
F('9e8c0919', 'https://www.flickr.com/photos/37209452@N02/4225459902', 'Cezary Borysiuk (Flickr)', 'CC BY 2.0', '2009-12-28', 'Rynek Kościuszki',
  'a) ciepła żółta (latarnie), kolorowa iluminacja świąteczna; b) śnieg na schodach oświetlony ciepło i dość równo; c) brak; d) słabe-średnie; e) śnieg; f) plac pieszy — latarnie ozdobne kulowe przy pierzei',
  '≈1 (plac)', 'słabe', 'VERIFIED_WIZJA', 'typ T4; iluminacja świąteczna dominuje', 'https://live.staticflickr.com/2715/4225459902_7e81d436b4_b.jpg')
F('e85fe0c9', 'https://www.flickr.com/photos/37209452@N02/4181639418', 'Cezary Borysiuk (Flickr)', 'CC BY 2.0', '2009-12-13', 'panorama miasta z wysoka',
  'a) przeważają ciepłe żółte punkty, nieliczne bielsze; b) pul nie da się wyróżnić; c) nie dotyczy; d) długie pionowe i krzyżowe promienie — filtr gwiaździsty (efekt fotografa); e) UNVERIFIED; f) UNVERIFIED',
  'UNVERIFIED', 'nieocenialne (filtr)', 'VERIFIED_WIZJA', 'tylko barwa ogólna 2009', 'https://live.staticflickr.com/2786/4181639418_2dbfbe3c4f_b.jpg')

C('cm_002', 'Młynowa (wg najbliższej osi OSM)', '299438388 (9,0 m)', '-21,5',
  'a) ciepła pomarańczowa (sodowa) na elewacjach domów i jezdni; b) oprawy w kadrze brak; jezdnia na pierwszym planie oświetlona równo; c) brak widocznych przerw; d) nie dotyczy; e) sucho; f) brak',
  '≈1 w kadrze', 'nie dotyczy', 'VERIFIED_WIZJA', 'stan 2019')
C('cm_014', 'Lipowa', '1094406643 (4,1 m)', '-36,7',
  'a) sodowa pomarańczowa; b) jednoramienne oprawy na łukowych wysięgnikach wzdłuż chodnika i jezdni; nawierzchnia oświetlona ciągle; c) brak wyraźnych przerw; d) SILNE — mgła, wokół każdej oprawy duża poświata; e) TAK, mokra kostka, odbicia; f) chodnik oświetlony tymi samymi oprawami',
  '≈1', 'silne (mgła; promień ok. 0,2–0,3 wys. słupa)', 'VERIFIED_WIZJA', 'stan 2020; halo to efekt mgły, nie cecha oprawy')
C('cm_016', 'Plac NZS (Liniarskiego)', '723184438 (20,0 m)', '-34,1',
  'a) sodowa pomarańczowa; b) smukłe ozdobne słupy z pojedynczym łukowym ramieniem (pastorał) i dekoracją świąteczną; bruk oświetlony równo, bez kręgów; c) brak; d) średnie; e) wilgotny bruk, słabe odbicia; f) plac/chodnik — te same oprawy',
  '≈1', 'średnie', 'VERIFIED_WIZJA', 'typ T3 (ozdobna jednoramienna)')
C('cm_017', 'Lipowa (wg nazwy pliku; najbliższa oś OSM: Waryńskiego 10,5 m)', '40906206 (10,5 m)', '-9,0',
  'a) ciepła żółta (latarnie), białe-niebieskie lampki na drzewach; b) ozdobne latarnie z łukowym ramieniem po lewej; chodnik oświetlony równo; c) brak; d) słabe; e) sucho; f) deptak — chodnik ma te same oprawy',
  '≈1 (chodnik)', 'słabe', 'VERIFIED_WIZJA', 'typ T3; iluminacja świąteczna; plik spoza zbioru C60 (lista frames_meta C60 sprawdzona)')
C('cm_018', 'Rynek Kościuszki', '307638769 (29,1 m — plac)', '-10,0',
  'a) ciepła żółto-biała; b) latarnie ozdobne z dwiema kulami na poprzeczce (T); nawierzchnia placu oświetlona dość równo; c) brak; d) słabe-średnie; e) sucho; f) plac pieszy',
  '≈1 (plac)', 'słabe', 'VERIFIED_WIZJA', 'typ T4; dekoracje świąteczne na drzewach')
C('cm_024', 'Skłodowskiej-Curie (przy DH Central)', '207923562 (38,1 m)', '-13,3',
  'a) ciepła pomarańczowa w tle (latarnie z dekoracjami), witryny białe; b) latarnie w tle, puli nie widać; chodnik oświetlony głównie witrynami; c) nie dotyczy; d) słabe; e) sucho; f) chodnik — światło witryn',
  'UNVERIFIED', 'słabe', 'VERIFIED_WIZJA', 'kadr pomocniczy')
C('cm_kal', 'Kalinowskiego (wg nazwy pliku; najbliższa oś: Grochowa 10,7 m)', '307638766 (10,7 m)', '-15,5',
  'a) ciepła pomarańczowo-żółta; b) płaskie oprawy na jednoramiennych łukowych wysięgnikach przy prawej krawędzi jezdni; jezdnia po prawej oświetlona, w tle jaśniejsza; c) ciemne przerwy niewyraźne; d) słabe; e) sucho; f) chodnik w przebudowie bez własnego światła — oświetlony tylko poświatą',
  'ok. 1 (jezdnia po prawej)', 'słabe', 'VERIFIED_WIZJA', 'typ T2')
C('cm_kra', 'Krakowska', '261468661 (8,7 m)', '-6,7',
  'a) ciepła (elewacje żółtawe od światła ulicy); b) oprawy poza kadrem, jezdnia i chodnik z cienkim śniegiem oświetlone równo; c) nie widać; d) nie dotyczy; e) śnieg/mokro; f) brak; niebo szaro-fioletowe (chmury podświetlone przez miasto)',
  'UNVERIFIED', 'nie dotyczy', 'VERIFIED_WIZJA', 'kadr pomocniczy; łuna pod chmurami')

C('cm_kol', 'Kołłątaja', 'UNVERIFIED (brak GPS w opisie pliku)', '-10,3',
  'a) ciepła żółto-pomarańczowa; b) szereg 5–6 jednoramiennych łukowych latarń przy krawędzi jezdni (płaskie oprawy); na mokrej jezdni w głębi powtarzające się jaśniejsze plamy odbić pod kolejnymi oprawami; jezdnia na pierwszym planie (dalej od opraw) ciemniejsza; c) TAK, umiarkowane — na mokrej jezdni jasność „pulsuje” w rytmie słupów; d) średnie — poświata w opadzie śniegu; e) TAK, mokra jezdnia, odbicia wydłużone; f) chodnik po lewej (śnieg) oświetlony tymi samymi oprawami',
  'ok. 0,6–0,8 (jezdnia po stronie słupów jaśniejsza)', 'średnie (opad)', 'VERIFIED_WIZJA', 'typ T2; najlepszy kadr „pulsowania” jasności (ale na mokrej nawierzchni)')

# ---------------- kadry dzienne do typów opraw ----------------
T1 = 'T1: dwuramienna łukowa (pastorał) w pasie dzielącym, płaskie oprawy'
for k, ul, way, opis in [
    ('b0948023', 'gen. Maczka', '257357907 (3,1 m)', 'jasny (biały/jasnoszary) wysoki słup w pasie dzielącym po lewej, dwa łukowe ramiona w obie strony, płaskie wydłużone oprawy; kolejne 3–4 słupy w szeregu; po prawej ekran akustyczny'),
    ('9c0cc814', 'gen. Maczka', '249740766 (0,1 m)', 'jak b0948023: szereg dwuramiennych latarni w pasie dzielącym, 5–6 słupów w perspektywie'),
    ('75326b64', 'gen. Maczka', '606396474 (0,9 m)', 'dwuramienne łukowe w pasie dzielącym po lewej, szereg; ekrany akustyczne po prawej'),
    ('a3a2db1c', 'gen. Maczka', '257357743 (1,0 m)', 'dwuramienne łukowe w pasie dzielącym; w tle łuk kładki'),
    ('6ad5b307', 'gen. Maczka', '257358866 (2,8 m)', 'dwuramienne łukowe w pasie dzielącym, szereg w perspektywie'),
    ('3eba62ce', 'gen. Andersa przy rondzie Putry', '173985172 (0,7 m)', 'na pierwszym planie dwuramienna łukowa (ramiona wznoszą się po rozwidleniu, oprawy płaskie lekko uniesione); po prawej jednoramienna łukowa (T2); po lewej daleko słup z dwiema krótkimi ramionami; maszty sygnalizatorów'),
    ('5f92573a', 'Al. Tysiąclecia PP (płn.)', '882366266 (2,5 m)', 'dwuramienna łukowa przy krawędzi/pasie dzielącym po prawej; dalsze w szeregu'),
    ('86106e2b', 'Al. Tysiąclecia PP (płn., las)', 'UNVERIFIED (poza bbox)', 'dwuramienne w pasie dzielącym na wprost, jednoramienne łukowe przy lewej krawędzi (T2); słup na pierwszym planie po prawej bez oprawy w kadrze'),
    ('6af663fb', 'Al. Tysiąclecia PP (płn., las)', 'UNVERIFIED (poza bbox)', 'dwuramienna łukowa na pasie zieleni przy PRAWEJ krawędzi jezdni (nie w pasie dzielącym — poprawka audytu); szereg jednoramiennych łukowych przy lewej krawędzi'),
    ('aa64b81d', 'Al. Tysiąclecia PP (płn.)', 'UNVERIFIED (poza bbox)', 'dwuramienna łukowa na wprost; jednoramienne przy krawędziach'),
]:
    P(k, 'oprawa', ul, way, T1 if k not in ('86106e2b',) else T1 + ' + T2', 'kadr dzienny 2019 (przed wymianą LED 2023)', 'VERIFIED_WIZJA',
      'Co widać: ' + opis + '. Kolor słupa: jasnoszary/biały metaliczny.', 'nie dotyczy (dzień)', 'nie dotyczy', 'VERIFIED_WIZJA',
      'głowice opraw z 2019 — po 2023 wymienione na LED z płaskim kloszem (dokument 93688); sylwetka słupa/ramion bez zmian (ESTIMATED)')
for k, ul, way, opis in [
    ('4033e6b8', 'Al. Tysiąclecia PP przy rondzie Putry', '197904079 (0,1 m)', 'po prawej wysoki jasny słup z jednym łukowym ramieniem i płaską oprawą nad jezdnią; dalej dwuramienne w pasie dzielącym'),
    ('3717771d', 'Al. Tysiąclecia PP (rondo Putry)', '266084696 (1,0 m)', 'maszt sygnalizatora z łukowym wysięgnikiem na pierwszym planie (nie latarnia); w tle po prawej jednoramienna latarnia, estakada z ekranem'),
]:
    P(k, 'oprawa', ul, way, 'T2: jednoramienna łukowa przy krawędzi jezdni', 'kadr dzienny 2019', 'VERIFIED_WIZJA', 'Co widać: ' + opis + '.', 'nie dotyczy (dzień)', 'nie dotyczy',
      'VERIFIED_WIZJA', '3717771d: latarnia tylko w tle — kadr pomocniczy')

json.dump(out, open(os.path.join(HERE, 'frames.json'), 'w'), ensure_ascii=False, indent=0)
print(len(out), 'kadrów')
