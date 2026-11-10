"""Verified offline Fab import. Run from repo: uv run --project tools/worldgen python tools/worldgen/fab/prepare.py.

Only reviewed, hash-pinned assets are processed. No credentials, downloads or source
files enter the repository. Mesh and per-tier texture products share one ignored
directory, with a provenance manifest describing every copied/derived file.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import re
import stat
import struct
import subprocess
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path("art-source/world/megascans/_generated")
MANIFEST = Path("Data/SourceManifests/fab-megascans-2026-11-10.json")
TIERS = {"Low": 512, "High": 1024}
CHANNELS = {"basecolor": ("basecolor", "diffuse"), "normal": ("normal",),
            "roughness": ("roughness",), "ao": ("ao",), "opacity": ("opacity",),
            "metalness": ("metalness",), "displacement": ("displacement",),
            "translucency": ("translucency",)}
# Per prototype, not a scene/frame allowance. WORKING_VALUE pending phone profiling.
BUDGETS = {"plant": [1800, 700, 180], "3d": [2400, 800, 200]}
SOURCE_TRANSFORMS = {
    "small-granite-rock": {"bake_parent_transform": True, "expected_parent_scale": 0.01,
        "expected_parent_rotate_x_degrees": 90,
        "evidence": "wgyxecr.json meta length=0.26m,width=0.18m,height=0.08m; FBX world_root parent supplies 0.01 scale and X90 rotation"},
}
LOG = logging.getLogger("fab")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_members(zf: ZipFile):
    """Reject traversal, links, duplicate names and implausible archive sizes."""
    members = zf.infolist()
    if sum(m.file_size for m in members) > 8 * 1024**3:
        raise ValueError("Fab archive exceeds 8 GiB working safety limit")
    seen = set()
    for member in members:
        name = member.filename.replace("\\", "/")
        p = PurePosixPath(name)
        if p.is_absolute() or ".." in p.parts or ":" in name or stat.S_ISLNK(member.external_attr >> 16):
            raise ValueError(f"Unsafe Fab archive member: {name}")
        if name.casefold() in seen:
            raise ValueError(f"Duplicate Fab archive member: {name}")
        seen.add(name.casefold())
    return [m for m in members if not m.is_dir()]


def select_maps(zf: ZipFile, billboard=False):
    members = safe_members(zf)
    result = {}
    for channel, suffixes in CHANNELS.items():
        for suffix in suffixes:
            candidates = sorted((m for m in members if
                Path(m.filename).suffix.lower() in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
                and (("_billboard_" in m.filename.lower()) == billboard)
                and Path(m.filename).stem.lower().endswith("_" + suffix)), key=lambda m: m.filename)
            if candidates:
                result[channel] = candidates[0]
                break
    return result


def read_review(root: Path):
    path = root / "tools/worldgen/fab/review.json"
    return json.loads(path.read_text(encoding="utf-8"))["items"] if path.exists() else {}


def _write_json(path, value):
    _no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _no_links(path: Path):
    if path.resolve() != path.absolute():
        raise ValueError(f"Fab output must not traverse a symlink/junction: {path}")


def _source_path(root, relative):
    path = root / relative
    if not path.resolve().is_relative_to((root / "Data/raw/fab").resolve()):
        raise ValueError("Fab source ZIP must be inside Data/raw/fab")
    _no_links(path)
    return path


def sync_glb_textures(path, textures, root, billboard_textures=None):
    """Refresh embedded glTF maps too, retaining geometry and buffer indices."""
    raw = path.read_bytes()
    length = struct.unpack_from("<I", raw, 12)[0]
    gltf = json.loads(raw[20:20 + length])
    if any(set(node) & {"translation", "rotation", "scale", "matrix"} for node in gltf.get("nodes", [])):
        raise ValueError(f"Fab GLB node transforms must be baked before export: {path}")
    binary_start = 20 + length + 8
    binary = raw[binary_start:]
    replacements = {}
    def image_view(texture):
        image = gltf["images"][gltf["textures"][texture["index"]]["source"]]
        image["mimeType"] = "image/png"
        return image["bufferView"]
    for material in gltf.get("materials", []):
        selected = billboard_textures if material.get("name", "").endswith("_billboard") and billboard_textures else textures
        pbr = material.get("pbrMetallicRoughness", {})
        for channel, texture in (("basecolor", pbr.get("baseColorTexture")),
                                 ("normal", material.get("normalTexture"))):
            if texture and channel in selected:
                replacements[image_view(texture)] = (root / selected[channel]).read_bytes()
        texture = pbr.get("metallicRoughnessTexture")
        if texture and "roughness" in selected:
            rough = Image.open(root / selected["roughness"]).convert("L")
            metal = (Image.open(root / selected["metalness"]).convert("L") if "metalness" in selected
                     else Image.new("L", rough.size, 0))
            buffer = io.BytesIO()
            Image.merge("RGB", (Image.new("L", rough.size, 255), rough, metal)).save(buffer, format="PNG")
            replacements[image_view(texture)] = buffer.getvalue()
        if "opacity" in selected:
            material["alphaMode"] = "MASK"
            material["alphaCutoff"] = 0.5
    new_binary = bytearray()
    for i, view in enumerate(gltf.get("bufferViews", [])):
        data = replacements.get(i, binary[view.get("byteOffset", 0):view.get("byteOffset", 0) + view["byteLength"]])
        while len(new_binary) % 4:
            new_binary.append(0)
        view["byteOffset"] = len(new_binary)
        view["byteLength"] = len(data)
        new_binary.extend(data)
    gltf["buffers"][0]["byteLength"] = len(new_binary)
    while len(new_binary) % 4:
        new_binary.append(0)
    encoded = json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded += b" " * (-len(encoded) % 4)
    result = (struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(encoded) + 8 + len(new_binary))
              + struct.pack("<I4s", len(encoded), b"JSON") + encoded
              + struct.pack("<I4s", len(new_binary), b"BIN\0") + new_binary)
    path.write_bytes(result)


def _meshes(zf, destination, aid=None, first_variant_only=False):
    candidates = sorted((m for m in safe_members(zf) if m.filename.lower().endswith(".fbx")), key=lambda m: m.filename)
    # Rebuild our own LODs from each original highest-detail variant, never ship
    # Quixel's high-poly LOD0 or mistake source LODs for separate variants.
    chosen = [m for m in candidates if not re.search(r"_lod[1-9]\d*\.", m.filename, re.I)]
    result = []
    for member in chosen[:1] if first_variant_only else chosen:
        match = re.search(r"_(Var[A-Za-z0-9]+)_LOD0", member.filename, re.I)
        variant = match.group(1) if match else "default"
        fbx = destination / "source" / Path(member.filename).name
        _no_links(fbx)
        fbx.parent.mkdir(parents=True, exist_ok=True)
        fbx.write_bytes(zf.read(member))
        entry = {"variant": variant, "source": fbx, "member": member.filename}
        levels = {"grass-clumps": 1, "wild-grass": 2, "boxwood": 2, "elderberry": 2}
        if aid in levels:
            near_name = re.sub(r"_LOD0(?=\.)", f"_LOD{levels[aid]}", member.filename, flags=re.I)
            variant_names = [m.filename for m in candidates if re.sub(r"_LOD\d+(?=\.)", "_LOD0", m.filename, flags=re.I) == member.filename]
            billboard_name = max(variant_names, key=lambda n: int(re.search(r"_LOD(\d+)", n, re.I).group(1)))
            for key, name in (("source", near_name), ("billboard_source", billboard_name)):
                target = destination / "source" / Path(name).name
                _no_links(target)
                target.write_bytes(zf.read(name))
                entry[key] = target
            entry["member"] = near_name
            entry["billboard_member"] = billboard_name
        result.append(entry)
    return result


def prepare(root: Path = ROOT, blender: Path | None = None, only: set[str] | None = None, refresh_textures=False, first_variant_only=False):
    root = root.resolve()
    out = root / OUTPUT
    _no_links(out)
    if out.exists():
        for existing in out.rglob("*"):
            _no_links(existing)
    out.mkdir(parents=True, exist_ok=True)
    source = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    reviews = read_review(root)
    manifest_path = out / "manifest.json"
    previous = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"items": {}}
    report = {"schema": 1, "license": "Fab Standard License", "budgets_status": "WORKING_VALUE",
              "texture_max": TIERS, "items": {}}
    for item in source["items"]:
        aid = item["id"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", aid):
            raise ValueError(f"Unsafe Fab asset id: {aid}")
        if only and aid not in only:
            if aid in previous["items"]:
                prior = previous["items"][aid]
                review = reviews.get(aid, {})
                archive = _source_path(root, item["file"])
                current_review = review.get("source_sha256") == item["sha256"] and review.get("status") == "approved"
                if (current_review and archive.exists() and sha256(archive) == item["sha256"]
                        and prior.get("source_sha256") == item["sha256"]):
                    report["items"][aid] = prior
                else:
                    report["items"][aid] = {"source_sha256": item["sha256"],
                        "status": "missing" if not archive.exists() else ("rejected" if review.get("status") == "rejected" else "pending-review"),
                        "textures": {}, "models": [], "provenance": []}
            continue
        record = {"source_sha256": item["sha256"], "status": "missing", "textures": {}, "models": [],
                  "prototype": "fab_" + aid.replace("-", "_"), "provenance": []}
        report["items"][aid] = record
        archive = _source_path(root, item["file"])
        if not archive.exists():
            LOG.warning("Fab %s unavailable; existing procedural/CC0 fallback retained", aid)
            continue
        if sha256(archive) != item["sha256"]:
            raise ValueError(f"Fab SHA256 mismatch: {aid}")
        review = reviews.get(aid, {})
        if review.get("source_sha256") != item["sha256"] or review.get("status") != "approved":
            record["status"] = "rejected" if review.get("status") == "rejected" else "pending-review"
            LOG.warning("Fab %s %s: %s; fallback retained", aid, record["status"], review.get("reason", "no pinned review"))
            continue
        # Urban Trash is a multi-material collection. Require explicit selection
        # instead of pairing one arbitrary albedo with an unrelated mesh.
        if aid == "urban-trash":
            record["status"] = "rejected"
            record["reason"] = "multi-asset collection requires per-subasset review/selection"
            continue
        dest = out / aid
        _no_links(dest)
        with ZipFile(archive) as zf:
            maps = select_maps(zf)
            for texture_group, maps, texture_dest in [("textures", maps, dest)] + (
                    [("billboard_textures", select_maps(zf, billboard=True), dest / "billboard")]
                    if select_maps(zf, billboard=True) else []):
                record[texture_group] = {}
                for tier, maximum in TIERS.items():
                    record[texture_group][tier] = {}
                    for channel, member in maps.items():
                        _no_links(texture_dest / tier)
                        with Image.open(io.BytesIO(zf.read(member))) as original:
                            # Fab scalar JPEGs may be red-only RGB, not grey.
                            # Luminance conversion would multiply opacity by .299
                            # and make every leaf fail the .5 alpha cutoff.
                            image = (original.convert("RGB") if channel in {"basecolor", "normal"}
                                     else original.convert("RGB").getchannel("R"))
                            image.thumbnail((maximum, maximum), Image.Resampling.LANCZOS)
                            if channel == "normal":
                                vector = np.asarray(image, dtype=np.float32) / 127.5 - 1
                                vector /= np.maximum(np.linalg.norm(vector, axis=2, keepdims=True), 1e-6)
                                image = Image.fromarray(np.clip(np.rint((vector + 1) * 127.5), 0, 255).astype(np.uint8))
                            path = texture_dest / tier / (channel + ".png")
                            _no_links(path)
                            path.parent.mkdir(parents=True, exist_ok=True)
                            image.save(path, optimize=False)
                        rel = path.relative_to(root).as_posix()
                        record[texture_group][tier][channel] = rel
                        record["provenance"].append({"path": rel, "sha256": sha256(path), "source_member": member.filename})
                    # Unity URP Lit reads smoothness from metallic-map alpha. Keep
                    # roughness too for other consumers and explicit provenance.
                    paths = record[texture_group][tier]
                    if "basecolor" in paths and "opacity" in paths:
                        base_path = root / paths["basecolor"]
                        base = Image.open(base_path).convert("RGBA")
                        opacity = Image.open(root / paths["opacity"]).convert("L")
                        if opacity.size != base.size:
                            opacity = opacity.resize(base.size, Image.Resampling.LANCZOS)
                        base.putalpha(opacity)
                        base.save(base_path)
                        for entry in record["provenance"]:
                            if entry["path"] == paths["basecolor"]:
                                entry["sha256"] = sha256(base_path)
                                entry["opacity_source_member"] = maps["opacity"].filename
                    if "roughness" in paths:
                        rough = Image.open(root / paths["roughness"]).convert("L")
                        metallic = (Image.open(root / paths["metalness"]).convert("L") if "metalness" in paths
                                    else Image.new("L", rough.size, 0))
                        packed = Image.merge("RGBA", (metallic, metallic, metallic, ImageOps.invert(rough)))
                        packed_path = texture_dest / tier / "metallic_gloss.png"
                        packed.save(packed_path)
                        rel = packed_path.relative_to(root).as_posix()
                        paths["metallic_gloss"] = rel
                        record["provenance"].append({"path": rel, "sha256": sha256(packed_path),
                                                     "source_member": maps["roughness"].filename})
            models = [] if refresh_textures else _meshes(zf, dest, aid, first_variant_only)
        if refresh_textures:
            prior = previous["items"].get(aid, {})
            if prior.get("source_sha256") == item["sha256"]:
                record["models"] = prior.get("models", [])
                record["provenance"].extend(p for p in prior.get("provenance", []) if p["path"].endswith(".glb"))
        if models and not blender:
            record["status"] = "textures-only"
            LOG.warning("Fab %s textures prepared but Blender missing; mesh fallback retained", aid)
        else:
            record["status"] = "ready"
        if refresh_textures and item["kind"] in {"3d", "plant"} and not record["models"]:
            record["status"] = "textures-only"
        if blender:
            for model in models:
                target = dest / model["variant"]
                _no_links(target)
                request = {"source": str(model["source"]), "output": str(target),
                           "prototype": record["prototype"], "variant": model["variant"],
                           "budgets": BUDGETS.get(item["kind"], BUDGETS["3d"]),
                           "textures": {k: str(root / v) for k, v in record["textures"]["High"].items()}}
                request["source_transform"] = SOURCE_TRANSFORMS.get(aid, {})
                if "billboard_source" in model:
                    request["billboard_source"] = str(model["billboard_source"])
                    request["billboard_textures"] = {k: str(root / v) for k, v in record["billboard_textures"]["High"].items()}
                    request["budgets"] = [8000 if aid in {"boxwood", "elderberry"} else 4000, 16, 4]
                request_path = dest / (model["variant"] + "-request.json")
                _write_json(request_path, request)
                subprocess.run([str(blender), "-b", "--factory-startup", "--python-exit-code", "1", "-P",
                                str(root / "tools/blender/world/fab_prepare.py"), "--", str(request_path)], check=True)
                mesh_report = json.loads((target / "report.json").read_text(encoding="utf-8"))
                combined = Path(mesh_report["path"])
                mesh_report["path"] = combined.relative_to(root).as_posix()
                record["provenance"].append({"path": mesh_report["path"], "sha256": sha256(combined), "source_member": model["member"]})
                for lod in mesh_report["lods"]:
                    p = Path(lod["path"])
                    lod["path"] = p.relative_to(root).as_posix()
                    record["provenance"].append({"path": lod["path"], "sha256": sha256(p), "source_member": model["member"]})
                record["models"].append(mesh_report)
        for model in record["models"]:
            for rel in {model["path"], *(lod["path"] for lod in model["lods"])}:
                sync_glb_textures(root / rel, record["textures"]["High"], root, record.get("billboard_textures", {}).get("High"))
        for entry in record["provenance"]:
            if entry["path"].endswith(".glb"):
                entry["sha256"] = sha256(root / entry["path"])
        # Source FBX files are retained only in the same ignored generated tree.
        _write_json(manifest_path, report)
    _write_json(manifest_path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender", type=Path)
    parser.add_argument("--only", action="append", help="process only this source id (repeatable)")
    parser.add_argument("--first-variant-only", action="store_true", help="process only the active VarA prototype")
    parser.add_argument("--refresh-textures", action="store_true", help="retain existing matching mesh products")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    report = prepare(blender=args.blender, only=set(args.only) if args.only else None, refresh_textures=args.refresh_textures, first_variant_only=args.first_variant_only)
    print(json.dumps({aid: v["status"] for aid, v in report["items"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
