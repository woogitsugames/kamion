# 10 — Architektura aplikacji, repo i DLC

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
│       ├── Platform/ (Android, iOS, haptyka, uprawnienia, sklep — abstrakcje)
│       ├── Content/ (RegionPackageManager, manifesty, entitlement adapter)
│       ├── Telemetry/  Editor/ (buildery, importery, generatory)  Tests/
│       └── Art/ Truck/ World/ Shared/
├── art-source/ truck/ world/     # .blend i źródła (LFS)
├── tools/ worldgen/ blender/ telemetry/ physics-runner/ audio/ asset-validation/ .venv
├── data/ raw/ (poza gitem)  Data/ SourceManifests/ Schemas/ Samples/
├── scripts/ setup-windows.ps1 doctor.ps1 build-android.ps1 test.ps1 visual-qa.ps1 import-region.ps1
├── tests/ physics/ golden/ gis/
└── artifacts/ (poza gitem: APK, logi, zrzuty, raporty)
```

## 2. Zasady architektury
- Moduły jako asmdef, mało i sensownie; zależności jednokierunkowe (Physics nie zna UI). Prosty composition root, bez ciężkiego frameworka.
- **Autorytatywne definicje danych z wersją schematu i migracjami**: `VehicleDefinition`, `TrailerDefinition`, `CargoDefinition`, `RoadGraph`, `RegionManifest`, `DeliveryJob`, `CompanyDefinition`, `SaveSchema`, `CountryRules` (znaki, przepisy, prędkości, ruch prawo/lewostronny jako dane — nigdy `if (country == "DE")` w kodzie).
- **Zapis gry**: ID regionu + stabilna pozycja globalna (double) + ID drogi/pasa, nie surowy `Transform`. Własny format (JSON/binarny), bez `PlayerPrefs` dla stanu gry.
- Platforma neutralna od dnia 1: zero API Android-only w logice; platformowe rzeczy za interfejsami.
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
- **Addressables** z katalogami per region; AssetBundles są platformowo specyficzne (osobny build dla Androida i iOS).
- **Google Play**: AAB + Play Asset Delivery (install-time / fast-follow / on-demand) — sprawdź aktualne limity rozmiarów. Własny CDN tylko zgodnie z zasadami sklepu. iOS — mechanizmy zgodne z Apple (sprawdź przy porcie).
- PAD i paczki to **dane/assety, nie kod wykonywalny**.
- Abstrakcja uprawnień (entitlements) bez implementacji płatności, dopóki właściciel nie zdecyduje o modelu biznesowym.

Testy systemu treści: brak paczki, uszkodzona paczka, niezgodny manifest, przerwane pobieranie, brak miejsca, zapis w usuniętym regionie (bezpieczny fallback do bazy), nieposiadana paczka, przejazd przez granicę regionów, aktualizacja paczki z migracją zapisu.

## 4. Poziomy jakości mapy Polski (docelowo)
- **Tier A — handcrafted/verified**: Białystok, kluczowe miasta i trasy.
- **Tier B — procedural + QA**: większość dróg krajowych/wojewódzkich i miejscowości.
- **Tier C — data-only**: istnieje w grafie planowania, niedostępne do jazdy — gra nigdy nie udaje, że jest.
Nie ogłaszaj „całej Polski”, gdy zbudowane są fragmenty.
