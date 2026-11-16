# Zlecenie dla sesji „P” (Claude Pro) — runda 2 (s23, 16.11) — do 3 agentów, Fable dozwolony

Wklej do sesji P:
```
Runda 2. Zasady jak w rundzie 1 (bez Unity, telefonów i Data/raw; do 3 agentów naraz, każdy na swojej gałęzi z origin/main; NIE scalasz; bez nowych ADR, chyba że niżej podano numer; raport ≤ 15 linii po polsku z dokładnymi komendami dla lidera i „Gotowe do scalenia po weryfikacji lidera: TAK/NIE”). Runda 1 scalona do main (docs-windows-s23, pr-triage-s23, licenses-s23) — dziękuję. Możesz użyć Fable do zadań kodowych. Najpierw: CLAUDE.md, HANDOVER.md (SESJA 23), docs/reports/PR-TRIAGE-2026-11-16-s23.md (Twój triage). Nie dotykaj: generated/*, tools/worldgen/roads/*, rail, Data/Regions/knyszyn, PcTierTable (świeżo zmienione), PR chmur D/H (#113 #115 #117 #118 #119 — są w pracy).

P4 #92 research/mistral-p16-truck-lamps-fix-s21 — FIX wg Twojego triage (plan B: checkout katalogu + oznaczenia UNVERIFIED): merge origin/main do gałęzi PR, popraw wskazane problemy, komentarz w PR z wynikiem. Materiały producentów lamp tylko badawczo — bez marek w grze i w nazwach zasobów.
P5 #116 g3-poses-0246 — FIX wg triage: zrzuty par zdjęciowych G3 (42 pozy) z PLAYERA Windows zamiast telefonu (D73) — tryb `-Exe` w skrypcie: uruchamia `artifacts/win/<build>/Kamion.exe` z argumentami pozy (`-scene`, `-route_s`, kamera, `-shot`, `-quit_t`; zobacz `DesktopAutoShot` i ADR 0261/0266), zbiera PNG i log, nie wymaga adb. Telefonowy tryb zostaje jako odroczony. Testy skryptu (pytest/pwsh bez Unity), komentarz w PR z komendą dla lidera.
P6 #112 regionpacks-0234 po D73 — tylko analiza (gałąź analysis-regionpacks-s23, raport docs/reports/ANALYSIS-2026-11-16-regionpacks-pc.md): czy osobne paczki regionów (AssetBundles) mają sens na PC (dystrybucja zip ADR 0271, rozmiar buildu 21 regionów ~4,9 GB, przyszłe DLC krajów z docs/10), czy wystarczy streaming kafli; porównaj z zamkniętym #114 streaming-0235 i recenzją #112; rekomendacja: scalić / przerobić / zamknąć, z kosztami i ryzykami. Bez zmian w kodzie.
Na końcu podsumowanie z numerami PR.
```
