# DK8: szew Wasilków 01/02 i oznakowanie Korycina — 2026-11-20

Gałąź `dk8-seam-cli`. Bez Unity, przebudowy kafli i pushowania.

## Przyczyny i poprawki

1. **Nie ginie krótki odcinek DK8.** Way 876126468 długości 27,6 m jest końcową sekcją
   łańcucha `c:w211148033:2182588693-2182588703`. `network.py:687` łączy krawędzie przez węzły
   stopnia 2; parametr końca QA pochodzi z `sec_idx`, więc identyfikator całego łańcucha nie musi
   zawierać numeru way na szwie. Nie zmieniono przycinania ani reguły łączenia krótkich odcinków.
2. **Fałszywe „urwanie” w QA i jednostronny taper w generatorze.** D94 przesuwa bocznie osie
   (`network.py:760`). Przy ukośnej drodze przesuwa się także współrzędna w kierunku normalnym
   do krawędzi kafla. Koniec DK8 w 01 ma N=599294,921933, a serwisowej w 02 N=599295,091205,
   wobec szwu N=599295. Odchylenia 0,078/0,091 m przekraczają `SEAM_EPS_M=0,05`.
   `qa/seams.py:304` odrzucał je **przed** dopasowaniem ±5 m. `seam_taper.py:299` stosował
   analogiczny filtr sąsiadów, przez co tylko 01 dostawał taper DK8 9,00→8,75 m, a 02 pozostawał
   przy 8,50 m. Przynależność końca do szwu jest teraz ustalana z granicznego węzła grafu
   (`End.boundary_xy`, `End.on_seam`), a pomiar położenia nadal używa wygenerowanej osi.
   Nie zwiększono tolerancji. Obie strony dostają ten sam taper: 8,75 m na szwie, po 12,5 m w kaflu.
3. **Brak linii w Korycinie:** na way 304733170 trasa przechodzi na sekcję jednopasową.
   `network.py:173` zeruje wtedy `edge_strip`; `markings.py:200` uzależniał domyślne P-7b klasy
   A/S/GP od `edge_strip > 0`, więc obie linie krawędziowe znikały. Reguła oznakowania nie wymaga
   już opaski: bez niej linia 0,24 m leży w całości na asfalcie, z osią 0,12 m od krawędzi.
   Zachowane są override `none/left/right/both`, zakaz oznakowania budowy/ronda i osobna reguła
   mierzonych `lane_edges`. Drogi niższych klas nadal wymagają jawnego override.

## Dowody i ograniczenia

- `artifacts/dk8-seam-cli/seams.{json,md}`: 5 dróg; 0 zgłoszeń urwania; szerokość, pasy,
  rozstaw linii i odległości krawędzi asfaltu DK8 zgodne po obu stronach.
- Raport nadal ma **2 FAIL położenia osi, po 0,25 m** (DK8 i serwisowa). To istniejące różnice
  przesunięcia D94 między kaflami, wcześniej zasłonięte błędnym zgłoszeniem urwania. Nie są
  podnoszone progi ani zerowane różnice. Istniejący link trasy 01→02 opisany w ADR 0315 pozostaje.
  Naprawa detekcji końców i symetrii taperu nie jest naprawą bocznego położenia osi.
- Regresje używają prawdziwych grafów/overrides i płaskiej wysokości: sprawdzają oba kierunki
  ładowania sąsiada przez generator oraz trójkąty prawej linii po `drop_overlapping` na
  stacjach 450/480/510 m Korycina. Nie jest to wizualny PASS ani pomiar nowego GLB/NMT.
- Test syntetyczny QA sprawdza, że ukośny przesunięty koniec jest dopasowany, jego rzeczywisty
  błąd położenia nadal daje FAIL, a droga kończąca się przed szwem nadal jest wykrywana jako brak.
- Logi pytest: `artifacts/dk8-seam-cli/pytest.log` i `pytest-widen.log`.

Walidacja podstawowa: **66 passed, 1 xfailed** (213,96 s). Polecenie:

```powershell
uv run --project tools/worldgen python -m pytest -q tests/gis/test_dk8_seam_cli.py tests/gis/test_seams_0224.py tests/gis/test_seam_taper_0275.py tests/gis/test_markings_pl_standards.py tests/gis/test_markings_pl_verify.py
```

Jedyny xfail jest istniejącym testem P-21. Dwa istniejące `PytestUnknownMarkWarning` dotyczą
`pytest.mark.unit` w testach oznakowania (drugie `pytest_configure` w conftest zastępuje rejestrację).
Nie zmieniano skip/xfail, ratchetów ani konfiguracji pytest.

Dodatkowa regresja D94 i przekrojów szwów: **45 passed** (208,91 s), łącznie **111 passed,
1 istniejący xfailed**:

```powershell
uv run --project tools/worldgen python -m pytest -q tests/gis/test_road_widen_0306.py tests/gis/test_seams_p3_0304.py
```

Powtórzenie QA (CLI zwraca 0 również przy wierszach FAIL; wynik oceniono z raportu):

```powershell
uv run --project tools/worldgen python -m tools.worldgen.qa.seams --tiles dk8-wasilkow-01,dk8-wasilkow-02 --json artifacts/dk8-seam-cli/seams.json --md artifacts/dk8-seam-cli/seams.md
```

## Integracja

Przebudować **wyłącznie `dk8-wasilkow-01`, `dk8-wasilkow-02`, `dk8-korycin-01`**:
`uv run --project tools/worldgen python tools/worldgen/roads/build_world.py --region <id>`.
Przebudowę wykonać w tle zgodnie z istniejącą obsługą slotów heavy; następnie odświeżyć trasy
`uv run --project tools/worldgen python scripts/export-route.py --region <id>` i zależne linki
zgodnie z ADR 0306. Powtórzyć `qa.seams` po obu stronach oraz obejrzeć linię Korycina po imporcie
w osobnej sesji Unity. W tej sesji żaden z tych buildów/importów nie został uruchomiony.
