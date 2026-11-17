# Jak grać w Kamion na PC (Windows) — instrukcja dla właściciela i testerów

Stan kodu: `origin/main` z 16.11.2026, wieczór (sesja 23, po scaleniu streamingu `int-stream-s23`). Wszystko poniżej jest wyczytane z kodu i skryptów; źródło każdego
przypisania klawisza, przycisku, osi i argumentu (`ścieżka:linia`) jest w komentarzu na dole pliku. Czego nie dało się
ustalić z kodu, oznaczono **UNVERIFIED**. Liczby wydajności i wymagań to **WORKING_VALUE** (niezmierzone na klasach D74).

---

## 1. Uruchomienie

### 1.1 Folder buildu (`artifacts/win/kamion-<wersja>-<sha>[-low][-regions][-dev]/`)

| Plik | Co robi |
|---|---|
| `Kamion.exe` | Gra. Bez argumentów startuje w **pełnym ekranie bez ramki** w natywnej rozdzielczości monitora (ProjectSetup.ApplyStandaloneWindowSettings), chyba że plik ustawień mówi inaczej (sekcja 3). Alt+Enter przełącza pełny ekran / okno; okno można powiększać myszą. Uwaga: Unity pamięta ostatni tryb okna — jeśli po starszym buildzie gra otwiera się w oknie, naciśnij raz Alt+Enter. |
| `Kamion-okno.cmd` | Start w oknie 1600 × 900 (jedyny launcher wymuszający okno), do menu startowego. |
| `Kamion-<region>.cmd` | Jeden plik na **każdy region, którego scena jest w buildzie** (lista z logu buildu), np. `Kamion-knyszyn.cmd`, `Kamion-knyszyn-w.cmd`, `Kamion-dk65-05.cmd`. Tryb ekranu jak `Kamion.exe` (pełny ekran bez ramki) i od razu `-scene <region>`. Bez strumieniowania. |
| `Kamion-korytarz.cmd` | **Ciągła jazda** (sekcja 1.4): tryb ekranu jak `Kamion.exe`, start w regionie knyszyn, `-stream 1`. Powstaje tylko, gdy w buildzie są regiony `knyszyn` **i** `knyszyn-s` **oraz** scena kafla `World_knyszyn-s_Tile` (bez niej szew zostaje zamknięty; build-hygiene-s23). |
| `Kamion-d3d11.cmd`, `Kamion-korytarz-d3d11.cmd` | Awaryjnie (sekcja 1.6): to samo co `Kamion.exe` / `Kamion-korytarz.cmd` z `-force-d3d11`. Korytarzowy tylko razem z `Kamion-korytarz.cmd`. |
| `build-id.json` | Skrót zawartości `Kamion_Data` — gra pokazuje go w menu, w „Informacjach” i w logu `[BOOT]`; po nim rozpoznaje się build. |
| `Kamion.exe.sha256`, `build.json` | Metadane buildu (suma exe, liczba plików, rozmiar). Suma exe nie identyfikuje buildu (exe to ten sam launcher Unity w każdym buildzie). |

Launchery pisze `scripts/postbuild-windows.py` (wywoływany przez `scripts/build-windows.ps1` po udanym buildzie).
Każdy `.cmd` przekazuje dalej własne argumenty (`%*`), np. `Kamion-okno.cmd -tier Low -fps 30` albo
`Kamion-korytarz.cmd -force-d3d11`. Gotowe warianty D3D11: `Kamion-d3d11.cmd`, `Kamion-korytarz-d3d11.cmd` (sekcja 1.6).

`-scene` działa **raz na uruchomienie**: po „Menu” w jeździe zostajesz w menu startowym (log
`[BOOT] launch argument scene already used this run`), a nie wracasz do regionu z launchera. Region wybierzesz wtedy
w menu („REGION — START NA POCZĄTKU TRASY” → „Jedź w wybranym regionie”).

### 1.2 Paczka zip dla testera (ADR 0271)

Tworzy ją lider: `uv run --no-project python scripts/package-windows.py artifacts/win/<folder buildu>` →
`artifacts/dist/kamion-<wersja>-<sha>[-low][-regions][-dev][-dirty]-<skrót zawartości>-win64.zip` (+ `.sha256`, `.json`).

| W paczce | Nie ma w paczce |
|---|---|
| `Kamion.exe`, `Kamion_Data\`, `build-id.json`, `Kamion-okno.cmd` | launchery `-scene` regionów spoza buildu (np. `Kamion-knyszyn-w.cmd`, gdy knyszyn-w nie ma w buildzie) |
| `Kamion-<region>.cmd` — dla regionów w buildzie (bez wyjątku „deweloperskiego”; także `Kamion-knyszyn.cmd`) | |
| `Kamion-korytarz.cmd` — gdy region knyszyn jest w buildzie (paczka sprawdza region z `-scene`) | |
| `README.txt` (wymagania, start, SmartScreen, ścieżki logów) | `build.json`, `Kamion.exe.sha256`, `*.pdb`, foldery `*_DoNotShip` |
| `THIRD_PARTY_NOTICES.txt`, `SHA256SUMS.txt` | |
| `collect-logs.ps1` + `Zbierz-logi.cmd` (zbieranie logów) | |

Skąd skrypt wie, co jest w buildzie: lista scen z logu buildu (`build.json` → `log`), a bez logu `build.json`
`regions`/`regionsFile` rozwinięte katalogiem regionów; bez `build.json` żaden launcher regionu nie trafia do paczki
(ADR 0271, uzupełnienie s23).

Tester:
1. Rozpakuj **cały** zip do zwykłego folderu (nie uruchamiaj gry z wnętrza zip).
2. Uruchom `Kamion.exe` (pełny ekran), `Kamion-okno.cmd` (okno) albo — jeśli jest — `Kamion-korytarz.cmd` (ciągła jazda).
3. Windows może pokazać „System Windows ochronił ten komputer” (SmartScreen) — gra nie ma podpisu cyfrowego.
   Sprawdź sumę SHA256 pliku zip z tą od autora, potem „Więcej informacji” → „Uruchom mimo to”.

### 1.3 Argumenty wiersza poleceń

Zapis: `Kamion.exe -nazwa wartość` (argumenty gry: zawsze para; flaga bez wartości na końcu linii jest ignorowana).
Argumenty silnika Unity (`-screen-*`, `-window-mode`, `-force-d3d11`, `-logFile`) czyta sam Unity, nie kod gry.
Kolejność ważności: argument > zapisany wybór > wartość domyślna.

**Dla gracza / testera**

| Argument | Wartości | Domyślnie (bez argumentu) | Uwagi |
|---|---|---|---|
| `-scene` | id regionu (np. `knyszyn`, `dk65-05`), skrót (`c` = bialystok-industrial-c, `dojlidy` = id bez `bialystok-`), albo nazwa sceny (`DrivingLab`, `WorldC`) | menu startowe | Region ładuje się w wersji High, jeśli bieżący tier to High/Ultra i scena High jest w buildzie. Raz na uruchomienie (sekcja 1.1). |
| `-stream` | `1` | wyłączone (każda inna wartość też = wyłączone) | Strumieniowanie sąsiednich kafli — ciągła jazda między regionami (sekcja 1.4). |
| `-tier` | `Low` / `Medium` / `High` / `Ultra` (wielkość liter dowolna) | zapisany wybór, a bez niego dobór sprzętowy (sekcja 4) | Tylko na ten przebieg — pliku ustawień nie zmienia. |
| `-fps` | liczba > 0 (np. `30`, `60`, `1000` = praktycznie bez limitu) | 60 na PC (WORKING_VALUE) albo zapisany wybór | Tylko na ten przebieg. |
| `-route_s` | metry od początku trasy regionu (≥ 0) | punkt startowy regionu | Gdy wskazane miejsce jest zablokowane, start przesuwa się wzdłuż trasy (log `[START]`). |
| `-route_end` | metry (> 0) | koniec trasy | Gdzie autopilot trasy łagodnie się zatrzyma. |
| `-trailer` | `solo`, `empty`/`pusta`, `24`/`24t`, `40`/`40t` | plac: zapisany wybór (pierwszy raz 24 t); region: zestaw z naczepą | `solo` = sam ciągnik. |
| `-lighting` | `clear`, `overcast`, `lowsun`, `dusk` | wybór „Pora dnia” z menu | Nieznana nazwa → ostrzeżenie w logu. |
| `-screen-fullscreen`, `-screen-width`, `-screen-height` | Unity: `0`/`1`, piksele | — | Jeśli podasz dowolny `-screen-*`, `-window-mode` albo `-popupwindow`, gra **nie** nakłada trybu ekranu z pliku ustawień (sekcja 1.5). |
| `-window-mode` | Unity (tylko Windows): `exclusive` / `borderless` | — | Rodzaj pełnego ekranu. Żaden launcher go nie podaje (od alt-window-s23 korytarz bierze tryb z ustawień). |
| `-force-d3d11` / `-force-d3d12` | Unity (tylko Windows), **bez wartości** | API wybrane przez Unity (sekcja 1.6) | Wymusza Direct3D 11 / 12. Awaryjnie przy crashu D3D12 (sekcja 1.6). |

**Pomiarowe (nie dla zwykłej gry)**

| Argument | Wartości | Domyślnie | Co robi |
|---|---|---|---|
| `-autopilot` | `route` (jedzie trasą regionu), `straight080` (prosta), `circle25` / inna wartość (okrąg na placu) | wyłączony | Autopilot do pomiarów; HUD pokazuje „AUTOPILOT (pomiar)”. |
| `-speed` | km/h | `route` 50, `straight080` 80, `circle25` 25, inny okrąg 40 | Prędkość autopilota. Przy `route` domyślnie zestaw 40 t. |
| `-shot` / `-shot_t` / `-quit_t` | plik PNG / sekundy / sekundy | brak / 20 s / brak | Zrzut ekranu po `shot_t` s i wyjście po `quit_t` s. |
| `-telemetry 1`, `-devhud 1`, `-camlog 1`, `-pc_tiers 0`, `-engine_audio el\|synth` | | wyłączone | Telemetria CSV, HUD diagnostyczny, log pozycji kamery, tiery mobilne zamiast PC, zestaw dźwięku silnika. |

### 1.4 Ciągła jazda między regionami (`-stream 1`, `Kamion-korytarz.cmd`)

`Kamion-korytarz.cmd` = `Kamion.exe -scene knyszyn -stream 1 %*` (tryb ekranu z pliku ustawień, bez niego pełny ekran bez ramki).

Co robi `-stream 1` (ADR 0235 / 0273, scalone 16.11 jako `int-stream-s23`):
- Czytany przy każdym starcie sceny jazdy w regionie (także regionu wybranego potem z menu w tym samym uruchomieniu).
  Bez niego region kończy się jak dotąd: zamknięcie drogi i komunikat „Koniec mapy za ok. 250 m: droga zamknięta,
  zwolnij”.
- Włącza się tylko, gdy region startowy jest w grafie kafli i co najmniej jedna **sąsiednia scena kafla**
  (`World_<id>_Tile`, przy treści High `World_<id>_High_Tile`) jest w buildzie. Inaczej w logu `[STREAM] off: …`
  i jazda jak bez argumentu. Po włączeniu w logu `[STREAM] on: start <region>, …`.
- Sąsiednie kafle doładowują się w tle w promieniu ok. **400 m** (25 m/s × (8 + 1 + 1) s + 150 m; WORKING_VALUE),
  najwyżej **4 kafle** naraz, w budżecie pamięci świata PC: Low 640 / Medium 800 / High 1450 / Ultra 2000 MB
  (WORKING_VALUE). Gdy sąsiad jest gotowy, zamknięcie drogi na wspólnej krawędzi znika; sąsiada, którego nie ma
  w buildzie, nie ładuje — tam szew zostaje zamknięty.
- Treść High kafli tylko wtedy, gdy region startowy wystartował w scenie `_High` (tier High/Ultra i scena High
  w buildzie); przy Low/Medium strumieniuje się treść Low.
- Autopilot trasy (`-autopilot route`) przechodzi przez szwy: trasa kafla jest doklejana, gdy jej początek leży
  ≤ 3 m od końca bieżącej.

**Kafle w grafie** (`tile_graph.json`, 21 kafli = 21 regionów katalogu):

| Łańcuch trasy | Kafle |
|---|---|
| główny (17 kafli, = zestaw `d67`) | bialystok-industrial-c → bialystok-maczka → bialystok-kleeberga → bialystok-knyszynska → dk65-01 … dk65-11 → knyszyn-s → knyszyn |
| boczny (2 kafle) | knyszyn-w → dk65-monki-01 |
| bez łańcucha | dw671-tykocin-01 (sąsiaduje z knyszyn-w, knyszyn-s, narożnikiem z knyszyn), bialystok-dojlidy (bez sąsiadów) |

**Przerwy (z danych w `origin/main`):**
- **bialystok-dojlidy** nie ma w grafie żadnego sąsiada → nigdy się nie strumieniuje; tylko jako osobny region.
- **knyszyn ↔ knyszyn-w**: kafle mają wspólną krawędź, ale trasa knyszyn kończy się na Rynku (nie na krawędzi
  kafla), więc nie ma portalu trasy — autopilot tam nie przejdzie. Jazda ręczna na zachód (DK65 Obozowa) otworzy szew
  tylko wtedy, gdy scena kafla knyszyn-w jest w buildzie; `Kamion-korytarz.cmd` wymaga knyszyn, knyszyn-s i sceny kafla knyszyn-s.
  Przejazdu przez ten szew nikt nie sprawdził (**UNVERIFIED**).
- **dw671-tykocin-01**: trasa zaczyna się na krawędzi z knyszyn-w, ale trasa knyszyn-w wychodzi na północ (do Moniek)
  → brak portalu; jazda ręczna przez szew — jak wyżej, **UNVERIFIED**.
- **Końce mapy**: dk65-monki-01 (krawędź zachodnia, „next lattice tile (-10,9) not built”), dw671-tykocin-01
  (krawędź południowa, „(-9,6) not built”) — tam „Koniec mapy”.
- Region zaimportowany przed ADR 0235 nie ma sceny `_Tile` i build jej nie dołącza → szew z nim zostaje zamknięty.
  Które sceny `_Tile` istnieją, zależy od lokalnego importu (`_Generated/`, poza gitem) — z repo nie da się tego ustalić.
- Pierścienia Mońki / Tykocin (world2: dk65-monki-02…07, monki, dw671-tykocin-02…09, tykocin) **nie ma** w `origin/main`
  (katalog regionów ma 21 regionów).

Jedyny pomiar przejazdu (HANDOVER 16.11 16:5x): knyszynska → dk65-01 → 02 → 03, 0 zamkniętych szwów.

**Ciągła jazda z innego regionu:** launcher regionu przekazuje argumenty, więc np. `Kamion-dk65-05.cmd -stream 1`
(okno 1600 × 900) albo `Kamion.exe -scene dk65-05 -stream 1` (pełny ekran z projektu / pliku ustawień).

### 1.5 Pełny ekran i okno

| Start | Tryb |
|---|---|
| `Kamion.exe` bez argumentów | z pliku ustawień (sekcja 3), a bez pliku — projekt: `fullscreenMode: 1` (bez ramki, rozdzielczość natywna) |
| `Kamion-okno.cmd` | okno 1600 × 900 (`-screen-fullscreen 0 -screen-width 1600 -screen-height 900`) |
| `Kamion-<region>.cmd`, `Kamion-korytarz.cmd`, `Kamion-*-d3d11.cmd` | jak `Kamion.exe` (bez `-screen-*`; `-force-d3d11` nie zmienia trybu ekranu) |

- Z dowolnym `-screen-*` / `-window-mode` / `-popupwindow` gra przy starcie **pomija** tryb ekranu z pliku ustawień.
- Okna 1600 × 900 **nie da się powiększyć** przeciągnięciem: w projekcie `resizableWindow: 0` (zgłoszenie właściciela
  16.11 15:2x; poprawka zaplanowana, w `origin/main` jej nie ma). Zmień tryb w menu (sekcja 3) albo uruchom `Kamion.exe`.
- **Alt+Enter**: w projekcie `allowFullscreenSwitch: 1` — wg dokumentacji Unity to pozwala przełączać pełny ekran /
  okno skrótem systemowym. Na buildzie Kamion nie sprawdzone (**UNVERIFIED**), podobnie jak to, czy zmiana trafia do
  pliku ustawień.
- Trwała zmiana: menu startowe → **Ekran, grafika, dźwięk** → „Tryb okna” (okno / bez ramki / pełny ekran),
  „Rozdzielczość” → Zastosuj (sekcja 3).

### 1.6 Awaryjnie: Direct3D 11 (`-force-d3d11`)

16.11 gra padła u właściciela (exe 13104cf215, knyszyn, pełny ekran bez ramki, RTX 5070) z błędem
`d3d12: Device failed error (887a0001)` (urządzenie D3D12 usunięte); lider uruchomił ją potem z `-force-d3d11`.
Przyczyna nieustalona (hipoteza o równoległym obciążeniu GPU przez Unity — **UNVERIFIED**).

- Projekt nie ustawia listy API grafiki dla Windows (w ProjectSettings są wpisy tylko dla iOS i Androida) → Unity
  wybiera API sam; którego używa domyślnie — z repo nie wynika (crash pokazuje D3D12).
- Gdy gra pada (zwłaszcza z „d3d12” / „Device failed” w `Player.log`), uruchom `Kamion-d3d11.cmd` (menu) albo
  `Kamion-korytarz-d3d11.cmd` (jazda ciągła); inne starty: dopisz argument, np. `Kamion-okno.cmd -force-d3d11`,
  `Kamion-knyszyn.cmd -force-d3d11`.
- Czy D3D11 usuwa problem — jedna obserwacja, bez pomiaru (**UNVERIFIED**). W zgłoszeniu podaj, czy był `-force-d3d11`.

---

## 2. Sterowanie

W jeździe działają jednocześnie: klawiatura, pad (dowolny w układzie Xbox/PlayStation) i kierownica USB. Klawiatura
i pad mają przypisania **do zmiany** w grze (sekcja 2.5). Gdy otwarte jest menu/ustawienia, sterowanie pojazdem jest
wstrzymane (klawisze i pad nawigują po menu).

### 2.1 Jazda

| Akcja | Klawiatura | Pad | Kierownica (profil G29 — UNVERIFIED) |
|---|---|---|---|
| Gaz | W lub ↑ | prawy spust | pedał gazu |
| Hamulec | S lub ↓ | lewy spust | pedał hamulca |
| Kierownica | A / D lub ← / → (narasta, sama wraca) | lewa gałka (poziomo) | koło (bezwzględnie) |
| Hamulec postojowy (przełącz) | Spacja | przycisk dolny (Xbox A) | przycisk `button1` |
| Jazda D | 1 | przycisk lewy (X) | — |
| Luz N | 2 | przycisk prawy (B) | — |
| Wsteczny R | 3 | środkowy lewy (Back/Select) | bieg R w H-shifterze |
| Bieg w górę | E | prawy bumper (RB) | prawa łopatka (`button5`) |
| Bieg w dół | Q | lewy bumper (LB) | lewa łopatka (`button6`) |
| Tryb ręczny / automat | M | — (do przypisania) | — |
| Retarder mocniej | X | krzyżak w dół | `button2` |
| Retarder słabiej | Z | wciśnięcie lewej gałki | `button3` |
| Tempomat zjazdu | B | — (do przypisania) | — |

### 2.2 Światła, sygnały, naczepa

| Akcja | Klawiatura | Pad | Kierownica (G29, UNVERIFIED) |
|---|---|---|---|
| Kierunkowskaz w lewo | `,` (przecinek) | krzyżak w lewo | — |
| Kierunkowskaz w prawo | `.` (kropka) | krzyżak w prawo | — |
| Światła awaryjne | H | krzyżak w górę | `button4` |
| Klakson (trzymaj) | K | wciśnięcie prawej gałki | — |
| Sprzęg naczepy (uzbrój / rozprzęgnij) | **T** | — (do przypisania) | — |
| Podpory naczepy | G | — (do przypisania) | — |

### 2.3 Kamera i widok

| Akcja | Klawiatura | Pad | Mysz |
|---|---|---|---|
| Następna kamera (kabina → pościg → orbita) | **C** lub Tab | przycisk górny (Y) | — |
| Rozglądanie | — | prawa gałka | przeciągnij po ekranie (który przycisk myszy — UNVERIFIED) |
| Przybliżenie | — | — | kółko myszy |
| Lusterka w okienkach na ekranie (wł./wył.) | L | — (do przypisania) | — |
| HUD: szczegóły minimalne / rozszerzone (ADR 0283) | I | — (do przypisania) | — |
| Kamera cofania (wymuś) | V | — (do przypisania) | — |
| Pełna mapa | — | — | klik minimapy (dokładny gest UNVERIFIED); kółko = zoom mapy |

Kamera cofania włącza się też sama na biegu R.

### 2.4 Menu

| Akcja | Klawiatura | Pad | Mysz |
|---|---|---|---|
| Menu / wstecz (w jeździe: zamyka mapę, potem ustawienia, potem wraca do menu startowego) | Esc | środkowy prawy (Start) | przycisk „Menu” w HUD |
| Ruch po menu | strzałki, Tab | krzyżak, lewa gałka | najechanie |
| Wybór | Enter | przycisk dolny (A) | klik |
| Zamknij panel ustawień PC (= Anuluj) | Esc | przycisk prawy (B) | „Anuluj” albo prawy przycisk myszy |
| Zakładki ustawień (Grafika, Sterowanie, Dźwięk, Rozgrywka, Lusterka; ADR 0283) | Q / E | LB / RB | klik zakładki |
| Przewijanie ekranu „Informacje” | ↑ / ↓, PgUp / PgDn | prawa gałka, krzyżak góra/dół | kółko |

Esc i Start pada są na stałe (nie da się ich przypisać). K działa jako klakson zawsze, nawet po zmianie przypisania
klaksonu (kod czyta K bezpośrednio).

Przyciski HUD (np. Menu, Reset) obsługuje tylko mysz — nie łapią fokusu pada ani klawiatury.

### 2.5 Zmiana przypisań (rebinding)

Menu startowe → **Ustawienia** → zakładka **Sterowanie** → **Kierownica, pedały, kamera…** → sekcja „KLAWIATURA I PAD” →
**Przypisania i czułość…** (przycisk jest widoczny tylko w scenie jazdy, gdy działa wejście PC). Na telefonie przycisk
nazywa się dalej „Ustawienia sterowania”. (ADR 0283.)

- Strony **Klawiatura** / **Pad**. Kliknij przypisanie i naciśnij nowy klawisz/przycisk.
- Anulowanie: Backspace (klawiatura) albo Start pada; po 10 s bez wciśnięcia — anulowane samo. Esc nie da się przypisać.
- Konflikt z inną akcją jest pokazywany jako ostrzeżenie.
- „Przywróć domyślne” — dla bieżącej strony.
- Strojenie: pad — „Martwa strefa gałki”, „Krzywa gałki (1 = liniowa)”, „Skręt przy prędkości”;
  klawiatura — „Szybkość skrętu”, „Skręt przy prędkości”.
- Zapis: plik `input_bindings.json` w folderze danych gry (sekcja 5).

### 2.6 Kierownica, pedały, H-shifter

- Wykrywanie automatyczne po identyfikatorze USB / nazwie: profile Logitech G29, G920, G923, Thrustmaster T300, T150,
  Fanatec CSL i profil ogólny. **Wszystkie przypisania osi i przycisków w profilach są UNVERIFIED** (nikt nie
  sprawdził ich na sprzęcie).
- Zakres obrotu w grze: 270–900°, domyślnie z profilu **540°**. **W grze nie ma ekranu ustawień kierownicy**
  (zakres, kalibracja) — ustawienia istnieją tylko jako zapis w rejestrze Unity (`controls.wheel`).
- Bez kalibracji: pierwszy odczyt = środek / pedał puszczony, zakres uczy się z ruchu. Trzymaj koło prosto
  i nie wciskaj pedałów przy starcie sceny.
- **Force feedback nie działa** — kod liczy siłę, ale nie ma jeszcze sterownika wyjścia (koło nie stawia oporu).
- H-shifter (G29/G920/G923): biegi 1–6 + R; przełącznik zakresu (`button7`) dodaje 6 → 12 biegów.
  Luz dopiero po 0,6 s poza bramką. Skok o kilka biegów naraz zmienia bieg skrzyni tylko o 1 (ograniczenie kodu).
- Sprzęgło (pedał) jest odczytywane, wpływ na jazdę — UNVERIFIED (skrzynia zautomatyzowana).
- Kierownica dotykowa (telefon, D70): domyślnie 270°, w „Ustawieniach sterowania” 180–900° co 90°. Na PC nie dotyczy
  kierownicy USB.

---

## 3. Ustawienia PC (ADR 0270, zakładki ADR 0283)

Menu startowe → **Ustawienia** (tylko na PC; jeden ekran, zakładki **Grafika · Sterowanie · Dźwięk · Rozgrywka ·
Lusterka**, przełączanie Q / E, LB / RB albo kliknięciem). Zmiany działają po **Zastosuj**; „Anuluj” / Esc / pad B /
prawy przycisk myszy odrzuca; „Przywróć domyślne” wczytuje domyślne **otwartej zakładki**. Po zmianie trybu ekranu gra pyta „Zachować nowy tryb
ekranu?” i po **15 s** bez odpowiedzi wraca do poprzedniego.

| Ustawienie | Wybór | Domyślnie |
|---|---|---|
| Rozdzielczość | lista monitora | natywna |
| Tryb okna | okno / bez ramki / pełny ekran | bez ramki |
| Synchronizacja pionowa | wyłączona / włączona | wyłączona (gdy włączona, limit klatek jest wyszarzony) |
| Limit klatek | 30 / 60 / 75 / 120 / 144 / bez limitu | 60 |
| Jakość grafiki | auto / niska / średnia / wysoka / ultra | auto (pokazuje, co wybrało, np. „auto (wysoka)”) |
| Skala HUD | 80–140 % co 10 % | 100 % |
| Jednostki prędkości | tylko km/h | km/h |
| Głośność ogólna / Silnik / Otoczenie / Sygnały kabiny | 0–100 % co 5 % | 100 % |
| Rozgrywka: Szczegóły HUD | minimalne / rozszerzone (też klawisz I w jeździe) | minimalne |
| Rozgrywka: HUD w widoku z kabiny | auto / pasek / tylko ostrzeżenia (auto: gdy w kabinie działają zegary, zostają ostrzeżenia i kierunkowskazy) | auto |
| Rozgrywka: Kontrolki dotykowe | auto / zawsze / nigdy | auto |
| Lusterka: Okienka lusterek | wyłączone / włączone (też klawisz L) | włączone |
| Lusterka: Rozmiar | 30–60 % wysokości ekranu co 2 % | 42 % (WORKING_VALUE) |
| Lusterka: Położenie w pionie / Odsunięcie od krawędzi | 0–100 % co 10 % (podgląd układu w zakładce) | 0 % / 0 % |
| Lusterka: Na zewnątrz / do środka, W dół / w górę | ±6° / ±3° co 0,5° (obraca widok obu lusterek głównych) | 0° / 0° |

Plik: `settings_pc.json` w folderze danych gry. Argumenty `-tier` / `-fps` wygrywają z plikiem tylko na dany przebieg.

Menu startowe ma też szybkie przyciski: **Pora dnia (trasy)** (Pochmurno / Niskie słońce / Zmierzch),
**Jakość grafiki** (Low / Medium / High / Ultra), **Limit klatek** (30 / 60 FPS) — zapisywane od razu.

„Ustawienia sterowania” (sterowanie i kamera) zmieniają się od razu i zapisują same: kamera z kabiny
(„Czułość rozglądania”, „Pole widzenia” 45–75°, „Ruch głowy”), dźwięk (zestaw synteza / ElevenLabs), sekcje
„KIEROWNICA DOTYKOWA” i „GYRO” (na PC bez znaczenia) oraz:

**Kontrolki dotykowe** — Menu startowe → **Ustawienia sterowania** → sekcja „KONTROLKI DOTYKOWE I EKRAN” → **Pokazuj**:

| Wybór | Działanie |
|---|---|
| **auto** (domyślnie) | telefon: zawsze widoczne; PC: ukryte, pokazują się dopiero po pierwszym dotknięciu ekranu dotykowego w tej sesji |
| zawsze | zawsze widoczne (kierownica, pedały, R/N/D, dźwignia, kierunkowskazy na ekranie; HUD w układzie dotykowym) |
| nigdy | zawsze ukryte (HUD w układzie monitora) |

Zapis od razu w rejestrze Unity (PlayerPrefs `ui.touchControls`), nie w `settings_pc.json`. Jeśli na PC bez ekranu
dotykowego widzisz kierownicę i pedały na ekranie, masz zapisane „zawsze” (tak było u właściciela 16.11) — ustaw
**auto** albo **nigdy**. Obok: „Skala HUD (monitor)”.

---

## 4. Wymagania (D74) i który tier wybrać

Wszystko **WORKING_VALUE** — niezmierzone na sprzęcie klasy minimalnej i zalecanej.

| | Minimalne | Zalecane |
|---|---|---|
| System | Windows 10 64-bit | Windows 10 64-bit |
| Procesor | Intel Core i5-6400 / AMD Ryzen 3 1200 | Intel Core i5-9600 / AMD Ryzen 5 3600 |
| Grafika | NVIDIA GTX 660 / AMD RX 460 / Intel HD 630 (2 GB VRAM) | NVIDIA GTX 1660 / AMD RX 590 |
| Pamięć | 8 GB RAM | 12 GB RAM |
| Dysk | ≤ 25 GB | ≤ 25 GB |
| Cel | tier Low, 1080p, 30 fps | tier High, 1080p, 60 fps |

Co wybiera **auto** (przy pierwszym starcie, bez zapisanego wyboru):

| Warunek (po kolei) | Tier |
|---|---|
| renderer programowy albo zintegrowana grafika (np. Intel HD) | Low |
| RAM < 7000 MB | Low |
| VRAM nieznany | Medium |
| VRAM < 3500 MB | Low |
| VRAM < 5500 MB | Medium |
| VRAM ≥ 5500 MB i RAM ≥ 11000 MB | High (przy RAM < 11000 MB → Medium) |
| Ultra | nigdy automatycznie — tylko ręcznie |

Rada dla testera: zacznij od **auto**. Jeśli klatki skaczą albo spadają poniżej celu — o jeden tier niżej.
Ultra tylko na mocnej karcie. Jedyny pomiar: maszyna deweloperska RTX 5070, 1920 × 1080, postój — Low 535 /
Medium 379 / High 334 / Ultra 194 fps (to **nie** jest referencja dla klas D74).

---

## 5. Logi, dane i zrzuty

| Co | Gdzie |
|---|---|
| Log gry (bieżący i poprzedni) | `%USERPROFILE%\AppData\LocalLow\woogitsugames\Kamion\Player.log`, `Player-prev.log` |
| Diagnostyka klatek | ten sam folder, podfolder `diag\` (`frametimes.csv`, `summary.json`; przy `-camlog 1` też `campose.csv`) |
| Ustawienia | ten sam folder: `settings_pc.json`, `input_bindings.json` (że to ten sam folder co log — wg dokumentacji Unity, UNVERIFIED na buildzie) |
| Raporty awarii Unity | `%TMP%\woogitsugames\Kamion\Crashes\` (zwykle `%LOCALAPPDATA%\Temp\…`) |
| Zrzut pamięci Windows (WER) | `%LOCALAPPDATA%\CrashDumps\Kamion.exe.<pid>.dmp` — tylko gdy w Windows włączone lokalne zrzuty (klucz rejestru `LocalDumps`; wg Microsoft domyślnie wyłączone, domyślny folder właśnie ten). U właściciela 16.11 taki plik powstał. |

**Zbieranie logów:** uruchom `Zbierz-logi.cmd` z folderu gry. Powstaje zip na Pulpicie z: `Player.log`,
`Player-prev.log`, `diag\`, 5 najnowszymi zrzutami awarii i `system.txt` (Windows, procesor, RAM, karta graficzna,
monitory, wolne miejsce, suma exe). Nazwa użytkownika i komputera są zamieniane na `<user>` / `<pc>`. Nic nie jest
wysyłane samo. Wolniejsza, pełniejsza wersja: `powershell -NoProfile -ExecutionPolicy Bypass -File collect-logs.ps1 -DxDiag`.
Zrzuty awarii (`*.dmp`) **nie są anonimizowane** (mogą zawierać nazwę użytkownika Windows); bez nich:
`Zbierz-logi.cmd -NoCrashes`.

`Zbierz-logi.cmd` dołącza też zrzuty Windows `%LOCALAPPDATA%\CrashDumps\Kamion*.dmp`: 2 najnowsze, każdy do 1 GB
(większe i starsze tylko wypisuje w `system.txt` — wtedy dołącz plik ręcznie); `-NoCrashes` pomija także je.
Parametry: `-MaxDumps`, `-MaxDumpMB`, `-DumpDir`. Też nieanonimizowane.

---

## 6. Jak zgłosić błąd

W repo nie ma ustalonego kanału zgłoszeń — **zgłoszenie wysyłasz do właściciela** (tak, jak dostałeś grę).

Dołącz:
1. Zip z `Zbierz-logi.cmd` (uruchom **zaraz po** problemie, przed kolejnym startem gry — inaczej log się nadpisze;
   poprzedni zostaje jako `Player-prev.log`).
2. **Region** (nazwa z menu albo argument `-scene`) i mniej więcej **gdzie** (ulica, rondo, km trasy).
3. **Godzinę** zdarzenia (żeby znaleźć miejsce w logu).
4. **Tier** i limit klatek (z menu albo z argumentów), tryb okna, którym launcherem (`Kamion-korytarz.cmd` /
   `-stream 1`?) i czy z `-force-d3d11`.
5. Czym sterowałeś: klawiatura / pad (jaki) / kierownica (jaka).
6. Opis: co robiłeś → co się stało → czego się spodziewałeś. Czy powtarza się?
7. Zrzut ekranu (klawisz Print Screen / Win+Shift+S) albo krótkie nagranie.

Nie dołączaj danych osobowych. Przed wysłaniem możesz otworzyć zip i sprawdzić zawartość.

---

## Rozbieżności z ADR i dokumentami (stan kodu wygrywa)

Przegląd s23 (2026-11-16, gałąź `docs-fixes-s23`): dokumenty, które kłamały, dostały sekcję „Uzupełnienie s23
(zgodność z kodem)”; kodu gry (`game/**`) nie zmieniano.

| # | Rozbieżność | Stan |
|---|---|---|
| 1 | ADR 0261 §6 / „Otwarte”: klawiatura `KeyboardDriverInput`, „mapowanie nie jest konfigurowalne” | **naprawione** w ADR 0261 (uzupełnienie): `PcInputBridge` wstawia `KeyboardBindingsDriverInput` + `GamepadDriverInput`, przypisania do zmiany (ADR 0264) |
| 2 | ADR 0261 nie wymienia Tab (kamera) ani L (lusterka) | **naprawione** w ADR 0261 (uzupełnienie) |
| 3 | ADR 0261 §3: tylko `Kamion-okno.cmd` i `Kamion-knyszyn.cmd` | **naprawione** w ADR 0261 (uzupełnienie: trzy launchery) |
| 4 | `package-windows.py` pakował `Kamion-knyszyn-w.cmd` także bez regionu knyszyn-w w buildzie | **naprawione** w `scripts/package-windows.py` (launcher `-scene` tylko dla sceny/regionu w buildzie), testy `tests/dist`, ADR 0271 i docs/12 (uzupełnienie) |
| 5 | ADR 0270 §4: „auto = High jak ADR 0261” (to samo w ADR 0261 §5) | **naprawione** w ADR 0270 i ADR 0261 (uzupełnienie: dobór sprzętowy ADR 0269, progi, nigdy Ultra) |
| 6 | HANDOVER 16.11 00:0x: „`Kamion-knyszyn.cmd` startuje knyszyn-w” | **zostaje** — to wpis historyczny w dzienniku lidera, poprawiony już wpisem HANDOVER 16.11 04:0x; skrypt startuje `knyszyn` |
| 7 | `dist/windows/README.txt.in`: niepełna lista klawiszy, pad 3 akcje | **naprawione**: pełna lista klawiszy i pada wg `DrivingActionCatalog` + gdzie zmienić przypisania |
| 8 | ADR 0263: FFB bez wyjścia, brak kreatora kalibracji i panelu kierownicy | **naprawione** w ADR 0263 (uzupełnienie opisuje stan: `NullForceFeedbackSink`, brak UI, ustawienia tylko w PlayerPrefs `controls.wheel`); sama funkcja **zostaje do zrobienia** (natywny sink FFB, UI — `game/**`) |
| 9 | Menu startowe: „brak w tym APK” / „Region niedostępny w tym APK” także na PC | **zostaje** — tekst w kodzie gry (`GameBootstrap.cs:232`, `BootMenu.cs:121`), poza zakresem zmian dokumentacji |
| 10 | D70 (270°/900°) a kod: dotykowa 180–900°, USB 270–900° (domyślnie 540°) | **naprawione** w ADR 0263 (uzupełnienie rozdziela oba zakresy); D70 (decyzja właściciela) bez zmian — nie podaje minimum, 180° to wartość z kodu |

Przegląd P19 (16.11 wieczór, gałąź `player-guide-r2`, tylko ta instrukcja):

| # | Rozbieżność | Stan |
|---|---|---|
| 11 | ADR 0261, uzupełnienie s23 §3: „trzy launchery, `build-windows.ps1:94-96`” | **zostaje** w ADR (dopisek ADR 0276 w tym samym pliku mówi już o `Kamion-<region>.cmd`); stan kodu: launchery pisze `postbuild-windows.py` — `Kamion-okno.cmd`, `Kamion-<region>.cmd` dla każdego regionu w buildzie, `Kamion-korytarz.cmd` |
| 12 | `build-windows.ps1` (nagłówek i komentarz przy postbuild): „launchers (windowed)” | **zostaje** — `Kamion-korytarz.cmd` jest pełnoekranowy; tylko komentarz |
| 13 | `collect-logs.ps1` / `Zbierz-logi.cmd` nie zbiera `%LOCALAPPDATA%\CrashDumps` (tam był dump crasha D3D12 16.11) | **poprawione** (build-hygiene-s23): `collect-logs.ps1` zbiera `Kamion*.dmp` (2 najnowsze, ≤ 1 GB), README w zipie o tym mówi |
| 14 | `dist/windows/README.txt.in` (README w zip): brak `Kamion-korytarz.cmd`, `Kamion-<region>.cmd`, `-force-d3d11`, `CrashDumps` | **poprawione** (build-hygiene-s23): README opisuje korytarz, skróty regionów, `Kamion-d3d11.cmd` / `Kamion-korytarz-d3d11.cmd`, CrashDumps |
| 15 | HANDOVER 16.11 15:2x: skróty dla gracza pełny ekran bez ramki, `resizableWindow` + Alt+Enter | **częściowo** — pełny ekran ma tylko `Kamion-korytarz.cmd`; `Kamion-okno.cmd` / `Kamion-<region>.cmd` nadal 1600 × 900, `resizableWindow: 0` |
| 16 | ADR 0261 „Otwarte”: „Dotykowy HUD jest widoczny także na PC” | **nieaktualne** w ADR — kod (ADR 0265) ukrywa go na PC przy „auto”; widoczny tylko przy zapisanym „zawsze” |
| 17 | Wcześniejsza wersja tej instrukcji: „argumentu `-stream` w `origin/main` nie ma” | **naprawione** — streaming scalony 16.11 (`int-stream-s23`), opis w sekcji 1.4 |

## UNVERIFIED (do sprawdzenia przez właściciela/testera)

- Wszystkie przypisania osi i przycisków kierownic w `wheel_profiles.json` (żaden profil nie sprawdzony na sprzęcie).
- Wpływ pedału sprzęgła na jazdę.
- Który przycisk myszy obraca widok (przeciąganie) i jak dokładnie otworzyć pełną mapę z minimapy.
- Że `settings_pc.json`, `input_bindings.json` i `diag\` leżą w tym samym folderze co `Player.log` (wynika z
  dokumentacji Unity i ze skryptu `collect-logs.ps1`, nie z pomiaru).
- Działanie pada w playerze (ADR 0261: „Pad: UNVERIFIED”).
- `collect-logs.ps1` nie był uruchomiony na Windows (ADR 0271 „Nieuruchomione”).
- Alt+Enter na buildzie (`allowFullscreenSwitch: 1`) i czy zmiana trybu skrótem zapisuje się w `settings_pc.json`.
- Domyślne API grafiki Unity na Windows dla tego projektu (brak listy w ProjectSettings) i czy `-force-d3d11` usuwa
  crash `887a0001` (jedna obserwacja).
- Przejazd przez szwy knyszyn ↔ knyszyn-w i knyszyn-w ↔ dw671-tykocin-01 (brak portalu trasy; nikt nie jechał);
  zmierzony tylko odcinek knyszynska → dk65-03.
- Które regiony mają sceny `_Tile` w danym buildzie (zależy od lokalnego importu, poza gitem).
- Czy na komputerach testerów powstają zrzuty w `%LOCALAPPDATA%\CrashDumps` (WER `LocalDumps` domyślnie wyłączone).

<!-- źródła (ścieżka:linia | fragment, który musi być w tej linii; origin/main):
scripts/build-windows.ps1:87 | $name = "kamion-$version-$sha
scripts/build-windows.ps1:134 | $exePath.sha256
game/ProjectSettings/ProjectSettings.asset:15 | companyName: woogitsugames
game/ProjectSettings/ProjectSettings.asset:16 | productName: Kamion
game/ProjectSettings/ProjectSettings.asset:114 | fullscreenMode: 1
scripts/package-windows.py:9 | -win64.zip
scripts/package-windows.py:520 | artifacts/dist
scripts/package-windows.py:75 | "build.json", "Kamion.exe.sha256"
scripts/package-windows.py:71 | *_DoNotShip
scripts/package-windows.py:73 | *.pdb
scripts/package-windows.py:507 | Zbierz-logi.cmd
dist/windows/README.txt.in:9 | Rozpakuj cały folder
dist/windows/README.txt.in:11 | SmartScreen
dist/windows/README.txt.in:13 | Uruchom mimo to
game/Assets/_Project/Platform/PlatformServices.cs:35 | string flag = "-" + key;
game/Assets/_Project/Platform/PlatformServices.cs:36 | args.Length - 1
game/Assets/_Project/Gameplay/GameBootstrap.cs:178 | GetLaunchArgument("scene")
game/Assets/_Project/Gameplay/GameBootstrap.cs:179 | LaunchSceneFor(scene)
game/Assets/_Project/Gameplay/GameBootstrap.cs:217 | RegionScenes.UsesHighContent(QualityTiers.Current)
game/Assets/_Project/Gameplay/RegionCatalog.cs:113 | a.alias
game/Assets/_Project/Gameplay/RegionCatalog.cs:114 | CityPrefix + t
game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json:155 | "alias": "c"
game/Assets/_Project/Gameplay/GameBootstrap.cs:65 | GetLaunchArgument("tier")
game/Assets/_Project/Gameplay/GameBootstrap.cs:68 | QualityTiers.SavedTier
game/Assets/_Project/Gameplay/GameBootstrap.cs:74 | PcGraphicsTiers.DefaultFor(hw, out string why)
game/Assets/_Project/Rendering/Runtime/QualityTiers.cs:36 | StringComparison.OrdinalIgnoreCase
game/Assets/_Project/Rendering/Runtime/QualityTiers.cs:13 | "Low", "Medium", "High", "Ultra"
game/Assets/_Project/Gameplay/GameBootstrap.cs:105 | GetLaunchArgument("fps")
game/Assets/_Project/Gameplay/GameBootstrap.cs:39 | DesktopTargetFps = 60
game/Assets/_Project/Gameplay/GameBootstrap.cs:108 | QualityTiers.SavedFrameRate
game/Assets/_Project/UI/Settings/PcSettingsRuntime.cs:59 | !fpsFromArgument
game/Assets/_Project/UI/Settings/PcSettingsRuntime.cs:61 | !tierFromArgument
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:379 | GetLaunchArgument("route_s")
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:380 | GetLaunchArgument("route_end")
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:408 | [START] start moved along the route
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:209 | GetLaunchArgument("trailer")
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:296 | case "solo"
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:297 | case "pusta"
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:298 | case "24t"
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:299 | case "40t"
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:38 | DefaultSpawn = LabSpawn.Cargo24t
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:216 | m_Spawn = LabSpawn.Empty
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:248 | GetLaunchArgument("lighting")
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:246 | clear | overcast | lowsun | dusk
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:249 | lighting = menuLighting
game/Assets/_Project/Core/Settings/DisplayModes.cs:153 | StartsWith("-screen-"
game/Assets/_Project/UI/Settings/PcSettingsRuntime.cs:57 | StartupDisplayPolicy.ShouldApply
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:208 | GetLaunchArgument("autopilot")
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:72 | StraightRunMode = "straight080"
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:564 | mode == "circle25"
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:185 | AUTOPILOT (pomiar)
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:228 | GetLaunchArgument("speed")
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:360 | s > 0 ? s : 50f
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:525 | s > 0 ? s : 80f
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:568 | (r25 ? 25f : 40f)
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:212 | LabSpawn.Gross40t
game/Assets/_Project/Gameplay/DesktopAutoShot.cs:29 | arg("shot")
game/Assets/_Project/Gameplay/DesktopAutoShot.cs:30 | arg("quit_t")
game/Assets/_Project/Gameplay/DesktopAutoShot.cs:36 | arg("shot_t"), 20f
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:258 | GetLaunchArgument("telemetry") == "1"
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:179 | GetLaunchArgument("devhud") == "1"
game/Assets/_Project/Gameplay/GameBootstrap.cs:93 | GetLaunchArgument("camlog") == "1"
game/Assets/_Project/Rendering/Runtime/PcGraphicsTiers.cs:42 | "-pc_tiers"
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:167 | GetLaunchArgument("engine_audio")
game/Assets/_Project/Gameplay/PcInputBridge.cs:60 | new GamepadDriverInput(Actions.Gamepad
game/Assets/_Project/Gameplay/PcInputBridge.cs:61 | new KeyboardBindingsDriverInput(Actions.Keyboard
game/Assets/_Project/Gameplay/PcInputBridge.cs:65 | Bootstrap.Keyboard.Enabled = false
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:131 | m_Mixer.Add(PcWheel.Input)
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:772 | m_Mixer.MenuOpen
game/Assets/_Project/Input/DrivingActionCatalog.cs:68 | "<Keyboard>/w", "<Keyboard>/upArrow"
game/Assets/_Project/Input/DrivingActionCatalog.cs:68 | <Gamepad>/rightTrigger
game/Assets/_Project/Input/DrivingActionCatalog.cs:69 | "<Keyboard>/s", "<Keyboard>/downArrow"
game/Assets/_Project/Input/DrivingActionCatalog.cs:69 | <Gamepad>/leftTrigger
game/Assets/_Project/Input/DrivingActionCatalog.cs:50 | "<Keyboard>/a", "<Keyboard>/d"
game/Assets/_Project/Input/DrivingActionCatalog.cs:51 | "<Keyboard>/leftArrow", "<Keyboard>/rightArrow"
game/Assets/_Project/Input/DrivingActionCatalog.cs:67 | <Gamepad>/leftStick/x
game/Assets/_Project/Input/DrivingActionCatalog.cs:77 | <Keyboard>/space
game/Assets/_Project/Input/DrivingActionCatalog.cs:77 | <Gamepad>/buttonSouth
game/Assets/_Project/Input/DrivingActionCatalog.cs:73 | <Keyboard>/1
game/Assets/_Project/Input/DrivingActionCatalog.cs:73 | <Gamepad>/buttonWest
game/Assets/_Project/Input/DrivingActionCatalog.cs:74 | <Keyboard>/2
game/Assets/_Project/Input/DrivingActionCatalog.cs:74 | <Gamepad>/buttonEast
game/Assets/_Project/Input/DrivingActionCatalog.cs:75 | <Keyboard>/3
game/Assets/_Project/Input/DrivingActionCatalog.cs:75 | <Gamepad>/select
game/Assets/_Project/Input/DrivingActionCatalog.cs:71 | <Keyboard>/e
game/Assets/_Project/Input/DrivingActionCatalog.cs:71 | <Gamepad>/rightShoulder
game/Assets/_Project/Input/DrivingActionCatalog.cs:72 | <Keyboard>/q
game/Assets/_Project/Input/DrivingActionCatalog.cs:72 | <Gamepad>/leftShoulder
game/Assets/_Project/Input/DrivingActionCatalog.cs:76 | <Keyboard>/m
game/Assets/_Project/Input/DrivingActionCatalog.cs:78 | <Keyboard>/x
game/Assets/_Project/Input/DrivingActionCatalog.cs:78 | <Gamepad>/dpad/down
game/Assets/_Project/Input/DrivingActionCatalog.cs:79 | <Keyboard>/z
game/Assets/_Project/Input/DrivingActionCatalog.cs:79 | <Gamepad>/leftStickPress
game/Assets/_Project/Input/DrivingActionCatalog.cs:87 | <Keyboard>/b
game/Assets/_Project/Input/DrivingActionCatalog.cs:80 | <Keyboard>/comma
game/Assets/_Project/Input/DrivingActionCatalog.cs:80 | <Gamepad>/dpad/left
game/Assets/_Project/Input/DrivingActionCatalog.cs:81 | <Keyboard>/period
game/Assets/_Project/Input/DrivingActionCatalog.cs:81 | <Gamepad>/dpad/right
game/Assets/_Project/Input/DrivingActionCatalog.cs:82 | <Keyboard>/h
game/Assets/_Project/Input/DrivingActionCatalog.cs:82 | <Gamepad>/dpad/up
game/Assets/_Project/Input/DrivingActionCatalog.cs:83 | <Keyboard>/k
game/Assets/_Project/Input/DrivingActionCatalog.cs:83 | <Gamepad>/rightStickPress
game/Assets/_Project/Input/DrivingActionCatalog.cs:88 | <Keyboard>/t
game/Assets/_Project/Input/DrivingActionCatalog.cs:89 | <Keyboard>/g
game/Assets/_Project/Input/DrivingActionCatalog.cs:84 | "<Keyboard>/c", "<Keyboard>/tab"
game/Assets/_Project/Input/DrivingActionCatalog.cs:84 | <Gamepad>/buttonNorth
game/Assets/_Project/Input/DrivingActionCatalog.cs:90 | <Gamepad>/rightStick
game/Assets/_Project/Input/DrivingActionCatalog.cs:85 | <Keyboard>/l
game/Assets/_Project/Input/DrivingActionCatalog.cs:86 | <Keyboard>/v
game/Assets/_Project/Input/DrivingActionCatalog.cs:157 | if (d.Visible) Binding(sb, ref first, prefix + index, "", ""
game/Assets/_Project/Camera/CameraRig.cs:5 | Cab = 0, Chase = 1, Orbit = 2
game/Assets/_Project/Gameplay/PcInputBridge.cs:79 | m_Rig.NextMode()
game/Assets/_Project/Input/GamepadDriverInput.cs:64 | a.Look.ReadValue<Vector2>()
game/Assets/_Project/UI/Driving/DrivingHud.cs:216 | AddLookDelta
game/Assets/_Project/UI/Driving/DrivingHud.cs:217 | AddZoom
game/Assets/_Project/UI/Driving/TouchWidgets.cs:165 | drag = look around / orbit, scroll = zoom
game/Assets/_Project/Gameplay/NavigationInstaller.cs:36 | mini.OnOpenMap = full.Open
game/Assets/_Project/UI/Navigation/FullMapView.cs:697 | e.scrollDelta.y
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:821 | m_Selector == GearSelector.Reverse
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:785 | kb.escapeKey.wasPressedThisFrame
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:785 | pad.startButton.wasPressedThisFrame
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:787 | FullMapView.HandleBack()
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:788 | ReturnToMenu()
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:793 | kb.kKey.isPressed
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:792 | kb.cKey.wasPressedThisFrame
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:184 | OpenMenu = ReturnToMenu
game/Assets/_Project/UI/Layout/UiFocus.cs:14 | arrows / Enter / Esc, pad stick / d-pad / A / B
game/Assets/_Project/UI/Layout/UiFocus.cs:186 | k.tabKey.wasPressedThisFrame
game/Assets/_Project/UI/Layout/UiFocus.cs:58 | HUD button: pointer only
game/Assets/_Project/UI/Settings/PcSettingsPanel.cs:156 | escapeKey.wasPressedThisFrame
game/Assets/_Project/UI/Settings/PcSettingsPanel.cs:157 | Gamepad.current.buttonEast.wasPressedThisFrame
game/Assets/_Project/UI/AboutPanel.cs:136 | g.rightStick.ReadValue().y
game/Assets/_Project/UI/AboutPanel.cs:140 | k.upArrowKey.isPressed
game/Assets/_Project/UI/AboutPanel.cs:141 | k.pageUpKey.isPressed
game/Assets/_Project/UI/ControlSettingsPanel.cs:181 | KLAWIATURA I PAD
game/Assets/_Project/UI/ControlSettingsPanel.cs:182 | Przypisania i czułość…
game/Assets/_Project/UI/BootMenu.cs:282 | Ustawienia sterowania
game/Assets/_Project/Gameplay/PcInputBridge.cs:67 | ControlSettingsPanel.OpenInputBindings = OpenBindings
game/Assets/_Project/UI/InputBindingsPanel.cs:190 | "Klawiatura"
game/Assets/_Project/UI/InputBindingsPanel.cs:192 | "Pad"
game/Assets/_Project/Input/DrivingActions.cs:165 | WithControlsExcluding("<Keyboard>/escape")
game/Assets/_Project/Input/DrivingActions.cs:166 | "<Gamepad>/start" : "<Keyboard>/backspace"
game/Assets/_Project/Input/DrivingActions.cs:167 | WithTimeout(10f)
game/Assets/_Project/Input/DrivingActions.cs:149 | return a.name
game/Assets/_Project/UI/InputBindingsPanel.cs:210 | Przywróć domyślne
game/Assets/_Project/UI/InputBindingsPanel.cs:152 | Martwa strefa gałki
game/Assets/_Project/UI/InputBindingsPanel.cs:154 | Krzywa gałki (1 = liniowa)
game/Assets/_Project/UI/InputBindingsPanel.cs:156 | Skręt przy prędkości
game/Assets/_Project/UI/InputBindingsPanel.cs:162 | Szybkość skrętu
game/Assets/_Project/Input/InputBindingsStore.cs:53 | input_bindings.json
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:28 | "id": "lg-g29"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:57 | "id": "lg-g920"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:80 | "id": "lg-g923"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:103 | "id": "tm-t300"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:126 | "id": "tm-t150"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:149 | "id": "ft-csl"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:30 | UNVERIFIED-MAPPING
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:35 | "defaultRangeDeg": 540
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:36 | "control": "stick/x"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:37 | "throttle": { "control": "stick/y"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:38 | "brake":    { "control": "rz"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:39 | "clutch":   { "control": "slider"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:42 | "button13", "button14", "button15", "button16", "button17", "button18"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:43 | "shifterReverse": "button19"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:45 | "paddleUp": "button5"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:46 | "paddleDown": "button6"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:48 | "RangeToggle", "control": "button7"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:49 | "ParkingBrake", "control": "button1"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:50 | "RetarderMore", "control": "button2"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:51 | "RetarderLess", "control": "button3"
game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json:52 | "Hazard", "control": "button4"
game/Assets/_Project/Input/HidWheelDriverInput.cs:121 | intent.ShiftDelta += 1
game/Assets/_Project/Input/HidWheelDriverInput.cs:122 | intent.ShiftDelta -= 1
game/Assets/_Project/Input/HidWheelDriverInput.cs:105 | intent.DirectSteer = true
game/Assets/_Project/Input/HidWheelDriverInput.cs:98 | first reading = centre
game/Assets/_Project/Input/HidWheelDriverInput.cs:118 | intent.Clutch = Pedal(m_Clutch
game/Assets/_Project/Input/WheelSteeringMap.cs:22 | RangeMinDeg = 270f, RangeMaxDeg = 900f
game/Assets/_Project/Input/WheelSettings.cs:14 | PrefKey = "controls.wheel"
game/Assets/_Project/Input/PcWheel.cs:15 | NullForceFeedbackSink.Instance
game/Assets/_Project/Input/ForceFeedback.cs:24 | public bool Available => false;
game/Assets/_Project/Input/HShifterMapper.cs:22 | GatesPerRange = 6
game/Assets/_Project/Input/HShifterMapper.cs:26 | NeutralHoldS = 0.6f
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:806 | if (intent.ShiftDelta > 0) input.ShiftUp = true;
game/Assets/_Project/Input/ControlSettings.cs:43 | public float wheelRangeDeg = TouchHalfRangeComfortDeg;
game/Assets/_Project/Input/ControlSettings.cs:29 | TouchHalfRangeComfortDeg = 270f
game/Assets/_Project/Input/ControlSettings.cs:23 | RangeMin = 180f, RangeMax = 900f
game/Assets/_Project/UI/ControlSettingsPanel.cs:190 | Step(Settings.wheelRangeDeg, d, 90f
game/Assets/_Project/UI/BootMenu.cs:290 | PcSettingsTexts.MenuButton
game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:10 | Ekran, grafika, dźwięk
game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:38 | Zastosuj
game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:40 | Zachować nowy tryb ekranu?
game/Assets/_Project/Core/Settings/DisplayModes.cs:105 | DefaultSeconds = 15f
game/Assets/_Project/UI/Settings/PcSettingsPanel.cs:243 | T.Resolution
game/Assets/_Project/Core/Settings/PcSettingsData.cs:64 | UsesNativeResolution => width <= 0
game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:20 | "okno", "bez ramki", "pełny ekran"
game/Assets/_Project/Core/Settings/PcSettingsData.cs:61 | mode = WindowModes.Borderless
game/Assets/_Project/Core/Settings/PcSettingsData.cs:108 | public bool vsync;
game/Assets/_Project/Core/Settings/PcSettingsData.cs:192 | the menu greys it out
game/Assets/_Project/Core/Settings/PcSettingsData.cs:99 | FpsCaps = { 30, 60, 75, 120, 144, 0 }
game/Assets/_Project/Core/Settings/PcSettingsData.cs:100 | DefaultFpsCap = 60
game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:27 | "auto", "niska", "średnia", "wysoka", "ultra"
game/Assets/_Project/Core/Settings/PcSettingsData.cs:110 | graphicsTier = TierChoices.Auto
game/Assets/_Project/UI/Settings/PcSettingsPanel.cs:366 | T.TierLabels[0] + " ("
game/Assets/_Project/Core/Settings/PcSettingsData.cs:103 | HudScaleMin = 0.8f, HudScaleMax = 1.4f, HudScaleStep = 0.1f
game/Assets/_Project/Core/Settings/PcSettingsData.cs:111 | hudScale = 1f
game/Assets/_Project/UI/Settings/PcSettingsPanel.cs:262 | T.UnitsMetric
game/Assets/_Project/Core/Settings/PcSettingsData.cs:104 | VolumeStep = 0.05f
game/Assets/_Project/Core/Settings/PcSettingsData.cs:78 | master = 1f
game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:31 | Głośność ogólna
game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:34 | Sygnały kabiny
game/Assets/_Project/Core/Settings/PcSettingsStore.cs:132 | settings_pc.json
game/Assets/_Project/UI/BootMenu.cs:270 | Pora dnia (trasy)
game/Assets/_Project/UI/StartMenuOptions.cs:18 | "Pochmurno", "Niskie słońce", "Zmierzch"
game/Assets/_Project/UI/BootMenu.cs:272 | Jakość grafiki
game/Assets/_Project/UI/BootMenu.cs:276 | Limit klatek
game/Assets/_Project/Rendering/Runtime/QualityTiers.cs:14 | SupportedFrameRates = { 30, 60 }
game/Assets/_Project/UI/StartMenuOptions.cs:43 | persist: true
game/Assets/_Project/UI/ControlSettingsPanel.cs:283 | Zmiany działają od razu i zapisują się same.
game/Assets/_Project/UI/ControlSettingsPanel.cs:227 | Czułość rozglądania
game/Assets/_Project/UI/ControlSettingsPanel.cs:228 | Pole widzenia
game/Assets/_Project/Input/ControlSettings.cs:36 | FovMin = 45f, FovMax = 75f
game/Assets/_Project/UI/ControlSettingsPanel.cs:231 | Ruch głowy
game/Assets/_Project/UI/ControlSettingsPanel.cs:236 | "synteza", "ElevenLabs"
docs/11_DECYZJE_WLASCICIELA.md:125 | Intel Core i5-6400 / AMD Ryzen 3 1200, NVIDIA GTX 660 / AMD RX 460 / Intel HD 630 (2 GB VRAM), 8 GB RAM
docs/11_DECYZJE_WLASCICIELA.md:125 | Cel: tier Low, 1080p, **30 fps**
docs/11_DECYZJE_WLASCICIELA.md:126 | Intel Core i5-9600 / AMD Ryzen 5 3600, NVIDIA GTX 1660 / AMD RX 590, 12 GB RAM
docs/11_DECYZJE_WLASCICIELA.md:126 | Cel: tier High, 1080p, **60 fps**
docs/11_DECYZJE_WLASCICIELA.md:127 | ≤ 25 GB
docs/11_DECYZJE_WLASCICIELA.md:124 | Windows 10 64-bit
game/Assets/_Project/Rendering/Runtime/PcTierTable.cs:156 | IsSoftware(hw.gpuName)
game/Assets/_Project/Rendering/Runtime/PcTierTable.cs:157 | IsIntegrated(hw.gpuName)
game/Assets/_Project/Rendering/Runtime/PcTierTable.cs:121 | LowBelowRamMb = 7000
game/Assets/_Project/Rendering/Runtime/PcTierTable.cs:123 | UnknownVramTier = PcTier.Medium
game/Assets/_Project/Rendering/Runtime/PcTierTable.cs:115 | LowBelowVramMb = 3500
game/Assets/_Project/Rendering/Runtime/PcTierTable.cs:117 | MediumBelowVramMb = 5500
game/Assets/_Project/Rendering/Runtime/PcTierTable.cs:119 | HighMinRamMb = 11000
game/Assets/_Project/Rendering/Runtime/PcTierTable.cs:125 | AutoCeiling = PcTier.High
HANDOVER.md:243 | Low 535 / Medium 379 / High 334 / Ultra 194 fps
scripts/collect-logs.ps1:42 | AppData\LocalLow\$Company\$Product
scripts/collect-logs.ps1:25 | $Company = 'woogitsugames'
scripts/collect-logs.ps1:26 | $Product = 'Kamion'
scripts/collect-logs.ps1:59 | 'Player.log', 'Player-prev.log'
scripts/collect-logs.ps1:60 | 'diag'
scripts/collect-logs.ps1:43 | $Company\$Product\Crashes
scripts/collect-logs.ps1:28 | $MaxCrashes = 5
scripts/collect-logs.ps1:12 | system.txt
scripts/collect-logs.ps1:14 | <user> / <pc>
scripts/collect-logs.ps1:15 | nothing is uploaded anywhere
scripts/collect-logs.ps1:30 | [switch]$DxDiag
scripts/collect-logs.ps1:37 | GetFolderPath('Desktop')
game/Assets/_Project/Telemetry/DiagnosticsSampler.cs:185 | Path.Combine(Application.persistentDataPath, "diag")
game/Assets/_Project/Telemetry/DiagnosticsSampler.cs:187 | frametimes.csv
game/Assets/_Project/Telemetry/DiagnosticsSampler.cs:189 | summary.json
game/Assets/_Project/Gameplay/GameBootstrap.cs:97 | campose.csv
docs/adr/0261-build-windows.md:99 | nie jest konfigurowalne
docs/adr/0261-build-windows.md:22 | Kamion-okno.cmd` i `Kamion-knyszyn.cmd`
docs/adr/0271-dystrybucja-pc.md:16 | deweloperski `Kamion-knyszyn.cmd`
docs/adr/0270-menu-ustawien-pc.md:27 | auto = High jak ADR 0261
docs/adr/0261-build-windows.md:72 | Pad: UNVERIFIED
HANDOVER.md:236 | `Kamion-knyszyn.cmd` startuje knyszyn-w
game/Assets/_Project/UI/BootMenu.cs:121 | Region niedostępny w tym APK
game/Assets/_Project/Gameplay/GameBootstrap.cs:232 | brak w tym APK
scripts/postbuild-windows.py:47 | WINDOW_ARGS = "-screen-fullscreen 0 -screen-width 1600 -screen-height 900"
scripts/postbuild-windows.py:48 | WINDOW_LAUNCHER = "Kamion-okno.cmd"
scripts/postbuild-windows.py:166 | return f"Kamion-{region_id}.cmd"
scripts/postbuild-windows.py:178 | launcher_text(f"-scene {rid}")
scripts/postbuild-windows.py:162 | {WINDOW_ARGS}{tail} %*
scripts/postbuild-windows.py:26 | the build (read from the "[BUILD] Windows x64 -> ... scenes=[...]" line of the build log
scripts/postbuild-windows.py:52 | CORRIDOR_LAUNCHER = "Kamion-korytarz.cmd"
scripts/postbuild-windows.py:53 | CORRIDOR_NEEDS = ("knyszyn", "knyszyn-s")
scripts/postbuild-windows.py:180 | if all(r in regions for r in CORRIDOR_NEEDS):
scripts/postbuild-windows.py:54 | -screen-fullscreen 1 -window-mode borderless -scene knyszyn -stream 1 %*
scripts/postbuild-windows.py:44 | BUILD_ID = "build-id.json"
scripts/postbuild-windows.py:21 | "<ver> (<sha>) · dane <contentHash>" in the menu, the "Informacje" screen
scripts/build-windows.ps1:137 | $RepoRoot/scripts/postbuild-windows.py
scripts/build-windows.ps1:13 | launchers (windowed; the project default is fullscreen)
scripts/build-windows.ps1:136 | # (Kamion-okno.cmd + Kamion-<region>.cmd; ProjectSettings default is fullscreen, not changed here, ADR 0261).
scripts/package-windows.py:78 | (int-h3-s23: no developer-only exception any more; Kamion-knyszyn.cmd starts the knyszyn region for testers)
scripts/package-windows.py:266 | is in the build; Kamion-okno.cmd and other launchers without -scene always ship.
scripts/package-windows.py:79 | LAUNCHER_SCENE_RE = re.compile(
scripts/package-windows.py:509 | Bez zrzutow: Zbierz-logi.cmd -NoCrashes
game/Assets/_Project/Gameplay/GameBootstrap.cs:172 | Both are one-shot per process (int-h3-s23
game/Assets/_Project/Gameplay/GameBootstrap.cs:182 | [BOOT] launch argument scene already used this run: staying in the menu
game/Assets/_Project/UI/BootMenu.cs:184 | REGION — START NA POCZĄTKU TRASY
game/Assets/_Project/UI/BootMenu.cs:121 | RegionStartLabel = "Jedź w wybranym regionie"
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:241 | platform.GetLaunchArgument("stream")
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:221 | public static bool IsRequested(string streamArgument) => EnabledOverride ?? streamArgument == "1";
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:206 | if (!IsRequested(streamArgument)) return null;
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:157 | [STREAM] off: region {start.regionId} not in the tile graph
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:169 | [STREAM] off: no neighbour tile scene of
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:180 | Debug.Log($"[STREAM] on: start {start.regionId}
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:208 | EndsWith("_High", System.StringComparison.Ordinal) ? RegionScenes.HighTier : RegionScenes.LowTier
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:209 | StreamingSettings.BudgetForTier(Game.Rendering.QualityTiers.Current, !Application.isMobilePlatform);
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:481 | Not in this APK: stay Unloaded; the seam stays closed
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:26 | then the tile is Ready and the seam with each Ready neighbour opens
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:81 | public float routeJoinM = 3f;
game/Assets/_Project/World/Runtime/Streaming/TileSceneSource.cs:48 | public bool IsAvailable(string region, string tier) => m_InBuild(RegionScenes.TileScenePathFor(region, tier));
game/Assets/_Project/World/Runtime/RegionScenes.cs:26 | "World_dk65-04_Tile", "WorldC_Tile", "World_knyszyn_High_Tile"
game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs:40 | public float maxSpeedMs = 25f;
game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs:42 | public float loadTimeS = 8f;
game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs:44 | public float activationTimeS = 1f;
game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs:46 | public float cookTimeS = 1f;
game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs:48 | public float marginM = 150f;
game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs:55 | public int maxTiles = 4;
game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs:71 | BaseLoadRadiusM => maxSpeedMs * (loadTimeS + activationTimeS + cookTimeS) + marginM
game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs:99 | case "Low": return 640f;
game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs:100 | case "Medium": return 800f;
game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs:101 | case "High": return 1450f;
game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs:102 | case "Ultra": return 2000f;
game/Assets/_Project/Editor/Build/RegionBuildList.cs:121 | ADR 0235: the streamed tile scene goes with its region when it was imported (older imports: none).
game/Assets/_Project/World/Import/WorldSceneBuilder.cs:222 | [IMPORT] tile scene {tilePath}
game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/tile_graph.json:782 | "id": "bialystok-industrial-c..knyszyn",
game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/tile_graph.json:804 | "id": "knyszyn-w..dk65-monki-01",
game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json:161 | "name": "d67",
game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json:183 | "name": "d67-full"
tools/worldgen/streaming/tile_graph.py:14 | A portal is a route exit of tile A that is the route entry of tile B on their shared edge
Data/Regions/knyszyn/route_endpoints.json:3 | -> roundabout DK65/DW671 -> DW671 Tykocka -> Rynek.
Data/Regions/knyszyn-w/route_endpoints.json:3 | DK65 Obozowa north-westbound from the east tile edge (seam with knyszyn
Data/Regions/dk65-monki-01/route_endpoints.json:3 | next lattice tile (-10,9) not built
Data/Regions/dw671-tykocin-01/route_endpoints.json:3 | from the north tile edge (seam with knyszyn-w
Data/Regions/dw671-tykocin-01/route_endpoints.json:3 | next lattice tile (-9,6) not built
game/Assets/_Project/Gameplay/WorldSafetyNet.cs:35 | Koniec mapy za ok. 250 m: droga zamknięta, zwolnij
HANDOVER.md:272 | 18 pierścienia: dk65-monki-02..07, monki, monki-e, dw671-tykocin-02..09, tykocin
HANDOVER.md:311 | **int-stream-s23: GATE PASS** (run2: knyszynska→dk65-01→02→03, 4 kafle, 0 zamkniętych szwów
HANDOVER.md:312 | **SCALONE int-stream-s23** (`b2fb6303c`)
game/ProjectSettings/ProjectSettings.asset:87 | defaultIsNativeResolution: 1
game/ProjectSettings/ProjectSettings.asset:102 | resizableWindow: 0
game/ProjectSettings/ProjectSettings.asset:113 | allowFullscreenSwitch: 1
game/ProjectSettings/ProjectSettings.asset:538 | m_BuildTargetGraphicsAPIs:
game/ProjectSettings/ProjectSettings.asset:539 | m_BuildTarget: iOSSupport
game/ProjectSettings/ProjectSettings.asset:542 | m_BuildTarget: AndroidPlayer
game/Assets/_Project/Core/Settings/DisplayModes.cs:153 | a == "-window-mode" || a == "-popupwindow"
HANDOVER.md:299 | Właściciel: okno gry nie da się powiększyć
HANDOVER.md:300 | `d3d12: Device failed error (887a0001)`
HANDOVER.md:300 | Doraźnie: lider uruchomił z `-force-d3d11`
HANDOVER.md:300 | `%LOCALAPPDATA%\CrashDumps\Kamion.exe.73136.dmp`
game/Assets/_Project/Input/Display/TouchControlsPolicy.cs:10 | Auto = 0,
game/Assets/_Project/Input/Display/TouchControlsPolicy.cs:35 | default: return handheldBuild || (touchscreenPresent && touchSeen);
game/Assets/_Project/Input/Display/TouchControlsPolicy.cs:33 | case TouchControlsMode.Always: return true;
game/Assets/_Project/Input/Display/TouchControlsPolicy.cs:34 | case TouchControlsMode.Never: return false;
game/Assets/_Project/Input/Display/TouchControlsPolicy.cs:76 | "zawsze" : m == TouchControlsMode.Never ? "nigdy" : "auto"
game/Assets/_Project/Input/Display/TouchControlsPolicy.cs:86 | PrefTouchControls = "ui.touchControls"
game/Assets/_Project/Input/Display/TouchControlsPolicy.cs:102 | PlayerPrefs.GetInt(PrefTouchControls, 0)
game/Assets/_Project/Input/Display/TouchControlsPolicy.cs:118 | PlayerPrefs.SetInt(PrefTouchControls, (int)v);
game/Assets/_Project/UI/Layout/UiViewport.cs:109 | bool desktop = m_DesktopOverride ?? !TouchControlsPolicy.Current;
game/Assets/_Project/UI/ControlSettingsPanel.cs:201 | "KONTROLKI DOTYKOWE I EKRAN"
game/Assets/_Project/UI/ControlSettingsPanel.cs:202 | Segment3(content, left, ref y, "Pokazuj"
game/Assets/_Project/UI/ControlSettingsPanel.cs:204 | "Skala HUD (monitor)"
game/Assets/_Project/UI/ControlSettingsPanel.cs:186 | "KIEROWNICA DOTYKOWA"
game/Assets/_Project/UI/ControlSettingsPanel.cs:214 | "GYRO (PRZECHYŁ TELEFONU)"
HANDOVER.md:302 | kontrolki dotykowe na PC = zapisane ustawienie właściciela `ui.touchControls=1` (nie bug)
scripts/collect-logs.ps1:43 | $crashDir = Join-Path $env:TEMP "$Company\$Product\Crashes"
scripts/collect-logs.ps1:29 | [switch]$NoCrashes,
scripts/collect-logs.ps1:15 | Crash dumps (*.dmp) are binary and are NOT
docs/adr/0261-build-windows.md:107 | `Kamion-knyszyn-w.cmd` (`-scene knyszyn-w`) — `scripts/build-windows.ps1:94-96`
docs/adr/0261-build-windows.md:88 | skróty `Kamion-<region>.cmd` powstają dla każdego regionu w buildzie
docs/adr/0261-build-windows.md:98 | Dotykowy HUD (kierownica, pedały ekranowe) jest widoczny także na PC
dist/windows/README.txt.in:10 | Kamion.exe (pełny ekran) albo Kamion-okno.cmd (okno 1600 x 900)
dist/windows/README.txt.in:43 | Raporty awarii: %TMP%\woogitsugames\Kamion\Crashes
-->

<!-- dokumentacja zewnętrzna (sprawdzona 16.11.2026):
Unity 6000.0, Player command line arguments (-force-d3d11, -force-d3d12, -screen-fullscreen, -window-mode exclusive|borderless, -popupwindow, -logFile):
  https://docs.unity.com/en-us/engine/6000.0/manual/unity-editor/command-line-arguments/player
Unity 6000.0, PlayerSettings.allowFullscreenSwitch: "Enable to allow users to switch between full-screen and windowed mode using OS-specific keyboard shortcuts."
  https://docs.unity.com/en-us/engine/6000.0/script-reference/unityeditor/playersettings/allowfullscreenswitch
Microsoft Learn, Collecting User-Mode Dumps (WER LocalDumps): "This feature is not enabled by default."; DumpFolder default %LOCALAPPDATA%\CrashDumps
  https://learn.microsoft.com/en-us/windows/win32/wer/collecting-user-mode-dumps
-->
