# STATUS test-hygiene-s24

- 18.11 krok 1: przyczyny ustalone; poprawki: CarPaint (Ignore bez zestawu car_grime_clean spoza gita), LightPost (Ignore bez zaimportowanego regionu C), repin-generated-guids.ps1 + wywołanie w new-agent-worktree.ps1 (naczepa w main ma cac16030...), test_ec_chimneys UTF-8 (cp1250 na Windows), test_world_roads fixture cofa zapisy build() (w tym cache far-field w main przez junction).
- NASTĘPNY KROK: `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64` w worktree (Library z win-build skopiowana).
- 22:50 EditMode r1 (świeży worktree): 1387 / 1266 pass / 5 fail / 111 skip; 4 cele OK, 5 nowych porażek = brak prefabu TRAKT (Mirror x2, DoorCrown x3) -> Ignore z komendą budowy.
- NASTĘPNY KROK: EditMode r2 (artifacts/run-editmode.ps1 z r2)
- 23:05 EditMode r2: 1387 / 1265 pass / 0 fail / 117 skip, ale Unity exit 2: 5 x Inconclusive (Assume.That na brak TRAKT) -> Assert.Ignore (EditMode+PlayMode); test.ps1 pokazuje Inconclusive i exit Unity.
- NASTĘPNY KROK: EditMode r3
- 23:10 EditMode r3 (świeży worktree): 1387 / 1265 pass / 0 fail / 0 inconclusive / 122 skip, Unity exit 0. r4 z danymi (TRAKT zbudowany, car_grime_clean Medium): 36/36 pass w 7 dotkniętych klasach (ArtPrefabs z naczepą przepiętą skryptem). Dowody: artifacts/test-hygiene-s24/ (main).
- KONIEC. Lider: scalić; na main jednorazowo `pwsh scripts/repin-generated-guids.ps1` (naczepa cac16030 -> ab5e5ba6) gdy żaden Unity nie ma main otwartego.
