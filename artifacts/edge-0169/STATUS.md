# edge-0169 STATUS (ADR 0169)
- Done: one closure list (`WorldEdgeBuilder.ResolveClosures`), Python copy removed, duplicate tests, sign colours, navgraph `dead_ends.py`, ADR, pairs.
- Numbers: 36 -> 34 closures, 8060 -> 7754 tris, draws +0 on 6 cameras; EditMode 500/497/2 known/1 skipped; PlayMode WorldEdgeRecoveryTests 3/3; pytest 82 passed 1 xfailed.
- Open: visual-critic review; U-20 dimensions UNVERIFIED; 30 no-return edges of the route graph not fixed (proposal in the ADR); phone not measured.
- NEXT: leader: `git merge edge-0169`, then `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c -SkipCopy` (or RebuildEdgeBatch) and `python tools/docs/adr_index.py`.
