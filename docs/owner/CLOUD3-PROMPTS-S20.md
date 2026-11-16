# Prompty dla dwóch sesji Claude Code w chmurze (po 2 agentów Opus, tylko GitHub) — s20

Każda sesja dostaje osobny blok. Obie: repo woogitsugames/kamion, brak Unity/telefonów/Data/raw. Zadania nie dublują pracy lokalnej (agenci 0199–0202, Argon) ani research (Mistral, chmury #1/#2, GPT).

## SESJA X — wklej:
```
Repo GitHub woogitsugames/kamion (Kamion — mobilny symulator ciężarówki, Białystok 1:1). Nie masz Unity, telefonów ani Data/raw. Masz 2 agentów Opus. Najpierw przeczytaj CLAUDE.md, docs/owner/AGENT-RULES.md, docs/06, HANDOVER.md (blok „SESJA 20”). Lider (inna sesja) jest jedynym integratorem main — Ty pracujesz na gałęziach i otwierasz PR, nie scalasz.

X1 — audyt licencji i atrybucji (gałąź docs/licenses-audit-s20): docs/LICENSES.md ma obejmować KAŻDE źródło danych/zasobu używane w repo i grze. Przejdź: research/** (manifesty/sources.md — licencje: Wikimedia Commons CC0/CC BY/CC BY-SA, KartaView CC BY-SA, Mapillary CC BY-SA, Panoramax, OSM ODbL, GUGiK, BDL — Bank Danych o Lasach, IMGW, Dz.U./ISAP, UNECE), art-source/** (teksty licencji, *.json meta), Data/SourceManifests/**, game/Assets/**/LICENSE*, docs/adr (wzmianki o źródłach). Wynik: uzupełniony docs/LICENSES.md (tabela: źródło, licencja, wymagana atrybucja, gdzie użyte w grze/pipeline, czy trafia do buildu), plik docs/reports/LICENSES-AUDIT-S20.md z brakami i ryzykami (np. CC BY-SA w buildzie = obowiązek share-alike? oceń, cytując licencję), lista atrybucji do ekranu „Informacje” w grze (docs/owner/ATTRIBUTION-SCREEN-DRAFT.md). Nie zmieniaj kodu.

X2 — przegląd marek i logo (gałąź docs/brand-sweep-s20): CLAUDE.md zasada 8: bez cudzych marek, logo, nagrań producentów w grze. Przeszukaj CAŁE repo poza research/** (tam cytaty są dozwolone) i poza plikami pojazdu, które poprawia lokalny agent 0201 (game/**/Vehicle/**/*.json gearbox/engine/vehicle, tools/physics-runner/Tests/*, DrivingLabSceneBuilder.cs, ContactShadowCaster.cs): tools/worldgen/**, Data/Regions/**/overrides.yaml i *.json (nazwy firm/sklepów jako treść znaków/szyldów w grze!), art-source/**, game/Assets/** (teksty, nazwy materiałów, prefabów, napisy na tablicach). Wynik: docs/reports/BRAND-SWEEP-S20.md (plik:linia, co, czy trafia do buildu/na ekran, proponowana neutralna nazwa). Zmieniaj sam tylko oczywiste przypadki w komentarzach i dokumentacji poza research/; kod/dane/assety — tylko raport (lider zdecyduje). PR.

Zasady: commit + push po każdym kroku; bez zmyślania; nagłówki HTTP bez nazwy projektu; stopka commitów zgodna z modelem. Na końcu PR (bez scalania) i krótkie podsumowanie.
```

## SESJA Y — wklej:
```
Repo GitHub woogitsugames/kamion (Kamion — mobilny symulator ciężarówki, Białystok 1:1). Nie masz Unity, telefonów ani Data/raw. Masz 2 agentów Opus. Najpierw przeczytaj CLAUDE.md, docs/03 (etapy i bramki), docs/owner/AGENT-RULES.md, HANDOVER.md (blok „SESJA 20”). Lider (inna sesja) jest jedynym integratorem main — Ty pracujesz na gałęziach i otwierasz PR, nie scalasz.

Y1 — jeden backlog z otwartych punktów (gałąź docs/backlog-s21): przejdź WSZYSTKIE docs/reports/REVIEW-*.md (od s15 do s20), sekcje „Otwarte” we wszystkich docs/adr/*.md oraz HANDOVER.md (follow-upy s19–s20). Zbuduj docs/owner/BACKLOG-S21.md: tabela (id, obszar: świat C / Dojlidy / ciężarówka / fizyka / rendering / audio / UI / perf / research, opis 1 zdanie, źródło plik:sekcja, priorytet P0/P1/P2 z recenzji, status: otwarte / w toku (gałąź) / prawdopodobnie zamknięte (dowód), szacunek wielkości S/M/L). Deduplikuj (ten sam problem w kilku recenzjach = jeden wiersz z wieloma źródłami). Na końcu: top 15 do następnej sesji z uzasadnieniem (wpływ na bramki, rozpoznawalność, wydajność A16). Nie zmieniaj kodu.

Y2 — stan bramek i Definition of Done (gałąź docs/gates-status-s20): na podstawie docs/03, docs/reports/GATE-1.md, GATE-2.md, GATE-3.md, GATE12-PHONE-2026-11-14-A16.md, REVIEW-2026-11-14-s20-gate3-phone.md, docs/PERFORMANCE_BUDGETS.md i ADR-ów — dokument docs/reports/GATES-STATUS-S20.md: dla każdej bramki (1–3 i kolejnej) lista kryteriów, stan (spełnione z dowodem: plik/liczba / niespełnione / niezmierzone), co blokuje zamknięcie, dokładne komendy pomiarów (scripts/*.ps1) do uruchomienia przez lidera; osobno: lista decyzji właściciela potrzebnych do zamknięcia (np. metryka „≤ 12 klatek > 40 ms”, S24+ High 60 FPS nieosiągalne — GPU p50 ~23 ms). Sprawdź spójność liczb między dokumentami i wypisz rozbieżności. Nie zmieniaj kodu.

Zasady: commit + push po każdym kroku; bez zmyślania (każde twierdzenie z odnośnikiem plik:linia); stopka commitów zgodna z modelem. Na końcu PR (bez scalania) i krótkie podsumowanie.
```
