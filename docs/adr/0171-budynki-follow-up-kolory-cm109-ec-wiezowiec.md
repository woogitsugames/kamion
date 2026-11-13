# ADR 0171 — follow-up budynków po 0167: kolory okładzin (cm109685822, EC cm92458760, wieżowiec 177786/178689)

Status: PROPOSED na gałęzi `bldg2-0171` (2026-11-13, s17); nie scalone; ocena `visual-critic` wymagana.
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

## 3. Walidacja (runda r2, zmierzone)

`build_world` exit 0, import exit 0, vqa Low-clear exit 0, SBS Low clear + overcast 42 + 42 pary. Dowody (poza gitem):
`artifacts/bldg2-0171/` w katalogu głównym — `pairs/Low-clear|Low-overcast`, `four-frames-r2-Low-clear.jpg`,
`r2/budget-vs-base.txt`, `r2/stats.txt`, `base-stats-Low-clear.txt`, `tools/`, `logs/`. Runda r1: `pairs-r1/`.

| Wielkość | Wynik |
|---|---|
| draws, tier Low, 48 kamer kontrolnych, baza = ta gałąź przed zmianą | **+0 we wszystkich 48** (r1: +2 w 8 kamerach G3-A — LOD0 chunku 6_6 rysowany z bliska dostał `plaster_slate_blue`, a `plaster_band_grey` został na 8 trójkątach biurowca `bdot:…C926`; override `g3a-small-office-no-band`, powód budżetowy, confidence low) |
| trójkąty | maks. +1,95 % (cab-grain; LOD0 wieżowca z oknami punktowymi +3500), mediana ok. +0,1 % |
| prymitywy LOD1 budynków (65 chunków) | netto 0; trójkąty LOD1 94 604 → 94 938 (+0,35 %) |
| kamery kontrolne baza → r2, piksele z |Δ| > 25 | stretch-02 4,3 %, kwadrat-park-gate 3,2 %, pozostałe 46 ≤ 0,53 % (mediana 0,0 %) |
| testy `tests/gis` 0167 / 0171 / g3b_frontage | 29 zielonych (pełny `tests/gis` nie uruchomiony w tej rundzie) |

Kolory (średni sRGB wycinka, Low): budynek EC overcast (50,75,105) wobec ciemnego członu na zdjęciu (59–64,81,98–100)
— było (40,61,82); długie jasne skrzydło na zdjęciu (101,133,143) pozostaje jaśniejsze i bardziej cyjanowe. Pawilon:
ściana boczna w słońcu (112,129,145) — było (172,168,155); overcast (69,81,97). Wieżowiec: ściana w słońcu
(160,157,145), ciepła, z oknami punktowymi — zdjęcie (214,209,190) jest nadal jaśniejsze.

## 4. Otwarte

- Ocena `visual-critic` (subagent nie uruchamia subagentów) i zrzuty z telefonu (APK Low na A16).
- Wieżowiec jaśniejszy / bledszy: wymaga nowego materiału z wariantem dalekiej elewacji (+2 draw w 6_6) albo
  rozjaśnienia sceny (ekspozycja / światło — poza zakresem). Długa elewacja na zdjęciu jest prawie biała, szczyt
  piaskowy — dwa tony = kolejny draw.
- Jasne skrzydło budynku EC (drugi odcień błękitu) — odrzucone w 0167 z powodu draw; bez zmian.
- Szyby LOD1 pawilonu na ścianie SW odbijają niebo jasnobłękitnie (materiał ramy `hall_flashing`, metal 0,3).
- `generated/` nie jest commitowane — przebudowa świata po scaleniu + powtórka SBS Low.
- Fakty z przeglądu M53 (`docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p3.md`; kolory ESTIMATED ze zdjęć), poza
  zakresem 0171 (żaden z tych budynków nie leży w kadrach cm109 / cm924 / 177786 / 178689) — do osobnego zadania:
  bloki Białostoczka kremowobiałe z czerwonobrązowymi / pomarańczowymi balkonami i pastelowymi szczytami; punktowce
  białe z żółtymi / czerwonymi / pomarańczowymi panelami; Tysiąclecia 6 żółtozielony, Tysiąclecia 10 biały; MPZP
  XXVII/451/26 (nowa zabudowa): elewacje maks. 3 kolory z zakresu biel / beż / brąz / szarość. Kolumny `kolor_srgb`
  z PR #50 ani przypisań budynków z tamtego manifestu NIE używać (błędna w 4 z 5).
