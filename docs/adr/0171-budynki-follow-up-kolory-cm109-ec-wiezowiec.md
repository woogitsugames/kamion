# ADR 0171 — follow-up budynków po 0167: kolory okładzin (cm109685822, EC cm92458760, wieżowiec 177786/178689)

Status: WIP na gałęzi `bldg2-0171` (2026-11-13, s17); nie scalone.
Źródło: `docs/reports/visual/REVIEW-2026-11-13-s17-0167.md` (P1 cm109 ściana boczna, P2 EC za ciemny / okna bez
białych ram, P2 wieżowiec szary zamiast bladożółtego).

## 1. Ustalenia (rozpoznanie, zmierzone)

Narzędzia w `artifacts/bldg2-0171/tools/` (`px.py` — średni sRGB wycinka, `chunkmats.py`, `glbmats.py`, `primdiff.py`).
Zdjęcia tylko jako referencja (te same co w ADR 0167: Commons Rakoon cm92458760 CC BY 3.0, cm109685822 CC0;
Mapillary richlv 177786140912399 / 178689077481862 CC BY-SA 4.0).

- **Wieżowiec.** Override `g3a-office-tower-colour` DOCIERAŁ do LOD1 (`plaster_beige__far_ribbon`, 144 trójkąty).
  Szarość (175,175,165) nie pochodziła z koloru ściany: budynek dostał z haszu wariant `ribbon`, a rzędy `ribbon`
  atlasu dalekiej elewacji niosą własne szare spandrele — beż zostawał tylko na narożnikach i pasie klatki. Na
  zdjęciach ściana szczytowa jest gładka, piaskowa, z jedną kolumną okien, długa elewacja jasna z rzędami okien.
- **Pawilon cm109.** Ściana boczna (SW) to już `hall_plinth` (albedo 0,25 neutralne); w słońcu renderuje się jako
  (172,168,155) = beżowoszary. Stosunek jasności ekranu (liniowo) do albedo na tej ścianie: 1,65. Zdjęcie: łupkowy
  błękit, piętro to rząd osobnych okien, parter witryny.
- **Budynek EC cm924.** `plaster_blue` 0,09/0,19/0,31 renderuje ścianę jako (44,60,77) (mediana); zdjęcie
  (58,81,113)–(100,140,180). Okna na zdjęciu mają szerokie białe ramy dwudzielne; LOD1 rysował pełne ciemne prostokąty.

## 2. Decyzja

1. `materials.py`: `plaster_blue` → 0,12/0,26/0,46 (×1,35–1,5 ku błękitowi; WORKING_VALUE). Nowy
   `plaster_slate_blue` 0,09/0,13/0,20 (cel ok. (105,125,155) na ścianie w słońcu przy współczynniku 1,65;
   WORKING_VALUE; tylko autorskie frontony, bez `__far_*`).
2. `frontage.py`: klucz `frame: {material, material_lod1, width_m}` — jasna rama (4 listwy + słupki) w licu ściany
   wewnątrz otworu na obu LOD-ach (LOD1: tylko lica, w materiale, który chunk już rysuje; bez nakładania się
   powierzchni — ściana jest w tym miejscu wycięta, więc bez z-fightingu). Klucz przeszklenia `window_m: [szer, przerwa]`
   — pas dzielony na osobne okna punktowe.
3. `buildings_mesh.py`: override budynku `ribbon: true|false` (autorski typ okien biurowca; 2 linie).
4. `overrides.yaml` (authored_overrides, przeżywają reimport): `g3a-kwadrat-blue-pavilion` — ściana
   `plaster_slate_blue`, piętro `window_m: [1.5, 1.5]`; `g3a-ec-blue-office` — `frame` (LOD0 `window_frame`, LOD1
   `plaster_grey`); `g3a-office-tower-colour` — `ribbon: false, bands: false` (jeden ton `plaster_beige`, rzędy
   `office` zamiast `ribbon`).
5. Budżet draw (LOD1, Low): pawilon +1 materiał w chunku 6_6 (`plaster_slate_blue`), wieżowiec −1
   (`plaster_beige__far_ribbon` znika, `plaster_beige__far_office` chunk 6_6 już rysuje); ramy EC w `plaster_grey`,
   który chunk 6_7 już rysuje.

Odrzucone: nowy bladożółty materiał wieżowca z wariantem dalekiej elewacji (+2 draw w 6_6); osobny biały materiał
ram w LOD1 (`window_frame` nie jest rysowany przez LOD1 chunku 6_7: +1 draw).

## 3. Walidacja

(w toku — runda r1)
