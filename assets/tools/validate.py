"""Validate saved geometry measurements, files, PNGs and reference exclusions."""
import argparse
import math
import re
import subprocess
import sys

from PIL import Image

from catalog import ROOT, checksum, entries, fingerprint, outputs, read, references


def png_errors(path, entry, cfg):
    size = cfg["texture"]["fitted_size" if entry["group"] == "B" else "rigid_size"]
    target = (size, size)
    is_icon = entry["category"] == "icons"
    is_logo = entry["category"] == "branding" and path.stem == "logo"
    if path.name == "preview.png" or is_logo:
        target = (1024, 1024)
    elif is_icon:
        side = int(path.stem.rsplit("_", 1)[1])
        target = (side, side)
    elif entry["category"] == "branding":
        target = (1280, 640) if path.stem == "repo_banner" else (512, 512)
    try:
        with Image.open(path) as img:
            if img.format != "PNG" or img.size != target:
                return [f"{path.name} must be a {target[0]}×{target[1]} PNG"]
            img.verify()
        if is_icon or is_logo:
            with Image.open(path) as img:
                if img.mode != "RGBA" or img.getchannel("A").getextrema() != (0, 255):
                    return [path.name + " requires visible art and a transparent background"]
                if is_icon:
                    mask = img.getchannel("A")
                    for channel in "RGB":
                        if sum(img.getchannel(channel).histogram(mask)[:255]):
                            return [path.name + " contains non-white icon pixels"]
    except (ValueError, SyntaxError, OSError) as exc:
        return [f"Unreadable PNG {path.name} ({type(exc).__name__})"]
    return []


def bounds_errors(name, data):
    dims = data["dimensions_m"]
    low, high = data["bbox_m"]
    if any(len(v) != 3 for v in (dims, low, high)):
        return [name + " incomplete 3D bounds"]
    for span, a, b in zip(dims, low, high):
        if not all(math.isfinite(x) for x in (span, a, b)) or span <= 0 or not math.isclose(
                span, b - a, abs_tol=1e-6, rel_tol=1e-6):
            return [name + " invalid or inconsistent bounding box"]
    return []


def inspect(e, record, cfg, hashes=True):
    i=e["id"]; errors=[]
    if not re.fullmatch("[a-z][a-z0-9]*(?:_[a-z0-9]+)*",i):
        errors.append("Invalid asset ID")
    if record.get("status")=="skipped_no_reference":
        missing = references(e, cfg) if e["group"] == "B" else []
        if not missing or record.get("reason") != "Missing " + ", ".join(missing):
            errors.append("Incorrect missing-reference status")
        return errors
    if record.get("status")!="ok":
        return [record.get("reason","Missing successful build record")]
    if record.get("fingerprint")!=fingerprint(e):
        errors.append("Manifest, convention or generator has changed")
    paths=outputs(e)
    expected_files = {p.relative_to(ROOT).as_posix() for p in paths}
    if set(record.get("files", [])) != expected_files or set(record.get("sha256", {})) != expected_files:
        errors.append("Report file inventory differs from the required asset paths")
    for p in paths:
        label=p.relative_to(ROOT).as_posix()
        if not p.is_file():
            errors.append("Missing "+label); continue
        if hashes and record.get("sha256",{}).get(label)!=checksum(p):
            errors.append("Changed file "+label)
        if p.suffix==".fbx":
            with p.open("rb") as f:
                header=f.read(27)
            if header[:23] != b"Kaydara FBX Binary  \x00\x1a\x00" or int.from_bytes(header[23:27], "little") != cfg["fbx"]["version"]:
                errors.append("Unexpected FBX version")
        if p.suffix==".png":
            errors.extend(png_errors(p, e, cfg))
    if e["group"]=="UI":
        return errors
    stats=record.get("objects",{})
    parts={i:e["type"]}
    if e["category"]=="ammunition": parts[i+"_quiver"]="quiver"
    if i=="ce_dg_nord_scramasax": parts[i+"_sheath"]="sheath"
    if set(stats)!={name+level["suffix"] for level in cfg["lods"] for name in parts}:
        return errors+["Incorrect LOD object names"]
    orient = cfg["orientation"]
    up = "XYZ".index(orient["up"][-1])
    tip = "XYZ".index(orient["weapon_tip"][-1])
    face = "XYZ".index(orient["shield_face"][-1])
    width = ({0, 1, 2} - {up, face}).pop()
    for base,kind in parts.items():
        info=stats[base]; low,high=cfg["limits"][kind]["triangles"]
        if not low<=info["tris"]<=high: errors.append(f"{base} triangle budget {info['tris']}")
        dims=info["dimensions_m"]
        if e["category"] == "shields":
            dim = dims[up]
        elif e["group"] == "A" and kind != "trade_good":
            dim = dims[tip]
        else:
            dim = max(dims)
        lo,hi=cfg["limits"][kind]["size_m"]
        if lo is not None and not lo-.0001<=dim<=hi+.0001:
            errors.append(f"{base} dimension {dim:.4f} m outside {lo} to {hi}")
        if kind in cfg["width_m"]:
            a,b=cfg["width_m"][kind]
            if not a-.0001<=dims[width]<=b+.0001: errors.append(f"{base} width {dims[width]:.4f} m")
        if kind in ("round_shield", "buckler") and not lo-.0001 <= dims[width] <= hi+.0001:
            errors.append(f"{base} horizontal diameter {dims[width]:.4f} m")
        if kind == "trade_good" and cfg["origins"]["trade_goods"] == "base_center":
            low, high = info["bbox_m"]
            ground = high[up] if orient["up"].startswith("-") else low[up]
            if abs(ground) > .001 or any(abs((low[k] + high[k]) / 2) > .001 for k in range(3) if k != up):
                errors.append(base + " origin outside base centre")
        for level in cfg["lods"]:
            name=base+level["suffix"]; data=stats[name]
            errors.extend(bounds_errors(name, data))
            if not data["applied_transforms"] or data["materials"]!=1 or data["uv_sets"]!=1:
                errors.append(name+" transform, material or UV set")
            if data["loose_vertices"] or data["non_triangles"] or data["degenerate_faces"]:
                errors.append(name+" loose, non-triangular or degenerate geometry")
            u,v=data["uv_bounds"]
            if not -.00001<=u<=v<=1.00001: errors.append(name+" UV out of bounds")
            if abs(data["tris"]-info["tris"]*level["ratio"])>max(8,.045*info["tris"]):
                errors.append(name+" LOD ratio")
    return errors


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--category"); ap.add_argument("--only")
    args=ap.parse_args()
    items=entries(); cfg=read(ROOT/"conventions.json"); records=read(ROOT/"asset_report.json",{})
    errors=[]
    if len(items)!=len({e["id"] for e in items}): errors.append("Duplicate manifest IDs")
    staged=subprocess.run(["git","diff","--cached","--name-only","--","assets/reference"],cwd=ROOT.parent,capture_output=True,text=True,check=True)
    if staged.stdout.strip(): errors.append("Reference file staged")
    selected=[e for e in items if (not args.category or args.category==e["category"]) and (not args.only or args.only==e["id"])]
    if not selected: errors.append("Empty selection")
    for e in selected:
        try: errors.extend(e["id"]+"  "+msg for msg in inspect(e,records.get(e["id"],{}),cfg))
        except Exception as ex: errors.append(e["id"]+"  "+str(ex))
    print("\n".join(errors) if errors else f"Validated {len(selected)} manifest entries")
    return bool(errors)


if __name__=="__main__":
    sys.exit(main())
