# lights-0197 (ADR 0197) live — chmura, bez Unity/Blendera; gałąź lights-0197 (origin)
- 2026-11-15 krok 1 (229c1fddc): LampPhotometry.cs (czysty C#), limiter z odniesieniem (alfa stanu, BrakeNits dla 6/10/16/17),
  tekstura stanu 32×1, grupy naczepy TAIL 16 / STOP 17 w eksporterach, bursztyn (1, 0.22, 0), _PlateIllum 0,006.
  `dotnet test tools/lamp-check` 185/185. Stop:pozycyjne po limiterze 15,4:1 (było 1,015:1 przy E 1e-2).
- Krok 2: ADR 0197 (PROPOSED), poprawki tekstu ADR 0178 pkt 2 i ADR 0181 (R4 → R148 5.11.3 SOURCED).
- Ustalenie: obszar bursztynu R48 leży POZA sRGB (granica bieli y ≥ 0,790 − 0,670x) — recenzja M59 G3 się myliła;
  (1, 0.22, 0) = najbliższy punkt z zapasem do granicy zieleni (0,0159 xy od obszaru; minimum 0,0153 przy g 0,24).
- NASTĘPNY KROK (lider, Windows): komendy z artifacts/lights-0197/PR-BODY.md (Blender trailer_export → BuildBatch ×3 → visual-qa → EditMode)
- KONIEC sesji chmurowej: sha w raporcie; NASTĘPNY KROK jako komenda: `dotnet test tools/lamp-check` (sprawdzenie) → komendy lidera z PR-BODY.md.
