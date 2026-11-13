# STATUS dojlidy-import-0174 (ADR 0174)
- WorldLibrary.cs: per-region street library (props/signs/textures) — C reads art-source only, other regions Data/raw/derived/<id>/ with per-file fallback. 8 call sites switched. EditMode WorldLibraryTests (reflection).
- build_world dojlidy running in background (heavy slot).
- NEXT: pwsh scripts/import-region.ps1 -Region bialystok-dojlidy (after build.status = exit 0)
