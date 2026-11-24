"""Round-trip rigid FBXs in Blender. Pass paths after --, or omit to audit all built FBXs."""
import json
import sys
from pathlib import Path

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def audit(path, entry, cfg):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path), use_image_search=False)
    objects = list(bpy.context.scene.objects)
    errors = []
    base_names = {entry["id"]: entry["type"]}
    if entry["category"] == "ammunition":
        base_names[entry["id"] + "_quiver"] = "quiver"
    if entry["id"] == "ce_dg_nord_scramasax":
        base_names[entry["id"] + "_sheath"] = "sheath"
    expected = {name + lod["suffix"] for name in base_names for lod in cfg["lods"]}
    if {obj.name for obj in objects} != expected or any(obj.type != "MESH" for obj in objects):
        return ["unexpected scene objects"]
    if bpy.data.actions:
        errors.append("animation data")

    for name, kind in base_names.items():
        principal = bpy.data.objects[name]
        lower, upper = cfg["limits"][kind]["size_m"]
        size = max(principal.dimensions)
        if lower is not None and not lower-1e-4 <= size <= upper+1e-4:
            errors.append(f"{name} spans {size:.4f} m")
        base_faces = len(principal.data.polygons)
        low, high = cfg["limits"][kind]["triangles"]
        if not low <= base_faces <= high:
            errors.append(f"{name} has {base_faces} faces")
        for lod in cfg["lods"]:
            obj = bpy.data.objects[name + lod["suffix"]]
            mesh = obj.data
            if not np.allclose(obj.matrix_world, np.eye(4), atol=1e-5):
                errors.append(f"{obj.name} has unapplied transforms")
            if len(mesh.materials) != 1 or len(mesh.uv_layers) != 1:
                errors.append(f"{obj.name} material/UV count")
            if any(len(f.vertices) != 3 or f.area <= 1e-14 for f in mesh.polygons):
                errors.append(f"{obj.name} has non-triangular or degenerate faces")
            if len({v for f in mesh.polygons for v in f.vertices}) != len(mesh.vertices):
                errors.append(f"{obj.name} has loose vertices")
            if abs(len(mesh.polygons) - base_faces*lod["ratio"]) > max(8, base_faces*.045):
                errors.append(f"{obj.name} LOD budget")
            if mesh.uv_layers.active:
                uv = np.array([corner.uv[:] for corner in mesh.uv_layers.active.data])
                if not np.isfinite(uv).all() or uv.min() < -1e-5 or uv.max() > 1+1e-5:
                    errors.append(f"{obj.name} UV coordinates outside atlas")

    # With image search disabled, this tests the paths carried in the FBX.
    # The packed metal/gloss/AO sidecar is bound by the game material.
    for material in {slot.material for obj in objects for slot in obj.material_slots}:
        if not material or not material.node_tree:
            errors.append("missing material")
            continue
        shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
        for socket, filenames in [
            ("Base Color", [path.stem + "_d.png"]),
            ("Normal", [path.stem + "_n.png", "src_maps/normal.png"]),
        ]:
            links = shader.inputs[socket].links
            node = links[0].from_node if links else None
            if node and node.type == "NORMAL_MAP" and node.inputs["Color"].links:
                node = node.inputs["Color"].links[0].from_node
            if not node or node.type != "TEX_IMAGE" or not node.image:
                errors.append(f"missing {socket} texture connection")
                continue
            image_path = Path(bpy.path.abspath(node.image.filepath)).resolve()
            if image_path not in [(path.parent / rel).resolve() for rel in filenames] or not image_path.is_file():
                errors.append(f"unresolved {socket} texture {image_path}")

    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    for lod in cfg["lods"]:
        bpy.ops.object.select_all(action="DESELECT")
        active = [bpy.data.objects[name + lod["suffix"]] for name in base_names]
        for obj in active:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active[0]
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.uv.select_overlap(extend=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        for obj in active:
            folded = sum(f.select for f in obj.data.polygons)
            if folded:
                errors.append(f"{obj.name} has {folded} faces with overlapping UVs")
    return errors


if __name__ == "__main__":
    cfg = json.loads((ROOT / "conventions.json").read_text(encoding="utf-8-sig"))
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8-sig"))
    entries = {entry["id"]: entry for entry in manifest["assets"] if entry["group"] == "A"}
    paths = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    paths = [Path(p).resolve() for p in paths] or sorted(
        p for p in (ROOT / "build").glob("*/*/*.fbx") if p.stem in entries)
    issues = []
    for path in paths:
        try:
            errors = audit(path, entries[path.stem], cfg)
        except Exception as ex:
            errors = [str(ex)]
        issues.extend(f"{path.stem}: {error}" for error in errors)
    print(f"Round-tripped {len(paths)} rigid FBXs, found {len(issues)} issues.")
    if issues or not paths:
        raise RuntimeError("\n".join(issues) or "No FBX files selected")
