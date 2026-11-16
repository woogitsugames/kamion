# 12 — Dystrybucja PC (Windows x64)

Decyzja: ADR 0271. Kontekst: D73 (Windows platformą główną), D74 (wymagania jak ETS2/ATS), ADR 0261 (build Windows).
Budżet zakupów 0 zł (CLAUDE.md). Wszystkie odczyty stron zewnętrznych: **dostęp 2026-11-15**. Kwota bez linku = nie ma
jej w tym dokumencie; czego nie dało się potwierdzić u źródła — `UNVERIFIED`.

## 0. Skrót (co zrobić, w kolejności)
1. **Najpierw zamknąć blokery licencyjne** (§5): R-P0-2 (oferta bazy pochodnej OSM, ODbL §4.6) — decyzja właściciela.
   Dopóki jest otwarty, paczka = tylko testerzy zamknięci (`package-windows.py` bez `--release`).
2. Build: `pwsh scripts/build-windows.ps1 -Slot -Regions '<lista>'` (z czystego commitu, bez `-Development`).
3. Paczka: `uv run --no-project python scripts/package-windows.py artifacts/win/kamion-<ver>-<sha>-regions`
   → `artifacts/dist/kamion-<ver>-<sha>[-regions]-<dane>-win64.zip` + `.sha256` + `.json` (lista plików); `<dane>` = 12 hex
   skrótu zawartości `Kamion_Data` (ADR 0276). Albo jednym poleceniem: `build-windows.ps1 … -Package`.
4. Pierwszy kanał: **itch.io** (0 zł z góry, udział platformy wybierany przez twórcę, strona może być ukryta/z kluczami).
5. Steam później (100 USD za aplikację, 21 dni od opłaty, strona „coming soon” ≥ 2 tygodnie, weryfikacja tożsamości i podatków).
6. Bez podpisu kodu na start (SmartScreen ostrzeże — opisane w README paczki); podpis dopiero przy decyzji o kosztach.

## 1. Kanały wydania

### 1.1 itch.io — zalecany pierwszy kanał (koszt 0 zł)
| Temat | Ustalenie | Źródło |
|---|---|---|
| Opłata wstępna | „itch.io costs nothing to use” — strona i upload bez opłat | https://itch.io/docs/creators/faq |
| Udział platformy | „open revenue sharing”: twórca sam wybiera procent dla itch.io; domyślnie **10 %**, zakres 0–100 % | FAQ j.w.; https://itch.io/docs/creators/payments |
| Opłaty płatności | PayPal i Stripe: **0,30 USD + 2,9 %** za transakcję | https://itch.io/docs/creators/payments |
| Model wypłat | „Direct to you” (PayPal/Stripe twórcy) albo „Collected by itch.io, paid later” (wtedy EU VAT po stronie itch.io) | FAQ j.w. |
| Podatki | przy wypłatach przez itch.io: „Tax Interview”; bez numeru podatkowego domyślne potrącenie **30 %**; formularze podatkowe na koniec roku. Nazwa formularza dla osoby z PL (W-8BEN?) i stawka po umowie PL–USA — `UNVERIFIED` | payments j.w. |
| Wypłata | minimum **5 USD**; środki dostępne 7 dni po zakupie; przegląd wypłaty zwykle 10–14 dni | payments j.w. |
| Limit rozmiaru pliku | „Individual file size is limited”, ≤ 10 plików na stronę, limit podnosi support; **konkretna liczba `UNVERIFIED`** (nasz folder 4 923 MB, ADR 0261) — przy uploadzie przez butler sprawdzić komunikat | FAQ j.w. |
| Narzędzie | **butler** (MIT, open source, github.com/itchio/butler): `butler push <katalog|zip> user/gra:kanał`; nazwa kanału z `win`/`windows` = tag Windows; `--userversion 0.1.0` lub `--userversion-file`; `--dry-run` | https://itch.io/docs/butler/ , https://itch.io/docs/butler/pushing.html |
| AI w treści | od 11.2024 pole „AI disclosure” (obowiązkowe dla asset packów; dla gier wg doniesień opcjonalne — `UNVERIFIED` u źródła). Nasze dźwięki ElevenLabs = AI → zaznaczać uczciwie | PC Gamer / Engadget 11.2024 (źródła wtórne) |
| Konto | zakłada **właściciel** (agenci nie zakładają kont) | — |

Zalecenie: projekt itch.io jako **Restricted / klucze dla testerów** do czasu zamknięcia §5, potem publiczny
„pay what you want” albo darmowy — decyzja właściciela (model biznesowy, docs/10 §3). Push:
`butler push artifacts/dist/kamion-<ver>-<sha>-win64.zip <konto>/kamion:windows-beta --userversion <ver>+<sha>`
(butler sam robi łatki delta między wersjami kanału; zip jest rozpakowywany po stronie itch.io).

### 1.2 Steam — później
| Temat | Ustalenie | Źródło |
|---|---|---|
| Opłata | „$100 USD (or equivalent) fee for each new app”; **bezzwrotna**; zwracana w wypłacie po ≥ 1 000 USD Adjusted Gross Revenue; Valve dolicza VAT do opłaty | https://partner.steamgames.com/doc/gettingstarted/appfee |
| Okres oczekiwania | „A 21-day waiting period between when you paid the app fee and when you can release” | https://partner.steamgames.com/doc/gettingstarted/onboarding |
| Strona „coming soon” | publicznie widoczna **≥ 2 tygodnie** przed premierą | onboarding j.w.; https://partner.steamgames.com/doc/store/releasing |
| Przegląd | „between 1-5 days” (onboarding); strona sklepu „typically takes 3-5 business days”, zgłosić ≥ 7 dni przed planowanym startem; build po zaakceptowaniu strony | onboarding, releasing j.w. |
| Tożsamość, podatki, bank | dane prawne podmiotu; dane podatkowe weryfikowane przez zewnętrzną usługę, „may take up to 30 days”; konto bankowe na tę samą nazwę | onboarding j.w. |
| Ankieta treści | **Content Survey** obowiązkowa przed przeglądem; generuje oceny dla kilku regionalnych instytucji ratingowych; sekcja o **AI** (Pre-Generated vs Live-Generated) — u nas Pre-Generated: dźwięki ElevenLabs | https://partner.steamgames.com/doc/gettingstarted/contentsurvey |
| Grafiki sklepu | m.in. Header 920×430, Small 462×174, Main 1232×706, Vertical 748×896, Library 600×900, Library Hero 3840×1240, Logo; zrzuty ≥ 1920×1080 16:9 (minimalna liczba zrzutów nie podana na stronie) | https://partner.steamgames.com/doc/store/assets |
| Udział Valve | stawka (powszechnie podawane 70/30) **nie jest na odczytanych stronach** — `UNVERIFIED` (Steam Distribution Agreement widoczna po zalogowaniu) | — |

Koszt 100 USD łamie budżet 0 zł → **wymaga zgody właściciela** (pytanie niżej). Kolejność: strona „coming soon” można
przygotować w trakcie 21 dni; build przez SteamPipe (dokumentacja Steamworks, poza zakresem tego ADR).

### 1.3 GOG / Epic — notka
- **GOG**: kuracja („Hand-picking the best in gaming”, https://www.gog.com/indie — formularz „Submit your game”);
  warunki finansowe na stronie nie są podane — `UNVERIFIED`. Bez DRM, więc nasz zip jest zgodny z ich modelem.
- **Epic Games Store**: strona dystrybucji odmówiła odczytu (HTTP 403). Źródła wtórne: opłata 100 USD za produkt
  (rozbieżne opisy zwrotności), 100 % przychodu do 1 mln USD netto rocznie na produkt, potem 88/12 — **wszystko
  `UNVERIFIED`** do odczytu https://store.epicgames.com/distribution przez właściciela.
- **Microsoft Store**: jedyny sposób na brak ostrzeżeń SmartScreen (Microsoft re-podpisuje, §3.2) — koszt konta i
  wymagania MSIX `UNVERIFIED`, niezbadane w tym zadaniu.

## 2. Folder buildu Windows → paczka

Faktyczne wyjście (`scripts/build-windows.ps1`, `BuildCommands.BuildWindows`, ADR 0261):
`artifacts/win/kamion-<ver>-<sha>[-dirty][-low][-regions][-dev]/` z `Kamion.exe` (`BuildCommands.WindowsExeName`).
Backend skryptów: **Mono** (`scriptingBackend` w ProjectSettings ma tylko wpis Android, a dla Windows Mono jest domyślne).

| Plik / folder | Do paczki? | Dlaczego |
|---|---|---|
| `Kamion.exe` | tak | „The project executable file” (Unity 6000.3, *Windows standalone binaries*: https://docs.unity.com/en-us/engine/6000.3/manual/platform-specific/windows/standalone-binaries) |
| `UnityPlayer.dll` | tak | natywny silnik, podpisany certyfikatem Unity (j.w.) |
| `Kamion_Data/` | tak | „all the data needed to run your application” (j.w.) |
| `MonoBleedingEdge/` | tak | runtime Mono (backend Mono) — opis folderu nie występuje na stronie Unity; potrzebny do startu |
| `UnityCrashHandler64.exe` | tak | obsługa awarii playera (zapis zrzutu, §6) — opisu brak na stronie Unity 6000.3; zostawiamy |
| `GameAssembly.dll` | tak (tylko IL2CPP) | dziś nie powstaje (Mono) |
| `WinPixEventRuntime.dll` | **nie wydajemy buildów dev** | „Unity only creates this file if you enable the Development Build” (j.w.) — skrypt traktuje go jak znacznik buildu dev |
| `*.pdb` | **nie** | „Symbol files for debugging”, kopiowane tylko przy *Copy PDB files* (j.w.) |
| `Kamion_BurstDebugInformation_DoNotShip/` | **nie** | symbole Burst; nazwa folderu jest instrukcją Unity. Oficjalny opis zawartości — brak (changelog Burst wspomina tylko nazwę: https://docs.unity3d.com/Packages/com.unity.burst@1.8/changelog/CHANGELOG.html). `build-windows.ps1` przenosi `*_DoNotShip` do `artifacts/win/symbols/<build>/` (ADR 0276) |
| `Kamion_BackUpThisFolder_ButDontShipItWithYourGame/` | **nie** | powstaje przy IL2CPP (kod C++ i symbole); oficjalnej strony brak — tylko nazwa i forum Unity (https://discussions.unity.com/t/why-this-folder-generated-backupthisfolder-butdontshipitwithyourgame/901854). Zachować w `artifacts/` do symbolizacji awarii |
| `build.json`, `Kamion.exe.sha256`, `Kamion.content.json`, `Kamion.top.txt`, `Kamion.variants.txt`, `Kamion_Data.sha256` | **nie** | nasze metadane buildu (ADR 0261, 0276) — zostają w `artifacts/` |
| `build-id.json` | tak | git sha + skrót zawartości `Kamion_Data` (ADR 0276); gra czyta go przy starcie i pokazuje w menu / „Informacje” / logu |
| `Kamion-okno.cmd` | tak | start w oknie 1600×900 (ProjectSettings domyślnie pełny ekran) |
| `Kamion-<region>.cmd` | **nie** | skróty deweloperskie, po jednym na region buildu (`-scene <region>`, ADR 0276); tester wybiera region w menu |

Paczka dokłada: `THIRD_PARTY_NOTICES.txt` (generowany z `game/Assets/_Project/UI/Resources/About/attributions.txt`, czyli
**ten sam tekst co ekran „Informacje”** — jedno źródło prawdy), `README.txt` (z `dist/windows/README.txt.in`: wymagania D74,
start, SmartScreen, logi), `SHA256SUMS.txt`, `collect-logs.ps1` + `Zbierz-logi.cmd`.

Skrypt: `scripts/package-windows.py` (stdlib, Python ≥ 3.10). Zip powtarzalny (posortowane wpisy, stała data
2000-01-01, stałe uprawnienia; README zawiera datę pakowania). Odmawia: buildu dev (bez `--allow-dev`), brudnego
checkoutu (bez `--allow-dirty`), braku `Kamion.exe`/`Kamion_Data`/`UnityPlayer.dll`. `--release` dodatkowo kończy
się kodem 3 przy otwartych blokerach z §5. Testy: `uv run --no-project --with pytest pytest tests/dist -q` (CI: job `dist-tests`).

## 3. Zip vs instalator, podpis, wersje

### 3.1 Zip (zalecany) vs instalator
| | Zip (domyślny) | Inno Setup | WiX Toolset |
|---|---|---|---|
| Koszt | 0 | licencja pozwala na każde użycie, także komercyjne (`license.txt`: „use this software for any purpose, including commercial applications”), ale od 6.5.0 autor **prosi** użytkowników komercyjnych o zakup licencji: „It is not strictly required” (https://jrsoftware.org/files/is/license.txt, https://jrsoftware.org/isorder.php); cena na stronie nie podana | kod MS-RL (https://github.com/wixtoolset/wix/blob/main/LICENSE.TXT) + **Open Source Maintenance Fee**: organizacje > 10 000 USD rocznego przychodu muszą sponsorować projekt (https://docs.firegiant.com/wix/osmf/) — poniżej progu 0 |
| itch.io | natywnie (butler, aplikacja itch) | zbędny | zbędny |
| Steam | zbędny (SteamPipe instaluje folder) | zbędny | zbędny |
| Zalety | zero zależności, odtwarzalny, delta w butler | skróty, odinstalowanie | MSI dla firm |

Zalecenie: **zip**. Szablon `dist/windows/kamion.iss` istnieje (nieskompilowany) na wypadek dystrybucji poza
sklepami; użycie Inno przy sprzedaży = najpierw decyzja właściciela (prośba autora o licencję). WiX — nie (MSI
niepotrzebne, a OSMF zacznie obowiązywać przy przychodzie > 10 000 USD).

### 3.2 Podpis kodu i SmartScreen
Źródło: Microsoft, *SmartScreen reputation for Windows app developers* (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation, aktualizacja 2026-08-17):
- Brak podpisu: ostrzeżenie „Windows protected your PC”, użytkownik musi wybrać „Run anyway”; reputacja liczona od zera
  dla każdej nowej wersji. Certyfikat samopodpisany = jak brak podpisu.
- OV/EV: ostrzeżenie do czasu zbudowania reputacji, ale z nazwą wydawcy; **„EV certificates no longer bypass SmartScreen”**
  — dopłata do EV „no longer justified”.
- **Azure Artifact Signing** (dawniej Trusted Signing): „Starts at $9.99/month”, wymaga walidacji tożsamości;
  reputacja rośnie z liczbą pobrań. Dostępność dla osób prywatnych w PL — `UNVERIFIED`.
- Windows 11 *Smart App Control* może blokować niepodpisane pliki bez reputacji (ta sama strona).
- Ceny certyfikatów OV/EV u CA — tylko serwisy odsprzedawców, rozbieżne → `UNVERIFIED`, nie podajemy.

Zalecenie przy 0 zł: **bez podpisu** na itch.io/testy; README paczki opisuje ostrzeżenie i weryfikację SHA256.
Zachowanie SmartScreen dla gier instalowanych przez klienta Steam/itch — niesprawdzone u źródła (`UNVERIFIED`).
Przy pierwszej sprzedaży poza Steamem: Artifact Signing (~10 USD/mies.) — decyzja właściciela.

### 3.3 Wersjonowanie i changelog
- Wersja = `bundleVersion` z ProjectSettings (dziś `0.1.0`, semver 2.0: https://semver.org/). Paczka:
  `kamion-<ver>-<sha>[-low][-regions][-dev][-dirty]-<dane>-win64.zip` — wzór APK `kamion-<ver>-<sha>.apk` i folderu buildu
  (ADR 0261) + `-regions` (build ze scenami regionów, recenzja #134 P2-1) + `<dane>` = skrót zawartości `Kamion_Data`
  (ADR 0276: `Kamion.exe` jest w każdym buildzie ten sam, więc sam sha commitu nie odróżnia dwóch buildów).
  Warianty w nazwie tylko gdy odbiegają od domyślnego: `-low` (świat Low), `-dev`, `-dirty` (obie tylko dla testerów).
- Zasada semver dla nas: PATCH = poprawki bez zmiany zapisu i danych regionów; MINOR = nowy region/funkcja, zapis
  zgodny; MAJOR = niezgodny zapis lub paczki regionów (docs/10 §3 `compatibleGameVersions`). 0.x = przed wydaniem.
- `--userversion <ver>+<sha>` w butler; w Steamie opis buildu = ta sama etykieta.
- Changelog: `CHANGELOG.md` w formacie *Keep a Changelog* (https://keepachangelog.com/) prowadzi lider przy każdym tagu
  `v<ver>` — **tworzy go lider** przy pierwszym wydaniu (plik w korzeniu repo; nie zakładam go tu, żeby nie dublować HANDOVER).
- Zmianę `bundleVersion` robi tylko lider (ProjectSettings).

## 4. Wymagania sprzętowe na stronę sklepu (D74)
Klasy przyjęte przez właściciela (D74, wzorowane na kartach ETS2/ATS). **Progi FPS, rozdzielczość i dysk = WORKING_VALUE**
do czasu pomiaru na sprzęcie tych klas (pomiar na RTX 5070 dewelopera nie zastępuje klas — D74, ADR 0260).

| | Minimalne | Zalecane |
|---|---|---|
| System | Windows 10 64-bit (Unity 6000.3 wymaga 21H1 / build 19043 lub nowszego¹) | Windows 10 64-bit (21H1+) / Windows 11 |
| Procesor | Intel Core i5-6400 / AMD Ryzen 3 1200 | Intel Core i5-9600 / AMD Ryzen 5 3600 |
| Pamięć | 8 GB RAM | 12 GB RAM |
| Grafika | NVIDIA GTX 660 / AMD RX 460 / Intel HD 630 (2 GB VRAM) | NVIDIA GTX 1660 / AMD RX 590 |
| Dysk | ≤ 25 GB (WORKING_VALUE; dziś folder 4 923 MB — ADR 0261) | j.w. |
| Cel | Low, 1080p, 30 fps (WORKING_VALUE) | High, 1080p, 60 fps (WORKING_VALUE) |

¹ https://docs.unity.com/en-us/engine/6000.3/manual/platform-specific/windows/requirements-and-compatibility (także: x64 z SSE2, DX10/11/12 lub Vulkan).
Ryzyko z D74: Intel HD 630 przy obecnym świecie (do 2 M tris High) — pomiar Low na iGPU przed publikacją wymagań.
Na stronie sklepu nie publikujemy FPS (SCS też nie publikuje); kolumna „Cel” jest wewnętrzna — w README paczki
oznaczona jako wstępna.

## 5. Licencje zasobów w buildzie

Źródło: `docs/LICENSES.md` (tabela zbiorcza, 42 źródła) i `docs/reports/LICENSES-AUDIT-S20.md`.

**Co musi trafić do paczki** (robi to `package-windows.py` → `THIRD_PARTY_NOTICES.txt`, plus ekran „Informacje” w grze, ADR 0230):
OSM „© OpenStreetMap contributors” + ODbL 1.0; GUGiK (NMT/orto/BDOT10k, LoD1/LoD2 CC BY 4.0); BDL; baza G3 (ODbL);
Poly Haven CC0 (dobrowolnie); Commons PD; Inter — pełny tekst SIL OFL 1.1; DejaVu (Bitstream Vera); glTFast — pełny
tekst Apache 2.0; Unity („Gra stworzona w Unity”).

| # | Pozycja | Status | Działanie |
|---|---|---|---|
| B1 | **R-P0-2 — ODbL §4.6**: dane nawigacji (`Nav/*.bytes`) to baza pochodna OSM w buildzie; brak adresu oferty bazy | **BLOKER publicznej dystrybucji** (P0 audytu; `attributions.txt` sam mówi „NIE dystrybuować APK poza urządzenia właściciela”; ADR 0230) | właściciel wybiera miejsce publikacji danych/metody → lider wpisuje adres do `attributions.txt`, usuwa notkę R-P0-2; `--release` zacznie przechodzić |
| B2 | Suno (free = brak praw komercyjnych, D8) | **brak w buildzie**: `docs/LICENSES.md` nie ma żadnego wpisu Suno (tylko D8 jako możliwość, `PROTOTYPE_ONLY`) | nic; jeśli kiedyś dojdzie muzyka Suno — tylko plan płatny, wpis w LICENSES |
| B3 | ElevenLabs SFX v3 (plan płatny Pro, dźwięki w buildzie) | P1: Service-Specific Terms SFX `UNVERIFIED` (R-P1-4) | odczytać warunki przed sprzedażą; ujawnić AI w ankiecie Steam i na itch.io |
| B4 | Fab / Quixel Megascans (Fab Standard License) | P1: pełny EULA nieprzeczytany (R-P1-5); w buildzie tylko gdy pliki lokalne obecne przy buildzie | przed sprzedażą przeczytać EULA na koncie; `build.json`/`Kamion.content.json` pokazuje, czy trafiły |
| B5 | Pakiety Unity (URP — Unity Companion License, Burst, Input System…) | P1: licencje i ewentualne „Third Party Notices” silnika `UNVERIFIED` (R-P1-3) | lider na maszynie z Unity: `Library/PackageCache/*/LICENSE.md` → rejestr i `attributions.txt` |
| B6 | GUGiK CC BY 4.0 + art. 40a Pgik w jednej bazie z ODbL | P1 przegląd prawny (R-P1-1) | przed sklepem |
| B7 | Odwzorowanie realnych obiektów (swoboda panoramy) | P1 (R-P1-6) | przegląd prawny; bez logo/marek (zasada 8) |

**Unity Personal — ekran powitalny**: Unity 6 pozwala użytkownikom Personal wyłączyć lub zmienić ekran „Made with Unity”
(„Added the option on Unity Personal to disable or customize the Made with Unity splash screen”; dla edytorów sprzed
Unity 6 nie wolno — https://support.unity.com/hc/en-us/articles/212165803; „Splash screen optional with Unity 6” —
https://unity.com/products/pricing-updates). Personal: „available to customers with up to $200,000 in revenue and
funding” (ta sama strona). U nas ekran jest **włączony** (`m_ShowUnitySplashScreen: 1`, `m_ShowUnitySplashLogo: 1`)
— zmiana = decyzja lidera/właściciela (ProjectSettings), nie wymóg licencji.

**Czcionki**: Inter (OFL 1.1, „Inter” = Reserved Font Name, plik niezmieniony, tekst licencji obok — OK);
DejaVu tylko jako raster w teksturach; `LegacyRuntime.ttf` = zasób Unity. Brak nowych plików czcionek do paczki.

## 6. Logi i awarie u testera
- **Player.log**: `%USERPROFILE%\AppData\LocalLow\<CompanyName>\<ProductName>\Player.log` (Unity 6000.3, *Log files reference*:
  https://docs.unity.com/en-us/engine/6000.3/manual/get-started/project-configuration/log-files). U nas
  `…\LocalLow\woogitsugames\Kamion\Player.log` (+ `Player-prev.log` z poprzedniego uruchomienia; `usePlayerLog: 1`).
  Tam też nasz `diag\` (`summary.json`, `frametimes.csv` — używa ich `build-windows.ps1 -Run`).
- **Zrzuty awarii**: `%TMP%\CompanyName\ProductName\Crashes` (`UnityEngine.Windows.CrashReporting.crashReportFolder`,
  https://docs.unity.com/en-us/engine/6000.3/script-reference/unityengine/windows/crashreporting/crashreportfolder.md),
  czyli `%TMP%\woogitsugames\Kamion\Crashes`; „assigned a unique path on startup”. Zapisuje je `UnityCrashHandler64.exe`
  (dlatego zostaje w paczce). Do symbolizacji potrzebne są nasze `*_DoNotShip` / `*_BackUpThisFolder…` / pdb —
  **archiwizować je per wersja w `artifacts/win/<build>/`** (nie kasować przed wydaniem następnej wersji; dziś
  `build-windows.ps1` kasuje `*_DoNotShip` — propozycja zmiany w ADR 0271 §Propozycje).
- **Zbieranie**: `scripts/collect-logs.ps1` (w paczce + `Zbierz-logi.cmd`): Player.log, Player-prev.log, diag\,
  5 najnowszych folderów Crashes, `system.txt` (Windows, CPU, RAM, GPU + sterownik, dyski, SHA256 exe, nazwa paczki),
  opcjonalnie `-DxDiag`. Nazwa użytkownika i komputera zastępowane `<user>`/`<pc>`. Wynik: `kamion-logi-<ts>.zip`
  na Pulpicie. Nic nie jest wysyłane automatycznie — tester wysyła plik ręcznie (bez zewnętrznych serwisów).
  Działa w Windows PowerShell 5.1 (nie wymaga PS 7). **Nieuruchomiony** (chmura bez Windows) — do sprawdzenia przez lidera.
- **Unity Cloud Diagnostics**: wg strony planów Unity jest w planie Personal (źródło wtórne w wyszukiwarce; limity
  `UNVERIFIED`). Wymaga konta Unity Cloud i wysyła dane graczy do Unity → nie włączamy bez decyzji właściciela i
  informacji o prywatności dla graczy (RODO). Zostajemy przy ręcznym zip.

## 7. IL2CPP czy Mono na PC
Dziś: **Mono** (ADR 0261 „Otwarte”: „Scripting backend Standalone = Mono … IL2CPP do rozważenia przy wydaniu”;
ProjectSettings: `scriptingBackend: Android: 1` — tylko Android ma IL2CPP).

Porównanie wg Unity 6000.3 (*Introduction to scripting back ends*,
https://docs.unity.com/en-us/engine/6000.3/manual/programming-environment/scripting-backends/intro.md):

| | Mono | IL2CPP |
|---|---|---|
| Czas buildu | „Faster iteration, smaller linking steps” | „Slower (C++ codegen, compiling, and linking)” |
| Start | „Typically slower with JIT” | „Typically faster (fully native, no JIT warmup)” |
| Rozmiar | mniejszy kod | „Larger native binaries” |
| Refleksja / generyki | pełne, JIT | bez `Reflection.Emit`/`dynamic`; czasem podpowiedzi AOT; `link.xml` / `[Preserve]` |
| Debug | szybkie, czytelne stosy | wspierane, stosy opcjonalnie wzbogacane |
| Narzędzia | brak dodatkowych | „Visual Studio 2019 with C++ Tools component or later and Windows SDK 10.0.19041.0 or newer” (Windows requirements, §4 przypis 1) |
| Modowanie | zarządzane DLL w `Kamion_Data/Managed` — łatwe do podglądu/patchowania | trudniejsze (natywny `GameAssembly.dll`); nie jest ochroną |

Unity: „prefer IL2CPP if Player builds need faster startup, stricter platform compliance, and more predictable performance”.
U nas gorąca pętla fizyki i tak może iść przez Burst (działa z oboma backendami). Wpływ na FPS w naszej grze — **niezmierzony**.

**Zalecenie**: zostać przy **Mono** dla buildów testowych (czas buildu już 628 s BuildPlayer, ADR 0261); przed pierwszym
wydaniem publicznym zrobić **pomiar A/B** (ten sam commit, Mono vs IL2CPP: czas buildu, rozmiar folderu, czas startu do
`[START]`, p50/p95/p99 frame time na trasie `-autopilot route`), na maszynie z VS C++. Decyzja na podstawie liczb, zmiana
w ProjectSettings przez lidera. IL2CPP generuje `*_BackUpThisFolder_ButDontShipItWithYourGame` — paczka go wyklucza.

## 8. Pytania do właściciela
1. R-P0-2: gdzie publikujemy bazę pochodną OSM (dane nawigacji) — publiczne repo generatorów czy osobne archiwum na ODbL?
2. Pierwszy kanał itch.io: model (darmowe / „zapłać ile chcesz” / płatne), widoczność (ukryta dla testerów?), udział itch.io (domyślnie 10 %), kto zakłada konto.
3. Steam: zgoda na 100 USD (poza budżetem 0 zł) i kiedy.
4. Podpis kodu: zostajemy bez podpisu (ostrzeżenie SmartScreen) czy Artifact Signing ~10 USD/mies.?
5. Ekran powitalny Unity: zostawić czy wyłączyć (w Unity 6 Personal dozwolone)?
6. Unity Cloud Diagnostics: tak/nie (wysyła dane graczy do Unity)?
