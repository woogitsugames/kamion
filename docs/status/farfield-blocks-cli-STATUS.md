# STATUS farfield-blocks-cli — s24

- Naprawiono własność budynków far-field (bbox wszystkich zarejestrowanych kafli + ≥400 m od tras, raw i po kompresji), dachy Low/High oraz palety materiałów.
- Runtime rezerwuje sektory od Register, niezależnie od Ready/Unloading; dodano testy EditMode. Review innego agenta wykonany; audyt źródłowy/maski poprawione po uwagach.
- Końcowo: pytest 85 PASS/1 SKIP (brak raw cache), runner .NET 35/35 PASS, w tym 5 nowych przypadków EditMode ze wspólnych źródeł; review runtime bez blokera. Logi/XML/TRX: `artifacts/farfield-blocks-cli/`. Unity i build_world nieuruchamiane, bez push.
- Obejrzano owner-01 i t1200/t1210; log nie potwierdza Ready między t1200/t1210 (dk65-05 Ready dopiero ok. DIAG t1310). Dokładny wyzwalacz tej klatki UNVERIFIED; filtr usuwa możliwość takich proxy w korytarzu.
- Raport: `docs/reports/farfield-blocks-cli-s24.md`; ADR 0311. Wszystkie zmiany i dowody wyłącznie w tym worktree.
- NASTĘPNY KROK (lider, osobna sesja z regeneracją/Unity): `uv run --project tools/worldgen python tools/worldgen/streetscape/far_field.py --region dk65-04`, potem import Low/High i próba Windows według raportu; pełna aktualizacja obejmuje 49 kafli.
