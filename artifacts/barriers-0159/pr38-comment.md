Recenzja M30 (agent świata, ADR 0159, gałąź `barriers-0159`). PR nie jest scalany na GitHubie — zmiana weszła przez `git merge origin/mistral/30-fence-drive-panel` do gałęzi `barriers-0159` i trafi do main z integracją lidera.

**Werdykt: przyjęte z jedną poprawką.**

1. **Reguła ogólna, nie wyjątek** — tak. W `layout()` nie ma identyfikatora działki ani współrzędnych; kryterium to długość przebiegu (< `STUB_M`) i odchylenie od obu osi ramki działki (> `SKEW_DROP_DEG`), z wyjątkiem przęsła zakotwiczonego w słupku bramy. Stała opisana jako WORKING_VALUE z uzasadnieniem.
2. **Mutacja** — po wyłączeniu reguły (`SKEW_DROP_DEG = 180`) `test_skewed_corner_tooth_is_dropped_but_a_long_diagonal_boundary_stays` pada (asercja `stubs_dropped >= 2`), po przywróceniu przechodzi. Test regionowy liczy panele > 15° na danych repo (43 przed regułą), więc także pada bez reguły.
3. **Znaleziona wada (poprawiona w `barriers-0159`)**: ząb połączony z obu stron był usuwany bez zastępstwa, więc w linii ogrodzenia zostawała dziura — w teście syntetycznym 2 m między (20, 10) a (20, 12), przy r16_drive_3 dwa panele 1,14 m + 0,76 m. Dotyczy to też zębów na froncie (warunek skosu stoi przed `if r["front"]`, więc front nie jest już chroniony). Poprawka: usunięte zęby, które się stykają, są łączone w łańcuch i zastępowane cięciwą, jeśli cięciwa leży wzdłuż osi ramki (≤ `SKEW_DROP_DEG`), ma 0,6 m … 2 × `STUB_M` i oba jej końce trafiają w przebieg, który zostaje (`teeth_bridged` w wyniku `layout()`). Test syntetyczny sprawdza, że w miejscu zęba stoi jeden prosty panel.
4. **Test regionowy**: `diag == 7` zamienione na `diag <= 7` — dokładna liczba zmienia się z każdą zmianą danych regionu; asercja „każdy panel > 15° jest długi albo frontowy” zostaje bez zmian.
5. Uwaga do opisu PR: liczby 621 → 583 i 43 → 7 są z planu na płaskiej wysokości syntetycznej (bez regeneracji świata) — to poprawnie zaznaczono; po regeneracji w `barriers-0159` kadr `r16_drive_3` został obejrzany w renderze (wynik w `docs/adr/0159-*.md`).

Szczegóły i liczby po regeneracji: `docs/adr/0159-barriers-screens-putry-andersa.md`, sekcja „PR #38”.
