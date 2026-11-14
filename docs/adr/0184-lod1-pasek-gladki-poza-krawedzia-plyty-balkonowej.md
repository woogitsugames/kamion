# ADR 0184 — LOD1 bloków i biurowców: gładki pasek atlasu dalekiej elewacji poza krawędzią płyty balkonowej

Status: ACCEPTED (2026-11-13, s19/s20). Źródło: ADR 0180 §1 („przy okazji zmierzone”), HANDOVER „Follow-upy P2”,
recenzja `docs/reports/REVIEW-2026-11-13-s19-0180-r2.md` P2.2 („białe łaty w LOD1 NW” wieżowca).

## 1. Ustalenia (zmierzone)

- `lod1_wall` (`tools/worldgen/streetscape/buildings_mesh.py`) rysuje ścianę LOD1 bloku / biurowca w materiale
  `<tynk>__far_<rodzaj>` (atlas rzędów kondygnacji `facade_far`, 24,0 × 45,8 m). Margines ściany po lewej i prawej
  stronie przęseł okiennych to jeden quad na całą wysokość ściany, mapowany na „gładki pasek” atlasu:
  u 0,2..1,2 m, v `FAR_PLAIN_V` = 0,65..0,95 m.
- Ten prostokąt leży w przęśle 0 pierwszego rzędu atlasu (`balcony_1`, rząd 0), a przęsło 0 to balkon. Malarz atlasu
  (`art-source/world/materials/_src/sets_buildings.py::facade_far`) maluje krawędź płyty balkonowej od
  v = `FAR_V0` − 0,14 do + 0,02 m na szerokości osi przęsła ± 1,35 m (u 0,15..2,85 m).
- Pomiar na `T_facade_far_BaseColor.png` (1024 px, 2,34 cm / px), średnia kolumn u 0,2..1,2: 187 / 255 do v 0,79;
  190 przy v 0,85; 205–206 od v 0,87 do 0,99. W przęśle 1 (okno, u 3,9..4,9) w tym samym zakresie v: 186,6–188,3.
- Skutek: górne ok. 30 % wysokości każdego gładkiego quada LOD1 (pas 0,86..0,95 z 0,65..0,95 rozciągnięty na całą
  ścianę) ma ton krawędzi płyty: o ok. 10 % jaśniejszy niż tynk (206 / 187). Na 11-kondygnacyjnym wieżowcu to trzy
  górne kondygnacje — „białe łaty” z recenzji 0180 r2 (podgląd programowy
  `artifacts/atlas-0184/tower-lod1-elevations-before-SW-SE-NW-NE.png`, panel NW: pas między grupami okien i przy
  krawędziach; ściana NW idzie regułą ogólną, nie `facades`). Na blokach: jaśniejsze prostokąty przy narożnikach na
  wysokości najwyższej kondygnacji (`block2-lod1-elev-before-over-after.png`, górny rząd).
- Profil Low (`lod_policy.Low.bld = 0`) pokazuje LOD1 wszędzie poza chunkami do 60 m od trasy startowej, więc na
  telefonie widać to z bliska, nie tylko „z dystansu”. Profil High przełącza na LOD1 dopiero od 700 m.
- LOD0 nie używa `FAR_PLAIN_V` (ściany LOD0 mają materiał tynku i komórki atlasu okien).

## 2. Decyzja

1. Nowa stała `facade_atlas.FAR_PLAIN_U`: 1 m pośrodku pierwszego przęsła pierwszego rzędu atlasu, które nie jest
   balkonem (wyliczana z `FAR_ROWS`, obecnie przęsło 1: u 4,0..5,0 m). `lod1_wall` mapuje gładkie quady na
   `FAR_PLAIN_U` × `FAR_PLAIN_V`. `FAR_PLAIN_V` zostaje 0,65..0,95 (powyżej strefy `_SPLASH` v < 0,6).
2. W nowym miejscu atlas jest czystym tynkiem od v 0 do 1,4 m (zaciek pod parapetem zaczyna się na `FAR_V0` + 0,9 −
   0,5) i 1,15 m w obie strony w u (krawędzie płyt sąsiednich przęseł kończą się 0,15 m w głąb własnego przęsła).
   Zapas ≥ 0,45 m w każdą stronę wystarcza dla mipów do 4. poziomu (37 cm / teksel); przesunięcie samego v do 0,85
   zostawiałoby 1 cm zapasu i krawędź płyty wracałaby na dalszych mipach.
3. Test `tests/gis/test_world_v31.py::test_far_plain_strip_is_clear_of_painted_cells`: prostokąt paska z marginesem
   0,4 m nie dotyka przęsła balkonowego ani okna / zacieku, leży nad strefą `_SPLASH`, a `lod1_wall` bloku z balkonami
   używa dokładnie tego prostokąta w obu gładkich quadach.

Zmienia się wyłącznie UV0 czterech wierzchołków gładkich quadów: geometria, liczba trójkątów, materiały, tekstury i
draw calle bez zmian. Atlas nie jest przemalowywany.

Odrzucone: skrócenie `FAR_PLAIN_V` do 0,65..0,85 (jak `frontage.FACADE_PLAIN_V`) — poprawne na mipie 0, ale bez zapasu
na mipy; przemalowanie atlasu (osobny pusty pas) — zmiana tekstury i wszystkich wierszy UV dla zysku, który daje
przesunięcie paska.

## 3. Poza zakresem / otwarte

- `frontage.lod1_facade` (ściany z regułą `facades`, ADR 0180) nadal mapuje gładkie kawałki na u 0,2..1,2,
  v 0,65..0,85: na mipie 0 czysto (podgląd programowy), na dalszych mipach ma 1 cm zapasu do krawędzi płyty.
  Zalecenie: użyć tam `FA.FAR_PLAIN_U` (jedna linia); nie zmieniane tutaj (reguły wieżowca należą do 0180).
- Recenzja 0180 r2 P2.1 (różny wzór NW w LOD0 / LOD1) i pozostałe punkty — nie dotyczą paska gładkiego.

## 4. Walidacja

- Test `tests/gis/test_world_v31.py::test_far_plain_strip_is_clear_of_painted_cells` zielony. Pełny `pytest tests/gis`
  (worktree, 19 min 37 s): 1080 passed, 2 xfailed, 1 failed — `test_road_fidelity::test_report_not_stale`
  (raport fidelity nieaktualny względem `overrides.yaml` z ADR 0180; niezależne od tej zmiany).
  EditMode: 518, 517 passed, 1 skipped (`artifacts/tests/editmode-20261113-220123.xml`).
- build_world: manifest — zmienione tylko sha / bytes plików, trójkąty bez zmian.
- Budżet (Unity, `budget-Low-overcast.txt`, `budget-High-overcast.txt`, kamery r10_block_1..5 + r10_office_2):
  draw calle +0, trójkąty +0,00 % na każdej kamerze, Low i High. High (LOD0) piksel w piksel identyczny (AE 0).
- BEFORE / AFTER LOD1 (Low, własne kamery `artifacts/atlas-0184/lod1_cameras.json`, chunki > 60 m od trasy; BEFORE =
  świat zbudowany z tymczasowym starym paskiem u 0,2..1,2, niezacommitowanym): we wszystkich zmienionych obszarach
  AFTER jest ciemniejszy o 8–17 / 255 (np. `a184_hi_d_p` overcast: 141,7 → 125,0 na 159 393 px), zgodnie z pomiarem
  206 → 187 w §1. Cropy `artifacts/atlas-0184/crops/lod1_*_Low-overcast_before_after.jpg`: na `a184_hi_d_p` jasne
  prostokąty marginesów i najwyższej kondygnacji znikają, ściana ma jeden ton tynku; bloki `a184_blk_*` — znikają jaśniejsze pionowe pasy przy narożnikach,
  mniejsza skala; `a184_tower_n` — subtelne wyrównanie tonu.
- `a184_tower_p` (wieżowiec od NW): 0 zmienionych pikseli — ściany widoczne z tej kamery idą przez
  `frontage.lod1_facade` (§3), nie `lod1_wall`. Białe łaty z recenzji 0180 r2 P2.2 w silniku nie są tu potwierdzone
  ani usunięte; pozostaje zalecenie z §3. Pionowe białe kreski na narożniku wieżowca (`a184_tower_n`, przed i po) —
  inna przyczyna, otwarte.
- Porównanie ze zdjęciem właściciela: nie dotyczy wprost (zmiana tonu tynku w LOD1); kierunek zgodny z refs —
  jednolity tynk bez jaśniejszych pasów przy narożnikach bloków.
