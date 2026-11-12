# STATUS — sbs-poses (ADR 0130, s12)

- 2026-11-12: worktree + copies/junctions ready. Helper `artifacts/sbs-poses/tools/poselib.py` reproduces prepare() camera formula (verified: all Mapillary cameras match sbs_cameras.json except the 2 lead-promoted ones, 0.056 m look_at diff because lead used horizon 0.52 unrectified).
- Resection from photo: 3281350 portal legs x=0.145/0.434 + EC chimneys -> heading = SfM, pos (-310.0,-193.05) (~73 m back from GPS); 297817 portal far x=0.445/0.566 + chimneys -> heading +1.15, pos (-367.2,-150.1).
- NEXT: render r1 probes: `pwsh -c "pwsh C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Acquire -Owner claude-sbs-poses; pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Width 1280 -Height 960 -Gate3 artifacts/sbs-poses/r1/cameras.json -Cameras (gc artifacts/sbs-poses/r1/ids-4x3.txt) -OutputDir artifacts/sbs-poses/r1/renders"` (+16:9 1280x720 ids-16x9), then release slot.
