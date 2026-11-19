# STATUS lanes-audit-s24 (ADR 0301)
Zadanie: audyt pasów/szerokości jezdni na trasie autopilota industrial-c -> maczka -> kleeberga -> knyszynska; poprawki w generatorze.
Worktree: .claude/worktrees/lanes-audit-s24 (gałąź lanes-audit-s24, -NoLibrary -CopyDerived: prywatna kopia derived).

## Log
- 19.11: worktree; narzędzie tools/worldgen/qa/lane_width_audit.py (ortofoto HR 0,08 m / arkusz 0,25 m vs generator w pamięci, przekroje co 50 m po route_start).
  NASTĘPNY KROK: `uv run --project tools/worldgen python tools/worldgen/qa/lane_width_audit.py --region bialystok-maczka --fetch --out artifacts/lanes-audit-s24/before`
- 19.11 pomiar „przed” (4 kafle, 174 stacje co 50 m, ortofoto HR 0,08 m): artifacts/lanes-audit-s24/before/*.md + strips_*.jpg.
  Główne: DK8 Maczka 3 pasy: ortofoto pasy 3,55–3,60 m, linie krawędziowe 10,8 m; generator 3×3,25 (BDOT 10,5 przycięte), jezdnia przesunięta ~1,0–1,5 m ku pasowi dzielącemu (oś OSM), trasa na linii pasa.
  Kleeberga 2 pasy: ortofoto 3,65/3,80 m, generator 3,35/3,40; Maczka w606396475: OSM 2 pasy, ortofoto 3 (pas przeplatania). Knyszyńska: szerokość ok (6,45 vs ~6,4 między liniami krawędziowymi), brak linii krawędziowych.
- Poprawka A (standards/network): BDOT może tylko poszerzyć pas do max §17 ust.1, dolna granica = standard klasy (A/S/GP/G).
  NASTĘPNY KROK: narzędzie qa/ortho_lane_fit.py -> Data/Regions/<id>/overrides.ortho_lanes.json (center_offset, lane_edges, lanes).
- 19.11 ~04:40: poprawka B — qa/ortho_lane_fit.py -> overrides.ortho_lanes.json (16 wpisów, 4 kafle), podłoga BDOT tylko jednokier. A/S/GP; trasy przeliczone; ADR 0301 (draft w docs/adr). Test 18/18.
  Po (generator w pamięci): maczka błąd linii mediana 0,50 -> 0,12 m, p90 1,52 -> 0,55; kleeberga 0,60 -> 0,30.
  W toku: artifacts/lanes-audit-s24/build.ps1 (build_world 4 kafli, slot heavy; status build/build.status).
  NASTĘPNY KROK: po build.status -> Library (robocopy z win-build gdy brak Unity tam) -> pwsh scripts/import-region.ps1 -Region bialystok-maczka -SkipCopy? -> visual-qa WorldC High.
- 19.11 ~05:40: fit mierzy też przeciwną jezdnię; 19 wpisów (maczka 14, kleeberga 6). Po (after2): maczka linie 0,50->0,10 m (p90 1,52->0,60), kleeberga 0,60->0,25, knyszynska bez zmian.
  Rendery przed: vqa/before/{bialystok-kleeberga,bialystok-maczka} (High overcast, kamery route_s*); po (r1 maczka, przed fitem przeciwnej jezdni): vqa/after/bialystok-maczka; pary vqa/view/pair-maczka-*.jpg.
  W toku: build.ps1 r2 (maczka -> kleeberga -> industrial-c -> knyszynska, ~45 min/kafel), pytest roads/world_roads/0233.
  NASTĘPNY KROK: po każdym kaflu `pwsh -File artifacts/lanes-audit-s24/vqa.ps1 -Region <id> -Tag after`, pary, visual-critic, kopia artifacts do main.
