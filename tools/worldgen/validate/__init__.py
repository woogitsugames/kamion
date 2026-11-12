"""World validator (M37): quality gate on the generated region data in Data/Regions/<id>/.

Read-only over Data/** (generated/*.json are committed, read-only inputs here). Finds errors visible to the
driver before the owner sees them: overlaps, discontinuities, terrain/road height problems, sign orientation
and occlusion. Emits findings with local E/N (metres of the region origin) + object id, an HTML/MD report
and a JSON of control cameras. Run:

    uv run --project tools/worldgen tools/worldgen/validate/run.py --region bialystok-industrial-c
"""
