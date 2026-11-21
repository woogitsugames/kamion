# seam-knw-s24 — STATUS

## 2026-11-21 krok 1
- Worktree gotowy (-CopyDerived), oba kafle zbudowane 21.11 00:52/00:59 (regen-wave-2).
- seams.py knyszyn|knyszyn-w: 1 FAIL (w300808749 service, oś 0,25 m); secondary w1478765548 (W wlot DW671) wg derived:network 11,75/11,75, oś identyczna — ale knyszyn 2x5,62 vs knyszyn-w 3x3,75 (UWAGA, kikut 6,7 m). Render pokazuje przesunięcie ⇒ siatka ≠ derived:network.
- NASTĘPNY KROK: pomiar przekroju GLB na szwie: `uv run --project tools/worldgen python -m tools.worldgen.qa.seam_section --help`
