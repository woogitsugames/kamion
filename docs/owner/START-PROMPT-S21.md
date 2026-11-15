# Prompt startowy — sesja 21 (przejęcie po s20, stan 15.11 ~19:00)

```
Kontynuujesz projekt Kamion (mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1) w C:\Users\matma\Documents\Claude\kamion. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion. Komunikacja po polsku.

PRZECZYTAJ NAJPIERW:
- HANDOVER.md, blok „SESJA 20”: wpisy idą chronologicznie, najnowsze są tuż nad linią „Ostatni przydzielony ADR: 0220”;
- CLAUDE.md;
- docs/owner/AGENT-RULES.md;
- docs/owner/S20-AGENT-PREAMBLE.md;
- docs/owner/S20-PR-REVIEW-BRIEF.md;
- docs/11_DECYZJE_WLASCICIELA.md (D63–D66).

ZASADY WŁAŚCICIELA:
- Agenci:
  - najwyżej 5 lokalnych agentów naraz; nowi na Fable, recenzje na Opusie;
  - nie zabijaj działających agentów; skończonych nie wznawiaj bez zgody;
  - agentom Fable każ ZAWSZE uruchamiać długie kroki w tle i od razu kończyć turę, bo watchdog zabija ich po 10 minutach bez postępu.
- Budzenie: załóż crony :07 (ZIP-y w Downloads), :17 (agenci i kolejka) i :47 (PR-y). Najpierw sprawdź CronList, żeby ich nie zdublować.
- Telefony: wolno ich używać. A16 to RFGL34SJYDZ. S24+ (RZCX60VE8ZY): bateria co najmniej 40 % na start, przerwij poniżej 30 %.
- Godziny podawaj w czasie Brukseli.
- Kierunek (D63/D64): najpierw z grubsza, potem detale; Białystok → DK65 → Knyszyn.
- Zakazy: Google Maps, Street View, Earth i 3D Tiles; marki i logo w grze. Zdjęcia właściciela tylko jako referencja: nie do gita i nie jako tekstury.

STAN:
- W regions.py jest 21 regionów: C, Dojlidy, maczka, kleeberga, knyszynska, dk65-01…11, knyszyn, knyszyn-s, knyszyn-w, dk65-monki-01, dw671-tykocin-01.
- Bramka 3 na A16, czysty APK af2570fccd: segmenty G3-A i G3-B ważne, w budżecie (docs/reports/GATE-3.md).
- Później scalono Argona 0188/0187/0189 i 0214. Po regen4 pytest gis ma 2 czerwone testy budżetu trójkątów High: stretch_04 ma 2,02 mln przy limicie 2 mln oraz test_world_v31. NAPRAW TO przed kolejnym APK i bramką.

AGENCI, KTÓRZY MOGLI JESZCZE DZIAŁAĆ (sprawdź artifacts/live/<nazwa>.md i gałęzie):
- tunnel-0211: tunel w kleeberga, r4;
- summer-led-0216: białe LED w Knyszynie;
- verify-cloud-b: #96 tory w Tykocinie; #90 i #95 mają werdykt SCAL, raporty w docs/reports/VERIFY-*;
- verify-cloud-c: #80 Ełcka i plac budowy, #82 podpory Putry.
Jeśli agent nie żyje, przejmij jego worktree nowym agentem (za zgodą właściciela).

NASTĘPNE KROKI LIDERA:
1. Scalić zweryfikowane PR chmur: #90, #95, #96 (#96 nie obsługuje warstw rail_* w imporcie Unity, więc to FIX), #80 (zmienić Ełcką z 6,9 na 6,6 m według D66; ujednolicić plac budowy na szwie dk65-05/06 z mechanizmem 0214), #82, #97 (rondo Knyszyn, po 0216). PR #79 (światła) wymaga renderów; #92 M59-FIX = FIX.
2. Przebudować dk65-06…11 na bieżącym main: `pwsh artifacts/dk65-tiles2-0214/tools/chain.ps1 -Tiles dk65-06,dk65-07,dk65-08,dk65-09,dk65-10,dk65-11 -Tag r4`. Poprawić szew 10/11 z knyszyn-s (przekrój K1).
3. Naprawić budżet trójkątów High, potem EditMode, nowy APK, gate3 na A16 i zrzuty z telefonu dla Argona 0188/0187/0189.
4. Kolejka D65: szlif Knyszyna według zdjęć (Rynek), torowisko wzdłuż DK65 (generator z #96), szpalery, ujednolicenie szwów DK65.
5. Inne sesje: chmura C ma prompt docs/owner/CLOUD-C-PROMPT-S20.md (ADR 0217–0220 zarezerwowane). Kolejne prompty dla chmur pisz do docs/owner/.
```
