param([Parameter(Mandatory)][ValidateSet('Main','Candidate')][string]$Mode)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$paths = @(
 'art-source/world/materials/_src/sets_facade.py',
 'art-source/world/materials/materials_spec.json',
 'game/Assets/_Project/Environment/Shaders/WorldPBR.shader',
 'game/Assets/_Project/Environment/Shaders/WorldCarPlate.shader',
 'game/Assets/_Project/Environment/Shaders/WorldCarPlate.shader.meta',
 'game/Assets/_Project/Tests/EditMode/CarPaintMaterialTests.cs',
 'game/Assets/_Project/Tests/EditMode/CarPaintMaterialTests.cs.meta',
 'game/Assets/_Project/Tests/EditMode/CarPlatePayloadTests.cs',
 'game/Assets/_Project/Tests/EditMode/CarPlatePayloadTests.cs.meta',
 'game/Assets/_Project/World/Import/InstanceImporter.cs',
 'game/Assets/_Project/World/Import/RegionImporter.cs',
 'game/Assets/_Project/World/Import/WorldPbrMaterials.cs',
 'game/Assets/_Project/World/Import/WorldCarPlateMaterials.cs',
 'game/Assets/_Project/World/Import/WorldCarPlateMaterials.cs.meta',
 'tests/gis/test_car_deposition.py',
 'tests/gis/test_car_map_fields.py',
 'tests/gis/test_car_plate_payload.py',
 'tests/gis/test_cars_r10.py',
 'tests/gis/test_cars_r11.py',
 'tests/gis/test_streetscape.py',
 'tools/worldgen/streetscape/export.py',
 'tools/worldgen/streetscape/life_cars.py',
 'tools/worldgen/streetscape/materials.py'
)
if ((git branch --show-current).Trim() -ne 'gpt-life-r1') { throw 'Unexpected branch' }
if ($Mode -eq 'Main') {
 git diff --quiet -- $paths
 if ($LASTEXITCODE -ne 0) { throw 'Uncommitted production changes; refusing to overwrite' }
 git restore --source=5f2aa277 --worktree -- $paths
} else {
 git restore --worktree -- $paths
}
if ($LASTEXITCODE -ne 0) { throw 'Source restore failed' }
@{mode=$Mode;base='5f2aa277';candidate_head=(git rev-parse HEAD).Trim();time=(Get-Date -Format o);paths=$paths} |
 ConvertTo-Json -Depth 3 | Set-Content -Encoding utf8 artifacts/life-r1/SOURCE-MODE.json
