"""Rasterize original surface definitions in each asset's unique UV layout."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

from materials import SURFACES

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from pack_textures import pack


def bake(source, output):
    data = np.load(source)
    cfg = json.loads((ROOT / "conventions.json").read_text(encoding="utf-8-sig"))["texture"]
    size = int(data["size"])
    uv = data["uvs"] * [size, -size] + [-.5, size-.5]
    canvas = Image.new("I", (size, size), -1)
    pen = ImageDraw.Draw(canvas)
    for i, tri in enumerate(uv):
        pen.polygon([tuple(p) for p in tri], fill=i)
    surface = np.array(canvas)
    y, x = np.nonzero(surface >= 0)
    index = surface[y, x]
    a,b,c = uv[index].transpose(1,0,2)
    p = np.stack((x,y),axis=1) - a
    u, v = b-a, c-a
    def det(a,b):
        return a[:,0]*b[:,1]-a[:,1]*b[:,0]
    denom = det(u,v)
    denom[abs(denom)<1e-10] = 1
    w1, w2 = np.clip(det(p,v)/denom,0,1), np.clip(det(u,p)/denom,0,1)
    weights = np.stack((np.maximum(0,1-w1-w2),w1,w2),axis=1)
    weights /= weights.sum(axis=1,keepdims=True)
    pos = np.einsum("ij,ijk->ik", weights, data["xyz"][index])
    occlusion = np.einsum("ij,ij->i",weights,data["ao"][index])
    mid = data["material"][index]
    rgb = np.zeros((len(x),3),np.uint8)
    rough = np.zeros(len(x),np.uint8)
    metal = np.zeros_like(rough)
    relief = np.zeros_like(rough)
    phase = int.from_bytes(hashlib.sha256(output.name.encode()).digest()[:2],"little")*.001
    for j, key in enumerate(data["keys"]):
        sel = mid == j
        if not sel.any():
            continue
        color,m,r,family = SURFACES[str(key)]
        swatch = np.frombuffer(bytes.fromhex(color),dtype=np.uint8).astype(float)
        xx,yy,zz = pos[sel].T
        wave = np.sin
        patina = (wave(37*xx+16*yy+phase)*wave(21*zz-12*yy)+.55*wave(83*zz+47*xx)*wave(71*yy-39*xx))/1.55
        grain = wave(540*xx+713*yy+6*wave(32*zz)+2*wave(55*xx))
        pores = wave(1467*xx+763*yy+559*zz)*wave(839*zz-991*yy+813*xx)
        weave = .5*(wave(910*(xx+.62*yy))*wave(55*zz)+wave(975*(zz+.4*yy))*wave(51*xx))
        if family == "metal":
            detail = 1.5*grain + 2.6*patina + .9*pores
        elif family in ("wood","horn"):
            detail = 15*grain + 4*wave(2.2*grain+41*zz) + 7*patina
        elif family in ("cloth","fur"):
            detail = 14*weave + 7*patina + 3*pores
        elif family in ("leather","paint"):
            detail = 8*patina + 5*pores + 2*grain
        else:
            detail = 7*patina+3*pores
        rgb[sel] = np.clip(swatch + detail[:,None],0,255)
        rough[sel] = np.clip(r*255 + 1.15*detail,0,255)
        metal[sel] = round(m*255)
        relief[sel] = np.clip(128 + detail*.88,0,255)
    dist, nearest = distance_transform_edt(surface<0,return_indices=True)
    pad = dist <= 2*cfg["uv_padding_at_1024"]*size/1024
    src = output / "src_maps"
    src.mkdir(parents=True,exist_ok=True)
    def field(vals, bg):
        arr = np.empty((size,size)+vals.shape[1:],dtype=np.uint8)
        arr[:] = bg
        arr[y,x] = vals
        arr[pad] = arr[nearest[0][pad],nearest[1][pad]]
        return arr
    def save(name, array):
        Image.fromarray(array).save(src / (name+".png"),compress_level=4)
    save("basecolor",field(rgb,[92,83,73]))
    save("metallic",field(metal,0))
    save("roughness",field(rough,160))
    save("ao",field(np.uint8(np.clip(occlusion,0,1)*255),255))
    height = field(relief,128)
    save("height",height)
    dy,dx = np.gradient(height.astype(float)/255)
    vec = np.stack((-dx*.9,dy*.9,np.ones_like(dx)),axis=-1)
    vec /= np.linalg.norm(vec,axis=-1,keepdims=True)
    save("normal",np.uint8(np.rint((vec+1)*127.5)))
    pack(output,cfg)


if __name__ == "__main__":
    bake(Path(sys.argv[1]),Path(sys.argv[2]))
