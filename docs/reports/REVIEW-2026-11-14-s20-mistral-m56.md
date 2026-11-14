# Przegląd M56 (P13 estakady Andersa: A rondo Putry, B rondo Pamięci Bieżeństwa 1915) — s20, 2026-11-14

**Werdykt: FIX.** Część dokumentowa i OSM jest dobra. Cytaty z UM Białystok i STRABAG zgadzają się ze świeżo pobranymi stronami, a md5 PDF-u PFU jest zgodny. Długości jezdni odtwarzają się co do 0,1 m z naszego PBF. Mistral użył właściwych way mostowych (`bridge=viaduct`), a nie ramp z listy zadania. Seed audytu da się odtworzyć, licencje są czyste, Google nie użyto. Oddanie nie spełnia jednak kryteriów w części zdjęciowej:
- **Z 23 kadrów (12 Commons + 11 Panoramax) obejrzano 4, a 059 ma sporną notatkę. 18 kadrów nie obejrzano.** Audyt 20 % nie obejrzał ponownie ani jednego obrazu.
- Trzy wiersze **SOURCED są fałszywe**: słupy A „owalne”, PFU „Sulika i Maczka, w tym E4 (obiekt A)” i „ekrany po obu stronach” na B.
- 4 kierunki kadrów Panoramax są błędne.
- Luki, które zadanie kazało zamknąć (połowa SE estakady B, ekran na jezdni A w stronę centrum), rozstrzygają kadry CC0 **już wpisane do manifestu**, ale nieobejrzane.

Blok poprawek: `docs/owner/MISTRAL-FIXES-12.md` § M56-FIX. Nic nie scalono, nic nie scommitowano, PR #54 bez komentarza.

## 1. Zakres i metoda

- PR #54, gałąź `origin/research/mistral-p13-andersa-viaducts` @ `6f39fc260` (3 commity od main). `git diff --stat main...` pokazuje 6 plików wyłącznie w `research/mistral/p13-andersa-viaducts/`: README, manifest (78 wierszy), sources, audit, `files/.gitignore`, `files/README.md`. Pliki obejrzano przez `git archive` w scratchu.
- **ZIP `mistral-p13-andersa-viaducts-files.zip` (8 736 124 B, sha256 `de50ff75…`) nie dotarł** do `research/_incoming`. Kadry pobrałem sam: Commons przez API imageinfo (960 px, dla P13-015/059/061 oryginał i wycinki), Panoramax przez `assets.sd` z API itemu. **Obejrzałem 16 kadrów:** P13-015 (+ wycinek 5520 px), 016, 017, 018, 019, 021, 022, 024, 026, 028, 059 (+ 2 wycinki 3840 px), 060, 061 (+ wycinek), 062, 063, 066. Wszystkie pomniejszone do ≤ 960 px.
- OSM: `Data/raw/osm/podlaskie-261108.osm.pbf`, pyosmium (`uv run` w tools/worldgen, `python -I`). Strony kamer względem osi liczone w lokalnym układzie ENU.
- Dokumenty sprawdzone ponownie: UM Maczka, UM Andersa, STRABAG (HTML) oraz PFU (PDF, tekst przez pypdf). Strony BIP z dylatacjami E4 (P13-007/008) nie pobierałem.
- Gra: `Data/Regions/bialystok-industrial-c/overrides.yaml` (`andersa-viaduct-*`), `viaduct_underdeck.json`, `generated/landmarks/viaduct_putry_underdeck.spec.json`, `viaduct_biezenstwa.spec.json`, `gate3_reference_map.json`.

## 2. Kryteria akceptacji M56

| Kryterium | Wynik |
|---|---|
| Dokumenty urzędowe (rok, wykonawca, schemat, przęsła, podpory, ekrany…) osobno A i B | **CZĘŚCIOWO.** Rok, wykonawca, koszt i „dwudźwigarowa sprężona” (B) są poprawne. Przęsła, podpory, skrajnia i wysokość ekranu nie są publicznie dostępne. To uczciwie oznaczone UNVERIFIED i jest akceptowalne. Jeden SOURCED (P13-009, PFU) jest przypisany do złego obiektu (§4). |
| Każdy kadr OBEJRZANY, zdanie „co widać” | **NIE.** 4 z 23 kadrów mają zdanie „co widać”: 7204, Andersa_Maczka 2 i 3, 20200711_072453. 059 ma sporną notatkę z sesji, a 18 kadrów opisano „nie obejrzano (limit narzędzia)”. Błędne są: kształt słupów w P13-016/017/034 („owalne”) i notatka z sesji dla 059 („ekrany po obu stronach”). |
| Zdjęcia: każdy rząd podpór A i B, połowa SE B, obie strony obu jezdni A | **NIE** w oddaniu. Ale kadry CC0 z manifestu to rozstrzygają: P13-018 (zewnętrzny ekran jezdni SE-bound A), P13-061/062 (połowa SE estakady B), P13-026 (strona od pasa dzielącego, A). §3, §5. |
| Tabela parametr → wartość → źródło → status zgodna z polami override'ów | **TAK** (forma), z błędami treści (§3, §4). |
| Pozycje WGS84 6 miejsc, kierunek z API/EXIF albo UNVERIFIED, przypisanie ≤ 60 m z way_id | **CZĘŚCIOWO.** Pozycje i odległości są zgodne. **Kierunki P13-021/023/028/029 są błędne** (§3). |
| Samokontrola ≥ 20 %, jawny seed, kadry ponownie OBEJRZANE | **CZĘŚCIOWO.** Seed 20261113 → te same 16 id, w tej samej kolejności ✓. Ponownego obejrzenia brak („blocked_by_tool_limit” przy każdym kadrze), więc dla kadrów kryterium jest niespełnione. |
| Licencje, zakaz Google, Mapillary bez cudzego tokenu | **TAK.** CC0/CC BY (Rakoon), CC BY-SA (Borawski, Panoramax stanton) jako referencja, ODbL, GUGiK. Prasa i strony wykonawców tylko jako fakty. |
| Zmiany tylko w `research/mistral/p13-andersa-viaducts/`, ZIP + sha w PR | **TAK** (ZIP nie dotarł do lidera). |

## 3. Oględziny kadrów — opis Mistrala a obraz

Strona kamery względem osi jezdni z PBF. A: jezdnia „NW” Mistrala = ways 173985172+23844386 (ruch na NW, leży po stronie **NE**). Jezdnia „SE” = 25447143+173985170 (ruch na SE, leży po stronie **SW**). Rozstaw osi wynosi 14,0 m.

| Kadr | Opis / status M56 | Co widać (recenzent) | Ocena |
|---|---|---|---|
| P13-015 (CC0, 7204) | żółte słupy, zielony gzyms, ekrany przezroczyste | Kamera 28 m na NE. Zewnętrzna krawędź pomostu NE z ekranem przezroczystym na słupkach. Gzyms zielony ✓. **Słupy prostokątne z fazowanymi narożami i głowicą** (wycinek 5520 px), w parach, ochra/musztarda | ✓ poza kształtem |
| P13-016 (BY-SA) | słupy owalne, zielony gzyms, ekrany | Kamera po stronie SW. Pomost SW z ekranem na krawędzi zewnętrznej. Koniec estakady: mur oporowy z bloczków z **czerwonym pasem** na koronie, ekran także na rampie. Słupy nie są owalne | ✗ (kształt) |
| P13-017 (BY-SA) | słupy owalne… | Widok spod/pomiędzy pomostami. Bok pomostu z zielonym gzymsem, ekran na słupkach, za nim balustrada. Słupy fazowane, w parach | ✗ (kształt) |
| P13-018 (CC0) | UNVERIFIED, nie obejrzano | Kamera 9 m na SW od jezdni SE-bound. **Ekran przezroczysty na zewnętrznej (SW) krawędzi jezdni SE-bound.** Za nim drugi pomost (zielony gzyms). Słupy w parach, rury odwodnienia pod wspornikiem | **rozstrzyga P13-040** |
| P13-019 (Panoramax) | UNVERIFIED | Strona SW. Oba pomosty: bliższy z ekranem, dalszy niżej w perspektywie. Słupy ochrowe w regularnym rytmie pod oboma | dowód (ref.) |
| P13-021 (Panoramax) | UNVERIFIED, kierunek 14,3° | Rampa: koniec estakady, przyczółek, mur oporowy z bloczków z czerwonym pasem i ekranem. Po prawej ekran naziemny (zielony panel + szkło). **API `view:azimuth` = 268°.** Wpisano EXIF `GPSImgDirection` 14,34° z `Ref = M` (magnetyczny, Nexus S) | kierunek ✗ |
| P13-022 (Panoramax) | UNVERIFIED | Strona SW, pomost z ekranem, dalszy pomost, słupy fazowane | dowód (ref.) |
| P13-024 (Panoramax) | UNVERIFIED | **Estakady nie ma w kadrze** (skrzyżowanie, ekran naziemny po prawej) | do usunięcia |
| P13-026 (Panoramax) | UNVERIFIED | Spod pomostu SW na pomost NE. **Od strony pasa dzielącego: ciemna balustrada z poziomymi rurami, bez ekranu.** Ekran widać dalej, na krawędzi zewnętrznej. Rura odwodnienia wzdłuż. Słup wyraźnie **graniasty z fazami** | **rozstrzyga stronę ekranu (ref.)** |
| P13-028 (Panoramax) | UNVERIFIED, kierunek 17,5° | Rampa, ekran naziemny z zielonymi słupkami po prawej, estakady prawie nie widać. API azimuth **275°** | kierunek ✗ |
| P13-059 (CC0, 20201102) | konflikt: „ekrany po obu stronach” vs ADR 0117 | Kamera 24 m na NE od NE pomostu. **Brak ekranu.** Stalowa balustrada z poziomymi prętami (~1,1 m), gzyms czerwony, słupy szare w parach (z boku bez pasa) | **ADR 0117 ma rację; obserwacja z sesji fałszywa** |
| P13-060 (CC BY) | „widziana od strony Elektrociepłowni” | Kamera przy końcu NW (59 m na NE), patrzy wzdłuż na SE. **EC jest w tle**, nie po stronie kamery. Czerwony gzyms, balustrada, brak ekranu, mur rampy z gładkich dużych paneli | ✓ z korektą |
| P13-061 (CC0) | UNVERIFIED, „kandydat połowy SE” | Kamera 25 m na SW. **Połowa SE estakady B:** czerwony gzyms, balustrada z poziomymi prętami, **brak ekranu**, słupy szare z **czerwonym pasem** na czole (wycinek 3840 px), przyczółek i mur rampy z gładkich paneli. Widać ≥ 4 rzędy między przyczółkiem a wyspą (ESTIMATED, rzędy częściowo się zasłaniają) | **zamyka lukę „brak kadru SE”** |
| P13-062 (CC0) | UNVERIFIED | Ten sam widok 20 s później, szerzej | ✓ (dubel pomocniczy) |
| P13-063 (CC BY) | UNVERIFIED | Flagi, skrzyżowanie, parking. **Estakady nie widać** | do usunięcia |
| P13-066 (CC0) | UNVERIFIED | Nieużytek, latarnie, wysoki budynek. **Estakady nie widać** | do usunięcia |

**Wynik:** w 4 obrazach opisanych przez Mistrala kolory, gzyms i ekrany są zgodne (015 = 041/043/044, 060 z korektą „EC w tle”). Kształt słupów jest błędny w 3 wierszach (016, 017, 034), a notatka z sesji dla 059 jest fałszywa. Z 10 nieobejrzanych kadrów, które obejrzałem: 5 to wartościowe dowody (018, 019, 022, 026, 061/062), 3 nie pokazują obiektu (024, 063, 066).

**Kierunki Panoramax:** kolekcja b3131ba1 (7 kadrów) zgadza się z API ±0,5°. Kolekcja 989ab5f4 (P13-021/023/028/029) ma w manifeście EXIF magnetyczny (14,3 / 13,1 / 17,5 / 17,3°). API `view:azimuth` podaje 268 / 242 / 275 / 274°. Kadry 021 i 028 z widokiem wzdłuż Maczka (~300°) potwierdzają wartości z API.

## 4. Dokumenty

- P13-001/002 (UM Maczka): „Dla każdej jezdni … estakadę nad Al. Tysiąclecia Państwa Polskiego o długości blisko 220 m” ✓. Uwaga: ta sama strona podaje „ponad 158 mln PLN”, a Inżynier Budownictwa „ponad 159 mln”. To dwa różne źródła, w sources.md obie liczby są oddane uczciwie.
- P13-046/052/053 (STRABAG) ✓. Mistral pominął dalszą część zdania: „…sprężonej **posadowionej bezpośrednio**”.
- P13-048–051 (UM Andersa) ✓. Strona mówi wprost o „budowie estakady na skrzyżowaniu ul. Gen. Wł. Andersa z ulicą I Armii Wojska Polskiego”. To lepszy cytat dla B niż Palisander (P13-055).
- **P13-009 (PFU, BIP 61046) — błąd przypisania.** Tekst PDF (pypdf, 7 stron, md5 zgodny) dotyczy ekranów **„na ul. Gen. N. Sulika i ul. Gen. St. Sosabowskiego”**. Lokalizacja to **„Przedłużenie ulicy Wł. Andersa”**, a podstawą jest „Tabela 11.1 Propozycja zabezpieczeń akustycznych” z analizy porealizacyjnej. E1–E19 to **numery proponowanych ekranów**, nie estakad. Zapisy „PFU: ul. Gen. N. Sulika i Gen. S. Maczka” (manifest, sources D4) i „w tym E4 (obiekt A)” (README §3, tabela A) są fałszywe. Ekran „E4” z PFU nie jest estakadą E4 z BIP 2024. Wiersz trzeba przepisać albo usunąć z obiektu A.
- P13-003 data „2011” wywnioskowana z daty publikacji artykułu (2011-10-10). Jest opisana w uwagach, OK.

## 5. OSM i geometria (PBF 2026-11-08)

- Długości (haversine, pyosmium): A NW-bound 107,2 + 111,8 = **219,0 m** ✓; A SE-bound 108,1 + 104,9 = **213,0 m** (Mistral 212,9) ✓; B 177876107 **195,8 m** ✓, 177895177 **195,5 m** ✓. Rozstaw osi A ≈ 14,0 m (Mistral 14,2) ✓.
- **Way z zadania i z override'ów to rampy, nie mosty.** 1101181473, 173956078, 284022563, 606396460 i 175157461 mają `layer=1` bez `bridge=*`. Mosty to 173985172/23844386/25447143/173985170 (A) i 177876107/177895177 (B). Mistral słusznie przeszedł na way mostowe, ale tego nie zgłosił. Gra łączy je w łańcuchy (`c:w1101181473…`, `c:w175157461…`), więc wynik się zgadza.
- Pod A leży **Rondo Krzysztofa Jakuba Putry** (ways 257367424/425/428, DK8/DK19). Identyfikacja obiektu A ✓.
- Nazewnictwo jezdni jest niespójne. A ma etykiety według kierunku ruchu („NW” leży po stronie NE). B ma etykiety według strony (SW/NE). Do ujednolicenia.
- OSM `wall=noise_barrier` w okolicy A (319142221…26, 312601353) leżą 30–60 m od osi. To ekrany naziemne, nie na pomoście. Mistral tego nie sprawdzał. Nic nie zmienia, ale warto to odnotować.

## 6. Porównanie z grą i co M56 może poprawić

| Element | Gra dziś | M56 + przegląd | Działanie |
|---|---|---|---|
| A długość pomostów | otwarty zakres 219,5 / 213,2 m | 219,0 / 213,0 m (OSM), „blisko 220 m” (UM) | ✓ potwierdzone, bez zmian |
| A szerokość pomostu | 10,7 m | ~11 m (orto 0,25 m/px, ESTIMATED) | ✓ w tolerancji |
| A słupy | fazowane 1,0 × 1,2 m, faza 0,25 (spec) | **prostokątne fazowane z głowicą** (CC0 7204, Panoramax 6fc62548) | ✓ geometria dobra. Tekst `reason` w `andersa-viaduct-putry-style` mówi „round piers” — poprawić opis |
| A ekrany | `screen_side: travel_right` (zewnętrzna krawędź), jezdnia SE-bound „assumed symmetric (UNVERIFIED)” | ekran na zewnętrznej krawędzi **obu** jezdni (015 CC0 dla NE, **018 CC0 dla SW**). Od pasa dzielącego balustrada (026 ref.) | zmienić UNVERIFIED → potwierdzone kadrem CC0 20221203_111814 |
| A podpory jezdni SE-bound | 5 rzędów, **przęsło 94,8 m** bez słupów (NW-bound: 7 rzędów, maks. 48,8 m) | kadry 018/019/022 ze strony SW pokazują słupy w regularnym rytmie pod pomostem SW | **P1 dla gry, do sprawdzenia:** prawdopodobnie brakują rzędy w łańcuchu `c:w173956078` (`pier_lines_skipped`). Kamera z 018 jako kontrolna |
| A rampy | `ramp_fascia: red`, ściany z bloczków | czerwony pas na koronie muru z bloczków, ekran na rampie (016, 021) | ✓ potwierdzone |
| B ekrany | `noise_screen: null` | **brak ekranów** po obu stronach (059 NE, 061/062 SW, 060) | ✓ konflikt zamknięty na korzyść gry |
| B słupy | stadium 0,70 × 1,40, czerwony pas, rozstaw 3,5 m | czerwony pas na czołach widoczny w połowie SE (061 CC0) | ✓ jakościowo. Wymiary nadal WORKING_VALUE |
| B rzędy / przęsła | 8 rzędów, 9 przęseł 4 × ~21,2 + 26,4 + 4 × ~21,3 m | połowa SE: ≥ 4 rzędy między przyczółkiem a wyspą (061, ESTIMATED) | wspiera symetrię z ADR 0144; liczenie rzędów zlecić w FIX |
| B przekrój | „box girders with sloped webs” (asset) | STRABAG: „konstrukcja **dwudźwigarowa** sprężona” | **otwarte:** słowo może oznaczać przekrój z dwoma żebrami albo 2 ustroje (po jednym na jezdnię). Bez zmian, dopóki kadr spodu (061, inne CC0) tego nie rozstrzygnie |
| B długość / rozstaw | 196,2 / 195,7 m, rozstaw 12,4 m | 195,8 / 195,5, 12,1 m | ✓ |
| B mury ramp | `ramp_wall_panels` | gładkie duże panele (060, 061) | ✓ potwierdzone |
| Referencje bramki 3 | `gate3_reference_map.json`: tylko 7204 (A) i 20201102 (B) | nowe CC0: 20221203_111814 (A, pomost SW + drugi pomost), 20210320_092717/092737 (B, połowa SE) | dodać jako kadry porównawcze (CC0, Rakoon) |

## 7. Licencje, samokontrola

- Licencje sprawdzone na Commons API: 015/018/059/061/062/066 CC0 (Rakoon), 060/063–065 CC BY 3.0 (Rakoon), 016/017 CC BY-SA 3.0 (Henryk Borawski, „referencja, nie tekstura”). Panoramax: CC-BY-SA-4.0 (stanton). Data i GPS zgadzają się z manifestem ✓. Google nie ma. Mapillary uczciwie pominięty.
- Samokontrola: seed i próba odtwarzalne ✓. Merytorycznie audyt sprawdził tylko żywotność URL i cytaty dokumentów. P13-009 dostał PASS, bo cytat jest w PDF, ale **kontekst cytatu zaprzecza przypisaniu**. P13-015/017/059 przeszły bez ponownego obejrzenia.

## 8. Dla lidera

- **Nie scalać** w obecnej postaci. Zmiany w grze nie są potrzebne do scalenia M56. Wniosek dla świata (§6) można przekazać już teraz:
  - (1) Ekran A na zewnętrznej krawędzi obu jezdni jest potwierdzony kadrem CC0 20221203_111814. Usuń „UNVERIFIED symmetric” z `andersa-viaduct-putry-style`.
  - (2) Popraw w `reason` opis słupów A z „round” na „chamfered rectangular”.
  - (3) **Sprawdź przęsło 94,8 m bez podpór na pomoście SE-bound A** (`viaduct_putry_underdeck.spec.json`, łańcuch `c:w173956078`) — to wygląda na lukę w modelu.
  - (4) B bez ekranów jest potwierdzone.
  - (5) Dodaj nowe referencje CC0 do bramki 3.
- ZIP M56 nie dotarł. Jeśli właściciel go ma, rozpakuj do `research/_incoming/mistral-p13-andersa-viaducts/`.
- Kadry i wycinki recenzenta (tymczasowe): scratch sesji `…/scratchpad/img/s_P13-*.jpg`, `c15.jpg`, `c59a/b.jpg`, `c61.jpg`.
