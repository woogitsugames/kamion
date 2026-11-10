# ARGON-TASK-01-WORLD-EDGE Status
- Branch: `argon-edge`
- Worktree: `.claude/worktrees/argon-edge`
- Last completed step: Step 1 — Added 4 edge-looking control cameras (`edge-north`, `edge-east`, `edge-west`, `edge-south`), imported `bialystok-industrial-c`, and captured `r0-before` baseline renders (`Low-clear`, `Low-overcast`, `High-clear`, `High-overcast`) + inspected all frames at <= 960 px.
  - `r0-before` baseline stats (`Low-clear`):
    - `edge-north`: `objects=10 drawsEst=43 shadowDrawsEst=21 trisK=59`
    - `edge-east`: `objects=9 drawsEst=46 shadowDrawsEst=18 trisK=63`
    - `edge-south`: `objects=14 drawsEst=114 shadowDrawsEst=69 trisK=124`
    - `edge-west`: `objects=13 drawsEst=46 shadowDrawsEst=15 trisK=70`
    - `dk8-dk19-exit`: `objects=23 drawsEst=77 shadowDrawsEst=2 trisK=106`
  - `r0-before` baseline critique (`docs/06_GRAFIKA_ANTI_AI_SLOP.md`):
    - `edge-north`: Forest ends with a knife-cut at `N=1024 m`; straight ahead past the U-20 barrier and in `dk8-dk19-exit` is a bright empty grass horizon.
    - `edge-east`: Beyond the 4-storey office building and fence at `E=1024 m`, the horizon is a flat uniform green prairie with zero buildings, trees, chimneys, or pylons.
    - `edge-west`: Beyond `E=-1024 m`, 4 road stubs on Maczka/slip roads protrude as 4.5 m tall grey ramps above the dropping apron, with a completely bare green horizon where Zawady/Dziesięciny blocks, halls, power lines, and forests should be.
    - `edge-south`: Beyond `N=-1024 m` (towards Białostoczek / Centrum / EC Białystok), the entire urban skyline and chimneys are missing — just flat green lawn.
- Next step (ready command):
  `uv run --project tools/worldgen python tools/worldgen/streetscape/far_field.py --region bialystok-industrial-c`
