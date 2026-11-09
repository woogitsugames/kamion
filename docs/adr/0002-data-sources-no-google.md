# ADR 0002 — Map data sources: OSM + GUGiK only
Status: Accepted (D4, D11, CLAUDE.md rule 8), 2026-11-09
Decision: World geometry comes only from OpenStreetMap (ODbL) and GUGiK (NMT, BDOT10k, LoD1/LoD2 buildings, orthophoto) plus the owner's own photos. Google Maps / Street View / Earth / 3D Tiles are banned as a source of anything.
Consequences: Every source recorded in docs/LICENSES.md with URL, date, SHA256. OSM/GUGiK attribution shown in-game. Raw data stays out of git (data/raw/) with a manifest + download script.
