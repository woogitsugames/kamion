# ADR 0271 — dystrybucja PC: paczka zip, itch.io najpierw, Steam później, bez podpisu kodu na start
Status: Proposed (chmura H r2, zadanie H9, gałąź `pc-dist-0271`), 2026-11-15. Do weryfikacji i scalenia przez lidera.
Powiązane: ADR 0260 (D73), ADR 0261 (build Windows), D74 (wymagania), ADR 0230 (atrybucje, R-P0-2), D8 (Suno), docs/12.

## Kontekst
Windows jest platformą główną (D73), istnieje build `scripts/build-windows.ps1` (ADR 0261), ale nie ma ustalonej
drogi „folder buildu → plik dla testera / sklepu”: co z folderu wolno wydać, w jakiej formie, z jakimi licencjami,
jak testerzy oddają logi, gdzie wydawać przy budżecie 0 zł. Szczegóły i źródła (dostęp 2026-11-15): `docs/12_DYSTRYBUCJA_PC.md`.

## Decyzja
1. **Forma: zip** `kamion-<ver>-<sha>[-low][-dev][-dirty]-win64.zip` + `.sha256` + `.json` (lista plików z SHA256),
   tworzony przez `scripts/package-windows.py` (stdlib) z folderu `artifacts/win/kamion-<ver>-<sha>…`. Wersja i sha
   z `build.json` (ADR 0261) albo nazwy folderu. Zip powtarzalny (posortowane wpisy, stała data i uprawnienia).
2. **Wykluczenia**: `*_BurstDebugInformation_DoNotShip/`, `*_BackUpThisFolder_ButDontShipItWithYourGame/`, `*.pdb`,
   metadane buildu (`build.json`, `Kamion.exe.sha256`, `Kamion.content.json`, `.top.txt`, `.variants.txt`), skrót
   deweloperski `Kamion-knyszyn.cmd`. Build dev (`WinPixEventRuntime.dll` / `-dev`) i brudny checkout — odmowa bez
   `--allow-dev` / `--allow-dirty`.
3. **Dodatki w paczce**: `THIRD_PARTY_NOTICES.txt` generowany z `UI/Resources/About/attributions.txt` (jedno źródło z
   ekranem „Informacje”, linie `#` pomijane, `@include` rozwijane), `README.txt` z `dist/windows/README.txt.in`
   (wymagania D74 oznaczone WORKING_VALUE, start, SmartScreen, ścieżki logów), `SHA256SUMS.txt`,
   `collect-logs.ps1` + `Zbierz-logi.cmd`.
4. **Bramka licencyjna**: `--release` kończy się kodem 3, dopóki `attributions.txt` zawiera notkę R-P0-2 (oferta bazy
   pochodnej OSM, ODbL §4.6). Bez `--release` paczka jest „tylko dla testerów” (ostrzeżenie w wyjściu i w `.json`).
5. **Kanały**: najpierw itch.io (0 zł z góry, udział wybierany przez twórcę, domyślnie 10 %; butler MIT), Steam po
   decyzji właściciela (100 USD/aplikację, 21 dni, „coming soon” ≥ 2 tyg., Content Survey z ujawnieniem AI). GOG/Epic —
   notka, warunki `UNVERIFIED`.
6. **Bez podpisu kodu** na start (Microsoft: EV nie omija już SmartScreen; Artifact Signing od 9,99 USD/mies. —
   decyzja właściciela). README paczki uczy weryfikacji SHA256 i „Uruchom mimo to”.
7. **Instalator nie jest domyślny.** Szablon `dist/windows/kamion.iss` (Inno Setup, nieskompilowany): licencja pozwala
   na użycie komercyjne, ale autor od 6.5.0 prosi komercyjnych użytkowników o zakup licencji → użycie po decyzji
   właściciela. WiX odrzucony (MSI zbędne; OSMF powyżej 10 000 USD przychodu).
8. **Logi**: tester uruchamia `Zbierz-logi.cmd` → zip na Pulpicie z `Player.log`, `Player-prev.log`, `diag\`,
   5 najnowszymi zrzutami z `%TMP%\woogitsugames\Kamion\Crashes`, `system.txt`; nazwa użytkownika/komputera
   zamieniana na `<user>`/`<pc>`; nic nie jest wysyłane automatycznie. Unity Cloud Diagnostics — nie bez decyzji
   właściciela (dane graczy u Unity).
9. **Backend**: zostaje Mono (stan ADR 0261); IL2CPP dopiero po pomiarze A/B przed pierwszym wydaniem publicznym.
10. CI: job `dist-tests` (`uv run --no-project --with pytest pytest tests/dist -q`).

## Propozycje dla lidera (nie zmieniane w tym ADR — pliki poza zakresem)
- `build-windows.ps1`: zamiast kasować `*_DoNotShip`, przenosić je do `artifacts/win/symbols/<name>/` (symbole Burst
  do analizy zrzutów awarii danej wersji); `package-windows.py` i tak ich nie spakuje.
- `build-windows.ps1`: opcjonalny krok `-Package` wołający `package-windows.py` po udanym buildzie.
- ProjectSettings (lider/właściciel): ekran powitalny Unity (w Unity 6 Personal wolno wyłączyć), ikona, `fullscreenMode`,
  wpis batchingu Standalone (ADR 0261 „Otwarte”: etykieta `build_info` w playerze ma `-dirty`, choć nazwa folderu i
  `build.json` — z których czyta `package-windows.py` — biorą sha sprzed startu Unity, więc paczka nie jest blokowana).
- `CHANGELOG.md` (Keep a Changelog) i tagi `v<ver>` zakłada lider przy pierwszym wydaniu.
- CLAUDE.md, mapa dokumentów: dopisać „12 dystrybucja PC” i komendę paczki.

## Walidacja
- **Uruchomione**: `uv run --no-project --with pytest pytest tests/dist -q` → 14 passed (Linux, Python 3.13, sztuczny
  folder buildu: wykluczenia, `.sha256` = SHA256 zipu, `SHA256SUMS.txt`, powtarzalność bajt w bajt, odmowa dev/dirty,
  nazwa `-low`, brak exe/Data, zły sha, `--dry-run`, generowanie notices z prawdziwego `attributions.txt`,
  `--release` przy otwartym R-P0-2, README bez placeholderów i z wymaganiami D74). Ręczny przebieg na sztucznym buildzie:
  14 plików w zipie, R-P0-2 zgłoszony jako bloker.
- **Nieuruchomione**: paczka z prawdziwego buildu 4,9 GB (brak buildu i Windows w chmurze; zip64 dla plików > 4 GB
  włączony `force_zip64`, ale nieprzetestowany na dużych plikach), `collect-logs.ps1` (brak Windows/PowerShell),
  `kamion.iss` (brak Inno Setup), upload butler (brak konta — agenci nie zakładają kont).

## Otwarte
- R-P0-2 (właściciel) — bloker publicznego wydania; R-P1-3/4/5 (Unity pakiety, ElevenLabs SFX, Fab EULA) przed sprzedażą.
- Limit rozmiaru pliku na itch.io (liczba `UNVERIFIED`), stawka Valve, warunki GOG/Epic — `UNVERIFIED`.
- Pomiar wymagań D74 na sprzęcie klasy min/zalecanej; pomiar A/B Mono vs IL2CPP.
