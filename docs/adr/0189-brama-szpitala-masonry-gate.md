# ADR 0189 — Brama szpitala przy Żurawiej (P11-129): zestaw `masonry_gate`
Status: Proposed (agent world-builder, s20, gałąź `hospgate-0189`), 2026-11-13. Do scalenia przez lidera.
Poprzednik: ADR 0179 (P11-129 poza zakresem), `REVIEW-2026-11-13-s19-0179.md` (P11-129 = N, „dla bramki 3 P0”).

## Kontekst
Kadr CC0 P11-129 (Rakoon, Commons, 2019-11-10) pokazuje wjazd na teren szpitala: po lewej mur z cegły ze słupami
i tablicami, po prawej ceglany ganek portierni pod betonowym daszkiem ze znakami, za nimi szlaban. W grze stał tam
szlaban reguły, białe ogrodzenie panelowe i pusta bryła portierni. OSM ma tylko `barrier=lift_gate` (węzeł) i linię
`barrier=fence`; BDOT10k tylko obrys portierni.

Ustalenia z samego kadru (1600 px; manifest P11 nie jest źródłem kodów znaków — polecenie lidera):
- mur jest z **szarej cegły silikatowej**, nie czerwonej; 23 warstwy + rolka, słupy z betonowymi czapami;
- znaki: **B-20** (wyblakły, na filarze), **C-2** nad **B-33 „20”** na słupie latarni, w głębi B-2. Strzałka
  zakrzywiona to C-2 („za znakiem”); prosta pozioma to C-1 („przed znakiem”). `REVIEW s20 m47-fix2` §3 w wierszu 129
  podaje to odwrotnie — do erraty;
- ortofoto GUGiK HighResolution (WMS, stan po 2019) pokazuje teren przebudowany: nowa droga i chodnik na południe,
  mur krótszy. Odtwarzamy kadr z 2019, osadzony na obecnej geometrii.

## Decyzja
1. Nowy rodzaj `authored_overrides`: **`kind: masonry_gate`** (`tools/worldgen/streetscape/masonry_gate.py`).
   Geometria w układzie bramy: początek `anchor.at_en`, `l` = w prawo od wjeżdżającego, `a` = ku ulicy. Elementy:
   `walls` (linia, słupy, tablice), `piers`, `canopy`, `platform`, `faces` (znak na murze), `boards`, `posts`
   (słup z latarnią i tarczami). Mur wycina ogrodzenie reguły (`fence_cut_m`).
2. **Jeden prototyp, jeden materiał, jeden atlas 1024 px** na zestaw (cegła 128 px/m, rolka, beton, tablice
   i lica znaków 256 px/m). Atlas idzie przez rejestr `boards` z kluczem `MG*`; `export.py` nie zmniejsza go do
   512 px i nie nakłada wspólnego „weather” (ma własne zużycie: wilgoć u podstawy, zacieki spod rolki, różny ton
   cegieł), roughness 0,85.
3. Cegła, tablice i tablice informacyjne to własne rysunki (PIL/numpy). Teksty neutralne („SZPITAL / Oddział I”,
   „WJAZD NA PODSTAWIE…”, „IZBA PRZYJĘĆ” z piktogramem H) — bez nazwy i godła prawdziwej instytucji, bez czerwonego
   krzyża. Lica znaków z `streetscape.signs` + C-2 narysowane w module.
4. Dane Dojlid: wpis `zurawia-hospital-gate` jako własny blok w `overrides.yaml`; kamera `photo_P11-129c`
   (10,7 m przed linią bramy, 1,5 m w lewo od osi, vFOV 36°).
5. Region C nie ma takiego wpisu — wynik bez zmian (test na danych).

## Parametry UNVERIFIED (do potwierdzenia przez zadanie badawcze M62 / zdjęcia właściciela)
Wszystkie wymiary odczytane z jednego kadru, WORKING_VALUE: mur 1,75 m + rolka 0,12 m, grubość 0,25 m; słupy
0,38 m co ~2 m; filar 1,5 × 0,5 × 1,95 m; spód daszku 2,55 m; B-20 0,8 m; tarcze 0,6 m; słup latarni 3,9 m;
długość muru wzdłuż ulicy (6,8 m za łukiem); ogniskowa zdjęcia (hFOV 50° przyjęte) i pozycja kamery.
Ganek stoi 3,4 m bliżej ulicy niż w rzeczywistości: droga z OSM biegnie ~20° obok prawdziwej osi wjazdu, więc
prawdziwe miejsce ganku wypada w obrysie BDOT portierni.

## Wskazówki z M62 (PR #53, `research/mistral-p19-hospital-gate`, nieprzejrzane) — porównane z kadrem
| M62 | Kadr 1600 px / ortofoto / graf | Przyjęto |
|---|---|---|
| mur: cegła ceramiczna czerwono-brązowa | cegła jasnoszara (silikatowa), czerwone są tylko tablice | kadr |
| wysokość muru 1,7–2,0 m | 23 warstwy ≈ 1,75 m + rolka | zgodne |
| 4 tablice | 5 tablic (2 × 2 + 1) | kadr |
| znaki na wspólnym słupku | B-20 na filarze, C-2 + B-33 na słupie latarni | kadr |
| B-20 800/900 mm, B-33 i C 600 mm | — | zgodne (0,8 / 0,6 m) |
| światło wjazdu 6,6 m (cięciwa OSM) | w grze 7,2 m między słupem a filarem | zbliżone; z kadru 4,4 m odrzucam |
| wjazd od SW (azymut 62°), Żurawia na SW | ortofoto: jezdnia Żurawiej leży na wschód od bramy; węzeł 874174701 to skrzyżowanie dróg wewnętrznych | ortofoto: wjazd z NE na SW (242°) |

## Budżet, walidacja, otwarte
Uzupełniane po renderze (sekcje niżej).
