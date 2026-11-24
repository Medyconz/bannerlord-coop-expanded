"""Create labelled category proofs from the final PNGs."""
import argparse
import math

from PIL import Image, ImageDraw, ImageFont

from catalog import ROOT, entries, outputs


def sheet(category):
    items=[e for e in entries() if e["category"]==category]
    proof=[]
    for e in items:
        paths=outputs(e)
        path=paths[0] if e["group"]=="UI" else paths[5]
        if path.is_file():
            proof.append((e,path))
    if not proof:
        return
    tile=260; cols=min(4,len(proof))
    img=Image.new("RGB",(cols*tile,60+math.ceil(len(proof)/cols)*(tile+39)), "#292927")
    draw=ImageDraw.Draw(img)
    draw.text((14,15),category.replace("_"," ").title(),font=ImageFont.load_default(size=26),fill="#e0d5b8")
    for k,(e,path) in enumerate(proof):
        x=k%cols*tile; y=60+k//cols*(tile+39)
        with Image.open(path) as original:
            art=original.convert("RGBA")
            art.thumbnail((tile-8,tile-8),Image.Resampling.LANCZOS)
            pos=(x+(tile-art.width)//2,y+(tile-art.height)//2)
            img.paste(art,pos,art)
        draw.text((x+8,y+tile+4),e["name"],fill="#f1eee7",font=ImageFont.load_default(size=15))
    target=ROOT/"previews"/f"contact_{category}.png"
    target.parent.mkdir(exist_ok=True)
    img.save(target)


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--category")
    args=ap.parse_args()
    for category in ([args.category] if args.category else sorted({e["category"] for e in entries()})):
        sheet(category)
