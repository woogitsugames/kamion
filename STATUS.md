# STATUS fields4-s24 (ADR 0334 r4: brzeg kukurydzy, koleiny, pola w dali, krawedz lasu far_field)

- Worktree `agent-a1e9a7a0a869fb425`, galaz `worktree-agent-a1e9a7a0a869fb425`; Library z win-build (Win64); prywatne kopie
  `Data/raw/derived/{knyszyn-w,dw671-tykocin-03}`, reszta derived = junction per kafel do main (NIE ruszac wspolnego derived).
- [krok 1] Diagnoza dw671-tykocin-03 edge-north (`artifacts/fields4-s24/probe_dw03_edgeN.png`): sciany = boki skrajnych rzedow
  kart przy szwach pasow (MAIZE_SEAM_CLEAR 1.6 m po obu stronach KAZDEGO szwu, takze bez miedzy -> korytarz 3.2 m z malowanymi
  rzedami na ziemi = "koleiny jak paski") i koniec kart na krawedzi kafla / bloku / zasiegu 220 m.
- [krok 2] Render "przed" (main derived, shader main) zrobiony: main `artifacts/fields4-s24/vqa/before/` (High clear+overcast, std + extra).
- [krok 3] Kod: field_crops r4 (szwy bez miedzy bez korytarza, strefa brzegu 4 m z kartami pojedynczymi / przerzedzonymi /
  odchylonymi, komorka brzegu w atlasie verge_atlas, rosliny przed linia), r4b (odstep = szerokosc miedzy shadera + 0,25 m),
  r4c (regula chunkow najpierw, chunk bez prymitywu = koniec lanu, CHUNK_MIN_TRIS 5600); shader (koleiny tramline z profilem,
  przerzedzenie, chwasty; daleki plan farK: ton pasow, przejazdy wzdluz rzedow, miedze/granice blokow ciemniejsze linie;
  oktawa warpu 610 m / 28 m + lustro FIELD_WARP_FAR); far_field (kwatery wieku, drzewa nad okapem, zejscie konca biegu).
  Testy: tests/gis/test_fields_r4_0334.py (8) + r3 + 0334 zielone.
- [krok 4] after (r4a) dw671-tykocin-03 + knyszyn-w: `vqa/after/`; poprawki r4b/r4c -> przebudowa + `vqa/after2/` w toku
  (`pwsh artifacts/fields4-s24/chain2.ps1`).
- UWAGA: derived knyszyn-w z main (przed) rozni sie od QA z HEAD w 25 chunkach -> +7..+9 draw na kilku kamerach trasy knyszyn-w
  nie pochodzi z r4 (obiekty bez zmian; banks +1 chunk). Do porownan uzywac banks_cmp.py / mat_cmp.py (QA HEAD vs po).
- [krok 5] r4d (run miedz przy kukurydzy do 220 m), koleiny lamane placami (tramline + droga polna), drzewa nad okapem tylko
  waskie korony. pytest 18 plikow: 236 passed, 1 failed = test_far_field::test_generated_far_field_qa_and_manifests (dane regionu C
  w derived main vs QA, niezalezne od r4). Szkic ADR: artifacts/fields4-s24/adr_r4.md.
- W toku: `pwsh artifacts/fields4-s24/chain4.ps1` (far_field obu kafli + import + render `vqa/final/`).
- NASTEPNY KROK: `uv run --no-project --with pillow python artifacts/fields4-s24/compare.py final -v`, wpisac liczby do adr_r4.md,
  dopisac do docs/adr/0334, commit, raport.

# STATUS bank-smear-s24 (smuga na skarpie tykocin route_s0160, ADR 0311 dopisek)

- Worktree `agent-a13a4ba7b73214d27`, galaz `worktree-agent-a13a4ba7b73214d27`; prywatna kopia `Data/raw/derived/tykocin` (reszta derived = junction do main), Library z win-build (Win64).
- [krok 1] Hook diag `KAMION_QA_DIAG`: `colorby:renderer|material|slot|prim|vcol|vcolb|nrm|wpos`, `mat:<prop>=v`, `noshadows` (VisualQaRunner + Editor/VisualQA/DiagPrimitive.shader).
- [krok 2] Smuga = `terrain_band`/`M_terrain_grass` (WorldPBR) widziany stycznie (skarpa 33 deg, slad tekstury 15-100x anizotropowy); nie rzut z normalnych (WorldSurface bez zmian).
- [krok 3] Poprawka: Var trawy z mipmapami (WorldPbrMaterials) + WorldPBR izotropowa probka/kolor darni na stoku przy skrajnej anizotropii. DC bez zmian (780). EditMode 39/39 (w tym GrassVarMipsTests), pytest GIS (shader/materials) 58 passed.
- Dowody: `artifacts/bank-smear-s24/sbs/` (przed|po, diag). Otwarte: cienka linia sylwetki skarpy zostaje (geometria/karty trawy - lider).
- NASTEPNY KROK: review + scalenie przez lidera; po scaleniu reimport kafli (tekstura Var trawy zmienia sig importu): `pwsh scripts/import-region.ps1 -Region <id> -BuildTarget Win64`.

# STATUS hv-wires-s24 (przewody WN, CRITIC s24 fala 11 pkt 1)

- [krok 1] Diagnoza: pylony na dk65-07 owner02-seam-n-cab to pylony FAR FIELD (kamera n=1080 > 1024, poza kaflem; dk65-08 nie wczytany).
  far_field.py dokleja kratownice 27 m co 210 m wzdluz WSZYSTKICH linii z pierscienia (BDOT OT_SULN_L dowolnego napiecia + OSM line/minor_line)
  i nigdy nie rysuje przewodow; BDOT "slup energetyczny" (glownie slupy SN) tez jako kratownica 26 m. dk65-07 far_field_qa: 307 pylonow, 0 przewodow.
  Kolor COL_PYLON_STEEL (0.27, 0.285, 0.30) liniowo = ~2.3x jasniej niz pylon_steel w kaflu -> w sloncu bialy.
- NASTEPNY KROK: audyt wszystkich kafli `uv run --project tools/worldgen python tools/worldgen/qa/hv_wires_audit.py`
- [krok 2] In-tile: power_supports bierze zmapowane wieze na linii (rzut) -> 31/298 -> 0/308 bez przesla; BDOT slup na linii WN = pylon.
- [krok 3] Far field: wieze tylko na liniach WN (BDOT wysokiego / OSM >=60kV), przesla z zawisem jako wstegi submesh 0, szew = podpora kafla,
  ocynk z rozrzutem, maszty bez trawers. dk65-07: 307 -> 31 wiez + 5 masztow, 30 przesel, 0 bez przewodow. ADR 0351, testy tests/gis/test_hv_wires_0351.py.
- NASTEPNY KROK: import Win64 dk65-07 + knyszyn-w (slot unity) i VQA -> artifacts/hv-wires-s24/
- [krok 4] far field knyszyn-w: 328 -> 44 wiez + 4 maszty, 44 przesla, 2 podpory szwu (= podpory kafla 737.9/792.2,1024). Kamery hv0351_* dodane.
  pytest (streetscape, world_v33, far_field*, pylons, hv_wires_0351, qa_tools): 405 passed. Import+VQA czeka na slot unity (skrypt w scratchpadzie).
- NASTEPNY KROK: po VQA after -> render before (podmiana far_field.glb z main), porownanie, visual-critic
- [krok 5] Daleki plan: linie SN do 600 m (slupy betonowe + 3 przewody, High). Import Win64 + VQA High-clear dk65-07 i knyszyn-w
  przed|po: artifacts/hv-wires-s24/{vqa-before,vqa-after,cmp}/ (kopia w main artifacts/hv-wires-s24). knyszyn-w hv0351-seam-n:
  przewody WN ciagle kafel -> szew -> daleki plan (przed: konczyly sie na szwie). dk65-07 owner02: zamiast 6 bialych kratownic
  bez przewodow - linia SN dk65-08 (slupy + przewody). Audyt: in-tile wieze bez przesla 31 -> 0; far 17 110 -> 0 w przebudowanych.
- DO ZROBIENIA (lider): far_field.py --region <id> dla wszystkich 54 kafli (~3,5 min/kafel, ekstrakcja GIS schematu 14);
  build_world dla 26 kafli z liniami WN/wiezami (lista w raporcie); ocena visual-critic (subagent nie tworzy subagentow).
- NASTEPNY KROK: brak - czeka na review/scalenie lidera. Nie scalone.
