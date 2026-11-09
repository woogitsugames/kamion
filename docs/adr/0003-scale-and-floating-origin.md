# ADR 0003 — Scale, coordinates, floating origin
Status: Accepted, 2026-11-09
Decision: 1 unit = 1 m, SI internally. X=east, Y=up, Z=north. Source CRS EPSG:2180 (PL-1992); world positions stored as double (region id + global position), rendered relative to a floating origin re-centred when the truck is > 2 km (WORKING_VALUE) from origin. Cities 1:1; intercity scale factor decided at Stage 7.
Consequences: Save files never store raw Transform positions. Physics shift on origin move tested (docs/04 §6 test 13).
