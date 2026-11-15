# streaming-0235 (zamknięty PR #114) — FIX s22 D12 (ADR 0273)
- Merge origin/main + regionpacks-0234. Opt-in `stream=1`; przypięty kafel odrodzenia; budżety PC (640/800/1450/2000 MB) + `worldMemoryHighMB`; `ITileSceneSource` (build albo paczka, dzierżawy); `scripts/stream-report.py`.
- Testy: pytest tile_graph + stream_report 10/10; EditMode polityki 24/25 pod .NET 8 (Decide_AllocatesNothing: 24 B artefakt runtime .NET, 0 B per wywołanie). Nieskompilowane w Unity.
- NASTĘPNY KROK (lider, po scaleniu #112): nowy PR z `streaming-0235` → main; `pwsh scripts/test.ps1 -Platform EditMode`.
