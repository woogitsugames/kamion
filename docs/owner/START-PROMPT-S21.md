# Prompt startowy — sesja 21 (przejęcie po s20)

Kontynuujesz projekt Kamion (Unity 6000.3.28f1 URP, Białystok 1:1) w `C:\Users\matma\Documents\Claude\kamion`. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion.

**Przeczytaj:** `HANDOVER.md` — blok „SESJA 20” (wpisy chronologicznie od góry bloku w dół; NAJNOWSZE są tuż nad linią „Ostatni przydzielony ADR: 0198”), `CLAUDE.md`, `docs/owner/AGENT-RULES.md`, `docs/owner/S20-AGENT-PREAMBLE.md`, `docs/owner/S20-PR-REVIEW-BRIEF.md`.

**Zasady właściciela (s20):** maks. 4 agentów naraz (Fable/Opus); nie wznawiaj skończonych/przerwanych agentów bez zgody; nie zabijaj działających; crony :07/:17/:47 (sesyjne — po restarcie aplikacji załóż od nowa; sprawdź CronList, nie dubluj). ≥ 85 % 5 h: nowi agenci tylko gdy działa < 2. Godziny resetu podawaj w czasie Brukseli.

**Kto co robi poza Tobą (stan 14.11 wieczór):**
- **Argon (Antigravity, lokalnie)** — gałęzie 0194, 0188, 0193, 0187, 0186, 0189 (`docs/owner/ARGON-PROMPT-S20.md`, wejście `docs/reports/ARGON-INPUT-S20.md`); raporty `docs/reports/ARGON-S20-*.md`, recenzje `REVIEW-ARGON-*.md`. Ty ich NIE wznawiasz; scalasz po przeglądzie.
- **Sesja kodu (2× Opus)** — ADR 0197 lights-0197 i 0198 piers-0198 (`docs/owner/CODE-SESSION-PROMPT-S20.md`, raporty `docs/reports/CODE-S20-*.md`) — jeśli właściciel zlecił.
- **Mistral** — do wklejenia `docs/owner/MISTRAL-FIXES-12.md` (aktualne bloki: M57, M59, M60*, M61); `MISTRAL-DOKONCZ-S20.md`; #57 M60 zamknąć/zawęzić; M63 w toku.
- **Chmura #1** (M58/M60/M65/M66/M68 — scalone poza M68 w przeglądzie), **chmura #2** (R1–R9: scalone R1/R3/R5/R7/R8; R9 FIX; R2/R4/R6 drafty do dokończenia — blok na końcu `CLOUD2-PROMPT-S20.md`), **GPT Chrome** (`research/_incoming/gpt-s20-*`: G3, M67, M69, M64).

**Następne kroki lidera:**
1. A16 offline w adb (od 19:43) — właściciel: odłączyć/podłączyć USB. Potem gate3 G3-B na APK `kamion-0.1.0-edb5524993.apk` (komenda w HANDOVER).
2. Przeglądy PR (brief) i raportów Argona/sesji kodu → scalenia → JEDNA regeneracja C + Dojlid → trucks/NightWindows → EditMode → APK → A16 gate3 + zrzuty.
3. Follow-upy gry zebrane w HANDOVER (s20): kalibracja zmierzchu/nocy (M60), światła R148 (0197), podpory Putry (0198), ściana NW wieżowca (M57), fizyka R3 (promień opony, naciski, marki w JSON), U-12b słupki (M58), pas Krywlany (M58), zieleń znaków (R1, ADR), A/B `androidBlitType` (R8), płot alpha-to-coverage (0185).

**Ostatni przydzielony ADR: 0198.**
