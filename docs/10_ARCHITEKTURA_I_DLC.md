# 10 — Architektura aplikacji, repo i DLC

> **D73 / ADR 0260 (15.11.2026):** platforma główna = **Windows Standalone x64** (ten sam projekt Unity 6000.3 URP);
> Android (potem iOS) = wersja późniejsza, lżejsza. Architektura się nie zmienia — zmienia się kolejność platform,
> domyślny cel buildów i bramek (`docs/03`, ADR 0266) oraz pytania o dystrybucję (§3a). Bez zmiany silnika.

## 1. Struktura repo (propozycja — dopracuj w ADR w Etapie 0)
```
truck-sim/
├── CLAUDE.md  README.md  PROMPT_STARTOWY.md
├── .claude/ agents/ skills/ settings.json      .mcp.json
├── docs/ 01…11, adr/, plan/, reports/, STATUS.md, ROADMAP.md, LICENSES.md,
│        ENVIRONMENT_AUDIT.md, DEVICE_MATRIX.md, PERFORMANCE_BUDGETS.md,
│        VEHICLE_REFERENCE_DATA.md, PHYSICS_VALIDATION.md, ART_BIBLE.md, map-decisions.md
├── game/                         # projekt Unity
│   └── Assets/_Project/
│       ├── Core/ (bootstrap, serwisy, settings, save, lokalizacja)
│       ├── Vehicle/Physics/ (czysty C#)  Vehicle/Runtime/ (adaptery Unity)
│       ├── World/ (Geo, Roads, Terrain, Streaming, FloatingOrigin, Import)
│       ├── Rendering/  Environment/  Traffic/  Gameplay/  UI/  Input/  Camera/  Audio/
│       ├── Platform/ (Windows/desktop, Android, iOS, haptyka, uprawnienia, sklep — abstrakcje)
│       ├── Content/ (RegionPackageManager, manifesty, entitlement adapter)
│       ├── Telemetry/  Editor/ (buildery, importery, generatory)  Tests/
│       └── Art/ Truck/ World/ Shared/
├── art-source/ truck/ world/     # .blend i źródła (LFS)
├── tools/ worldgen/ blender/ telemetry/ physics-runner/ audio/ asset-validation/ .venv
├── data/ raw/ (poza gitem)  Data/ SourceManifests/ Schemas/ Samples/
├── scripts/ setup-windows.ps1 doctor.ps1 build-windows.ps1 build-android.ps1 pc-metrics.ps1 device-metrics.ps1 test.ps1 visual-qa.ps1 import-region.ps1
├── tests/ physics/ golden/ gis/
└── artifacts/ (poza gitem: APK, logi, zrzuty, raporty)
```

## 2. Zasady architektury
- Moduły jako asmdef, mało i sensownie; zależności jednokierunkowe (Physics nie zna UI). Prosty composition root, bez ciężkiego frameworka.
- **Autorytatywne definicje danych z wersją schematu i migracjami**: `VehicleDefinition`, `TrailerDefinition`, `CargoDefinition`, `RoadGraph`, `RegionManifest`, `DeliveryJob`, `CompanyDefinition`, `SaveSchema`, `CountryRules` (znaki, przepisy, prędkości, ruch prawo/lewostronny jako dane — nigdy `if (country == "DE")` w kodzie).
- **Zapis gry**: ID regionu + stabilna pozycja globalna (double) + ID drogi/pasa, nie surowy `Transform`. Własny format (JSON/binarny), bez `PlayerPrefs` dla stanu gry.
- Platforma neutralna od dnia 1: zero API Android-only **i Windows-only** w logice; platformowe rzeczy za interfejsami (`IPlatformServices`: na PC `DefaultPlatformServices` — argumenty wiersza poleceń zamiast intent extras, brak czujników baterii/termiki).
- **Wejście za warstwą sterowania** (D56): klawiatura, pad, kierownica z FFB na PC; dotyk/gyro na telefonie — fizyka dostaje te same znormalizowane osie (skręt, gaz, hamulec, sprzęgło, bieg), nigdy surowe urządzenie.
- **Tiery jakości jako dane** (`QualityProfile`): PC dokłada treść na High/Ultra; dane bazowe regionów muszą nadal mieścić się w budżecie mobilnym (🔒 zabezpieczenie, `docs/03`), żeby wersja telefonowa nie wymagała osobnego pipeline'u świata.
- Offline: po pobraniu treści gra działa bez internetu.

## 3. Treść i DLC
**Core** (kod, pojazd, fizyka, UI, audio, system świata) + **Region Packs** (dane i assety regionu) + w przyszłości **Vehicle Packs**.

Manifest regionu (szkic — finalny schemat ze ścisłą walidacją):
```json
{
  "schemaVersion": 1,
  "id": "pl.podlaskie.bialystok.industrial-01",
  "country": "PL",
  "contentVersion": "0.1.0",
  "compatibleGameVersions": ">=0.1.0 <1.0.0",
  "worldCrs": "EPSG:2180",
  "scalePolicy": { "urban": 1.0, "intercity": null },
  "bounds": "...",
  "entryPoints": [ { "id": "...", "roadId": "...", "connectsTo": "..." } ],
  "routingGraphVersion": 1,
  "addressablesCatalog": "regions/pl/podlaskie/bialystok/catalog.json",
  "chunks": "...", "checksums": "...",
  "sources": { "osmExtractSha256": "...", "nmtSha256": "...", "bdotSha256": "..." },
  "licensesManifest": "licenses/pl-podlaskie.json",
  "entitlementId": null
}
```
- Regiony łączą się przez `entryPoints` (węzły graniczne grafu) — po zainstalowaniu sąsiedniej paczki sieć się spina bez zmian w kodzie.
- **Addressables** z katalogami per region; AssetBundles są platformowo specyficzne — **osobny build treści dla Windows (StandaloneWindows64)**, Androida i iOS. Na PC formaty kompresji tekstur inne niż ASTC (BC), więc rozmiar paczek regionu na PC ≠ rozmiar w APK — mierzyć osobno.
- **PC (platforma główna):** paczka gry + paczki regionów jako pliki danych obok gry (katalog Addressables per region); mechanizm dostarczania zależy od kanału dystrybucji — **nieustalony** (§3a).
- 🔒 **Google Play** (wersja telefonowa, później): AAB + Play Asset Delivery (install-time / fast-follow / on-demand) — sprawdź aktualne limity rozmiarów (D72: pojedynczy APK > ~4 GB wątpliwy, UNVERIFIED). Własny CDN tylko zgodnie z zasadami sklepu. iOS — mechanizmy zgodne z Apple (sprawdź przy porcie).
- PAD i paczki to **dane/assety, nie kod wykonywalny**.
- Abstrakcja uprawnień (entitlements) bez implementacji płatności, dopóki właściciel nie zdecyduje o modelu biznesowym.

### 3a. Wpływ D73 na DLC i dystrybucję — pytania do właściciela (bez decyzji sklepowych)
Nic z poniższego nie jest zdecydowane; do tego czasu kod ma tylko abstrakcję uprawnień (`entitlementId`), bez płatności.
1. **Kanał dystrybucji na PC** — sklep z platformą (który?), własna strona, kilka naraz? Od tego zależą: format aktualizacji,
   mechanizm DLC (osobne „depoty”/paczki vs pobieranie z własnego serwera), DRM, osiągnięcia, chmura zapisów.
2. **Model DLC na PC** — czy regiony/kraje mają być płatnymi DLC, darmowymi aktualizacjami, czy jedną pełną grą z dodatkami?
   Czy zakup na PC ma przenosić się na telefon (cross-buy) — to wymaga własnego konta gracza albo wspólnej platformy.
3. **Rozmiar instalacji** — PC zniesie wielokrotność limitu z D72, ale czy jest górna granica (np. dla klasy „min” z małym SSD)?
   Czy regiony mają być doinstalowywane na żądanie?
4. **Wersja telefonowa** — kiedy (po której bramce PC) i czy ma mieć tę samą mapę (lżejsze tiery), czy podzbiór regionów?
5. **Wymagania prawne/licencyjne dla PC** — atrybucje danych (OSM/GUGiK, ADR 0230) w menu „Informacje” zostają; czy kanał
   PC wymaga dodatkowych dokumentów (EULA, polityka prywatności, klasyfikacja wiekowa)?
6. **Kierownice** — czy wsparcie FFB (D56) jest wymogiem na premierę PC, czy aktualizacją?
7. **Mody** — na PC gracze oczekują modów; w `docs/01` są poza zakresem — czy to się zmienia?

Konsekwencje techniczne niezależne od odpowiedzi: AssetBundles per platforma (osobny build treści Windows), manifest regionu
bez zmian (`compatibleGameVersions`, `checksums`, `entitlementId`), testy systemu treści poniżej obowiązują na PC jako pierwszej platformie.

Testy systemu treści (najpierw na PC): brak paczki, uszkodzona paczka, niezgodny manifest, przerwane pobieranie, brak miejsca, zapis w usuniętym regionie (bezpieczny fallback do bazy), nieposiadana paczka, przejazd przez granicę regionów, aktualizacja paczki z migracją zapisu.

## 4. Poziomy jakości mapy Polski (docelowo)
- **Tier A — handcrafted/verified**: Białystok, kluczowe miasta i trasy.
- **Tier B — procedural + QA**: większość dróg krajowych/wojewódzkich i miejscowości.
- **Tier C — data-only**: istnieje w grafie planowania, niedostępne do jazdy — gra nigdy nie udaje, że jest.
Nie ogłaszaj „całej Polski”, gdy zbudowane są fragmenty.
