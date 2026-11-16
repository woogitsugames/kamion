# Zlecenie dla sesji w CHMURZE: recenzja kodu oddanych PR (do 8 agentów Opus), s21, 15.11 wieczór

Wklej:
```
Repo GitHub woogitsugames/kamion (Kamion: mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1 → DK65 → Knyszyn). Jesteś w chmurze: bez Unity, telefonów i Data/raw. Rola: NIEZALEŻNY RECENZENT kodu (Opus, jeden agent na PR). Nie piszesz nowych funkcji i NIE scalasz. Lider lokalny zbuduje świat, wyrenderuje i scali na podstawie Twoich raportów.

NAJPIERW (każdy agent): `git fetch origin`, przeczytaj CLAUDE.md, docs/owner/AGENT-RULES.md, docs/owner/S20-PR-REVIEW-BRIEF.md, HANDOVER.md (blok „SESJA 21” na dole), docs/11_DECYZJE_WLASCICIELA.md (D63–D69), docs/PERFORMANCE_BUDGETS.md, ADR danego PR i ADR, na których się opiera.

PR do recenzji (jeden agent na pozycję):
R1 #98 dk65-k1-0220 (ADR 0220, przekrój K1 w dk65-01…05);
R2 #106 seams-0224 (ADR 0224, narzędzie szwów + override tykocin) — razem z #98 i #80;
R3 #101 treerows-0222 (ADR 0222, szpalery);
R4 #102 rail-dk65-0223 (ADR 0223, linia 38) — razem z #96 rail-0217 i gałęzią rail-fix-s21, jeśli jest na origin;
R5 #97 roundabout-0218 (ADR 0218, rondo Knyszyn) — porównaj z opisem ronda DK65×Tykocka w docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md (zdjęcia właściciela);
R6 #93 putry-ring-0198b (ADR 0226) — razem z #82 piers-0198 (ADR 0198): dublują się czy uzupełniają;
R7 #104 region-select-0229 (ADR 0229, wybór regionów w buildzie i menu) — kluczowy dla następnego APK (D67: korytarz, APK ≤ 2 GB);
R8 #103 legal-0230 (ADR 0230, licencje i atrybucje).

DLA KAŻDEGO PR:
1. Przeczytaj cały diff. Szukaj błędów poprawności (logika, przypadki brzegowe, jednostki, osie X=wschód/Y=góra/Z=północ, CRS), naruszeń zasad z CLAUDE.md (zero GC w pętli jazdy, fizyka w stałym kroku, „nie zmyślaj” — liczby SOURCED/ESTIMATED/WORKING_VALUE, brak marek, legalność źródeł), zmian poza zakresem, zmian w ProjectSettings/Packages/asmdef/wspólnych scenach.
2. Uruchom testy możliwe bez Unity: `uv run --project tools/worldgen python -m pytest tests/gis -k <związane>` oraz pełne `tests/gis` (znany fail bez Data/raw: `test_road_fidelity::test_report_not_stale` — pomiń), `dotnet test` dla projektów .NET, których PR dotyka. Porównaj z origin/main (czy PR coś psuje).
3. Konflikty i kolejność scalania: `git merge-tree` z origin/main i z innymi PR z listy, które dotykają tych samych plików (szczególnie #98/#106/#80, #96/#102, #82/#93, #104 z resztą). Zaproponuj kolejność scalania całej listy.
4. Budżet: oszacuj wpływ na tris/draws/instancje per kamera (generated/streetscape_qa.json, frame_estimate) — region C jest na granicy 2 mln tris High.
5. Raport `docs/reports/REVIEW-2026-11-15-s21-code-<nr>.md` na gałęzi `reviews-code-s21` (jedna gałąź, push po każdym raporcie): werdykt **SCAL / FIX / ZAMKNIJ**, lista FIX z plikiem:linią i propozycją poprawki, wyniki testów, ryzyka, DOKŁADNE komendy dla lidera (build_world/import/visual-qa z nazwami kamer do obejrzenia, EditMode, pomiar A16). Werdykt także jako `gh pr comment <nr>`.
Na koniec jeden PR (nie draft) `reviews-code-s21` → main z tabelą: PR | werdykt | najważniejszy FIX | proponowana kolejność scalania. NIE scalaj niczego.

ZASADY: bez Google Maps, Street View, Earth i 3D Tiles; nagłówki HTTP bez nazwy projektu; stopka commitów zgodna z modelem; nie zmyślaj liczb.
```
