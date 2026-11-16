# Zlecenie dla sesji „P” (Claude Pro) — runda 8 (s23, 16.11 wieczór) — do 3 agentów, MODEL: Opus

Wklej do sesji P:
```
Runda 8. Zasady jak dotąd (bez Unity, telefonów i Data/raw; do 3 agentów, Opus; każdy na swojej gałęzi z origin/main; NIE scalasz; raport ≤ 15 linii z komendami i „Gotowe do scalenia po weryfikacji lidera: TAK/NIE”). Runda 7 scalona do main (JAK-GRAC-PC, research D3D12, START-PROMPT-S24) — dziękuję. Nie dotykaj: generated/*, tools/worldgen/*, Data/Regions/*, game/** (to są recenzje i dokumenty).

P22 recenzja kodu PR #169 (rynek-p1-s23, D41 Rynek Knyszyna P1) — gałąź review-169-s23, plik docs/reports/REVIEW-2026-11-16-pr169.md: poprawność (przypadki brzegowe, jednostki, deterministyczność), czy testy coś sprawdzają, zgodność z ADR 0227 i zasadami CLAUDE.md (WORKING_VALUE/UNVERIFIED, zero Google, bez marek), ryzyka przy przebudowie Knyszyna. Lista uwag P1/P2 z plik:linia.
P23 recenzja kodu PR #168 (stream-desktop-s23, D44 budżet streamingu z tieru PC) — gałąź review-168-s23, docs/reports/REVIEW-2026-11-16-pr168.md: jak wybierany jest tier i budżet pamięci na desktopie, czy telefon (Android) zachowuje stare budżety, alokacje GC w pętli, test EditMode.
P24 szkic ADR „D3D11 jako domyślne API grafiki na Windows” — gałąź adr-d3d11-draft, docs/adr/DRAFT-d3d11-default.md (bez numeru — numer nada lider): na podstawie docs/reports/RESEARCH-2026-11-16-d3d12-device-removed.md: kontekst, opcje (D3D12 domyślnie / D3D11 domyślnie / D3D11 + przełącznik w menu), koszty (funkcje URP niedostępne na D3D11 w Unity 6000.3 — cytuj dokumentację z datą), kryteria pomiaru (pc-metrics obu API), plan wycofania. Status: Proposed.
Na końcu podsumowanie.
```
