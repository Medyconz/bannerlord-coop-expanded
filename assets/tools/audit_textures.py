"""Check a model's game textures against its source maps, with an optional procedural rebake."""
import argparse
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from catalog import ROOT, entries, read


def load_png(path, modes, size):
    with Image.open(path) as image:
        if image.format != "PNG" or image.mode not in modes or image.size != (size, size):
            raise ValueError(f"{path.name} is {image.format} {image.mode} {image.size}, expected {modes} at {size}px")
        return np.array(image)


def compare(label, expected, actual):
    if expected.shape != actual.shape:
        raise ValueError(f"{label} channel counts differ")
    different = expected != actual
    if different.ndim == 3:
        different = different.any(axis=2)
    count = np.count_nonzero(different)
    if count:
        raise ValueError(f"{label} differs at {count:,} texels")


def audit(directory, size, config):
    src = directory / "src_maps"
    specs = {"basecolor": ("RGB", "RGBA"), "normal": ("RGB",),
             "metallic": ("L",), "roughness": ("L",), "ao": ("L",), "height": ("L",)}
    source = {name: load_png(src / f"{name}.png", modes, size) for name, modes in specs.items()}
    diffuse = load_png(directory / f"{directory.name}_d.png", specs["basecolor"], size)
    compare("diffuse / basecolor", source["basecolor"], diffuse)
    if diffuse.shape[2] == 4 and np.all(diffuse[:, :, 3] == 255):
        raise ValueError("diffuse has a redundant fully opaque alpha channel")

    source_normal = source["normal"]
    vectors = source_normal.astype(np.float32) / 127.5 - 1
    # Each Cartesian component has a maximum rounding error of half an 8-bit step.
    if np.any(np.abs(np.linalg.norm(vectors, axis=2) - 1) > np.sqrt(3) / 255 + 1e-6):
        raise ValueError("source normal contains non-unit directions beyond 8-bit rounding tolerance")
    normal = load_png(directory / f"{directory.name}_n.png", ("RGB",), size)
    expected = source_normal.copy()
    if config["normal_green_flip"]:
        expected[:, :, 1] = 255 - expected[:, :, 1]
    compare("game / source normal", expected, normal)

    packed = load_png(directory / f"{directory.name}_s.png", ("RGB",), size)
    for channel, definition in enumerate(config["packing"]):
        values = source[definition.removeprefix("1-")]
        expected = 255 - values if definition.startswith("1-") else values
        compare(f"packed {'RGB'[channel]} / {definition}", expected, packed[:, :, channel])


def rebake(directory, atlas):
    if not atlas.is_file():
        raise ValueError(
            f"no cached atlas for {directory.name}. Run python assets/tools/build.py "
            f"--only {directory.name} --force before the rebake check"
        )
    sys.path.insert(0, str(ROOT / "src"))
    from bake_maps import bake

    with tempfile.TemporaryDirectory() as scratch:
        rebuilt = Path(scratch) / directory.name
        bake(atlas, rebuilt)
        expected_files = {f"src_maps/{name}.png" for name in (
            "basecolor", "normal", "metallic", "roughness", "ao", "height"
        )}
        expected_files.update(f"{directory.name}_{suffix}.png" for suffix in ("d", "n", "s"))
        generated = {p.relative_to(rebuilt).as_posix() for p in rebuilt.rglob("*.png")}
        if generated != expected_files:
            raise ValueError(f"rebake output inventory differs: {sorted(generated ^ expected_files)}")
        for relative in sorted(generated):
            with Image.open(rebuilt / relative) as expected, Image.open(directory / relative) as shipped:
                compare(relative, np.array(expected), np.array(shipped))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="+", type=Path, help="model output directories")
    parser.add_argument("--rebake", action="store_true", help="also compare against a fresh bake from the cached atlas")
    args = parser.parse_args()
    config = read(ROOT / "conventions.json")["texture"]
    catalog = {e["id"]: e for e in entries()}
    failed = False
    for directory in args.directories:
        try:
            entry = catalog[directory.name]
            size = config["fitted_size" if entry["group"] == "B" else "rigid_size"]
            audit(directory, size, config)
            if args.rebake:
                rebake(directory, ROOT / ".work" / directory.name / "atlas.npz")
        except (ValueError, KeyError, OSError) as error:
            failed = True
            print(f"{directory.name}: {error}", file=sys.stderr)
        else:
            print(f"{directory.name}: textures verified")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
