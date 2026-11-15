# Ekran „Informacje” — projekt tekstu atrybucji (szkic X1, s20, 2026-11-14)

Źródło prawdy: tabela zbiorcza w `docs/LICENSES.md` (sekcja „Tabela zbiorcza źródeł (audyt X1, s20)”) i raport `docs/reports/LICENSES-AUDIT-S20.md`. Tekst poniżej (blok „DO WKLEJENIA”) jest gotowy do wstawienia w grze; pozycje w nawiasach kwadratowych `[WARUNKOWO: …]` wstawić tylko, gdy warunek jest spełniony w danym buildzie. Znacznik `UNVERIFIED` = treść do potwierdzenia przed wydaniem (nie wklejać bez sprawdzenia).

**Stan s21 (ADR 0230):** tekst w grze żyje w `game/Assets/_Project/UI/Resources/About/attributions.txt` (ten szkic jest historyczny). Dodane: pozycja „Bank Danych o Lasach” (Regulamin BDL cz. V: źródło, czas wytworzenia i pozyskania), dobrowolna pozycja „Zdjęcia referencyjne” (Mapillary contributors CC BY-SA 4.0, Panoramax, KartaView — bez logo, bo gra nie serwuje zdjęć ani danych z API Mapillary), link CC BY-SA 4.0. Dane Miasta Białystok — poza grą (warunki BIP: zakaz modyfikacji treści). Wymagania pilnują dane `tools/licenses/attribution_requirements.json` + pytest + `tools/about-runner`.

Zasady techniczne ekranu (wynikające z licencji):
- Ekran dostępny z menu głównego i z pauzy, bez połączenia z siecią (adresy jako tekst — ODbL 4.3a dopuszcza zwykły tekst URI, gdy hiperłącza nie są możliwe).
- Pełne teksty licencji **Apache 2.0** (glTFast) i **SIL OFL 1.1** (Inter) dołączone do buildu jako tekst do przewinięcia (OFL leży już w `game/Assets/_Project/UI/Resources/Fonts/Inter-OFL.txt`; tekst Apache 2.0 trzeba skopiować z pakietu glTFast — `LICENSE.md` w pakiecie, poza repo).
- Mapa nawigacji zachowuje własny podpis „© OpenStreetMap contributors” (`game/Assets/_Project/UI/Navigation/NavText.cs:9`).

---

## DO WKLEJENIA

### Mapy i dane

**OpenStreetMap**
Dane map, dróg, nazw ulic i budynków: © OpenStreetMap contributors.
Gra zawiera informacje z bazy OpenStreetMap, udostępnione na licencji Open Database License (ODbL) 1.0.
www.openstreetmap.org/copyright · opendatacommons.org/licenses/odbl/1-0/
Dane pochodne użyte w grze (sieć dróg i nawigacja) są udostępnione na licencji ODbL: [ADRES — do ustalenia przez właściciela, ryzyko R-P0-2 w raporcie audytu].

**Główny Urząd Geodezji i Kartografii**
Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl) — numeryczny model terenu, ortofotomapa (pomiary), Baza Danych Obiektów Topograficznych BDOT10k.
Modele 3D budynków LoD1 (2024) i LoD2 (2017): Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl), licencja CC BY 4.0 (creativecommons.org/licenses/by/4.0/legalcode.pl). Dane zostały przetworzone (wysokości i kształty dachów przeniesione do własnych modeli budynków).

**Treść tablic drogowych**
Treść tablic kierunkowych: opracowanie „research G3 s8-signs” na licencji ODbL 1.0, na podstawie danych OpenStreetMap contributors i zdjęć Mapillary contributors.

**Znaki drogowe**
Wzory znaków drogowych według rozporządzenia Ministra Infrastruktury w sprawie szczegółowych warunków technicznych dla znaków i sygnałów drogowych oraz urządzeń bezpieczeństwa ruchu drogowego i warunków ich umieszczania na drogach (t.j. Dz.U. 2019 poz. 2311); znaki narysowane od nowa.
*(Informacja dobrowolna — akt normatywny nie wymaga atrybucji.)*

### Modele, tekstury, niebo

**Poly Haven (CC0)**
Skany materiałów, niebo i gałązki drzew: Poly Haven (polyhaven.com), licencja CC0 1.0. Autorzy: Amal Kumar, Charlotte Baglioni, Dario Barresi, Dimitrios Savva, Greg Zaal, Jan Burghardt, Jarod Guest, Jenelle van Heerden, Rico Cilliers, Rob Tuytel, Sergej Majboroda.
*(Atrybucja dobrowolna — CC0 jej nie wymaga; lista autorów z `docs/LICENSES.md` sekcje „Skany materiałów CC0”, ADR 0070/0088/0108/0112, wiersze `world-viaduct-concrete`, `world-hero-fire-station-atlas`, `world-plot-kit-conifer-r8`.)*

**Wikimedia Commons**
Detal nawierzchni asfaltu na podstawie zdjęcia „Worn cracked asphalt pavement” — John Harvey, Wikimedia Commons, domena publiczna.
*(Dobrowolne.)*

[WARUNKOWO: tylko gdy build zawiera lokalnie zaimportowane zasoby Fab (`Assets/_Generated`, ADR 0084) — licencja Fab Standard nie wymaga atrybucji; wpis dobrowolny: „Wybrane skany roślin, kamieni i elementów ulicy: Quixel Megascans (Fab).” Przed wstawieniem sprawdzić w pełnym EULA, czy wolno używać nazw — `UNVERIFIED`.]

Pozostałe modele, tekstury i dźwięki — własne, wygenerowane kodem projektu.

### Dźwięk

Dźwięki silnika, pneumatyki i otoczenia: synteza własna projektu oraz nagrania wygenerowane w ElevenLabs Sound Effects (plan płatny właściciela) i przetworzone przez projekt.
*(Wzmianka o ElevenLabs dobrowolna — warunki nie wymagają atrybucji wg `docs/LICENSES.md`, wiersz `audio-elevenlabs-sfx-v3`; Service-Specific Terms SFX `UNVERIFIED` — sprawdzić przed wydaniem, czy nie ma tam wymogu.)*

### Czcionki

**Inter** — © 2016–2020 The Inter Project Authors (github.com/rsms/inter). SIL Open Font License 1.1 — pełny tekst poniżej. „Inter” jest zastrzeżoną nazwą fontu (Reserved Font Name).

**DejaVu Sans** — Bitstream Vera License oraz zmiany DejaVu w domenie publicznej (użyty jako obraz w teksturach znaków i tablic).
*(Dobrowolne — font nie jest dystrybuowany jako plik.)*

### Oprogramowanie

**Unity** — gra stworzona w Unity. [UNVERIFIED: dokładne brzmienie wymaganej informacji o Unity i ewentualnych „Third Party Notices” silnika — odczytać z warunków Unity na koncie właściciela; ekran powitalny Unity jest dziś włączony, `game/ProjectSettings/ProjectSettings.asset:20-21`.]

**glTFast** (com.unity.cloud.gltfast 6.20.0) — Apache License 2.0 — pełny tekst poniżej. [UNVERIFIED: wiersz „Copyright …” przepisać dosłownie z `LICENSE.md` pakietu; jeśli pakiet ma plik NOTICE — dołączyć jego treść.]

**Universal Render Pipeline** — fragmenty shadera © 2020 Unity Technologies ApS, Unity Companion License. [UNVERIFIED: czy licencja wymaga informacji w grze.]

[WARUNKOWO / UNVERIFIED: inne pakiety Unity obecne w APK (Burst, Collections, Mathematics, Input System, uGUI, AI Navigation) — dopisać po odczytaniu ich licencji (`Library/PackageCache/*/LICENSE.md`).]

### Pełne teksty licencji
- SIL Open Font License 1.1 — treść z `Inter-OFL.txt`.
- Apache License 2.0 — treść z pakietu glTFast.
- Linki: Open Database License 1.0 (opendatacommons.org/licenses/odbl/1-0/), CC BY 4.0 (creativecommons.org/licenses/by/4.0/legalcode.pl), CC0 1.0 (creativecommons.org/publicdomain/zero/1.0/).

---

## Czego NIE umieszczać (i dlaczego)

| Źródło | Powód |
|---|---|
| Mapillary, KartaView, Panoramax, Openverse, zdjęcia Commons CC BY / CC BY-SA | tylko referencja, żaden piksel w buildzie (`docs/LICENSES.md`, tabela zbiorcza, wiersze 9–13). Wyjątek: Mapillary w podpisie bazy G3 (wymagany przez ODbL G3). Dobrowolne podziękowanie możliwe, ale nie obowiązkowe |
| Freesound, OpenGameArt, BBC RemArc | nagrania tylko do porównań widm, nie w buildzie; RemArc i CC BY-NC — niekomercyjne |
| Dokumenty BIP/ZDM/BKM, regulaminy EKG ONZ, katalogi producentów, prasa | użyte tylko fakty/liczby |
| Nazwy firm i marek (punkty orientacyjne Dojlidy, marki z opisów referencji) | zasada 8 CLAUDE.md — bez cudzych marek w grze |
| Google (dowolne usługi) | zakaz ADR 0002; w repo brak takiego materiału (raport audytu, R-P2-5) |

## Pozycje warunkowe — podsumowanie
| Pozycja | Warunek |
|---|---|
| Adres danych pochodnych ODbL | decyzja właściciela o miejscu publikacji (R-P0-2) |
| Quixel Megascans (Fab) | build zawiera import Fab; brzmienie zgodne z pełnym EULA |
| ElevenLabs | zawsze dobrowolne; obowiązkowe tylko, jeśli Service-Specific Terms tego wymagają |
| Unity, URP, inne pakiety | po odczytaniu warunków Unity i licencji pakietów |
| Region Dojlidy | te same wpisy OSM/GUGiK (oba regiony korzystają z tych samych zbiorów) — bez osobnej pozycji |
