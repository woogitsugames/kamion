"""Read-only wave 15 road comparison. Pass --code to replay the pinned wave 14 generator."""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import yaml

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
WAVE14 = "4499ff9defa3c8d438a8f7272bcc804d30ae7ef6"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def git_file(ref, tile, name, optional=False):
    path = f"Data/Regions/{tile}/{name}"
    if optional:
        found = git("ls-tree", ref, "--", path)
        if not found:
            return None
    return git("show", f"{ref}:{path}").decode("utf-8")


def digest(values):
    rounded = np.round(np.asarray(values, dtype="<f8"), 8)
    rounded[rounded == 0] = 0
    return hashlib.sha256(rounded.tobytes()).hexdigest()[:20]


def power(args):
    sys.path.insert(0, str(args.code.resolve()))
    from roads.meshing import MeshBuf
    from streetscape import furniture

    with (HERE / "queue-full.csv").open(encoding="utf-8") as queue:
        tiles = sorted(row["tile"] for row in csv.DictReader(queue))
    stored = {tile: json.loads(git_file(WAVE14, tile, "generated/streetscape_sources.json")) for tile in tiles}
    pbf = ROOT / "Data/raw/osm/podlaskie-261108.osm.pbf"
    if not args.baseline:
        from streetscape import sources

        extracted = sources.extract_osm_power_ways_by_bboxes({t: tuple(s["bbox"]) for t, s in stored.items()}, pbf)

    def wire_mesh(src, origin):
        def flat(east, north):
            return np.zeros_like(east, dtype=float)

        placer = furniture.Placer(flat)
        furniture.misc_points(placer, SimpleNamespace(chains=[]), src, origin, {}, {})
        buf = MeshBuf()
        furniture.power_lines(furniture.Lin(buf, flat), src, origin, {}, pl=placer)
        parts = sorted((digest(part.V), digest(part.T)) for part in buf.parts)
        fingerprint = hashlib.sha256(json.dumps(parts).encode("ascii")).hexdigest()
        return len(buf.parts), sum(len(part.T) for part in buf.parts), fingerprint

    fields = ("tile", "osm_before", "osm_after", "osm_changed", "parts_before", "parts_after",
              "tris_before", "tris_after", "wire_mesh_changed", "fingerprint_before", "fingerprint_after")
    with args.out.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(fields)
        for tile, src in stored.items():
            info = yaml.safe_load(git_file(WAVE14, tile, "region.yaml"))
            origin = np.array([info["origin"]["x"], info["origin"]["y"]])
            old, other = [], []
            for way in src["osm"]["ways"]:
                target = old if way.get("tags", {}).get("power") in {"line", "minor_line"} else other
                target.append(way)
            before = wire_mesh(src, origin)
            new = old if args.baseline else extracted[tile]
            after = before if args.baseline else wire_mesh({**src, "osm": {**src["osm"], "ways": other + new}}, origin)
            writer.writerow((tile, len(old), len(new), old != new,
                             before[0], after[0], before[1], after[1], before[2] != after[2], before[2], after[2]))
    evidence = WAVE14 if args.baseline else f"{pbf.name} ({pbf.stat().st_size} bytes)"
    print(f"{len(tiles)} tiles from {evidence}", flush=True)


def replay(args):
    sys.path.insert(0, str(args.code.resolve()))
    from qa import seams
    from roads import markings, pipeline, seam_taper

    queue = list(csv.DictReader((HERE / "queue-full.csv").open(encoding="utf-8")))
    reports = {}
    tiles = []
    introduced = git("merge-base", WAVE14, "075c2ccc4").decode().strip()
    for entry in sorted(queue, key=lambda row: row["tile"]):
        tile = entry["tile"]
        qa = json.loads(git_file(WAVE14, tile, "generated/roads_qa.json"))
        if args.baseline:
            ov = []
            for name in (*pipeline.GENERATED_OVERRIDES, "overrides.yaml"):
                source = git_file(WAVE14, tile, name, optional=True)
                if source is not None:
                    data = json.loads(source) if name.endswith(".json") else yaml.safe_load(source)
                    ov.extend((data or {}).get("overrides") or [])
        else:
            ov = pipeline.load_overrides(tile)
        ctx = git_file(WAVE14, tile, "generated/osm_context.json", optional=True) if args.sides else None
        src = git_file(WAVE14, tile, "generated/streetscape_sources.json", optional=True) if args.sides else None
        tiles.append(seams.Tile(
            id=tile, region=yaml.safe_load(git_file(WAVE14, tile, "region.yaml")),
            graph=json.loads(git_file(WAVE14, tile, "roads.graph.json")), overrides=ov,
            roads_qa=qa, ctx=json.loads(ctx) if ctx else None,
            streetscape=json.loads(src) if src else None,
        ))
        manifest = f"Data/Regions/{tile}/generated/world_manifest.json"
        newer = git("log", "-1", "--format=%h", f"{introduced}..{WAVE14}", "--", manifest).decode().strip()
        last_qa = git("log", "-1", "--format=%h", WAVE14, "--",
                      f"Data/Regions/{tile}/generated/roads_qa.json").decode().strip()
        reports[tile] = {"wave14_manifest_commit": newer, "roads_qa_commit": last_qa,
                         "roads_qa_chain_count": qa["summary"]["chains"],
                         "roads_qa_markings": qa["summary"].get("markings", {})}
    pairs = seams.adjacent_pairs(tiles)
    print(f"{len(tiles)} tiles, {len(pairs)} seams; baseline={args.baseline}, sides={args.sides}", flush=True)
    if args.sides:
        nets = seams.build_nets(tiles, pairs, trims=True)
    else:
        nets = {tile.id: seams.build_plain(tile) for tile in tiles}
        ends = {tile: seam_taper.ends(net) for tile, net in nets.items()}
        neighbours = {tile: {} for tile in nets}
        for a, b, edge in pairs:
            neighbours[a.id][b.id] = [end for end in ends[b.id] if end.on_seam(edge)]
            neighbours[b.id][a.id] = [end for end in ends[a.id] if end.on_seam(edge)]
        for tile, net in nets.items():
            net.seam_tapers = seam_taper.plan(ends[tile], neighbours[tile])
            seam_taper.apply_widths(net, net.seam_tapers)

    for tile in tiles:
        net = nets[tile.id]
        qa_chains = {row["id"]: row for row in tile.roads_qa["chains"]}
        result = reports[tile.id]
        result["chains"] = {}
        result["seam_tapers"] = [taper.report() for taper in net.seam_tapers]
        result["seam_sides"] = [
            item for item in getattr(net, "seam_sides_report", []) if item.get("applied_m")
        ]
        for chain in net.chains:
            if chain.meta.get("absorbed"):
                continue
            sections = [net.sec_list[i] for i in np.unique(chain.sec_idx)]
            paint = []
            delta = chain.meta.get("edge_line_spacing_delta", np.zeros(len(chain.hw)))
            for index, half_width in enumerate(chain.hw):
                sec = net.sec_list[chain.sec_idx[index]]
                direction = chain.dirn[index]
                spacing = {"spacing_delta": delta[index]} if not args.baseline else {}
                edges = markings.edge_lines(sec, half_width, direction, **spacing)
                centre, boundaries, _ = markings.lane_layout(sec, half_width, direction)
                paint.extend([len(edges), *(offset for offset, _ in edges), len(boundaries), *boundaries,
                              int(centre is not None)])
                if centre is not None:
                    paint.append(centre)
            qa_row = qa_chains.get(chain.id)
            result["chains"][chain.id] = {
                "axis": digest(chain.line.p), "width": digest(chain.hw),
                "paint": digest(paint), "trims": [chain.t_a, chain.t_b],
                "sides": {
                    name: {key: digest(value) for key, value in side.items() if isinstance(value, np.ndarray)}
                    for name, side in chain.side.items()
                },
                "nominal_widths_m": sorted({sec.width for sec in sections}),
                "qa_nominal_widths_m": qa_row["width_m"] if qa_row else None,
                "end_widths_m": [round(float(2 * chain.hw[i]), 8) for i in (0, -1)],
                "length_m": round(chain.length, 1),
            }
        print(f"{tile.id}: {len(result['chains'])} chains", flush=True)
    args.out.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "tools/worldgen")
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--sides", action="store_true", help="also run second-pass shoulders and junction trims")
    parser.add_argument("--power", action="store_true", help="compare wire meshes with refreshed OSM")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.power:
        power(args)
    else:
        replay(args)
