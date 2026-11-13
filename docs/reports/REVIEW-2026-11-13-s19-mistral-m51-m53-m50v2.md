# Przegląd poprawek Mistrala: M51-FIX (PR #49), M53-FIX (PR #50), M50-FIX pass C (gałąź po #45) + stan FIX-9 — s19, 2026-11-13

Zakres: zgłoszenie właściciela „M51/M53/M50-FIX gotowe”. Wymagania: `docs/owner/MISTRAL-FIXES-8.md` (bloki M50/M51/M53-FIX). Poprzednie przeglądy: `docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p10.md`, `…-s17-mistral-r8-p3.md`, `…-s17-mistral-r8-p6p8p9p5.md`, `…-s18-mistral-fixes-r8.md`. Stan po `git fetch` (origin/main @ 5ab9e8bf6). Niczego nie scalono, nie skomentowano, nie wypchnięto. Wszystkie obrazy w próbach obejrzane osobiście (Read, arkusze 2×2 z oryginałów z ZIP-ów v2).

## 1. Werdykty

| PR / gałąź | sha oceniany | Werdykt | Akcja lidera |
|---|---|---|---|
| **M50** `research/mistral-p9-furniture-3` (PR #45 scalony; +7 commitów po scaleniu) | **3b34a98df** | **SCALIĆ** (drobna errata w REVIEW-NOTE) | `git merge --no-ff origin/research/mistral-p9-furniture-3` (merge-tree czysty; tylko `research/mistral/p9-furniture-3/`, 6 plików) |
| **M51** PR #49 `research/mistral-p10-greenery-3` | 84a8bc792 | **SCALIĆ Z ERRATĄ** (§3.5) | scalić PR + REVIEW-NOTE z erratą; opcjonalnie M51-FIX-2 (`MISTRAL-FIXES-10.md`) |
| **M53** PR #50 `research/mistral-p3-buildings-2` | 314720a8d | **SCALIĆ Z ERRATĄ** (§4.4) — po erracie 28 przyjętych (< 30) | scalić PR + REVIEW-NOTE z erratą; M53-FIX-2 (`MISTRAL-FIXES-10.md`) do domknięcia progu |
| FIX-9 (M52-FIX-3, M47-FIX-2, M54-FIX-2, M49-FIX-2) | — | **brak FIX-9 na origin** | nic (§5) |

Licencje: we wszystkich trzech brak Google Maps/Street View/Earth/3D Tiles (grep diffów + sources: zakaz jawnie zachowany); Mapillary nieużyty. Źródła: Commons CC0 / CC BY 3.0 / CC BY-SA 3.0 (Rakoon, Henryk Borawski), KartaView i Panoramax CC BY-SA 4.0 (referencja), GUGiK ortofoto CC BY 4.0, BIP/urzędowe. Żaden wiersz nie dyskwalifikuje się licencyjnie.

## 2. M50 — meble uliczne (pass C, sha 3b34a98df)

- Diff vs main: `README.md`, `REVIEW-NOTE.md` (+5, sync z main), `audit_20_percent.json`, `manifest.csv`, `sources.md`, nowy `vision_run.json`; 1014+/358−. Ostatnie 3 commity (5d6c6c0c0, 81c66da0b, 3b34a98df) zmieniają tylko `vision_run.json` (6 linii; JSON poprawny).
- Manifest 66 wierszy: **25 VERIFIED (dokumenty) / 15 VERIFIED_WIZJA / 26 NOT_FOUND / 0 TO_VERIFY** — zgodne z README. Errata s17 zastosowana: M50-059/060 → NOT_FOUND (płot posesji), M50-017 → NOT_FOUND (wiata BP).
- **Klatki v2 vs manifest:** 40 plików `frames/M50-*.jpg`; 37 bajtowo identycznych z ZIP v2 przeglądanym w s17 (wtedy 13/16 zgodnych, 3 błędy — teraz poprawione), nowe/zmienione: M50-054/055/065 (Panoramax 2560×1920), M50-066 (nowy). Duplikaty bajtowe 006=007 i 024=058 — zgodne z adnotacjami manifestu („ten sam kadr”).
- Próba (12 kadrów obejrzanych, 18 % wierszy; łącznie z s17 obejrzane wszystkie VERIFIED_WIZJA):

| id | status | manifest „co widać” | co faktycznie widać | ocena |
|---|---|---|---|---|
| 008 | VERIFIED_WIZJA (U-12) | odbojnica w-beam po lewej 5–10 m | stalowa bariera ochronna wzdłuż lewej krawędzi, blisko kamery; latarnie, znaki | ✓ |
| 066 | VERIFIED_WIZJA (latarnia) | latarnia po lewej, betonowe bariery, mur z zielenią i reklamą | latarnia pojedyncza lewo-środek (~30 m), betonowe separatory, ściana z zielonym pasem i billboardem, prawa ściana prześwietlona | ✓ |
| 054 | VERIFIED_WIZJA (sygnalizator) | sygnalizator na wysięgniku, most | sygnalizator na łukowym wysięgniku u góry kadru, estakada z ekranami, przejście | ✓ (pozycja „prawo” → raczej środek-góra) |
| 055 | VERIFIED_WIZJA (sygnalizator) | sygnalizatory lewo/środek/prawo, most | estakada, 2 maszty z sygnalizatorami, autobus | ✓ |
| 065 | NOT_FOUND (hydrant) | droga, siatka, latarnie, znaki | ekrany akustyczne, latarnie, znaki 70/E67; hydrantu brak | ✓ |
| 009 | NOT_FOUND (U-5a) | buspas, autobus 130 | autobus BKM 130, Bocaro, słup WN; słupka brak | ✓ |
| 012 | NOT_FOUND (żerdź) | żółta tablica | żółta tablica „Uwaga!”, latarnie, bariera; żerdzi brak | ✓ |
| 022 | NOT_FOUND (stojak) | 70, BP | znaki 70, stacja BP; stojaka brak | ✓ |
| 020 | NOT_FOUND (kosz) | przystanek z ludźmi | przystanek z wiatą i pasażerami; kosza nie widać | ✓ |
| 061 | NOT_FOUND (szafka) | przystanek po prawej | to samo miejsce co 020; szafki brak | ✓ |
| 062 | NOT_FOUND (stojak) | budynek z graffiti | pawilon z graffiti, parking P; stojaka brak | ✓ |
| 051 | NOT_FOUND (hydrant) | ciężarówki, zieleń | TIR-y, ekrany, latarnie; hydrantu brak | ✓ |

Zgodność 12/12. **Errata (do REVIEW-NOTE, nie blokuje):** README „JPG ≤ 1600 px” — M50-054/055/065 mają 2560×1920; `vision_run.json` ma 66 wpisów `frames`, a commity mówią „68/68”. Odległości „~50 m wg wizji” — szacunki modelu, traktować jako ESTIMATED.

## 3. M51 — zieleń osiedla (PR #49, sha 84a8bc792)

Diff: 21 plików, tylko `research/mistral/p10-greenery-3/`; merge-tree czysty. Manifest 60 wierszy (35 SOURCED / 24 ESTIMATED / 1 UNVERIFIED), identyczny z `metadane/manifest.csv` w ZIP v2.

### 3.1 Korony (zad. 1) — naprawione
- Nowy `crowns.geojson` (5258) = stary odbity N–S w kaflach 1024 m: 99,9 % punktów w ≤ 1 m od odbicia starego (mediana 0,25 m); bez odbicia mediana 13 m. W s17 to odbicie dawało 100 % trafień w zieleń → **rejestracja poprawna**.
- Własna nakładka na GUGiK WMS (okno w1, 53,1555 N 23,1525 E, north-up): korony na drzewach w ogrodach i przy blokach ✓; **zielony autobus na jezdni nadal wykryty jako korona** (filtr nie-roślinności usunął 1 obiekt: 5259→5258). `compact_greenery.geojson` (771 poligonów) obrysowuje zadrzewioną skarpę na N od bloków ✓, ale ma artefakty (długie proste krawędzie przez jezdnię/zabudowę).
- **Nakładki PNG w ZIP (`overlays/w1…w3`) są bezwartościowe jako dowód:** obraz odwrócony N–S względem WMS, a znaczniki narysowane tylko w lewym-górnym ~⅓ obrazu (zła skala px: 4800 px okna vs układ 0,25 m) — cyjan leży na dachach domów. Liczby 100/99,8/100 % liczone osobno, nie z tych PNG.
- Data ortofoto 2024-05-27 z GetFeatureInfo (arkusze 0,25 m; `orto_metadata.json`) ✓.

### 3.2 Przypisanie kadrów (zad. 2) — naprawione
Reguła ≤ 25 m zastosowana; 101–118 przypisane do Al. Tysiąclecia / Motoszko / Sokólskiej / Kombatantów (odległości zgodne z moim przeliczeniem s17), 104/105 jawnie „POZA progiem”, kierunek UNVERIFIED; **Skidelska/Wileńska/Łańcucka: 0 kadrów z wnętrza ulicy** — uczciwie. M51-117/216 ujednolicone.

### 3.3 Żywopłoty (zad. 3) — próba 26/60 wierszy (43 %)

| wiersz(e) | plik | manifest | co faktycznie widać | ocena |
|---|---|---|---|---|
| 101 | M51-101 | wlot Skidelskiej, krzewy przy płotach, palikowane drzewka, Shell | arteria z pomarańczowymi słupkami, TIR, domki, palikowane drzewka, logo Shell | ✓ |
| 103 / 204 | M51-103 | sygnalizacja, żywopłot ~1,2 m lewo, billboard | narożnik z tabliczką „ul. Michała Motoszko”, billboard, ciemne krzewy ~1,2 m po lewej; sygnalizacji nie widać | ✓ (drobna nieścisłość) |
| 107 / 207 | M51-107 | pas krzewów 1,5–3 m po prawej, Shell, Bocaro | ✓ wysoki zwarty pas zieleni po prawej przy chodniku | ✓ |
| 110 / 212 | M51-110 | iglasty pas 2–3 m po lewej, drewniany dom | drewniany dom, po lewej iglaki za siatką (>3 m, raczej drzewa niż żywopłot) | ⚠ |
| **112 / 214** | M51-112 | „niski strzyżony żywopłot 1,0–1,2 m po prawej wzdłuż chodnika” | ścieżka rowerowa, żółte barierki, **trawnik z zaparkowanymi autami — żywopłotu brak** (tak samo w s17, wiersz 214 był na liście do usunięcia) | **✗** |
| 114 / 215 | M51-114 | Circle K, bus 26, „Wspieramy polskie rolnictwo”, żywopłot ~1,5 m + ekran | ✓ stacja, autobus, billboard; żywopłotu i ekranu po prawej nie widać wyraźnie | ⚠ |
| 116 / 218 | M51-116 | autobus BKM, gęsty żywopłot 2–2,5 m za siatką | autobus BKM 768, za ogrodzeniem masa drzew/krzewów (nie formowany żywopłot) | ⚠ |
| 117 | M51-117 | krzyż przydrożny, brak żywopłotu | ✓ | ✓ |
| 118 | M51-118 | wiata 353 Sokólska / Al. Tysiąclecia, ekran obrośnięty | ✓ | ✓ |
| 127 / 223 | extra_103406 | iglasty pas ~2 m, mężczyzna z psem | ✓ szpaler tui za ogrodzeniem, raczej 2,5–3 m | ✓ |
| 128 / 224 | extra_103407 | iglasty pas ~1,5 m po prawej, brama | ✓ tuje przy bramie (~2 m) | ✓ |
| 129 / 225 | extra_103414 | liściasty pas ~1,2 m po lewej, graffiti | ✓ niski żywopłot w tle po lewej; „betonowa konstrukcja” to szafka z graffiti | ✓ |
| 130 / 232 | extra_105311 | żywopłot liściasty 2,5–3 m, Roto/ROCKWOOL | banery ✓; za siatką zarośla ~1–1,5 m pod drzewami — wysokość zawyżona | ⚠ |
| 132 / 233 | extra_105858 | pas ~1,0 m, billboardy | ✓ strzyżony żywopłot ~0,8–1 m, banery „Centrum dań na wynos” / giełda kwiatów | ✓ |
| 226 | walk_131152 | pas ~1,2 m po prawej, P/Koniec | ✓ krzewy przy chodniku, znaki P | ✓ |
| 227 | walk_131202 | iglasty pas 3–4 m po prawej | rząd świerków/tui w głębi za parkingiem (drzewa, nie front) | ⚠ |
| 228 | walk_131205 | pas ~1,2 m po lewej | ✓ krzewy przy bloku | ✓ |
| 229 | walk_131327 | strzyżony pas ~1,2 m po lewej | rabata ozdobna z krzewami i kwiatami, nie strzyżony pas | ⚠ |
| 230 | walk_131342 | pas ~1,0 m po prawej, nr 52 | tabliczka „1000-lecia Państwa Polskiego 52” ✓; po prawej niskie nasadzenia przy budynku, płotu brak | ⚠ |
| 231 | walk_125821 | pas wysokiej zieleni 4–6 m, plac zabaw | ✓ plac zabaw; po prawej skraj zadrzewienia — to nie żywopłot | ⚠ (uczciwie opisane jako „możliwy szpaler”) |

Wynik: 1 ✗, 8 ⚠ (typ/wysokość), reszta ✓. Próg „≥ 20 odcinków” formalnie spełniony (22), ale 9 odcinków (221, 222, 226–231) nie ma przypisanej ulicy (wnętrze kwartału, uczciwie POZA progiem), a 231/227 to drzewa. Odcinków przyulicznych z ulicą: 13.

### 3.4 Pliki
- **Brak w ZIP:** kadry wierszy **M51-119…126** i odcinków **M51-219…222** (Commons 20220725_123952, 123959, 124049, 125403, 125410, 125414, 125438, 132358, 132511, 132717). Manifest pisze „Plik w paczce ZIP v2”, a `ZAWARTOSC_v2.txt` przypisuje `walk_*.jpg` do 119–126 — w rzeczywistości `walk_*` to 125420, 125821, 131152, 131202, 131205, 131327, 131342, 131431 (odcinki 226–231 + 2 niewykorzystane). Pliki są CC0 na Commons — do pobrania.
- Drobne: M51-301 „2739 liściaste” vs README 2738.

### 3.5 Errata do REVIEW-NOTE (przy scaleniu)
1. **M51-214 usunąć / M51-112 = „brak żywopłotu”** (obraz: trawnik z autami).
2. Odcinki 221, 222, 226–231 — `ulica` pusta = wnętrze kwartału; **231 i 227 to drzewa/zadrzewienie, nie żywopłot**; 232 wysokość 1–1,5 m (nie 2,5–3); 229/230 rabata, nie strzyżony pas.
3. Kadry 119–126 i odcinki 219–222 — **plików brak w ZIP v2** (tylko URL Commons).
4. `overlays/*.png` — **nie są dowodem** (odwrócone N–S, zła skala znaczników). Rejestrację koron potwierdził przegląd s19 (odbicie starego zbioru + nakładka na WMS).
5. `crowns.geojson` zawiera fałszywe trafienia na zielonych autobusach/dachach — filtrować przed użyciem (agent 0170).

## 4. M53 — zabudowa (PR #50, sha 314720a8d)

Diff: 8 plików, tylko `research/mistral/p3-buildings-2/`; merge-tree czysty. `manifest.csv` i `manifest_v2.csv` **bajtowo identyczne** (duplikat). Manifest 55 wierszy: 17 OK / 13 OK-POŚREDNIE / 25 ODRZUCONY = 30 przyjętych. Kolumny `co_widac`, `kondygnacje_ze_zdjęcia`, `kondygnacje_porównanie`, `prostokat_sciany_px` dodane; k-means usunięty; typ 037–043 poprawiony na domy jednorodzinne ✓; s17-błędne 006/008 → ODRZUCONY ✓.

### 4.1 Próba — 18 przyjętych wierszy (33 % manifestu, 60 % przyjętych)

| id | adres w manifeście | zdjęcie | manifest `co_widac` | co faktycznie widać | ocena |
|---|---|---|---|---|---|
| **010** | Białostoczek 32 (geometria → Zagumienna 9/1, way 219256725) | 20230729 105139 | „na środku napis ZAGUMIENNA 9/1”, „SŁONECZNA 13” | środek = szczyt **„Zagumienna 40”**; napisu „Zagumienna 9/1” ani „Słoneczna 13” nie widać; kąt kamera→obrys 180° przy kadrze patrzącym ~320° (cel za plecami) | **✗ → ODRZUCONY** |
| 011 | Białostoczek 34 (geometria → Białostoczek 29) | 105139 | napis „Białostoczek 29” po prawej, 6 kond. | ✓ napis „BIAŁOSTOCZEK 29” na szczycie po prawej; rzędów okien ~5 (6 niepewne) | ✓ (adres do poprawy) |
| 012 | Białostoczek 27 (geometria → Zagumienna 40) | 105139 | napis „Zagumienna 40”, 4 rzędy okien | ✓ napis; szczyt bez okien — **kondygnacji nie da się policzyć** | ✓ / kondygnacje UNVERIFIED |
| 013 | Białostoczek 7 | 20221119 080708 | blok z czerwonymi balkonami lewo, STOP, krzyż | ✓ | ✓ |
| 014 | Białostoczek 11 (geometria → Białostoczek 4/1) | 080747 | tabliczka „4/1”, świerk, ogrodzenie | ✓ budynek za świerkiem i zielonym płotem, mała tabliczka | ✓ (adres do poprawy) |
| 019 | Białostoczek 21 (poczta) | 080519 | Poczta Polska, „21”, 2 kond. | ✓ | ✓ |
| 020 | Białostoczek 22 | 20241229 112510 | punktowiec, mural ks. Sopoćki, 10 rzędów | ✓ mural „Błogosławiony ks. Michał Sopoćko”; liczę ~11 rzędów balkonów | ✓ |
| 021 | Białostoczek 13A | 080601 | szary punktowiec, „13A”, 12 rzędów | punktowiec + szeroki blok, piekarnia/cukiernia w parterze; góra ucięta kadrem — **12 rzędów niepoliczalne** | ⚠ |
| **029** | Al. Tysiąclecia 10 | „Tysiąclecia 10 Białystok 3” | „w parterze Biedronka (witryna i szyld), przed budynkiem chodnik i trawnik”, d = 1,9 m | logo **Biedronki na dachu**, parter zasłonięty drzewami, zdjęcie z dużej odległości (d = 1,9 m niemożliwe) | **✗ opis** (cel ✓) |
| 030 | Andersa 46 JRG-2 | 20240626 103137 | parterowy, bramy garażowe, napis PSP | napis „PAŃSTWOWA STRAŻ POŻARNA” ✓; bramy niewidoczne (drzewa/tuje) | ✓ |
| **035** | Al. Tysiąclecia 6 | 20240530 122453 | żółtozielony biurowiec = Tysiąclecia 6; „8” na KONTEX w tle | **numer „8” jest na narożniku tego samego zielonego budynku** (przy wejściu) → raczej Tysiąclecia 8 (OSM way 264944866) | **✗ cel niepewny** |
| 037 | Skidelska 32 | 20240401 110819 | domy 2-kond. po obu stronach, cel lewo | ✓ | ✓ |
| 040 | Kowieńska 4 | 112303 | dom 2-kond. lewo, tabliczka ul. Grodzieńska | ✓ | ✓ |
| 044 | Al. Tysiąclecia 10A | „Tysiąclecia 10A Białystok 1” | wieżowiec 15 rzędów, „Rog…owsk” | ✓ (~15 rzędów); napisy są na wygrodzeniu budowy, nie w parterze; d = 4,9 m niemożliwe | ✓ |
| 045 | Zagumienna 20 | Cukiernia U Lecha | żółty pawilon, szyld, „20” | ✓ | ✓ |
| 046 | Andersa 38 (Biazet) | 20200711 073045 | 12 rzędów, napis BIAZET | ✓ (ochra, pionowy napis BIAZET); zdjęcie zza płotu z daleka (d 17,6 m wątpliwe) | ✓ |
| 047 | Andersa 38a | 20201102 152422 | 2-kond. szary, parking | ✓ | ✓ |
| 049 | Radzymińska 12 | Biedronka | pawilon, Biedronka, APTEKA | ✓ | ✓ |

Wynik: **3 ✗** (010 zły cel, 029 zmyślony opis, 035 prawdopodobnie zły budynek), 1 ⚠, 14 ✓. Wzorzec Mistrala nadal obecny: część `co_widac` to tekst wygenerowany bez obrazu (010, 029). Kolory 014/021/035 wiarygodne (sprawdzone wzrokowo), reszta uczciwie UNVERIFIED.

### 4.2 Weryfikacja OSM (rekasygnacje)
Lokalny `podlaskie-261108.osm.pbf`: way 219256725 = Zagumienna 9/1, 219353929 = Białostoczek 29, 219353921 = Zagumienna 40, 219824348 = Białostoczek 4/1, 219256879 = Poczta Polska Białostoczek 21, 215470474 = Białostoczek 13A (12 kond.), 211766102 = Białostoczek 22. **Geometria (lat/lon, lod1_id, osm_way, mh) rekasygnacji jest poprawna, ale kolumna `adres` w 010/011/012/014 nadal pokazuje stary adres** (Białostoczek 32/34/27/11).

### 4.3 Inne
- `kamera_d_m`/`kamera_kat_deg` dla zdjęć Borawskiego i Rakoona z „object location” (007, 029, 044, 045, 046, 049) to odległość od pozycji obiektu, nie kamery — nieprzydatne (029: 1,9 m, 045: 1,1 m przy zdjęciach z ulicy/z daleka).
- Licencja Borawskiego: 4 wiersze „CC BY-SA 3.0”, 2 „CC BY-SA 3.0 (tylko referencja)” — ujednolicić (referencja).
- `INDEX.csv`: `prostokat_sciany_px` w skali kopii 1920 px (×5/6 dla ZIP) — opisane ✓.

### 4.4 Errata do REVIEW-NOTE (przy scaleniu)
1. **M53-010 → ODRZUCONY** (napisu Zagumienna 9/1 nie ma; cel za kamerą).
2. **M53-035 → ODRZUCONY/UNVERIFIED** (numer „8” na zielonym budynku; prawdopodobnie Tysiąclecia 8, nie 6).
3. M53-029: `co_widac` błędny (Biedronka na dachu, nie w parterze; zdjęcie z daleka); cel i 12+ kondygnacji — ESTIMATED.
4. Kolumna `adres`: 010 → Zagumienna 9/1 (ale ODRZUCONY), 011 → **Białostoczek 29**, 012 → **Zagumienna 40**, 014 → **Białostoczek 4/1**.
5. M53-012 i M53-021: kondygnacje niepoliczalne na zdjęciu → UNVERIFIED (mh LoD1 obowiązuje).
6. `kamera_d_m`/`kąt` dla 007/029/044/045/046/049 — UNVERIFIED (pozycja obiektu, nie kamery).
7. Po erracie: **28 przyjętych** (16 OK + 12 OK-POŚREDNIE) — próg 30 niespełniony o 2; `manifest_v2.csv` = duplikat `manifest.csv`.

## 5. FIX-9 na origin
Sprawdzone `git log origin/main..origin/<gałąź>`: `research/mistral-p2-surfaces-2`, `research/mistral-p11-dojlidy-photos`, `research/mistral-p8-restrictions-3`, `research/mistral-p6-dojlidy-gates` — **0 commitów ponad main**. Gałęzie ze slashem: `research/mistral/p6-dojlidy-gates` (c3e5f4fcc, 15:49 — duplikat f7a4f289f z main, znany z s18) i `research/mistral/p2-surfaces-2` (5179c771e, 12:55 — stary szkielet). **Brak FIX-9 na origin** — bloki z `MISTRAL-FIXES-9.md` nadal do wykonania.

## 6. Pliki
- Bloki dla Mistrala: `docs/owner/MISTRAL-FIXES-10.md` (M51-FIX-2, M53-FIX-2; M50 bez bloku).
- Arkusze kontrolne (scratchpad, nie w repo): nakładka WMS koron/zwartej zieleni w oknie w1 oraz arkusze 2×2 kadrów.
