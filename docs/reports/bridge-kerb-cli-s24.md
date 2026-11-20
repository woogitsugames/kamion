# Mosty — bridge-kerb-cli, 2026-11-20

## Przyczyna

`tools/worldgen/roads/network.py:1626` w bazowej wersji (`structure_sides`) nadpisywał
`kind`, `mat`, szerokość i wysokość obu boków stałym przekrojem mostowym. Wyliczone
wcześniej `_tight_side` / flush znikało. `meshing.build_side_strip` poprawnie zaczynał
profil przy `hw_at`, ale nie wiedział już, że kapa wchodzi na sąsiednią jezdnię.
`cull_sides_on_carriageway` nie obejmował materiału `bridge_concrete`; nie naprawiał kapy.
Nie jest to pomylenie osi z krawędzią ani przypisanie szerokości całego mostu do jezdni.

Przykład: dk8-wasilkow-01, E=-956,28 N=388,51, pas 0 łańcucha
`c:w1220009818:2738085906-1590086880`. Przeszkoda pochodzi z
`c:w145631573:1154974806-1590086878:R:1`, materiał `bridge_concrete`.
W pobliskim przekroju obie połówki asfaltu mają po 6,125 m i zachodzą na siebie.
Odtworzenie z D94=0 i D94=0,25 pokazuje ten sam mechanizm.

## Zmiana

Nowa rodzina profilu BRIDGE: bufor asfaltowy 0,30 m przed krawężnikiem, kapa
ograniczona odstępem od sąsiedniej jezdni. Współdzielony lub zbyt wąski przekrój
wewnętrzny jest płaski. Limit jest nakładany po wygładzaniu, także po ponownym
oznaczaniu ramp podpartych ścianami. Pomosty na innych warstwach nie zmniejszają kapy.

Render i kolizja dostają ten sam profil. Przebudowa wstęgi hero czyta ten sam profil,
a `_station` specyfikacji hero odczytuje jego zewnętrzne krawędzie. Generator mostu
pomija osprzęt nieistniejącej kapy; regułowe bariery nie wracają na krawędź flush.
Osobne przebiegi profili nie pożyczają stacji flush do odtworzenia podniesionej kapy.
Parametry i konsekwencje: [ADR 0317](../adr/0317-mosty-przekroj-poza-jezdniami.md).

## Dowody i zakres walidacji

`tests/gis/test_bridge_clearance.py` obejmuje obie orientacje łańcuchów, szczeliny
od -0,5 do 8 m, inną warstwę, profil hero, ponowne zastosowanie przekroju oraz
zmienne szerokości i przejścia kapa/flush. Kontroluje faktyczne trójkąty renderu,
kolizji i barier, również pionowe lica oraz wierzchołki.

Testy danych wczytują istniejący graf i overrides, stosują D94 oraz trzy operacje
rozwidleń, następnie odtwarzają wybrane wstęgi drogowe na płaskiej wysokości.
Korzystają z istniejącego `roads.consistency.SurfaceIndex`; filtr materiałów zapobiega
ukryciu kapy przez priorytet współistniejącego chodnika/trawy. Nie zapisują generated.
Stary błąd jest odtwarzany przez przywrócenie poprzedniej rodziny URBAN pełnej kapy.

| Kafel | zapisane punkty bridge_kerb | odtworzone stare kapy | poprawione kapy w tych punktach |
|---|---:|---:|---:|
| dk8-wasilkow-01 | 63 | 63 | 0 |
| dk8-wasilkow-03 | 88 | 87 | 0 |
| bialystok-porosly | 9 | 2 | 0 |
| bialystok-bojary | 7 | 6 | 0 |

Wyniki odtworzenia dla D94=0 i 0,25. Liczby nie są nowymi pełnymi raportami QA kafli;
nie odtwarzamy wysokości NMT, wszystkich junction patches, szwów ani całego streetscape.
Pozostałe historyczne punkty wymagają ponownego sprawdzenia po regeneracji.

Dowody lokalne: `artifacts/bridge-kerb-cli/pytest-bridge.xml`,
`pytest-regressions.xml`, `dk8-cap-before-after.png` (obejrzany rzut trójkątów przed/po;
widoczne usunięcie obu betonowych pasów ze wspólnej nawierzchni DK8).
Nie jest to wizualny PASS playera. Unity, Blender i build_world nieuruchamiane.

Końcowe polecenia (z `. ./scripts/env.ps1`):

```powershell
uv run --project tools/worldgen python -m pytest -q -s tests/gis/test_bridge_clearance.py tests/gis/test_road_consistency.py tests/gis/test_guardrail_overlap.py tests/gis/test_hero_bridge.py --junitxml=artifacts/bridge-kerb-cli/pytest-bridge.xml
# 42 passed, 1 skipped (33,57 s)
uv run --project tools/worldgen python -m pytest -q tests/gis/test_road_widen_0306.py tests/gis/test_rural_xsec_0272.py -k 'not dw671_no_gullies' --junitxml=artifacts/bridge-kerb-cli/pytest-regressions.xml
# 75 passed, 1 deselected (204,56 s)
```

Wyłączono test `dw671_no_gullies`, który uruchamia cały etap drogowy kafla z płaskim
heightfieldem; pozostałe sprawdzenia nie przebudowują kafli. Zapisane raporty QA
dotyczą wcześniejszej generacji, natomiast nowy test mostów sprawdza zmieniony kod.
SKIP: istniejący `test_instances_emitted` — brak wygenerowanych chunków świata w worktree.

## Przebudowa po integracji

Obowiązkowo: **dk8-wasilkow-01, dk8-wasilkow-03, bialystok-porosly, bialystok-bojary**.
Zmiana dotyczy wszystkich mostów i ramp ścianowych: docelowo regenerować również
pozostałe używane kafle z takimi obiektami, w tym bialystok-industrial-c z hero mostu.
Zmiana specyfikacji hero wymaga odpowiadającej regeneracji jego assetu.
Następnie odświeżyć trasy/reimport i uruchomić pełne road_consistency,
route_obstacles oraz przejazd/render; sprawdzić szwy z sąsiadami.

Praca tylko w worktree `bridge-kerb-cli`, commit bez push.
