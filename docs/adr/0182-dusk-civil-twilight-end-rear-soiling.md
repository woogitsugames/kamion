# 0182 — Zmierzch = koniec zmierzchu cywilnego (stała ekspozycja od latarni) + model brudu tyłu naczepy

Status: kandydat (gałąź `dusk-0182`), nie scalone. Data: 2026-11-13. Dotyczy: ADR 0010 (kamery kontrolne), 0016 (look/D23), 0062 (zmierzch), 0108 (noc).

## Problem (recenzja s18 0178, P2)
1. **Zmierzch za jasny** — czytał się jak „ciemniejszy pochmurny dzień”: tabela ekspozycji podążała za zmierzchem (jak tryb nocny telefonu),
   więc tło miało p50 28–31 %, a plamy latarni ledwo odstawały. Niebo szaro-różowe zamiast niebieskiego zenitu.
2. **Brud drzwi naczepy = szum** — maska wypalona: jedna chmura szumu, identyczna na obu skrzydłach, z twardą górną krawędzią;
   taśmy konturowe czyste; Low bledszy od High (atlas 4× mniejszy).

## Decyzja
1. `LP_Dusk`: słońce −6° (koniec zmierzchu cywilnego, az. 300°), **stała EV100 4,0 (r5: 3,7 z toe)** (`autoExposure` off) zakotwiczona w oświetleniu
   ulicznym, nie w niebie: asfalt pod oprawą (EN 13201 M3–M5 0,5–1,0 cd/m²; StreetLamps 2500 cd / 8 m) ≈ 33 % ekranu, asfalt
   oświetlony tylko niebem ≈ 8 %. Natężenie z nieba: 3,4 lx przy czystym niebie (`SkyModel.CivilTwilightEndLux`), 2,87 lx z mgiełką
   presetu (zmierzone w EditMode). `LP_Night` zachowuje tabelę podążającą (ADR 0108). WORKING_VALUE.
2. `SkyModel.ApplyTwilightChroma`: niebieski zenit (absorpcja Chappuisa ozonu), ciepła poświata tylko nisko w stronę słońca.
3. `TruckExterior.shader` — własny blok `RearGrime` (`_RearGrime*`, ustawia `TrailerAssetBuilder`), w ramie obiektu naczepy;
   skrzydła drzwi oznaczone bitem 11 rendering layer (`TrailerVisualRig.RearDoorRenderingLayer`) i mapowane z zawiasu do ramy
   naczepy w pozycji zamkniętej (brud zostaje na drzwiach po otwarciu). Źródła: film z wiru za skrzynią (najgęstszy przy progu,
   falująca górna krawędź, pionowe smugi spływu wygaszane gdy < ~3 px — bez migotania, średnia zachowana), brud przy słupkach
   zawiasowych i uszczelce środkowej, wnęki (AO), zacieki z górnej belki i spod zawiasów; każde skrzydło własny seed i ilość;
   bloki 0181 (soczewki, tablica) nietknięte.
4. **r5 (recenzja s19 `REVIEW-2026-11-13-s19-0182` P1):** osad = wyschnięty spray drogowy `_RearGrimeColor` lin. (0,17; 0,13; 0,08)
   ≈ sRGB (115,100,79), krycie maks. 0,7 na lakierze / 0,9 na metalu i trimie + szybszy zanik lobu metalicznego (debug r5: próg, słupki
   i belka RUPD były w strefie z pełnym brudem, ale czytały się jak czyste aluminium przez lustrzane odbicie nieba); rozbryzg ~1 cm
   w ostatnich 14 cm nad progiem i niżej (wygaszany < 3 px); części nielakierowane ×0,8, klosze lamp ×0,35 (emisja bez zmian);
   zacieki z górnej belki: rzadkie (8 % w polu, do ~50 % przy zawiasach i uszczelce), klastrowane, długość 15–70 % wysokości,
   przerywane, szerokość 0,6–2,6 cm, ~25 % wymytych (jaśniejszych). Zmierzch: kontrastowy toe ADR 0080 (s 0,6, p 0,05) pod pulami
   + EV100 3,7 (pule i oświetlony pojazd zyskują to, co toe zabiera tłu); `LP_Night` bez toe. Horyzont w stronę słońca: B −15 %.

## Walidacja (WorldC, `pwsh scripts/visual-qa.ps1`, kamery trailer-34, truck-rear34, chase, route_putry_approach; luma Rec.709, %)
| klatka | before p50 | after4 p50 | before niebo (górne 10 %) | after4 niebo |
|---|---|---|---|---|
| High-dusk chase | 30,6 | 18,8 | 49,2 | 26,9 |
| High-dusk route_putry | 30,7 | 21,3 | 61,6 | 34,1 |
| High-dusk trailer-34 | 28,3 | 17,5 | 54,2 | 29,6 |
| High-dusk truck-rear34 | 17,1 | 8,9 | 30,7 | 16,0 |
| Low-dusk chase | 29,0 | 17,0 | 46,9 | 24,5 |
| Low-dusk trailer-34 | 25,5 | 16,0 | 51,4 | 27,1 |
| High-overcast trailer-34 | 45,6 | 44,6 | 83,5 | 83,4 |
| High-clear trailer-34 | 48,3 | 48,2 | 75,6 | 75,6 |

r5 (after5) p50: High-dusk chase 17,3 / route 20,3 / trailer-34 15,9 / truck-rear34 6,2; Low-dusk 15,5 / 17,9 / 14,4 / 5,9;
clear/overcast identyczne z after4 (±0,1 pp). Kontrast pula/asfalt w chase (kody sRGB): 101/33 → 107/28.

Pełne `lum.tsv` (before/after1–5): `artifacts/dusk-0182/<tag>/lum.tsv`. Clear/overcast: zmiana tylko na drzwiach naczepy (≤ 1 pp p50).
Obejrzane: zmierzch — niebieskie niebo, pomarańczowa poświata tylko przy horyzoncie, plamy latarni dominują, światła pojazdu
czytelne, brak przepału (p95 ≤ 43 %); drzwi — zacieki z góry + film dolny z pionowym spływem, High ≈ Low, skrzydła różne.
EditMode (r5): 536 testów, 533 OK, wszystkie dusk/look/toe zielone; 2 porażki `CarPaintMaterialTests.DepositionChannel_*` istnieją w bazie
9c7957db4 (kod `WorldPbrMaterials`, poza zakresem tej gałęzi).

## Otwarte
- **P1-4 pule latarni (follow-up oświetlenia):** plac w `chase` jest jasny, bo leży w kilku nakładających się pulach (scena ~0,07 lin.
  wobec ~0,01 z samego nieba), a nie przez toe; toe r5 przyciemnił tło (asfalt 33 → 28), ale wyraźne doły między słupami wymagają
  rozsyłu oprawy (stała do 60° od nadiru + okno 35 m w `KamionLampPools.hlsl`) i rozstawu latarń z worldgen — poza 0182.
- P1-5: truck-rear34 o zmierzchu p50 6 % — decyzja po zrzucie z A16 (ewent. EV 3,5).
- P2 follow-up: okna zapalone o zmierzchu (P2-6), glare opraw (P2-8), światło lamp tylnych na otoczenie (P2-9).
- Pomiar na telefonie (EV stała nie zmienia kosztu; shader +~20 ALU tylko na tyle naczepy) — przy następnym APK.
- Ocena właściciela: „czy zmierzch wystarczająco ciemny” (kierunek artystyczny).
