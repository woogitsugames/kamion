# klattow-fix-cli — 2026-11-19

Zakończono P2/P3: ograniczenie wymiarów korpusu i ganku, kontrola otworów z marginesem,
powrót do domu z reguły dla niezgodnego obrysu; płot W/E 2,6 / 4,5 m zgodnie z ADR 0305.
Testy rozszerzono o granice wymiarów, położenie otworów, odrzucanie obrysu i długości płotu.

Walidacja: `uv run --project tools/worldgen pytest tests/gis/test_dom_klattow_0305.py -q`
— 25 passed, 1 skipped (brak wygenerowanej tekstury log_whitewash), 6,87 s.
`git diff --check` bez błędów. Przegląd własny; bez niezależnego review agenta.

Zgodnie z zakresem: nie uruchamiano Unity ani build_world, nie zmieniano Data/raw.
Nie zweryfikowano renderów, buildu Windows/Android, wydajności ani kolizji wydłużonego
płotu z płotem działki w wygenerowanym świecie. Dotychczasowe pomiary w ADR są historyczne.

Następny krok po przekazaniu: `git show --stat HEAD` — przegląd lokalnego commita; bez push.
