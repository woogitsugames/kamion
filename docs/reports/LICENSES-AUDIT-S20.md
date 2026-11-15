# Audyt licencji i atrybucji — sesja 20 (X1, 2026-11-14)

Gałąź `docs/licenses-audit-s20`, baza: `main` @ `f2d50b6a9`. Zakres: tylko dokumenty (`docs/LICENSES.md`, ten raport, `docs/owner/ATTRIBUTION-SCREEN-DRAFT.md`). Kodu, danych ani zasobów nie zmieniano. Każde twierdzenie ma wskazany plik:linia albo URL obecny w repo; czego nie da się potwierdzić z repo, ma znacznik `UNVERIFIED`.

## 0. Inwentarz (krok 1)

### 0.1 Metoda
- `git ls-files` + `grep -rIl -i "licen[cs]e\|CC BY\|CC0\|ODbL\|attribution\|atrybucj"` po `research/**`, `art-source/**`, `Data/SourceManifests/**`, `game/Assets/**`, `tools/**`, `docs/adr/*.md`.
- Odczyt kolumn `licencja` / `licencja_url` / `zrodlo` wszystkich `research/**/manifest.csv`, `asset_manifest.csv`, `download_list.csv` (34 pliki CSV; część z separatorem `;`).
- Audyt maszynowy `uv run --project tools/licenses python tools/licenses/audit.py` (reguła zasobu: `tools/licenses/audit.py:1-25`) i testy `uv run --project tools/licenses pytest tools/licenses/tests -q`.
- Starsze gałęzie: `origin/mistral/14-licenses` (`a2466051b`) i `origin/mistral/31-licenses-audit` (`55457999b`) — porównane z `main` (`git diff HEAD origin/<gałąź>`).

### 0.2 Wynik audytu maszynowego na `main` (przed tą gałęzią)
| Miara | Wartość |
|---|---|
| zasoby śledzone (obraz/audio/model/font, bez `generated`) | 2603 (audio 132, model 16, obraz 2454, font 1) |
| pokryte wpisem w `docs/LICENSES.md` | 2425 |
| **bez wpisu** | **178** |
| podejrzane (Fab/Google w nazwie/treści) | 0 |
| `pytest tools/licenses/tests` | **1 failed, 8 passed** — `test_all_tracked_assets_covered_in_licenses_md` (`tools/licenses/tests/test_audit.py:85-91`, twardy fail od integracji r5) |

Zasoby bez wpisu (178): `research/gptpro/3-s8-signs/files/*.jpg` 145, `research/g7-street-greenery/files/*` 12, `research/gptpro/2-next-regions/files/G2-A0*.jpg` 9, `research/g5-street-furniture/files/*` 7, `game/Assets/_Project/Rendering/Resources/Night/T_Night*.png` 4, `research/g10-truck-restrictions/files/G10-S01_…png` 1.

### 0.3 Starsze gałęzie audytu licencji
- `mistral/14-licenses` (`a2466051b`): wiersze `truck-brand-marks-a2`, `truck-exterior-qa-0115`, `door_interface.json` i raport `AUDIT-LICENSES-2026-11-12-mistral.md` — **już w `main`** (`docs/LICENSES.md:144-148`, raport w `docs/reports/`). Nic do przeniesienia.
- `mistral/31-licenses-audit` (`55457999b`): `tools/licenses/*` i sekcja „Audyt śledzonych zasobów — M31” — **już w `main`** w wersji nowszej (lider poprawił w integracji r5: twardy fail zamiast `xfail`, test zbyt szerokich wzorców `*photo*`; `git diff HEAD origin/mistral/31-licenses-audit -- tools/licenses/tests/test_audit.py`). Gałąź jest starsza niż `main` (brak wierszy `audio-elevenlabs-sfx-v3-regen04`, `world-vehicle-lod-atlas`, sekcji ADR 0162). Nic do przeniesienia.
- Twierdzenia raportu `AUDIT-LICENSES-2026-11-12-mistral.md` sprawdzone: `make_logos.py` i SVG istnieją (`art-source/truck/brand/{bielik,narew,trakt}.svg`), wiersze w rejestrze są (`docs/LICENSES.md:144-148`) — **potwierdzone**.
- Twierdzenia `FAB-PATCH-LICENSE-2026-11-10.md` dotyczące publicznego repo: repo `woogitsugames/kamion` jest **publiczne** (`gh api repos/woogitsugames/kamion` → `"visibility": "public"`, 2026-11-14) — wniosek „nic z Fab w gicie” pozostaje kluczowy. Uwaga: `docs/11_DECYZJE_WLASCICIELA.md:17` (D11) nadal mówi „Prywatne GitHub” — rozbieżność do decyzji właściciela (§3, R-P1-5).

### 0.4 Źródła znalezione w repo (podsumowanie; szczegóły w tabeli zbiorczej `docs/LICENSES.md`)
- **Dane geograficzne do buildu:** OSM (Geofabrik), GUGiK NMT / ortofoto / BDOT10k / LoD1 2024 / LoD2 2017 — dla **dwóch** regionów: `bialystok-industrial-c` (w rejestrze) i `bialystok-dojlidy` (manifesty `Data/SourceManifests/*dojlidy*` — **brak w rejestrze**).
- **Referencje (nie do buildu):** Mapillary, KartaView, Panoramax, Wikimedia Commons, Openverse/Flickr, GUGiK WMS/WCS, ArcGIS Miasta Białystok, dokumenty BIP/ZDM/BKM/GDDKiA, akty Dz.U./ELI/ISAP, regulaminy EKG ONZ i EUR-Lex, Freesound/OpenGameArt/BBC RemArc (audio), katalogi producentów i prasa (tylko fakty), zdjęcia wklejone przez właściciela (tylko obserwacje).
- **Zasoby w buildzie:** Poly Haven (CC0), Fab/Megascans (Fab Standard, lokalnie poza gitem), ElevenLabs SFX (plan płatny), synteza własna, Inter (OFL), DejaVu Sans Bold (rasteryzowany), Unity + pakiety (glTFast Apache 2.0, URP Unity Companion License, pozostałe `UNVERIFIED`), własne generatory.
- **Nieużyte mimo wzmianek:** BDL (Bank Danych o Lasach), IMGW — 0 wystąpień poza instrukcją dla Mistrala (`docs/owner/MISTRAL-TASKS-10.md:204`); ambientCG — dopuszczony, nieużyty (`docs/LICENSES.md:82`); Suno — tylko zakaz w `CLAUDE.md`.

### 0.5 Stan po tej gałęzi
`docs/LICENSES.md`: tabela zbiorcza 40 źródeł (`docs/LICENSES.md:382`), nowe sekcje: region Dojlidy (:431), pakiety research śledzone w repo (:447), tekstury nocy (:461), silnik i pakiety Unity (:467), uwagi spójności (:473). Audyt maszynowy: **2603/2603 pokryte, 0 bez wpisu, 0 podejrzanych**; `pytest tools/licenses/tests` **9 passed**; `tests/gis/test_cc0_scans.py`, `test_fab_not_tracked.py`, `test_fab_atlas.py` — zielone (2026-11-14).

## 1. Teksty licencji użyte w ocenie

Teksty pobrane 2026-11-14 bez nagłówków identyfikujących projekt: `https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt`, `https://creativecommons.org/licenses/by/4.0/legalcode.txt`, `https://opendatacommons.org/licenses/odbl/1-0/`. Cytaty dosłowne (oryginał angielski), wnioski w §2.

**CC BY-SA 4.0, §1(a) — definicja Adapted Material:**
> „Adapted Material means material subject to Copyright and Similar Rights that is derived from or based upon the Licensed Material and in which the Licensed Material is translated, altered, arranged, transformed, or otherwise modified in a manner requiring permission under the Copyright and Similar Rights held by the Licensor.”

**CC BY-SA 4.0, §3(b) ShareAlike:**
> „In addition to the conditions in Section 3(a), if You Share Adapted Material You produce, the following conditions also apply. 1. The Adapter's License You apply must be a Creative Commons license with the same License Elements, this version or later, or a BY-SA Compatible License. 2. You must include the text of, or the URI or hyperlink to, the Adapter's License You apply. […] 3. You may not offer or impose any additional or different terms or conditions on, or apply any Effective Technological Measures to, Adapted Material that restrict exercise of the rights granted under the Adapter's License You apply.”

**CC BY 4.0 (brzmienie takie samo w BY-SA 4.0), §3(a) Attribution:**
> „1. If You Share the Licensed Material (including in modified form), You must: a. retain the following if it is supplied by the Licensor with the Licensed Material: i. identification of the creator(s) of the Licensed Material […]; ii. a copyright notice; iii. a notice that refers to this Public License; iv. a notice that refers to the disclaimer of warranties; v. a URI or hyperlink to the Licensed Material to the extent reasonably practicable; b. indicate if You modified the Licensed Material and retain an indication of any previous modifications; and c. indicate the Licensed Material is licensed under this Public License, and include the text of, or the URI or hyperlink to, this Public License. 2. You may satisfy the conditions in Section 3(a)(1) in any reasonable manner based on the medium, means, and context in which You Share the Licensed Material.”

**ODbL 1.0 — definicje:**
> „“Derivative Database” – Means a database based upon the Database, and includes any translation, adaptation, arrangement, modification, or any other alteration of the Database or of a Substantial part of the Contents. This includes, but is not limited to, Extracting or Re-utilising the whole or a Substantial part of the Contents in a new Database.”
>
> „“Produced Work” – a work (such as an image, audiovisual material, text, or sounds) resulting from using the whole or a Substantial part of the Contents (via a search or other query) from this Database, a Derivative Database, or this Database as part of a Collective Database.”
>
> „“Publicly” – means to Persons other than You or under Your control by either more than 50% ownership or by the power to direct their activities […]”

**ODbL 1.0 §4.3–§4.6 (wyciąg):**
> „4.3 […] if you Publicly Use a Produced Work, You must include a notice associated with the Produced Work reasonably calculated to make any Person that uses, views, accesses, interacts with, or is otherwise exposed to the Produced Work aware that Content was obtained from the Database, Derivative Database, or the Database as part of a Collective Database, and that it is available under this License.”
>
> „4.4 Share alike. a. Any Derivative Database that You Publicly Use must be only under the terms of: i. This License; ii. A later version of this License similar in spirit to this License; or iii. A compatible license. […] c. Derivative Databases and Produced Works. A Derivative Database is Publicly Used and so must comply with Section 4.4. if a Produced Work created from the Derivative Database is Publicly Used. d. Share Alike and additional Contents. For the avoidance of doubt, You must not add Contents to Derivative Databases under Section 4.4 a that are incompatible with the rights granted under this License.”
>
> „4.5 Limits of Share Alike. […] b. Using this Database, a Derivative Database, or this Database as part of a Collective Database to create a Produced Work does not create a Derivative Database for purposes of Section 4.4; and c. Use of a Derivative Database internally within an organisation is not to the public and therefore does not fall under the requirements of Section 4.4.”
>
> „4.6 Access to Derivative Databases. If You Publicly Use a Derivative Database or a Produced Work from a Derivative Database, You must also offer to recipients of the Derivative Database or Produced Work a copy in a machine readable form of: a. The entire Derivative Database; or b. A file containing all of the alterations made to the Database or the method of making the alterations to the Database (such as an algorithm), including any additional Contents, that make up all the differences between the Database and the Derivative Database.”

Polska ustawa o prawie autorskim (art. 4 — akty normatywne i urzędowe dokumenty/materiały; art. 33 — utwory wystawione na stałe w miejscach publicznych): tekstu ustawy **nie ma w repo** i nie był pobierany; repo powołuje art. 4 w manifestach research (np. `research/g5-street-furniture/sources.md:45`). Wnioski oparte na ustawie są niżej parafrazą z oznaczeniem `UNVERIFIED`.

## 2. Share-alike: co trafia do buildu, a co jest tylko referencją

| Sytuacja w projekcie | Ocena wg tekstu licencji | Wniosek |
|---|---|---|
| **Zdjęcia CC BY-SA (Mapillary, KartaView, Panoramax, Commons BY-SA) oglądane przez artystę/agenta**; odczytane proporcje, kolory jako liczby, układ, treść tablic; geometria i tekstury rysowane od zera (`docs/LICENSES.md:78`, :165-167, :380; `tools/refs/README.md:29-37`) | Adapted Material wymaga, by Licensed Material był „modified **in a manner requiring permission**” (§1(a)). Fakty (treść tablicy, wymiar, kolor jako liczba) i wygląd odtworzony własnymi środkami nie wymagają zgody autora zdjęcia — interpretacja, `UNVERIFIED` prawnie | **Share-alike nie ma zastosowania**, o ile żaden piksel zdjęcia CC BY-SA nie trafia do tekstur (ADR 0065; klasa `reference_only_owner_decision_for_pixels` w `tools/refs/README.md:32`). Zgodne ze stanem repo. |
| Piksele CC BY-SA w teksturze gry (dziś **brak**; zakazane bez decyzji właściciela) | Tekstura = Adapted Material → §3(b)(1) licencja adaptera BY-SA; §3(b)(3) zakaz dodatkowych warunków i „Effective Technological Measures” | Tekstura musiałaby być na BY-SA i dawać się wyodrębnić bez ograniczeń — konflikt z regulaminami sklepów. **Utrzymać zakaz.** |
| **Wycinki Mapillary i Commons BY-SA w publicznym repo** (`research/gptpro/3-s8-signs/files/` — 113 plików; `research/g5-street-furniture/files/G5-020…`, `G5-021…`; `artifacts/**/refs/**`) | Udostępnianie („Share”) materiału, częściowo przyciętego. §3(a)(1): autor, licencja, link, informacja o zmianach; wycinek = Adapted Material → §3(b): ta sama licencja | Spełnione przez rejestry: `asset_manifest.csv` ma kolumny `autor`, `licencja`, `url_źródła`, `modyfikacje`; G5 — `sources.md:36-39`. Ryzyko niskie (R-P2-1). |
| **Graf dróg, budynki, tło dalekie w `Data/Regions/*`** (wyciąg z OSM + GUGiK) | „Extracting or Re-utilising … in a new Database” = Derivative Database (definicja; §4.4(b)) | Baza pochodna ODbL, publiczna w repo → §4.4(a): licencja ODbL (lub zgodna). Rejestr już to zapisuje (`docs/LICENSES.md:13`, :32). |
| **Pliki nawigacji w APK** (`Nav/<region>.bytes`, `<region>_route.bytes`; `docs/LICENSES.md:152-153`) | Derivative Database dystrybuowana graczom („Publicly”) → §4.4(a) i §4.6 | **Share-alike ma zastosowanie.** Dane nawigacji na ODbL + oferta dla odbiorców: kopia bazy albo opis metody zmian (§4.6(a)/(b)). Publiczne repo z generatorami (`tools/ui/build_nav_map.py`, `tools/worldgen/navgraph/build_route_graph.py`) może spełniać §4.6(b), ale oferta musi dotrzeć do odbiorców gry (R-P0-2). |
| **Świat 3D, render, mapa w kabinie** | Produced Work. §4.5(b): tworzenie Produced Work nie tworzy Derivative Database; §4.4(c): jeśli Produced Work z bazy pochodnej jest używany publicznie, baza pochodna podlega §4.4; §4.3: wymagana informacja | Siatek świata **nie trzeba** licencjonować na ODbL; ale `Data/Regions/*` musi spełniać §4.4/§4.6, a gra musi pokazać informację z §4.3 (R-P0-1). |
| **Dane GUGiK CC BY 4.0 (LoD1/LoD2) w bazie pochodnej ODbL** | ODbL §4.4(d): nie wolno dodawać treści niezgodnych z prawami ODbL; CC BY 4.0 §3(a) wymaga atrybucji, a §2(a)(5) (parafraza, nie cytowane) zakazuje dodatkowych ograniczeń | Zgodność **nierozstrzygnięta w repo** → `LEGAL_REVIEW_REQUIRED` (R-P1-1). Praktycznie: zachować pochodzenie pól (`src: …`) i atrybucję GUGiK obok OSM. |
| **Baza G3 (ODbL) → treść tablic w grze** | Tekst tablic = Produced Work (§4.5(b)) → informacja z §4.3 | Atrybucja G3 w ekranie „Informacje” (wymóg już w `docs/LICENSES.md:380`). |
| **Skany CC0, synteza własna, ElevenLabs, Fab** | brak share-alike | Bez obowiązków SA; CC0 i Fab bez atrybucji. |

## 3. Luki i ryzyka

Skala: **P0** = przed jakąkolwiek dystrybucją poza urządzenia właściciela (testy zamknięte, sklep); **P1** = przed wydaniem w sklepie / przegląd prawny; **P2** = higiena, niskie ryzyko.

### P0

**R-P0-1. Brak ekranu „Informacje”/licencji w grze.** W kodzie gry jedyna atrybucja to „© OpenStreetMap contributors” na pełnej mapie nawigacji (`game/Assets/_Project/UI/Navigation/NavText.cs:9`; komentarze `NavMapData.cs:12`, `RouteGraph.cs:16`). Brak: informacji, że dane są na ODbL (§4.3), atrybucji GUGiK CC BY 4.0 (§3(a)(1)), atrybucji bazy G3, tekstu Apache 2.0 dla glTFast, tekstu OFL dla Inter. ADR 0002 wymaga atrybucji OSM/GUGiK w grze (`docs/adr/0002-data-sources-no-google.md:4`).
*Działanie (lider):* ekran „Informacje” wg `docs/owner/ATTRIBUTION-SCREEN-DRAFT.md` + pełne teksty Apache 2.0 i OFL 1.1 w buildzie. Dopóki APK trafia tylko na telefony właściciela, „Publicly” z ODbL nie zachodzi (definicja „Publicly”), więc blokuje dopiero pierwszą dystrybucję.

**R-P0-2. Oferta bazy pochodnej OSM (ODbL §4.6) dla danych nawigacji w APK.** Pliki `.bytes` nawigacji to Derivative Database w buildzie. Rejestr ma tylko `LEGAL_REVIEW_REQUIRED` (`docs/LICENSES.md:152-153`). Repo jest dziś publiczne, ale D11 mówi „Prywatne GitHub” (`docs/11_DECYZJE_WLASCICIELA.md:17`) — po zamknięciu repo nie będzie czym spełnić §4.6.
*Działanie (właściciel + lider):* (a) wybrać miejsce publikacji bazy pochodnej lub pliku zmian/algorytmu (publiczne repo z generatorami albo osobne archiwum danych regionu na ODbL); (b) w ekranie „Informacje” umieścić ofertę z adresem; (c) oznaczyć dane nawigacji licencją ODbL; (d) ADR.

### P1

**R-P1-1. Zgodność CC BY 4.0 (GUGiK LoD1/LoD2) i danych z art. 40a Pgik z ODbL w jednej bazie pochodnej** (`Data/Regions/*/buildings.geojson`, `roads.graph.json`, far-field). Manifesty zaznaczają, że podstawa ustawowa jest cytowana ze źródeł wtórnych, nie z ISAP (`Data/SourceManifests/gugik-nmt-2025-bialystok-dojlidy.json`, pole `license_status`). *Działanie:* przegląd prawny przed sklepem; do tego czasu podwójna atrybucja i pochodzenie pól.

**R-P1-2. Region Dojlidy nie był w rejestrze** (manifesty `*dojlidy*` bez wpisu do 2026-11-14). *Naprawione w tej gałęzi* (`docs/LICENSES.md:431`). *Działanie:* test w `tools/licenses` sprawdzający, że każdy `Data/SourceManifests/*.json` ma ID w rejestrze (dziś test pilnuje tylko plików zasobów).

**R-P1-3. Pakiety Unity i ekran powitalny — `UNVERIFIED`.** Licencje pakietów runtime (Burst, Collections, Mathematics, Input System, uGUI, AI Navigation) nie są w repo; ekran powitalny Unity włączony (`game/ProjectSettings/ProjectSettings.asset:20-21`); czy Unity wymaga w grze informacji o bibliotekach zewnętrznych — nieustalone. *Działanie:* na maszynie z Unity odczytać `LICENSE.md` pakietów z `Library/PackageCache` i informacje o licencjach zewnętrznych Unity; dopisać do rejestru i ekranu.

**R-P1-4. ElevenLabs — Service-Specific Terms SFX nieprzeczytane** (`docs/LICENSES.md:127-133`). Dźwięki są w buildzie. *Działanie:* odczytać warunki SFX dla planu Pro, zapisać cytat; zachować dowód aktywnego planu w dniu generacji (są notatki właściciela).

**R-P1-5. Fab Standard — pełny EULA nieprzeczytany, repo publiczne.** `FAB-PATCH-LICENSE-2026-11-10.md` opierał się na streszczeniu, które samo zastrzega, że „is not legally binding”. Ochrona przed wyciekiem działa (`tests/gis/test_fab_not_tracked.py` zielony; `fab-content-hashes.json`). *Działanie:* przed sklepem przeczytać EULA po zalogowaniu (`docs/LICENSES.md:205`); właściciel potwierdza widoczność repo (D11 vs stan faktyczny).

**R-P1-6. Odwzorowanie realnych obiektów i projektów** (budynki, wiadukty, wiaty BKM wg „wzoru plastycznego”). Rejestr mówi, że z dokumentów przetargowych wzięto tylko liczby (`docs/LICENSES.md:378`), ale model wiaty odtwarza wygląd projektu autorskiego (projektanci wskazani w `research/g5-street-furniture/manifest.csv`, G5-004/G5-005), a obiekty hero (Kwadrat Park, remiza JRG2, wiadukty) — wygląd budynków. Repo nie zawiera analizy dozwolonego użytku utworów wystawionych w przestrzeni publicznej (art. 33 ustawy — parafraza, `UNVERIFIED`). *Działanie:* punkt przeglądu prawnego „swoboda panoramy w grze komercyjnej”; do tego czasu bez logo, nazw i napisów firmowych (już przestrzegane).

### P2

**R-P2-1. Redystrybucja plików osób trzecich w publicznym repo (research).** 113 wycinków Mapillary CC BY-SA 4.0 i 2 zdjęcia Commons CC BY-SA 3.0 — atrybucja w manifestach wystarcza (§3(a)(2) „any reasonable manner”). *Działanie:* każdy nowy pakiet research z `asset_manifest.csv` (autor/licencja/URL/modyfikacje).

**R-P2-2. Kopie dokumentów o niepewnym statusie praw:** regulaminy EKG ONZ (P4-001, P4-002, P4-010 — „art. 4 … brak praw autorskich” w `research/gptpro/p4-truck-regulations/manifest.csv` vs „© UNECE/ONZ — publikacja z atrybucją dozwolona” w `research/mistral/p4-truck-regulations/manifest.csv`); rysunki przetargowe BKM/ZDM (`research/g5-street-furniture/sources.md:45-49`: „art. 4 pkt 2 pr. aut. - interpretacja do potwierdzenia”). Nie trafiają do buildu. *Działanie:* zastąpić kopie w publicznym repo linkami + SHA256 albo potwierdzić zasady UNECE i art. 4.

**R-P2-3. Niespójne lub niepotwierdzone licencje referencji:** Panoramax „CC BY-SA 2.0 FR” dla 3 kadrów z `panoramax.openstreetmap.fr` (`research/mistral/p9-furniture-3/manifest.csv:55-56`, :66; autor „nieoznaczony w metadanych”) vs CC-BY-SA-4.0 w pozostałych pakietach — `UNVERIFIED`; KartaView — licencja jako stała w kodzie (`tools/refs/open_sources.py:65`, :89); „ODbL 1.1” w `research/gptpro/p7-s8-signs-2/LICENSE-DATA.md:7` (błąd zapisu). ArcGIS Miasta Białystok i GTFS BKM bez licencji — tylko referencja (`tools/refs/bialystok_open_data.py:27`; `research/gptpro/p9-street-furniture-2/manifest.csv:32`). *Działanie:* przy najbliższym użyciu odczytać licencję u źródła i poprawić manifesty.

**R-P2-4. Materiały NC i „wszelkie prawa zastrzeżone” wśród referencji.** BBC RemArc (27 pozycji, `research/gptpro/9-audio-refs/manifest.csv:81-107`), CC BY-NC i RemArc w `research/gptpro/p5-audio-refs-2/manifest.csv` (16 wierszy), CC BY-NC-SA 2.0 (2 kadry Flickr — REJECTED, `research/mistral/p11-dojlidy-photos/manifest.csv:154-155`), zdjęcia wklejone przez właściciela (`docs/refs/owner-aerials-2026-11-10.md:3`). Żaden plik nie jest w gicie (0 plików audio w `research/`) ani w buildzie. *Działanie:* zasada „tylko link/obserwacja”; nigdy do `art-source` ani `game/`.

**R-P2-5. Materiał z Google (zakaz ADR 0002):** w śledzonych plikach **nie znaleziono** adresów Google Maps/Street View/Earth/3D Tiles (`git grep -iE` po `maps.google`, `google.*/maps`, `goo.gl/maps`, `maps.app.goo`, `streetview`, `googleusercontent`, `earth.google`, `tile.googleapis`, `ggpht` — 0 wyników, 2026-11-14). Wcześniej odrzucony plik wyglądający na zrzut z panoramy Google: `docs/LICENSES.md:288`. `google_transit.zip` w P9 to eksport GTFS Miasta Białystok (nazwa formatu, nie treść Google) — `research/gptpro/p9-street-furniture-2/sources.md:74`. Ograniczenie: z repo nie da się wykluczyć, że któreś zdjęcie Commons/Openverse samo jest zrzutem z usług Google — `UNVERIFIED`.

**R-P2-6. Spójność `docs/LICENSES.md`:** sprzeczne akapity o CC0 w sekcji świata (`docs/LICENSES.md:157` vs :159), sekcja „Fonts” z wierszami zasobów ciężarówki (:140-153), dwie kory sosny o podobnych ID z różnych źródeł (`pine_bark` Poly Haven CC0, :100; `pine-bark` Fab, :223 — odrzucona do pni, :253). Opisane w „Uwagi spójności” (:473); treści historycznych nie zmieniano.

**R-P2-7. Marki w danych pomocniczych.** Opisy referencji audio z markami pojazdów (np. M55-001 w `research/mistral/p5-audio-3/manifest.csv`), nazwy firm w danych Dojlidy (`tools/worldgen/regions.py`). W kodzie gry brak (`git grep` w `game/`). *Działanie:* nie przenosić do tekstów w grze (zasada 8 CLAUDE.md).

## 4. Rekomendacje dla lidera i właściciela (kolejność)

1. **Właściciel:** decyzja o widoczności repo (publiczne dziś vs D11 „prywatne”) — od niej zależą R-P0-2 i R-P1-5.
2. **Lider:** ekran „Informacje” z tekstem z `docs/owner/ATTRIBUTION-SCREEN-DRAFT.md` + teksty Apache 2.0 i OFL 1.1 (R-P0-1); oferta danych ODbL (R-P0-2); ADR dla obu.
3. **Lider (maszyna z Unity):** licencje pakietów i informacje o bibliotekach Unity, decyzja o ekranie powitalnym (R-P1-3).
4. **Właściciel:** Service-Specific Terms ElevenLabs SFX i pełny Fab EULA — cytaty do rejestru (R-P1-4, R-P1-5).
5. **Przed sklepem:** jeden przegląd prawny: R-P1-1 (ODbL × CC BY 4.0 × Pgik), R-P1-6 (swoboda panoramy), R-P2-2 (art. 4, UNECE).
6. **Higiena:** test „każdy manifest ma wpis w rejestrze”; poprawki manifestów z R-P2-3.

## 5. Pozycje `UNVERIFIED` w tym audycie
- Panoramax „CC BY-SA 2.0 FR” (3 kadry P9 Mistrala); data nalotu mozaiki WMS GUGiK; licencja danych ArcGIS Miasta Białystok i GTFS BKM.
- Status praw regulaminów EKG ONZ (sprzeczne opisy) i dokumentów przetargowych (art. 4 — interpretacja).
- Unity: warunki ekranu powitalnego, informacje o bibliotekach zewnętrznych, licencje pakietów runtime; czy Unity Companion License (fragmenty URP) wymaga informacji w grze.
- ElevenLabs Service-Specific Terms SFX; pełny Fab EULA (`LEGAL_REVIEW_REQUIRED`).
- Licencja Blendera jako narzędzia (nieopisana w repo; wyniki skryptów traktowane jako własne).
- Wnioski z ustawy o prawie autorskim (art. 4, art. 33) — tekst ustawy nie był czytany.
- Czy któreś zdjęcie Commons/Openverse nie jest zrzutem z usług Google.
