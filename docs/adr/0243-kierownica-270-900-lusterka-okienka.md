# ADR 0243: kierownica dotykowa 270°/900° i lusterka jako stałe okienka (D70)

Status: proponowany (2026-11-15, s21, gałąź `controls-0243`, agent G1 chmury G). Źródło: decyzja właściciela **D70**
(`docs/11_DECYZJE_WLASCICIELA.md`; zamyka decyzyjną część B-076): domyślny zakres kierownicy dotykowej **270°**
(900° w ustawieniach), lusterka jako **stałe okienka na ekranie**. Feel test bramki 2 (B-075) — później, poza zakresem.
Rozszerza ADR 0042/0046/0068 (budżet lusterek), 0058/0135 (kierownica), 0079 (układ HUD), 0136 r2 (rozdzielczość Low).

## 1. Stan zastany (origin/main @ 830b077b) — co już było

| Obszar | Stan przed tym ADR | Plik |
|---|---|---|
| Zakres kierownicy | domyślnie **270°** od pierwszego schematu ustawień (nigdy nie było 900° domyślnie: `git log -S "wheelRangeDeg = "`); krok 90° w zakresie 180–900°; przycisk „Ster.” w HUD przełącza 270 / 900 / gyro | `Input/ControlSettings.cs`, `UI/ControlSettingsPanel.cs`, `Gameplay/DrivingLabBootstrap.cs` |
| Zapis ustawień | jeden JSON w PlayerPrefs `controls.settings`, schemat 4 z migracjami v0→v4, `PlayerPrefs.Save()` po każdej zmianie (proces może zginąć) | `ControlSettings.Save/Load/Migrate` |
| Okienka lusterek | **istniały**: dwa `RawImage` 160×290 jedn. (obraz 150×280, odbity w poziomie) po obu stronach zestawu wskaźników, w strefie bezpiecznej (canvas = `Screen.safeArea`, ADR 0079); tylko w widoku z kabiny; chowane, gdy deweloperska telemetria / panel potrzebują miejsca | `UI/Driving/HudLayout.cs`, `UI/Driving/DrivingHud.cs` |
| Włącznik okienek | **przełącznik na stronie laboratorium** (panel deweloperski), osobny klucz PlayerPrefs `lab.mirrorInsets` (domyślnie 1) — poza ustawieniami gracza i poza schematem zapisu | `DrivingLabBootstrap` |
| Kamery lusterek | 6 kamer RT (R46 kl. II×2, IV×2, V, VI); okienka pokazują RT klasy II (ta sama tekstura co szkło w kabinie — zero dodatkowych renderów); `ForceRender` = klasa II jest kandydatem także, gdy szkła nie widać | `Vehicle/Runtime/RenderTextureMirror.cs` |
| Koszt na Low | limit 1 render/klatkę jako **kwota** (ważony round-robin ADR 0042) → z okienkami kandydat jest zawsze, więc **dokładnie 1 render lusterka w każdej klatce**; RT klasy II 224 × 0,75 = **168 px** wysokości (ADR 0136 r2) | `VehicleCameraBudget`, `MirrorRefreshSchedule` |
| Zmierzony koszt | A16 Low, kabina: „Mirrors (1 render/frame)” = **0,75–1,25 ms GPU p50** (ADR 0106, `docs/PERFORMANCE_BUDGETS.md` §„Measured: A16 Low GPU frame breakdown”) | — |

Wniosek: D70 w większości już działało jako ustawienie domyślne; brakowało (a) wyboru okienek w ustawieniach gracza
i w schemacie zapisu, (b) szybkiego wyboru 270/900 w ustawieniach, (c) tańszego harmonogramu na Low przy stale
widocznych okienkach, (d) logiki okienek i harmonogramu w klasach testowalnych EditMode (zestaw EditMode nie
referuje `Game.UI`, więc `HudLayout` testują tylko PlayMode).

## 2. Decyzja

1. **Ustawienia, schemat 5** (`ControlSettings`): pole `mirrorInsets` (domyślnie `true`), stałe
   `TouchHalfRangeComfortDeg = 270`, `TouchHalfRangeSimDeg = 900`, `SetTouchWheelPreset(bool)`, `TouchWheelSimRange` (próg 600°,
   jak dotychczasowy podział trybu „Ster.”). Linia `[CONTROLS]` dostaje `mirrors=insets|look`.
2. **Migracja v4→v5**: `mirrorInsets = true` (decyzja właściciela, ten sam wzór co v3→v4 w ADR 0135). Stary klucz
   `lab.mirrorInsets` nie jest już czytany. **Zakres kierownicy NIE jest resetowany**: 270° było domyślne od zawsze,
   więc zapisane 900° (albo 450°…) to świadomy wybór gracza; v5 z `mirrorInsets: false` zostaje `false`; zapis z
   przyszłego schematu zachowuje znane pola; wartości spoza 180–900 są przycinane.
3. **Panel ustawień**: wiersz „Zakres: komfort/sym.” 270° / 900° nad dotychczasowym krokowym „Zakres kierownicy”
   (krok 90° zostaje), wiersz „Lusterka: okienka / rozglądanie” w sekcji KAMERA. Przełącznik laboratorium zapisuje
   teraz to samo pole (`Controls.Save()` + `[CONTROLS] lab-mirrors`).
4. **Układ okienek** → czysta klasa `Game.Controls.MirrorInsetLayout` (`Input/MirrorInsetLayout.cs`): rozmiar 160×290
   jedn., ramka 5, `Place(...)` (lewe/prawe obok zestawu wskaźników, od górnego marginesu; zwraca `false`, gdy okienko
   wyszłoby poza strefę bezpieczną — wtedy HUD je chowa zamiast wcisnąć), `ToScreenPixels`, `Inside`,
   `TexelsPerPixel`. `HudLayout.Solve` woła `Place`; liczby i położenie **bez zmian** (testy PlayMode HudLayout).
5. **Harmonogram na Low z okienkami** → czysta klasa `Game.Vehicle.Runtime.MirrorInsetBudget`; `VehicleCameraBudget`
   tylko deleguje (`DueScheduleWith`, `FillSpare`, `MirrorIntervalFor(..., insets)`). Tylko Low i tylko przy
   okienkach: krok „due” z ADR 0068 (limit 1 jako górna granica, **bez dopełniania** wolnych slotów), interwały
   (WORKING_VALUE):

   | Klasa R46 | jazda | postój | przy 30 FPS |
   |---|---|---|---|
   | II (okienka + szkło) | 3 klatki | 3 klatki | 10 Hz |
   | IV, V, VI (tylko gdy szkło na ekranie) | 16 klatek | 32 klatki | 1,9 Hz / 0,9 Hz |

   Medium, High, Ultra i wszystkie poziomy bez okienek — **bez zmian** (test `Policy_OnlyLowWithWindows_ChangesTheSchedule`).
   Rozdzielczość RT bez zmian (Low 168 px).
6. **A/B na telefonie**: nowy klucz `rq_ab mirrorrate` (B = stary round-robin) w `ExtraViewCostMonitor`; `rq_mirror_rate 0`
   wymusza stary harmonogram na stałe.

## 3. Rachunek (WORKING_VALUE / ESTIMATED — do pomiaru)

**Interwały.** Obciążenie = Σ 1/interwał. Klasa II: 2 × 1/3 = 0,667. Wypukłe: k × 1/16 (k = liczba szkieł
IV–VI na ekranie, 0–4). Najgorszy przypadek (wszystkie 6): 0,667 + 0,25 = **0,917 < 1** — zostaje luz, więc klasa II nie
jest głodzona. Odrzucone: II co 4 + wypukłe co 8 (= 1,0, stała rywalizacja o slot, klasa II spada do 7,5 Hz) i II co 3
+ wypukłe co 12 (= 1,0, to samo). Interwał 3 dla klasy II = to, co round-robin już dawał przy typowym widoku
(2 kl. II + 2 wypukłe na ekranie: wagi 1+1+0,5+0,5, limit 1 → kl. II co 3. klatkę; symulacja: średnio 3,00) — okienka
nie tracą płynności; tanieją lusterka wypukłe (co 6 → co 16 klatek), które przy jeździe naprzód są małe i z boku.

**Symulacja** (`MirrorRefreshSchedule.StepDue`/`Step`, 960 klatek, ten sam kod co w grze; .NET runner, wynik poniżej):

| Scenariusz Low | renderów/klatkę stary → nowy | kl. II średnio / maks. odstęp | wypukłe średnio |
|---|---|---|---|
| tylko okienka (szkieł nie widać) | 1,000 → 0,667 | 3,00 / 3 | — |
| widok naprzód: II L/P + IV L + VI | 1,000 → 0,792 | 3,00 / 4 | 16,0 (było 6,0) |
| wszystkie 6 na ekranie, jazda | 1,000 → 0,917 | 3,00 / 4 (było 4,00) | 16,0 (było 8,0) |
| wszystkie 6, postój | 1,000 → 0,792 | 3,00 / 4 | 32,0 |

Maks. odstęp 4 = jitter jednej klatki, gdy wypukłe trafia na slot klasy II (dług przechodzi, średnia zostaje 3,00).

**GPU (ESTIMATED).** ADR 0106: 1 render lusterka/klatkę = 0,75–1,25 ms GPU p50 na A16 Low (mieszanka klas; RT wypukłych
jest mniejsza, więc oszczędność na nich może być niższa niż średnia). Δ renderów 0,083–0,333/klatkę →
**−0,06 do −0,42 ms GPU p50**; typowy widok naprzód (−0,208) → **−0,16 do −0,26 ms**. CPU: render lusterka to pełny
cull + submit (ADR 0068: 2,6–4,3 ms CPU w edytorze, telefon UNVERIFIED) — ta sama proporcja oszczędności.

**Rozdzielczość.** Obraz okienka 280 jedn.; na ekranie 1080 px krótszego boku przy nieznanym DPI 1 jedn. = 1 px →
168 / 280 = **0,60 teksela/piksel** (powiększenie 1,67×; test `Windows_TexelRatio_A16Low`). Większe ekrany (QHD+,
Fold, tablet) 0,41–0,49 (runner). Świadomie bez zmian: obniżenie do np. 128 px (0,46) da mniej niż harmonogram, bo
koszt lusterka na G57 to głównie cull/submit/geometria, nie wypełnianie (ADR 0068/0106); podniesienie do 224
(`rq_mirror_res 1.33`, 0,80) — do oceny wizualnej właściciela po pomiarze, nie teraz.

**Zero GC.** `MirrorInsetLayout` i `MirrorInsetBudget` bez alokacji (testy z `GC.GetAllocatedBytesForCurrentThread`);
`StepDue` bez alokacji (istniejący `MirrorCostTests`). Zapis ustawień alokuje tylko przy zmianie (poza pętlą).

## 4. Testy

- EditMode `Tests/EditMode/Controls0243Tests.cs` (12 testów): domyślne 270 + okienka + schemat 5; preset 270/900 i
  zapis/odczyt; migracja v4 (270/450/900 zachowane, okienka wł.), schemat bez pola, klucz legacy; v5 round-trip,
  przycięcie, reset; kierunek skrętu (prawo +, lewo −) w obu presetach i obu gestach + proporcja 270/900; okienka w
  `Screen.safeArea` na 9 ekranach (19,5:9, wycięcia, 16:9 720p, 21:9, QHD+, Fold ~1:1, tablet 16:10, 4:3): w kanwie,
  w pikselach strefy bezpiecznej, symetrycznie, obok i nie na zestawie wskaźników, nie nad drogą; „nie mieści się” →
  `false`; stosunek teksel/piksel; brak alokacji; tabela polityki per poziom; symulacje harmonogramu (jak w §3).
- Zmieniony `SteerFoldTests.Settings_Schema4_...`: zamiast „schemat == 4” → „≥ 4” i `CurrentSchema` po migracji.
- .NET runner `tools/controls-runner` (bez Unity, ta sama zawartość plików źródłowych + `UnityShim.cs`):
  `dotnet test tools/controls-runner/Tests/ControlsTests.csproj` → **13/13 zielone** (2026-11-15). `VehicleCameraBudget`
  (asembler z URP) nie jest tam kompilowany — testowany w EditMode.
- NIEuruchomione (brak Unity w chmurze): EditMode, PlayMode (`HudLayoutTests`, `ControlSettingsPanelTests` — nowe
  wiersze panelu), kompilacja Androida, visual QA panelu ustawień (szerokość przycisków 200 jedn. dla „rozglądanie”).

## 5. Pomiar dla lidera (A16 `RFGL34SJYDZ`, Low)

1. `pwsh scripts/test.ps1 -Platform EditMode` (oczekiwane: `Controls0243Tests` 12/12, reszta bez regresji), potem
   `pwsh scripts/test.ps1 -Platform PlayMode` (HudLayout, panel ustawień).
2. `pwsh scripts/build-android.ps1 -Install -Run -Serial RFGL34SJYDZ -Tier Low` — w logcat `[CONTROLS] loaded v5 ... mirrors=insets`.
3. A/B w jednym przejeździe (stały render scale, bez pacingu, kabina, trasa):
   `pwsh scripts/device-metrics.ps1 -Serial RFGL34SJYDZ -Launch -DurationSeconds 120 -Tier Low -Uncapped -Scene WorldC -Autopilot route -Trailer 40 -Extra "rq_scale=0.75,rq_pacing=0,rq_ab=mirrorrate,rq_ab_period=4"`
   → `[PASSAB] summary` (A = ADR 0243, B = stary round-robin): oczekiwane Δ GPU p50 0,1–0,4 ms; `[DIAG]` mirror
   renders/frame A ≈ 0,67–0,92, B = 1,00.
4. Koszt lusterek ogółem po zmianie: to samo z `rq_ab=mirrors`.
5. Wpisać wynik do `docs/PERFORMANCE_BUDGETS.md` (wiersz „Extra cameras”) i tu („Wynik”); jeśli Δ < 0,05 ms — zostawić
   (płynność kl. II bez zmian), jeśli okienka wyglądają skokowo przy 10 Hz — `rq_ab` nie pomoże, decyzja właściciela.

## 6. Konsekwencje i otwarte

- Okienka zostają w miejscu z ADR 0079 (obok zestawu wskaźników). Alternatywa „przy krawędziach ekranu, jak słupki A”
  koliduje z przyciskiem deweloperskim i telemetrią; do ewentualnej oceny właściciela razem z feel testem (B-075).
- Wypukłe lusterka na Low odświeżają się rzadziej (1,9 Hz w ruchu) — przy manewrach z rozglądaniem obraz w szkle
  kl. V/VI może wyglądać skokowo; mierzalne, odwracalne `rq_mirror_rate 0`.
- Pierwszy obraz lusterka wypukłego, które dopiero weszło w kadr, pojawia się na Low po ≤ 16 klatkach (start z
  przesunięciem fazy ADR 0068; to samo zjawisko na High przy interwale 4). Okienka kl. II mają obraz po ≤ 3 klatkach.
  Do sprawdzenia na telefonie przy rozglądaniu (czy szkło nie pokazuje przez ~0,5 s pustej tekstury).
- Dotknięte pliki poza własnością G1 (konieczne do zadania): `Vehicle/Runtime/RenderTextureMirror.cs` (3 linie
  delegacji w `Schedule`, nowe metody `VehicleCameraBudget`), `Vehicle/Runtime/MirrorInsetBudget.cs` (nowy),
  `Rendering/Runtime/ExtraViewCostMonitor.cs` (klucz `mirrorrate`). Bez zmian asmdef, ProjectSettings, Packages, scen, prefabów.
- Teksty panelu („Zakres: komfort/sym.”, „Lusterka”, „okienka”, „rozglądanie”) są — jak reszta panelu — w kodzie;
  tabela tekstów dla panelu ustawień nie istnieje (wzór: `UI/CabDisplays/CabDisplayText.cs`; osobne zadanie).

## Wynik

(do uzupełnienia przez lidera po pomiarze A16)
