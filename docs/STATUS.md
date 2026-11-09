# STATUS — 2026-11-09

## Stage 0 — in progress
- Done: starter docs imported, environment audit, repo + LFS + .gitignore, ADR 0001–0005.
- In progress: Unity Hub + 6000.3.28f1 install, Android toolchain, parallel tracks (physics core in pure C#, truck concepts A1/A2, OSM analysis of industrial-zone candidates).
- Blocked / needs owner: Unity Personal licence activation (sign-in in Unity Hub); Samsung A connected with USB debugging; repo visibility (public vs private per D11).

## Stage 0 — build-qa update (2026-11-09)
- Done: project hygiene + asmdefs, Android player settings + URP tiers as code (ADR 0006), Boot scene with diagnostics overlay and frame-time CSV, batchmode build/visual-QA/test/device scripts, doctor green, clean-clone build verified, APK installed on Galaxy A16, physics + audio code compile in Unity.
- Blocked / needs owner: Galaxy A16 is behind a PIN lock screen — unlock it so the Boot scene can be measured (FPS p50/p95/p99, PSS, temperature, phone screenshot). See docs/reports/GATE-0.md.
