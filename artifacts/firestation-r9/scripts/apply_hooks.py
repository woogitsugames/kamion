"""One-off patcher: wire hero_building into worldgen + the Unity importer (kept as a record of the edits)."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def patch(rel, pairs):
    p = REPO / rel
    raw = p.read_bytes()
    crlf = b"\r\n" in raw
    s = raw.decode("utf-8").replace("\r\n", "\n")
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70], s.count(a))
        s = s.replace(a, b)
    if crlf:
        s = s.replace("\n", "\r\n")
    p.write_bytes(s.encode("utf-8"))
    print("patched", rel)


patch("tools/worldgen/streetscape/stage.py", [
    ("from . import gate as GT\n", "from . import gate as GT\nfrom . import hero_building as HBD\n"),
    ("    blds = BM.load(fc, w.origin, overrides)\n",
     "    # hero buildings (override kind: hero_building, ADR 0070): authored asset instead of the rule facade\n"
     "    heroes = HBD.plan(rid, overrides, fc, w.origin, lambda e, n: float(np.asarray(zsmooth(e, n)).ravel()[0]), rep, log)\n"
     "    blds = BM.load(fc, w.origin, overrides, hero=HBD.targets(heroes))\n"),
    ("    vrep = {}\n    trees, forests = VG.place(src, origin, hf, zc, blocked, vrep)\n",
     "    hero_keepout = HBD.keepout(heroes)\n"
     "    if hero_keepout:\n"
     "        blocked |= PV.rasterize_polys(hero_keepout, hf)\n"
     "    vrep = {}\n    trees, forests = VG.place(src, origin, hf, zc, blocked, vrep)\n"),
    ("    return {\"zc\": zc, \"dist\": dist, \"mask\": mask, \"rmask\": rmask, \"col\": col, \"instances\": pl.items + trees,\n",
     "    instances = pl.items + trees\n"
     "    hero_tris = HBD.apply(w.buf, heroes, instances, rep, log)\n"
     "    if heroes or rep.get(\"hero_buildings\", {}).get(\"stale\"):\n"
     "        log(\"hero buildings\", {k: [x[\"id\"] for x in v] for k, v in rep[\"hero_buildings\"].items()})\n"
     "    return {\"zc\": zc, \"dist\": dist, \"mask\": mask, \"rmask\": rmask, \"col\": col, \"instances\": instances,\n"
     "            \"hero_tris\": hero_tris,\n"),
])

patch("tools/worldgen/streetscape/buildings_mesh.py", [
    ("def load(fc, origin, overrides):\n", "def load(fc, origin, overrides, hero=None):\n"),
    ("            o = ovr.get(f[\"id\"], {})\n",
     "            o = ovr.get(f[\"id\"], {})\n"
     "            if hero and f[\"id\"] in hero:      # replaced by an authored asset (streetscape.hero_building)\n"
     "                o = {**o, \"hero_asset\": hero[f[\"id\"]]}\n"),
    ("        key = b[\"id\"]\n        acc = Acc()\n",
     "        key = b[\"id\"]\n        acc = Acc()\n"
     "        if b[\"ovr\"].get(\"hero_asset\"):      # authored asset: only the collision prism of the footprint\n"
     "            counts[typ] -= 1\n"
     "            counts[\"hero_asset\"] = counts.get(\"hero_asset\", 0) + 1\n"
     "            for a, c_ in ring_edges(poly.exterior):\n"
     "                acc.quad(\"collision\", \"collision_building\", [a[0], a[1], zbot], [c_[0], c_[1], zbot],\n"
     "                         [c_[0], c_[1], ztop], [a[0], a[1], ztop])\n"
     "            roof_flat(acc, \"collision\", poly, ztop, mat=\"collision_building\", attic=0.0)\n"
     "            acc.flush(buf, key)\n"
     "            continue\n"),
])

patch("tools/worldgen/roads/build_world.py", [
    ("    props_meta = PR.export(st[\"codes\"], st[\"boards\"], out_root.parent / \"props\" if out_root != DEFAULT_OUT(region_id) else None)\n",
     "    props_meta = PR.export(st[\"codes\"], st[\"boards\"], out_root.parent / \"props\" if out_root != DEFAULT_OUT(region_id) else None)\n"
     "    props_meta = {**props_meta, **st.get(\"hero_tris\", {})}      # hero building assets (art-source/world/landmarks), frame estimate\n"),
    ("    elif proto.startswith(\"landmark_\"):\n",
     "    elif proto.startswith(\"landmark_fire_station\"):      # hero building (ADR 0070): LOD0 / LOD1 / silhouette\n"
     "        e = [150.0, 450.0, 20000.0]\n"
     "    elif proto.startswith(\"landmark_\"):\n"),
])

patch("tools/worldgen/streetscape/export.py", [
    ("            \"car_plates\": SG.png_bytes(LC.plate_atlas()),\n",
     "            \"car_plates\": SG.png_bytes(LC.plate_atlas()),\n"
     "            # hero fire station (ADR 0070): fence / gate / lettering, art-source/world/materials/_src/sets_fire_station.py --alpha\n"
     "            \"fire_station_alpha\": (ART / \"textures\" / \"fire_station_alpha.png\").read_bytes(),\n"),
])

patch("tools/worldgen/streetscape/materials.py", [
    ("\nM = {\n",
     "\n\ndef _mean_of_set(name, default):\n"
     "    \"\"\"Mean linear albedo of a generated texture set (materials_spec.json), so a calibrated atlas gets tint 1.\"\"\"\n"
     "    import json\n"
     "    from pathlib import Path\n"
     "    p = Path(__file__).resolve().parents[3] / \"art-source\" / \"world\" / \"materials\" / \"materials_spec.json\"\n"
     "    try:\n"
     "        return [round(float(x), 3) for x in json.loads(p.read_text(encoding=\"utf-8\"))[\"sets\"][name][\"albedo\"][\"mean_rgb_linear\"]]\n"
     "    except (OSError, KeyError, ValueError):\n"
     "        return default\n"
     "\n\nM = {\n"),
    ("    # landmarks\n    \"chimney_concrete\":",
     "    # hero fire station asset (ADR 0070, streetscape.hero_building): atlas on CC0 scans (colour = atlas mean, so the\n"
     "    # calibrated-set tint is 1), alpha-tested fence / gate / lettering\n"
     "    \"fire_station\": {\"color\": _mean_of_set(\"fire_station\", [0.30, 0.33, 0.39]), \"rough\": 0.8,\n"
     "                     \"surface\": \"concrete\", \"texture_set\": \"fire_station\"},\n"
     "    \"fire_station_alpha\": {\"color\": [1.0, 1.0, 1.0], \"rough\": 0.6, \"texture\": \"fire_station_alpha\",\n"
     "                           \"alpha_cutoff\": 0.5},\n"
     "    # landmarks\n    \"chimney_concrete\":"),
])

patch("game/Assets/_Project/World/Import/InstanceImporter.cs", [
    ("            // Landmarks (chimneys): visible across the district, never culled inside the far plane.\n",
     "            // Hero building assets (ADR 0070, art-source/world/landmarks): LOD0 / LOD1 / silhouette, never culled.\n"
     "            else if (proto.StartsWith(\"landmark_fire_station\")) e = new[] { 150f, 450f, 20000f };\n"
     "            // Landmarks (chimneys): visible across the district, never culled inside the far plane.\n"),
    ("            var impostors = GlbReader.Load(Path.Combine(art, \"vegetation\", \"trees_lod2.glb\"));\n",
     "            var impostors = GlbReader.Load(Path.Combine(art, \"vegetation\", \"trees_lod2.glb\"));\n"
     "            // Authored landmark assets (ADR 0067 / 0070): art-source/world/landmarks/<asset>/<asset>.glb, prototypes\n"
     "            // \"landmark_<asset>...\" (+ .lod1 / .lod2) in the same frame as street_props.glb.\n"
     "            var landmarkLibs = new List<GlbReader>();\n"
     "            string lmDir = Path.Combine(art, \"landmarks\");\n"
     "            if (Directory.Exists(lmDir))\n"
     "                foreach (var f in Directory.GetFiles(lmDir, \"*.glb\", SearchOption.AllDirectories).OrderBy(x => x, StringComparer.Ordinal))\n"
     "                    landmarkLibs.Add(GlbReader.Load(f));\n"),
    ("                var n0 = src.Find(name);\n                if (n0 == null) { Debug.LogWarning(",
     "                var n0 = src.Find(name);\n"
     "                if (n0 == null && !tree)\n"
     "                    foreach (var lib in landmarkLibs)\n"
     "                        if (lib.Find(name) is GlbReader.MeshNode ln) { src = lib; n0 = ln; break; }\n"
     "                if (n0 == null) { Debug.LogWarning("),
])
