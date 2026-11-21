# ADR 0325 — figura króla w Knyszynie i bruk Placu Czarnieckiego w Tykocinie

Status: Proposed (agent monuments-s24, 2026-11-21). Numer nadany przez lidera.
Powiązane: `artifacts/critic-s24-wave6/CRITIC.md` pkt 1.3 i 1.4 (FAIL), ADR 0320 (obiekty charakterystyczne — otwarty
pkt 4.1 „krata bruku” i status `PROXY_NOT_APPROVED` figury), ADR 0227 (Rynek w Knyszynie), ADR 0022 / 0063 (zestawy PBR),
D43 (referencje tylko z otwartych źródeł), docs/06 §2 (anti-slop).

## 1. Pomnik Zygmunta Augusta na Rynku w Knyszynie

**Co stoi naprawdę.** Wikimedia Commons (`Data/raw/refs/knyszyn-king-commons/manifest.jsonl`, poza gitem):
„Pomnik króla Zygmunta Augusta w Knyszynie, zdj. 18 lipca 2019 r” (Jwdys, CC BY-SA 4.0), „Podlaskie - Knyszyn - Knyszyn -
pomnik” (Athantor, CC BY-SA 4.0), „Knyszyn Zygmunt II August” (H. Borawski, CC BY-SA 3.0) + zdjęcia właściciela 1 / 8.
Brązowa postać w płaszczu do ziemi, który **zakrywa ręce**: graniasty „dzwon” z szerokimi pionowymi fałdami i szwem
z przodu, futrzane wyłogi schodzące w „V” na piersi, dwa łańcuchy z klejnotem, kreza, głowa z brodą, otwarta korona
z fleuronami. Na płaszczu napis, na cokole z szarego granitu ciemna tablica.

**Rozbieżność z raportem krytyka.** CRITIC 1.3 żąda „głowa, ramiona, fałdy, berło”. Głowa i fałdy — tak. **Rąk ani berła
rzeźba nie ma** (wszystkie trzy zdjęcia Commons), więc ich nie dodano: zasada „nie zmyślaj” ma pierwszeństwo przed
domysłem z renderu. Regalia, które są na rzeźbie (korona, łańcuchy z klejnotem, kreza, futro), zostały zamodelowane.

**Decyzja.** Bryła toczona z ADR 0320 (`monument_kit.lathe`, 16 boków) znika. Nowy moduł
`tools/worldgen/streetscape/knyszyn_king_0325.py` buduje figurę z części (układ lokalny: x w prawo, y do przodu, z od
wierzchu cokołu), wywoływany z `knyszyn_park_props_0227._king`:

- **płaszcz**: przekrój to wielobok z narożami na grzbietach fałd (`CORNERS`: 8 kątów, dziób na szwie z przodu), płaskie
  płaszczyzny między nimi, przejście w zaokrąglony przekrój na ramionach; bruzda szwu z przodu do wysokości zejścia
  wyłogów; drobne przesunięcia wierzchołków (±9 mm, stałe ziarno) — kute płaszczyzny zamiast powierzchni obrotowej;
- **głowa**: loft 15 × 11 z oczodołami, kośćmi policzkowymi i łukiem brwiowym w przekrojach + nos, brwi, powieki, uszy,
  włosy, broda w szpic i wąsy jako osobne części;
- **kreza** (plisowany torus, 26 plis), **korona** (obręcz z wywiniętą krawędzią, 4 wysokie + 4 niskie fleurony, perły),
  **wyłogi** (wałek z postrzępioną krawędzią na powierzchni płaszcza), **łańcuchy** (dwa, ogniwa jako zgrubienia) i klejnot;
- **cokół** jak w ADR 0320 + tablica z ramą na froncie (bez napisu). Napis na płaszczu pominięty (bez liternictwa w świecie).

Proporcje z frontalnego zdjęcia Commons: wysokość figury = 2,5 × szerokość u dołu, ramiona 0,58 szerokości dołu, głowa
z koroną 0,16 wysokości; szerokość u dołu 1,17 m = 0,75 szerokości wierzchu cokołu (jak ADR 0320). Figura 3,05 m na
cokole 1,09 m. Wszystko `WORKING_VALUE` (brak pomiaru). To stylizowana bryła low-poly, nie skan ani kopia rzeźby.

**Materiały** (bez tekstur, 3 wywołania w LOD0): `monument_bronze` (ciemny, metallic 0,85, rough 0,48),
`monument_bronze_patina` (futro, kreza, broda, włosy, rama tablicy: zieleńszy, rough 0,78, metallic 0,30),
`monument_bronze_rubbed` (korona, łańcuchy: jaśniejszy, wytarty). `monument_granite` dostaje własny zestaw modulacyjny
`granite_honed_tint` (ziarna skalenia / kwarcu / biotytu 3–11 mm, kafel 0,8 m) zamiast tynku. Wartości `WORKING_VALUE`
dobrane do zdjęć (zdjęcie to nie pomiar albedo). LOD1: jedna barwa `plinth_dark`, już obecna w kaflu.

## 2. Bruk Placu Czarnieckiego w Tykocinie

**Pomiar.** Wycinek ortofotomapy GUGiK (WMS, arkusz 0,25 m; `Data/raw/refs/tykocin-rynek-ortho/`, poza gitem), profil
„czerwoności” (R − B) rzutowany na kierunki co 0,25°, wewnątrz płyty (bez cienia pomnika), w EPSG:2180:

| Wielkość | Wartość | Status |
|---|---|---|
| normalne dwóch rodzin pasów | 53,75° i 143,75° od wschodu (prostopadłe) | zmierzone, ±0,25° |
| okres kraty | 2,251 m i 2,260 m → 2,255 m | zmierzone; 17 i 16 pasów, reszty < 0,06 m i < 0,10 m |
| faza | przecięcie pasów w 751807,72 / 600235,65 | zmierzone (±0,1 m) |
| szerokość pasa | FWHM 0,57 m przy rozmyciu arkusza → przyjęto 0,48 m (5 rzędów kostki ~9 cm ze zdjęcia) | WORKING_VALUE |
| opaska obwodowa | 0,75 m | WORKING_VALUE (na zdjęciu ok. 1,5 szerokości pasa) |
| naroża płyty | NW 751786,0/600245,7 · NE 751826,2/600254,8 · SE 751829,8/600222,5 · SW 751789,2/600218,0 | zmierzone, ±0,3 m (było ±1 m) |

Wygląd ze zdjęcia Commons „Mglisty poranek na placu Czarnieckiego w Tykocinie z pomnikiem” (K. Popławski, CC BY 4.0):
pola z jasnoszarej kostki granitowej układanej w łuki, pasy i opaska z drobnej czerwonej kostki w prostych rzędach.

**Decyzja.**
- Dwa zestawy proceduralne w `art-source/world/materials/_src/sets_plaza.py` (rejestrowane w `build_all.py` obok zestawów
  budynków): `sett_lattice_tykocin` — kafel = okres × √2 = 3,189 m, pasy na obu przekątnych kafla (dwa pola na kafel,
  wachlarz łuków obrócony o 90° w co drugim polu), barwy w zestawie; `sett_rows_tint` — drobna kostka w prostych rzędach
  jako mapa modulacyjna (kolor z manifestu). Kamienie z zaokrąglonymi narożami, łupaną powierzchnią, wędrującą fugą
  (±7 mm), piaskiem i mchem w spoinach. Żaden piksel zdjęcia nie jest użyty.
- `paved.py`: opcjonalne `uv_frame: {origin_epsg2180, angle_deg}` na `paved_area` — UV0 w metrach w tej ramie zamiast
  w osi obrysu. Płyta dostaje ramę = zmierzone przecięcie pasów + przekątna kraty (8,75°), więc pasy leżą tam, gdzie na
  ortofoto, niezależnie od triangulacji i kafla świata. To jest `authored_override` (przeżywa regenerację).
- `Data/Regions/tykocin/overrides.yaml`: płyta `plaza_sett_lattice`; opaska = cztery trapezy `plaza_sett_red` (rzędy
  kostki biegną wzdłuż każdego boku — UV z osi obrysu); obejścia trawników `plaza_sett_grey` (było `yard_paving`).
- Materiały kostki nie należą do `EDGED` (bez betonowego obrzeża) ani do zestawów „kostki betonowej” importera, więc
  nie dostają warstwy `_GRIME` (ciemne plamy „łaciatego” szumu z CRITIC 1.4). Kolizja: `collision_paving`.

## 3. Czego nie zrobiono / otwarte

1. Figura bez napisu na płaszczu i bez tekstury patyny (zacieki, wytarcia) — materiały są jednolite; patyna „we
   wnękach” jest tylko przez podział na trzy materiały.
2. Łuki kostki w polach są jednym wzorem na pole (obrót co drugie pole); prawdziwy układ wachlarzy nie był mierzony.
3. Donice z kwiatami, tablice przy ogrodzeniu pomnika Czarnieckiego, latarnie (CRITIC 1.5, ADR 0320 §4.2) — poza zakresem.
4. Ulice wokół placu (CRITIC 2.1, „mozaika”) należą do agenta road-surface-s24; `sett_rows_tint` nadaje się tam jako baza.

## 4. Liczby

Uzupełniane po rundach renderu — patrz niżej.
