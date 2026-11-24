import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".work"


def read(path, default=None):
    if default is not None and not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False)+"\n",encoding="utf8")
    temporary.replace(path)


def entries():
    return read(ROOT/"manifest.json")["assets"]


def references(e, cfg):
    refs=cfg["reference_files"]
    return [name for name in refs.get(e["type"],refs["human"]) if not (ROOT/"reference"/name).is_file()]


def fingerprint(e, *, normalize_newlines=True):
    common = ["conventions.json"]
    if e["group"]=="UI":
        sources = sorted(p.relative_to(ROOT) for p in (ROOT/"src").glob("ui_*.py"))
    elif e["group"]=="A":
        types = {"shields":["shields.py","prop_shapes.py"],"trade_goods":["trade_goods.py","prop_shapes.py"]}
        sources = [Path("src")/s for s in types.get(e["category"],["weapons.py"])]
        common += ["src/build_scene.py","src/bake_maps.py","src/materials.py","tools/pack_textures.py","tools/render_preview.py"]
    else:
        sources = []
    h=hashlib.sha256(json.dumps(e,sort_keys=True).encode())
    for p in [*common,*sources]:
        source = (ROOT/p).read_bytes()
        # Git can check out text as either CRLF or LF. The raw mode is only
        # for recognizing a pre-normalization record in its original checkout.
        if normalize_newlines:
            source = source.replace(b"\r\n", b"\n")
        h.update(source)
    return h.hexdigest()


def outputs(e):
    i=e["id"]
    if e["group"]=="UI":
        if e["category"]=="icons":
            return [ROOT/"ui"/"icons"/f"{i[6:]}_{s}.png" for s in (128,64)]
        return [ROOT/"ui"/"branding"/(i.removeprefix("ce_brand_")+".png")]
    dest=ROOT/"build"/e["category"]/i
    names=[i+".fbx", i+".blend", i+"_d.png",i+"_n.png",i+"_s.png","preview.png"]
    maps=["basecolor","normal","metallic","roughness","ao","height"]
    return [dest/name for name in names]+[dest/"src_maps"/(name+".png") for name in maps]


def checksum(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()
