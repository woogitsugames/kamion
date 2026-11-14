# -*- coding: utf-8 -*-
"""M65: wiersze kategorii 'nawierzchnia' — cytaty z dokumentow (strona PDF) i obserwacje zbiorcze z ortofotomapy."""
import statistics
import observations as O

ZDM_URL = 'https://www.bip.bialystok.pl/resource/103311/Za%C5%82.+nr+5_Wytyczne+do+projektowania.pdf'
ZDM_SHA = '11e87d1a3a8825afa107a461e100e37a1565d771bdef7d1dff06ca219235b16b'
ZDM = dict(url=ZDM_URL, url_pliku=ZDM_URL, sha256=ZDM_SHA, licencja='dokument urzędowy (art. 4 pr. aut.), BIP Białystok',
           autor='Urząd Miejski w Białymstoku / Zarząd Dróg Miejskich', region='C+Dojlidy (Białystok)')
DU_URL = 'https://eli.gov.pl/api/acts/DU/2019/2311/text/I/D20192311-c2.pdf'
DU_SHA = '8abcce24766fe743b5bbcd3d64771e70c1a6709c1db72fdf72adfebbfdc5d5c4'
DU = dict(url=DU_URL, url_pliku=DU_URL, sha256=DU_SHA, licencja='akt normatywny (art. 4 pr. aut.), Dz.U. 2019 poz. 2311',
          autor='Minister Infrastruktury (Dziennik Ustaw)', region='C+Dojlidy (przepis ogólnopolski)')
OBS = dict(url='https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution', licencja='GUGiK — dane publiczne (art. 40a ust. 2 pkt 1 PGiK); referencja',
           autor='GUGiK (oględziny wycinków: zespół cloud)')
ZT = 'Wytyczne do projektowania… ulic w Białymstoku (wersja „13 lipca 2018 r. / 2025 r.”, BIP zasób 103311), '

def z(page, quote, opis, wart='', jedn='', status='SOURCED', extra=''):
    return dict(ZDM, opis=opis, wartość=wart, jednostka=jedn, status=status, uwagi=ZT + 'str. PDF %s; cytat: „%s”%s' % (page, quote, ('; ' + extra) if extra else ''))

def d(page, quote, opis, wart='', jedn='', extra=''):
    return dict(DU, opis=opis, wartość=wart, jednostka=jedn, status='SOURCED', uwagi='Dz.U. 2019 poz. 2311, zał. nr 2, str. Dz.U. %s (PDF c2 str. %s); cytat: „%s”%s' % (page, page - 525, quote, ('; ' + extra) if extra else ''))

red = [v[2] for v in O.X.values() if v[1] == 'tak' and v[2] is not None]
white = [v[2] for v in O.X.values() if v[1] == 'nie' and v[2] is not None]
ROWS = [
 z(16, 'Przejazdy rowerowe w kolorze czerwonym – kolor RAL 3020, wykonane z masy chemoutwardzalnej ze środkiem uszorstniającym.',
   'Kolor i materiał czerwonych PRZEJAZDÓW rowerowych wg standardu miasta: RAL 3020, masa chemoutwardzalna uszorstniona (powłoka na asfalcie jezdni, nie asfalt barwiony w masie).', 'RAL 3020', 'kod RAL'),
 z(19, 'Droga dla rowerów poprowadzona wzdłuż innej drogi (…) oraz przejazd rowerowy musi mieć wyraźnie inny kolor.',
   'Wymóg odmiennego koloru DDR i przejazdu względem sąsiedniej nawierzchni — bez wskazania koloru ani kodu dla samej DDR.', 'brak liczby', '',
   extra='kodu RAL/Munsell dla barwionego asfaltu DDR w wytycznych NIE MA → UNVERIFIED'),
 z(18, 'Droga dla rowerów jednokierunkowa ma szerokość min. 1,5 m, dwukierunkowa ma szerokość min. 2 m.', 'Minimalne szerokości DDR wg standardu miasta.', '1,5 / 2,0', 'm'),
 z(18, 'Drogę dla rowerów można wyznaczyć za pomocą znaków poziomych i pionowych na chodniku, gdy ten (…) jest odpowiedniej szerokości - 3,5 m.',
   'Warunek wyznaczenia DDR na chodniku: szerokość chodnika 3,5 m.', '3,5', 'm'),
 z(18, 'Droga dla rowerów jest prowadzona między chodnikiem a jezdnią.', 'Położenie DDR w przekroju wg standardu: między chodnikiem a jezdnią.', '', '',
   extra='ROZBIEŻNOŚĆ standard↔orto: na ul. Kuronia i Mickiewicza (Dojlidy) oraz Al. Tysiąclecia (C) chodnik leży bliżej jezdni niż DDR (patrz wiersze odcinków)'),
 z(18, 'Droga dla rowerów jest położona niżej niż chodnik i wyżej niż jezdnia.', 'Niweleta DDR względem chodnika i jezdni (zasada, bez liczby).', 'brak liczby', ''),
 z(18, 'krawężnik betonowy "k1" 25x12x100cm', 'Rysunek nr 9: krawężnik/obrzeże najazdowe przy DDR — element 25×12×100 cm, rzędne „0” i „+3” po obu stronach (odsłonięcie 3 — jednostka na rysunku niepodana, przyjęto cm), podsypka cementowo-piaskowa 1:4 gr. 5 cm, ława z betonu B-15 gr. 10 cm.', '0,03 (odsłonięcie); 0,25×0,12×1,00 (element)', 'm',
   status='SOURCED (rysunek obejrzany); jednostka rzędnych ESTIMATED'),
 z(4, 'Wysokość krawężników przy przystankach autobusowych – 16 cm', 'Jedyna liczbowa wysokość krawężnika w wytycznych dotyczy przystanków; wysokość krawężnika jezdni przy DDR poza przystankami — brak w dokumencie.', '0,16 (tylko przystanki)', 'm',
   extra='wysokość krawężnika jezdni przy DDR: UNVERIFIED'),
 z(19, 'Droga dla rowerów na przecięciu z wjazdem na posesje zachowuje swój poziom (jest równa na długości).', 'Zasada ciągłości niwelety DDR przez wjazdy (skosy na wjazdach po stronie zjazdu, nie DDR).', 'brak liczby', '',
   extra='skosy/rampy wjazdów [m]: UNVERIFIED (brak liczby; z orto nieczytelne)'),
 z(19, 'powinny być wykonane w technologii bezszwowej, gdzie asfalt obu nawierzchni się zlewa bez użycia krawężników', 'Połączenie asfaltowej DDR z asfaltową jezdnią na przejeździe: bez krawężnika (bezszwowo) albo z krawężnikiem całkowicie wtopionym.', 'brak liczby', ''),
 z(20, 'Odległość „S” między zewnętrznymi krawędziami tych linii nie może być mniejsza niż: 1,8 m (…) jednokierunkowego, 3,0 m (…) dwukierunkowego', 'Szerokość przejazdu wg standardu miasta (powtórzenie Dz.U.).', '1,8 / 3,0', 'm'),
 z(20, 'Minimalna szerokość przejazdu dwukierunkowego wynosi 3,0 m, a minimalna szerokość przejścia dla pieszych wynosi 2,5m', 'Przejazd połączony jednostronnie z przejściem (P-10 + P-11): powierzchnia czerwona, min. 3,0 m + 2,5 m.', '3,0 / 2,5', 'm'),
 z(16, 'znaki P-23 („rower”) wykonanie zgodnie z aktualnymi przepisami o wymiarach 1,1 m x 2,0 m', 'Symbol P-23 na DDR 1,1 × 2,0 m, oznakowanie cienkowarstwowe; linia osiowa DDR = P-1d.', '1,1 × 2,0', 'm',
   extra='drugi cytat (str. 16): „Droga dla rowerów – linia osiowa o symbolu P-1d.”'),
 z(19, 'Bufor, w którym nie należy instalować żadnych elementów wystających powyżej 5 cm rozciąga się w odległości 50 cm od drogi dla rowerów.', 'Skrajnia DDR: bufor 0,5 m; urządzenia min. 1 m od DDR; min. 1,5 m od parkingu równoległego.', '0,5', 'm'),
 d(569, 'nie może być mniejsza niż: – 1,8 m – w przypadku przejazdu jednokierunkowego, – 3,0 m – w przypadku przejazdu dwukierunkowego', 'Znak P-11: szerokość przejazdu s mierzona między zewnętrznymi krawędziami dwóch linii przerywanych.', '1,8 / 3,0', 'm'),
 d(570, 'Dla zapewnienia dobrej widoczności przejazdów dla rowerzystów zaleca się dodatkowe oznaczenie powierzchni przejazdu barwą czerwoną.', 'Czerwona powierzchnia przejazdu — zalecenie (nie obowiązek); przykład rys. 4.2.2.2 lit. a.', 'brak liczby', ''),
 d(571, 'Powierzchnię przejazdu dla rowerzystów połączonego z przejściem dla rowerów oznacza się barwą czerwoną.', 'Przejazd połączony jednostronnie z przejściem (rys. 4.2.2.3): czerwień obowiązkowa.', 'brak liczby', '',
   extra='w tekście aktu „przejściem dla rowerów” (sic)'),
 dict(OBS, region='C', opis='Barwiony asfalt DDR w regionie C (rejon ronda pod estakadą Andersa/Al. Tysiąclecia–Maczka, ul. Bitwy Białostockiej przy rondzie, łącznice): na ortofotomapie czerwonobrązowy/bordowy, matowy, wyraźnie ciemniejszy i mniej nasycony niż czerwone pola przejazdów; na części odcinków spłowiały do różowoszarego (way 173956082; kadr Panoramax 54f16fec z 2019 r.). Biała linia osiowa przerywana i symbole P-23 na czerwonym tle. Granica z jasnym chodnikiem prosta, wzdłuż obrzeża.',
      wartość='opis słowny', jednostka='', status='ESTIMATED (oględziny orto 5 cm; bez RGB)',
      uwagi='odcinki: 284396207, 284396209, 257367441, 177903955, 282244166, 238234011, 613145836, 591365139, 173985179, 173956082; faktura kruszywa, plamy, łaty, wygląd zimą: UNVERIFIED (brak kadrów z poziomu pieszego — Commons niedostępne w sesji)'),
 dict(OBS, region='C+Dojlidy', opis='Czerwone pola przejazdów (powłoka wg wytycznych RAL 3020): jasna, żywa czerwień; pole prostokątne lub trapezowe (rozszerzone łukami wlotu), granica ostra — wyznaczona rzędami białych kwadratów P-11 albo krawędzią zebry; na przejazdach przez ruchliwe wloty czerwień wytarta do ciemnego asfaltu w dwóch śladach kół na pas (węzły 1882953779, 1882953782, 1166108041).',
      wartość='opis słowny', jednostka='', status='ESTIMATED (oględziny orto 5 cm; bez RGB)', uwagi='uszczelnienie/spoina na granicy czerwony–szary: UNVERIFIED (poniżej rozdzielczości orto)'),
 dict(OBS, region='C', opis='Czerwona kostka betonowa: (a) pasy rowerowe przy ul. Andersa wydzielone w chodniku/za przystankiem (way 177948306, 350559280, 177895175; ok. 2,1–2,2 m, bez linii osiowej), (b) ciąg 435369091 (ok. 3,65 m), (c) wąski pas separacyjny ok. 0,4 m między DDR a chodnikiem przy ul. Bitwy Białostockiej (way 591358181, 879051665), (d) krótkie pola przy krawężnikach przed przejściami (oba regiony).',
      wartość='0,4 (pas separacyjny); 2,1–2,2 (pas rowerowy)', jednostka='m', status='ESTIMATED (orto 5 cm, ±0,3 m; materiał „kostka” z rysunku spoin — niepewny)', uwagi='OSM nie ma colour dla żadnego z tych odcinków'),
 dict(OBS, region='C+Dojlidy', opis='Szerokości przejazdów odczytane z ortofotomapy a minimum z Dz.U./wytycznych (3,0 m dla dwukierunkowego): przejazdy czerwone n=%d, min %s, mediana %s, max %s m; przejazdy tylko białe n=%d, min %s, mediana %s, max %s m. Około połowy odczytów jest poniżej 3,0 m.' % (
      len(red), ('%.2f' % min(red)).replace('.', ','), ('%.2f' % statistics.median(red)).replace('.', ','), ('%.2f' % max(red)).replace('.', ','),
      len(white), ('%.2f' % min(white)).replace('.', ','), ('%.2f' % statistics.median(white)).replace('.', ','), ('%.2f' % max(white)).replace('.', ',')),
      wartość='%s (mediana, czerwone); %s (mediana, białe)' % (('%.2f' % statistics.median(red)).replace('.', ','), ('%.2f' % statistics.median(white)).replace('.', ',')), jednostka='m',
      status='ESTIMATED (orto 5 cm; profil jasności tools/crossing_profile.py ±0,15 m, ukośne ±0,5 m)', uwagi='pomiar między zewnętrznymi krawędziami rzędów kwadratów albo od rzędu kwadratów do krawędzi zebry (przejazd połączony)'),
]
