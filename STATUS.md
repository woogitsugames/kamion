# STATUS test-hygiene-s24

- 18.11 krok 1: przyczyny ustalone; poprawki: CarPaint (Ignore bez zestawu car_grime_clean spoza gita), LightPost (Ignore bez zaimportowanego regionu C), repin-generated-guids.ps1 + wywołanie w new-agent-worktree.ps1 (naczepa w main ma cac16030...), test_ec_chimneys UTF-8 (cp1250 na Windows), test_world_roads fixture cofa zapisy build() (w tym cache far-field w main przez junction).
- NASTĘPNY KROK: `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64` w worktree (Library z win-build skopiowana).
- 22:50 EditMode r1 (świeży worktree): 1387 / 1266 pass / 5 fail / 111 skip; 4 cele OK, 5 nowych porażek = brak prefabu TRAKT (Mirror x2, DoorCrown x3) -> Ignore z komendą budowy.
- NASTĘPNY KROK: EditMode r2 (artifacts/run-editmode.ps1 z r2)
