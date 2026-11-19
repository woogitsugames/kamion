& "C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s23\artifacts\dk19-tiles-s23/run-steps.ps1" -Log "C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s23/artifacts/logs/dk19-xsec40b.log" -Steps @(
  'uv run --project tools/worldgen python tools/worldgen/qa/ortho_xsec.py measure bialystok-bojary 137540631,581608908,672162903 40 artifacts/dk19-tiles-s23/xsec/bojary40b',
  'uv run --project tools/worldgen python tools/worldgen/qa/ortho_xsec.py measure bialystok-mickiewicza 25447094,257124463,279876738,636536003,665619497,540735092,248117601,349657603 40 artifacts/dk19-tiles-s23/xsec/mickiewicza40b')

