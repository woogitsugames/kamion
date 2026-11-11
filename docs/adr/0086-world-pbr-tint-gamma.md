# ADR 0086 — jeden liniowy kontrakt `_Tint` materiałów świata

Status: Proposed, S10 A (`gpt-tint-gamma`), 2026-11-11. Baza źródeł: main `4f7da66c`; integracja przez lidera, bez scalania tej gałęzi do main.

## Problem i pomiar

`WorldPBR.shader` deklaruje `_Tint` jako ShaderLab `Color`. Unity 6000.3.28f1 w Linear/D3D12 dekoduje tę wartość z sRGB podczas wysyłania do GPU również po `Material.SetVector`. Manifesty przechowują wartości liniowe. ADR0081 kompensował dekodowanie tylko dla materiałów budynków z `tint_linear`; pozostałe zestawy modulacyjne, niejednostkowe współczynniki zestawów kalibrowanych i pasy opon nadal otrzymywały zły mnożnik.

Dowód to **odczyt GPU rzeczywistego shadera**, nie sam odczyt `Material.GetColor`: `WorldPbrTintProbe` kopiuje bieżący WorldPBR do ignorowanego `_Generated`, zmienia tylko zwracany fragment na `_Tint`, zachowuje jego właściwości/CBUFFER i renderuje do liniowego ARGBFloat bez światła, tekstur i ekspozycji. Zapisano hash źródła, wersję Unity, API i 56 odczytów w `artifacts/tint-gamma-r1/tint-probe.json`.

| Liniowe wejście | GPU po surowym SetVector/SetColor | GPU po zapisie wejście.gamma |
|---:|---:|---:|
| 0,04 | 0,003096 | 0,040000 |
| 0,08 | 0,007194 | 0,080000 |
| 0,18 | 0,027212 | 0,180000 |
| 0,50 | 0,214041 | 0,500000 |
| 1,00 | 1,000000 | 1,000000 |
| 1,50 | 2,440062 | 1,500000 |
| 2,50 | 7,507028 | 2,500000 |

## Decyzja

1. Wszystkie cztery zapisy `_Tint` w `WorldPbrMaterials.Create` przechodzą przez `SetLinearTint`. API przyjmuje **liniowy mnożnik**, zapisuje jego `.gamma`, a GPU otrzymuje pierwotną wartość liniową. Obejmuje modulację, skalarny stosunek luminancji zestawu kalibrowanego, reset tintu oleju/farby oraz proceduralny decal opony. Współczynniki HDR zachowują zakres powyżej 1.
2. `tint_linear` pozostaje zgodnym metadanym starszych manifestów, ale nie steruje już konwersją. Materiały, które były poprawne po ADR0081, zachowują wartości GPU; tint równy 1 jest działaniem neutralnym. Audyt obejmuje 119 definicji PBR: 56 wcześniej poprawnych modulacyjnych, 33 pozostałe modulacyjne, 29 kalibrowanych i pas opon. Tabela wszystkich definicji: `material-contract-audit.json`.
3. Nie zmieniono shadera ani jego wariantów. Zachowano `_Tile = set_tile || elementScan || atlas`, wspólne `weather`/`runoff`, `macro`, `panel_m`, `splash_h`, skale normalnych/masek i fizyczne rozmiary tekstur. Asfalt zachowuje decyzję 0,08 liniowego albedo z ADR0080/0049.
4. Kalibracja po pierwszej pełnej rundzie z samą poprawką: ciemna kaseta ekranu urosła z 28/29/28 do 57/59/56 w High overcast wobec referencyjnych 36–40. `noise_panel_dark` zmieniono z 0,068/0,072/0,070 na **0,022/0,024/0,023 liniowo (WORKING_VALUE)**. Nie jest to pomiar fizycznego albedo farby.
5. Tynk remizy już miał neutralny tint; sama poprawka nie zmieniła jego koloru, lecz Low pozostawał o 13–15 poziomów poniżej celu. Zastosowano **jeden wspólny mnożnik 1,15 liniowo tylko do pigmentu tynku** w `sets_fire_station.py`: 0,185/0,260/0,365 → 0,21275/0,299/0,41975, WORKING_VALUE. Obejmuje pas tynku oraz tynk otaczający łuki/okrągłe okno. Piksele dachu, obróbek, szyb i szprosów są identyczne we wszystkich trzech tierach; wysokość/roughness również pozostają niezmienione. To mały konflikt liczbowy z późniejszym strumieniem E, nie zmiana bryły ani szkła.

## Dowód obrazu i kalibracji

Każda runda: **59 kamer × Low/High × overcast/clear = 236 PNG**, identyczne rozdzielczości 2340×1080 i kamery, ten sam plik Gate3 budynków. Low renderuje `WorldC`, High `WorldC_High`; obie sceny mają wspólny import MaterialTier Medium (rozdzielczości per spec, Fab mobile 512). `before` zbudowano i zaimportowano od zera na źródłach bazowych; 192/192 plików GLB/instances zgodnych z manifestem, Fab dostępny, bez fallback. `after-contract` pokazuje sam kontrakt; `after-calibrated` zawiera dwie powyższe kalibracje. Oryginalne pary zachowano przed odświeżeniem nieaktualnych fixture pojazdu.

Stałe ROI czytają pełne PNG; współrzędne i surowe liczby są w `measure_rois.py` i `*-roi.json`. Zdjęcia to porównanie **wyglądu ekranowego** zależnego od ekspozycji, pory i balansu bieli; nie wyprowadzamy z nich absolutnego albedo. Fotografia remizy 7197: zmierzony czysty fragment tynku 110,7/126,4/146,6 (nominalny cel 110/126/145 ±10). Fotografie hali: CC0 Rakoon `cm157094809` (pochmurno) i `cm109685822` (słońce); źródła/licencje w `docs/REFERENCES.md` i `artifacts/kwadrat-r9/refs`. Ekran: Mapillary p38/p40, opis pomiaru i lokalizacja w ADR0069/recenzjach s9. Różnice pogody/kąta nie są ukrywane jako pomiar materiału.

| Warunek | Asfalt średnia sRGB przed→po | Kostka przed→po | Tynk remizy RGB przed→po | Hala RGB przed→po | Kaseta ekranu RGB przed→po |
|---|---|---|---|---|---|
| Low overcast | 69,0→68,8 | 118,1→118,9 | 97/112/130→103/120/139 | 88/91/90→133/136/135 | 24/25/25→32/34/32 |
| High overcast | 72,7→72,6 | 124,4→125,2 | 105/121/137→111/129/147 | 94/98/97→136/139/139 | 28/29/28→36/38/37 |
| Low clear | 96,7→96,5 | 141,5→142,2 | 142/161/176→150/171/187 | 100/104/101→135/138/135 | 49/51/50→66/69/65 |
| High clear | 101,0→100,8 | 147,5→148,3 | 154/173/191→165/186/208 | 106/109/108→137/140/138 | 53/56/54→72/74/71 |

Cel tynku dotyczy dopasowanej pochmurnej fotografii, nie wymuszania tego samego RGB w słońcu. Oba profile overcast mieszczą się w ±10. Hala odzyskuje jasny profilowany metal (w pochmurnej fotografii 131/146/160, chłodniejszy WB; w słonecznej 200/209/217 przy innym oświetleniu). Nie przyciemniono jej ponownie dla zachowania wyglądu błędu. Niebo kontrolne jest niezmienione, asfalt przesuwa się o <0,2 poziomu, kostka o <1.

## Walidacja i granice

Wa?ne rozr??nienie fixture: `before`, `after-contract`, `after-calibrated` maj? ten sam skopiowany Generated pojazd. Po zamkni?ciu tych rund canonical TruckAssetBuilder/WorldTruckInstaller naprawi? brak MI_Ext_DoorGlassL, a pe?ny EditMode przeszed?226/226 (bez pomini??). `after-final` ma ju? kanoniczny pojazd; jego pe?nokadrowych r??nic/stats nie przypisujemy wy??cznie materia?om ?wiata. Dow?d zerowego kosztu wszystkich59 kamer dotyczy dopasowanej pary before/after-calibrated; ostatnia korekta7pigment?w nie dodaje geometrii, tekstur ani shader?w.

- `stats.txt` z wszystkich 59 kamer są **bajtowo identyczne** przed/po we wszystkich czterech warunkach: bez nowych draws/tris/instancji i bez nowych tekstur; brak twierdzenia o pomiarze GPU na telefonie.
- Testy regresji obejmują zapis/odczyt GPU siedmiu wartości 0,04…2,5, zachowanie kontraktów metrycznych/pogodowych i ochronę nietynkowych regionów atlasu.
- Dalsze wyniki pełnego GIS/EditMode i niezależny review: końcowy `artifacts/tint-gamma-r1/REPORT.md`. Pierwszy EditMode potwierdził wszystkie 14 nowych testów; trzy błędy dotyczyły nieaktualnej skopiowanej fixture TruckMaterials bez MI_Ext_DoorGlassL. Canonical TruckAssetBuilder/WorldTruckInstaller uruchamiane są dopiero po zamknięciu dopasowanych par.
- Samokrytyka: identyczne ciemne sylwetki drzew, stożkowe tuje, sterylne strefy zużycia, szum High i ekspozycja białych ścian w clear nadal wymagają swoich strumieni. Nie korygowano ich przez globalną ekspozycję ani ponowne zaciemnianie wszystkich materiałów.
- `_StripeA`, `_StripeB`, `_PearlTint` są sąsiednimi właściwościami Color z osobnym ryzykiem konwersji; pozostały poza tym zakresem zgodnie z koordynacją (PearlTint do późniejszej kalibracji lakieru G).
