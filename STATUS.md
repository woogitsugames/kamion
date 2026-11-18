# STATUS — knyszyn-p1-s24 (P1 z REVIEW-2026-11-18-s24-knyszyn)

Worktree `.claude/worktrees/knyszyn-p1-s24`, gałąź `knyszyn-p1-s24`. Skrypty (poza gitem): `artifacts/knyszyn-p1-s24/{unity1,rebuild,editmode,pytest}.ps1`, `budget.py`, `field_noise.py`. ADR: `docs/adr/0295-domy-drewniane-pola-zamkniecia-p1-knyszyn.md` (zmiana globalna) + wpis w 0287.

## Zrobione (kafle `knyszyn` i `knyszyn-w` przebudowane r2, zaimportowane Win64, VQA High clear)
- P1-1/P1-2 `buildings_mesh.wood_wall` + `wood_trim_white`, `wood_siding` k 0,85 (CV 0,0157→0,0324). Knyszyn: 25 domów drewnianych, 256 przebiegów desek, max 5,50 m (< kafel 6 m), budynki LOD0 656 343 → 669 021; knyszyn-w: 5 domów, 127 160 → 129 718. Dom Klattów: 21,1 m = 3,52 kafla → max przebieg 4,65 m.
- P1-3 `Data/Regions/knyszyn/world_edge.authored.json` (DK65 W: zamknięcie 49,4 → 12 m przed krawędzią) + `WorldEdgeBuilder.ReadSetbackOverrides`. W scenie pojedynczego kafla zapora nadal widoczna (~50 m dalej); DW671 W bez zmian (kafel kończy się 12,6 m za rondem); obie znikają przy streamingu z knyszyn-w.
- P1-4 `vegetation.field_mosaic` (pola 72 % kafla: B 0,624→0,327), ogrody PTZB mieszkaniowej (22 ha: B 0,628→0,269, odch. 0,264→0,050), shader `swardCalm` w `WorldPBR.shader` (globalny). `field_noise.py` rondo-owner-11 pole NE 0,0219→0,0165.
- Budżet (83 kamery, szacunek edytora): max draws 731→732 (śr. +1,65), max tris 2 333 091→2 339 271 (kadr kabinowy > 2 mln już przedtem).
- Testy: `tests/gis/test_wood_house_p1_s24.py` 9 passed; podzbiór GIS (materials/wood/knyszyn_look/typology/buildings_0167) 78 passed po przeliczeniu baseline 0238 kafla C; EditMode pełny 1254 passed / 3 failed (2 środowiskowe jak w regen-c-s24 + mój test, poprawiony), EditMode z filtrem closure/StartClearance 100 passed / 0 failed.
- Dowody: `artifacts/knyszyn-p1-s24/{before,after2,after2-w,sbs}` + kopia w main `artifacts/knyszyn-p1-s24/`.

## W toku
Pełny `pytest tests/gis` czeka na slot heavy: `artifacts/knyszyn-p1-s24/logs/pytest-gis.{log,status}`.

NASTĘPNY KROK: `Get-Content artifacts/knyszyn-p1-s24/logs/pytest-gis.status` → przy `exit=0` wpisać wynik do raportu; przy błędach `Select-String FAILED artifacts/knyszyn-p1-s24/logs/pytest-gis.log`. Potem ocena `visual-critic` (lider) na `artifacts/knyszyn-p1-s24/after2/*.jpg`.

## Otwarte
- Zdjęcia Domu Klattów od właściciela (kolor desek/opasek, okiennice, ganek).
- Kafle do przebudowy, żeby zobaczyć pola/domy drewniane: knyszyn-s (szew S) i pozostałe pozamiejskie; shader działa wszędzie od razu → kafel C i zatwierdzone kadry do ponownego renderu przez lidera.
- P2 (płot, wyspa ronda — D71, drzewa, overcast) nietknięte; fartuch poza kaflem bez mozaiki; piłokształtna skarpa DK65 (verge vs teren) istniała przed zmianą.
