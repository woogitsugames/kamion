# Knyszyn 0227 — plan pokryć dachów pierzei Rynku

Status: **propozycja, nie wdrożono**. Źródło: porównanie obrysów BDOT10k `Data/Regions/knyszyn/buildings.geojson` z lokalnym ortofoto GUGiK z 27.05.2025 (`Data/raw/derived/knyszyn/ortho_0p25m.tif`; źródło 0,10 m wg `Data/Regions/knyszyn/ortho.json` i manifestu 2025). Przypisanie adres–obrys: lokalny OSM `podlaskie-261108.osm.pbf`, przestrzenne dopasowanie. Kolor, rodzaj pokrycia i dobór najbliższego materiału gry: **ESTIMATED**; RGB ortofoto zależy od oświetlenia, cieni i nalotu i nie dowodzi, czy dach jest z blachy czy dachówki. Zmiany podlegają sprawdzeniu na renderach i zdjęciach właściciela; nie zmieniać elewacji na podstawie ortofoto.

## Powtarzalny stan generatora

`BM.load(...)` i `BM.house_palette(...)` na całym zbiorze budynków regionu oraz bieżących override'ach, bez filtrowania sąsiadów: 1 = czerwony; 2 = brązowy; 3 = grafitowy; 4 = brązowy; 5 = czerwony; 9 = brązowy. Paleta uwzględnia dwóch wcześniej przypisanych sąsiadów w odległości 40 m i dlatego odtwarzanie jej na samym podzbiorze 6 obrysów byłoby błędne.

| Adres | Cel `target.building` | Kolor ortofoto / pewność | Obecny materiał | Propozycja po QA |
|---|---|---|---|---|
| Rynek 1 | `bdot:2002917F-3002-5C99-E053-CC2BA8C01CFC` | ciemny niebieskoszary/grafitowy; kolor ESTIMATED, materiał fizyczny ESTIMATED | `roof_tiles_red` | `roof_metal_graphite` |
| Rynek 2 | `bdot:2002917F-3031-5C99-E053-CC2BA8C01CFC` | jasnoszary z rdzawą częścią; ESTIMATED, połacie różne | `roof_tiles_brown` | **nie ustawiać**: brak istniejącego jasnoszarego odpowiednika, podział połaci i materiał niepewne |
| Rynek 3 | `bdot:2002917F-3066-5C99-E053-CC2BA8C01CFC` | czerwonobrązowy; kolor i materiał ESTIMATED | `roof_metal_graphite` | `roof_tiles_red` jako najbliższy ciepły wariant; porównać z `roof_tiles_brown` na renderze |
| Rynek 4 | `bdot:2002917F-2D30-5C99-E053-CC2BA8C01CFC` | część brązowa/czerwona i część jasnoszara; ESTIMATED, obrys obejmuje zróżnicowane połacie | `roof_tiles_brown` | **nie ustawiać** jednego materiału; najpierw ustalić podział obrysu i połaci |
| Rynek 5 | `bdot:2002917F-3078-5C99-E053-CC2BA8C01CFC` | niebieskoszary/grafitowy; kolor i materiał ESTIMATED | `roof_tiles_red` | `roof_metal_graphite` |
| Rynek 9 | `bdot:2002917F-2E16-5C99-E053-CC2BA8C01CFC` | czerwonoceglasty; kolor i materiał ESTIMATED | `roof_tiles_brown` | `roof_tiles_red` |

`roof_metal_graphite` to najbliższy istniejący ciemny wariant, a nie dowód, że rzeczywiste pokrycie jest metalowe. Kształt dachu z LoD2 i wygląd na zdjęciu są odrębne; tych override'ów nie należy stosować do brył landmarków kościoła ani urzędu.

## Proponowane dane — NIE wpisywać przed zmianą i testem generatora

```yaml
# ESTIMATED: kolor i dobór materiału z ortofoto GUGiK 2025-05-27; rodzaj pokrycia niezweryfikowany.
- id: rynek-1-roof-0227
  target: {building: "bdot:2002917F-3002-5C99-E053-CC2BA8C01CFC"}
  reason: "ESTIMATED: dark grey roof in GUGiK orthophoto, 2025-05-27; physical covering unverified."
  confidence: medium
  verify: "Owner reference / same-pose render; physical covering unverified."
  set: {roof_material: roof_metal_graphite}
- id: rynek-3-roof-0227
  target: {building: "bdot:2002917F-3066-5C99-E053-CC2BA8C01CFC"}
  reason: "ESTIMATED: warm reddish-brown roof in GUGiK orthophoto, 2025-05-27; covering unverified."
  confidence: medium
  verify: "Compare red versus brown on render and owner photographs."
  set: {roof_material: roof_tiles_red}
- id: rynek-5-roof-0227
  target: {building: "bdot:2002917F-3078-5C99-E053-CC2BA8C01CFC"}
  reason: "ESTIMATED: blue-grey roof in GUGiK orthophoto, 2025-05-27; covering unverified."
  confidence: medium
  verify: "Owner reference / same-pose render; physical covering unverified."
  set: {roof_material: roof_metal_graphite}
- id: rynek-9-roof-0227
  target: {building: "bdot:2002917F-2E16-5C99-E053-CC2BA8C01CFC"}
  reason: "ESTIMATED: brick-red roof in GUGiK orthophoto, 2025-05-27; covering unverified."
  confidence: medium
  verify: "Owner reference / same-pose render; physical covering unverified."
  set: {roof_material: roof_tiles_red}
```

## Wymagana zmiana mechanizmu i testy

Obecnie `tools/worldgen/streetscape/buildings_mesh.py` przy `if pitched` oblicza `rmat = house_pal[key][1]` dla `typ == house`; `BM.target_sets` przechowuje pola `set`, lecz `roof_material` nie jest odczytywane. Sam YAML więc niczego nie zmieni. Proponowany mały opt-in: dla dachów skośnych domów użyć `b["ovr"].get("roof_material", house_pal[key][1])`; walidować wybrany materiał przeciw ograniczonej liście istniejących materiałów dachowych i zgłosić nieznany materiał z identyfikatorem budynku. Niezadane pola, inne typologie, geometria i paleta sąsiadów pozostają bez zmiany; override nie powinien przepisywać `house_palette`, aby nie zmienić losowo sąsiednich domów.

1. **Reprodukcja**: na pełnym rzeczywistym zbiorze budynków regionu sprawdzić cztery ID, ich bazową paletę oraz zastosowanie wskazanych materiałów. Nie zakładać stałych bazowych kolorów w teście po innych zmianach sąsiednich obrysów: zasadnicze asercje dotyczą wyjścia z override'em i zachowania reszty przy tej samej wersji danych.
2. **Lokalność / regresja**: uruchomić `BM.build` dla tych samych danych z override'em i bez niego; sprawdzić, że tylko wskazana bryła dostaje inny materiał dachu, na warstwach `buildings` i `buildings_low`, a sąsiednie budynki i materiały ścian się nie zmieniają.
3. **Walidacja**: nieznana nazwa materiału powoduje czytelny błąd, identyfikujący obiekt, bez cichego zastosowania niewłaściwego materiału. Dom bez override'u daje identyczny wynik jak przed dodaniem mechanizmu; materiały nie mogą wyjść poza rejestr `M`.
4. **Geometria i LOD**: porównać liczbę trójkątów, obrys, wysokości, normalne i identyfikator źródła przed/po: zmienia się materiał, nie geometria ani kolizja; obie warstwy dostają ten sam wariant. Pomiar statystyk draw calls i tris Low/High przed/po jest obowiązkowy, a nie zastępowany testem jednostkowym.
5. **QA wizualny**: import + te same kamery na wysokości oczu, zdjęcia właściciela | render w lokalnym `compare/`, bez publikacji zdjęć i bez użycia jako tekstur. Ocenę rozpoznawalności pozostawić właścicielowi. Rynek 2/4 i materialność pokryć pozostają otwarte.
