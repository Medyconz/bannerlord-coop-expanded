"""Validate saved geometry measurements, files, PNGs and reference exclusions."""
import argparse
import re
import struct
import subprocess
import sys

from PIL import Image

from catalog import ROOT, checksum, entries, fingerprint, outputs, read, references


def inspect(e, record, cfg, hashes=True):
    i=e["id"]; errors=[]
    if not re.fullmatch("[a-z][a-z0-9]*(?:_[a-z0-9]+)*",i):
        errors.append("Invalid asset ID")
    if record.get("status")=="skipped_no_reference":
        if e["group"]!="B" or not references(e,cfg):
            errors.append("Incorrect missing-reference status")
        return errors
    if record.get("status")!="ok":
        return [record.get("reason","Missing successful build record")]
    if record.get("fingerprint")!=fingerprint(e):
        errors.append("Manifest, convention or generator has changed")
    paths=outputs(e)
    for p in paths:
        label=p.relative_to(ROOT).as_posix()
        if not p.is_file():
            errors.append("Missing "+label); continue
        if hashes and record.get("sha256",{}).get(label)!=checksum(p):
            errors.append("Changed file "+label)
        if p.suffix==".fbx":
            with p.open("rb") as f:
                header=f.read(27)
            if not header.startswith(b"Kaydara FBX Binary") or struct.unpack("<I",header[23:27])[0]!=cfg["fbx"]["version"]:
                errors.append("Unexpected FBX version")
        if p.suffix==".png":
            with Image.open(p) as img:
                s=cfg["texture"]["rigid_size" if e["group"]=="A" else "fitted_size"]
                size=(s,s) if p.name!="preview.png" else (1024,1024)
                if e["group"]=="UI":
                    if e["category"]=="icons":
                        side=int(p.stem.rsplit("_",1)[1]); size=(side,side)
                        if img.mode!="RGBA": errors.append("Icon missing alpha "+p.name)
                    else:
                        size={"logo":(1024,1024),"repo_banner":(1280,640)}.get(p.stem,(512,512))
                if img.size!=size: errors.append("Incorrect PNG dimensions "+p.name)
                img.verify()
    if e["group"]=="UI":
        return errors
    stats=record.get("objects",{})
    parts={i:e["type"]}
    if e["category"]=="ammunition": parts[i+"_quiver"]="quiver"
    if i=="ce_dg_nord_scramasax": parts[i+"_sheath"]="sheath"
    if set(stats)!={name+level["suffix"] for level in cfg["lods"] for name in parts}:
        return errors+["Incorrect LOD object names"]
    for base,kind in parts.items():
        info=stats[base]; low,high=cfg["limits"][kind]["triangles"]
        if not low<=info["tris"]<=high: errors.append(f"{base} triangle budget {info['tris']}")
        dims=info["dimensions_m"]
        dim=max(dims)
        lo,hi=cfg["limits"][kind]["size_m"]
        if lo is not None and not lo-.0001<=dim<=hi+.0001:
            errors.append(f"{base} dimension {dim:.4f} m outside {lo} to {hi}")
        if kind in cfg["width_m"]:
            a,b=cfg["width_m"][kind]
            if not a<=dims[0]<=b: errors.append(f"{base} width {dims[0]:.4f} m")
        for level in cfg["lods"]:
            name=base+level["suffix"]; data=stats[name]
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
