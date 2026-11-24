"""Repack engine textures from original linear data and sRGB base colour."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def pack(directory, config):
    directory = Path(directory)
    src = directory / "src_maps"
    ident = directory.name
    with Image.open(src / "basecolor.png") as image:
        image.save(directory / f"{ident}_d.png")
    normal = np.array(Image.open(src / "normal.png").convert("RGB"))
    if config["normal_green_flip"]:
        normal[:, :, 1] = 255 - normal[:, :, 1]
    Image.fromarray(normal).save(directory / f"{ident}_n.png")
    channels = []
    for spec in config["packing"]:
        channel = np.array(Image.open(src / (spec.removeprefix("1-") + ".png")).convert("L"))
        channels.append(255-channel if spec.startswith("1-") else channel)
    Image.fromarray(np.stack(channels, axis=-1)).save(directory / f"{ident}_s.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    pack(parser.parse_args().directory, json.loads((ROOT / "conventions.json").read_text(encoding="utf-8-sig"))["texture"])
