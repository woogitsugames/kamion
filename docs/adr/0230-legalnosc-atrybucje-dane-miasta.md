# ADR 0230 — Legalność: dane Miasta Białystok poza grą, atrybucje BDL i referencji, wymagania ekranu „Informacje” jako dane

Status: Proposed (agent E3 chmury E, gałąź `legal-0230`), 2026-11-15. Scalenie: lider.
Dotyczy: ADR 0002 (zakaz Google), 0065 (zdjęcia CC BY-SA tylko referencja), 0066 (otwarte źródła referencji), 0073, 0187 (las
Krywlany z BDL), 0201 (marki w danych ciężarówki); BACKLOG-S21 B-131, B-065; `docs/reports/LICENSES-AUDIT-S20.md`,
`docs/reports/BRAND-SWEEP-S20.md`.

## Kontekst
1. Dane Miasta Białystok (ArcGIS Online, `tools/refs/bialystok_open_data.py`) miały w rejestrze „brak licencji w metadanych,
   `LEGAL_REVIEW_REQUIRED`” (ADR 0066:71) bez sprawdzenia warunków miasta.
2. Ekran „Informacje” (`attributions.txt`, s21) nie miał atrybucji Banku Danych o Lasach, choć parametry lasów Dojlid (ADR 0187)
   pochodzą z BDL, a Regulamin BDL wymaga podania źródła i czasu. Tabela zbiorcza `docs/LICENSES.md` w wierszu 40 błędnie
   podawała BDL jako nieużyty.
3. Warunki Mapillary, KartaView, Panoramax, OSM i GUGiK były w rejestrze opisane bez cytatów ze stron źródeł.
4. Audyt maszynowy licencji na `main` miał 360 plików research bez wpisu (pakiety s20–s21) — `pytest tools/licenses` czerwony.
5. B-065: pozostałe nazwy marek w kodzie gry.

## Decyzja
1. **Dane Miasta Białystok nie trafiają do gry ani do `Data/Regions/*`.** Ustalenia (2026-11-15, cytaty w `docs/LICENSES.md`,
   sekcja „Dane Miasta Białystok — status licencyjny”): 0/109 pozycji organizacji ArcGIS miasta ma `licenseInfo`; BIP Urzędu
   Miejskiego (zarządzenie 973/21) stawia warunki ponownego wykorzystywania, w tym „pozyskana treść informacji nie może być
   modyfikowana”; domniemanie „bez warunków” z art. 11 ust. 5 ustawy o otwartych danych dotyczy tylko BIP i portalu danych, a
   ArcGIS to „inny sposób” (art. 11 ust. 4). Baza pochodna w grze = modyfikacja + łączenie z ODbL → niedopuszczalne bez wniosku.
   Dane miasta zostają **wyłącznie referencją** (kontrola pozycji), a każda warstwa ma zamiennik OSM/GUGiK (tabela w rejestrze).
   Strażnik: `test_no_city_open_data_in_build_inputs` (pytest, `git grep` po identyfikatorach usług miasta w `Data/Regions`,
   `tools/worldgen`, `tools/ui`, `game/Assets`).
2. **Atrybucje na ekranie „Informacje”:** nowa pozycja „Bank Danych o Lasach” (źródło, czas wytworzenia: PUL 2017–2026 / stan
   2023, pozyskanie 14.11.2026 — Regulamin BDL cz. V lit. a); dobrowolna pozycja „Zdjęcia referencyjne” (Mapillary contributors,
   CC BY-SA 4.0; Panoramax CC BY-SA 4.0; KartaView bez twierdzenia o licencji, bo potwierdzona tylko wtórnie); link CC BY-SA 4.0.
   Logo Mapillary nie jest potrzebne: warunki wymagają go przy serwowaniu zdjęć lub danych z API Mapillary — gra nie robi żadnego.
   GUS Bank Danych Lokalnych: nieużywany (wiersz 42 rejestru, warunek „podane źródło” zapisany na przyszłość).
3. **Wymagania ekranu jako dane:** `tools/licenses/attribution_requirements.json` (wiersz tabeli zbiorczej → dokładne napisy;
   `always_visible` = nazwy i adresy ODbL / CC BY / CC BY-SA; `forbidden_visible`). Czytają je pytest
   (`tools/licenses/tests/test_attributions.py`) i czysty .NET (`tools/about-runner/Tests/LicensesCompletenessTests.cs`):
   każdy wiersz `docs/LICENSES.md` wymagający atrybucji w buildzie musi być zmapowany, każdy napis widoczny (nie w komentarzu `#`),
   lista znaczników zgodna z parserem. `AttributionDocument.Problems` zgłasza nagłówek bez treści („heading without text”).
4. **Rejestr:** sekcje „Dane Miasta Białystok — status licencyjny”, „Atrybucje — warunki źródeł” (cytaty z URL i datą dostępu),
   „Pakiety research s20–s21” (360 → 0 plików bez wpisu); wiersze 9–11, 14, 40–42 tabeli zbiorczej poprawione (BDL używany,
   Panoramax OSM-FR = CC-BY-SA-4.0 z `/api/configuration`, nie „CC BY-SA 2.0 FR”).
5. **Marki (B-065):** dane fizyki (`amt12_od_class.gearbox.json`, `diesel_r6_13l_368kw.engine.json`,
   `tractor_4x2_generic.vehicle.json`), `DrivingLabSceneBuilder.cs`, `ContactShadowCaster.cs` i `tools/physics-runner` były już
   neutralne na `main` (0201 / 32f4291b — `grep -i` po markach pojazdów, skrzyń i opon: 0 trafień). Zmienione teraz: komentarz
   `TruckAssetBuilder.cs` („AdBlue” → „AUS 32”), opis kamery kontrolnej w `WorldSceneBuilder.cs` i komentarze/komunikaty testów
   PlayMode WorldC (nazwa parku logistycznego → „depot gate”). **Nie zmieniane (świadomie):** identyfikatory kamer
   `kwadrat-park-gate` (`gate3_cameras.json` = kopia `Data/Regions/.../gate3_cameras.json`, `WorldPbrTintRound.cs`,
   komentarz `InstanceImporter.cs`) — zmiana rozspójniłaby dane kamer i dowody; nazwy obiektów FBX `adblue_*` w generatorach
   Blendera (BRAND-SWEEP #20) — wymagają eksportu i przebudowy prefabów (Blender/Unity, lider). Nazwy urządzeń testowych
   (Galaxy A16, Adreno) w komentarzach i notatkach profilu jakości — użycie opisowe, poza zakresem.

## Konsekwencje
- Pierwsza dystrybucja poza telefony właściciela nadal zablokowana przez R-P0-2 (oferta bazy pochodnej ODbL §4.6 — decyzja
  właściciela o miejscu publikacji) i przegląd prawny R-P1-1 (ODbL × CC BY 4.0 × Pgik).
- Nowa warstwa danych miasta wymaga wniosku o ponowne wykorzystywanie (decyzja właściciela) — do tego czasu strażnik blokuje.
- Nowy wiersz tabeli zbiorczej z atrybucją w buildzie bez wpisu w `attribution_requirements.json` = czerwony test (pytest i .NET).

## Weryfikacja
- `uv run --project tools/licenses pytest tools/licenses/tests -q` — 27 passed (przed: 1 failed, audyt 360 bez wpisu).
- `dotnet test tools/about-runner/Tests/AboutTests.csproj` — 30/30 (przed: 21).
- `dotnet test tools/physics-runner` — 277/277 (bez zmian w physics-runner).
- NIEuruchomione (brak Unity w chmurze): EditMode `Game.Tests.AttributionDocumentTests` (nowe przypadki), PlayMode WorldC
  (zmienione tylko komentarze/komunikat), build APK i podgląd ekranu „Informacje” na telefonie.

## Otwarte
- Treść zarządzenia 973/21 Prezydenta Miasta Białegostoku (nie pobrana) i to, czy ArcGIS Online to „inna oficjalna strona
  internetowa Miasta” — `UNVERIFIED`; `dane.gov.pl` nieosiągalny z chmury (503 / reset połączenia).
- KartaView: regulamin `kartaview.org/terms` nieczytelny bez przeglądarki — CC BY-SA 4.0 tylko ze źródła wtórnego.
- Mapillary §12 (dozwolone cele komercyjne) i BDL cz. V lit. b („w pierwotnie pozyskanej formie”) — `LEGAL_REVIEW_REQUIRED`.
- GUGiK LoD1/LoD2: strony Geoportalu z 2026-11-15 mówią „dowolne wykorzystanie” bez nazwy licencji; atrybucja CC BY 4.0 zostaje.
