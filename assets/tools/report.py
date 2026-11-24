"""Regenerate the release summary from validated build records."""
from collections import Counter
from catalog import ROOT, entries, read


def generate():
    manifest=entries()
    report=read(ROOT/"asset_report.json",{})
    def record(e): return report.get(e["id"],{"status":"pending"})
    rows=["# Coop Expanded art catalogue","",
          "Original game art for the Coop Expanded modpack. The catalogue counts a projectile and its filled quiver as one entry. Each icon entry includes both resolutions.","",
          "| Category | Built | Missing reference | Other / pending |","|---|---:|---:|---:|"]
    for category in dict.fromkeys(e["category"] for e in manifest):
        c=Counter(record(e)["status"] for e in manifest if e["category"]==category)
        rows.append(f"| {category.replace('_',' ')} | {c['ok']} | {c['skipped_no_reference']} | {c.total()-c['ok']-c['skipped_no_reference']} |")
    rows+=["","## Skipped entries",""]
    for e in manifest:
        rec=record(e)
        if rec["status"] not in ("ok","pending"):
            rows.append(f"- \x60{e['id']}\x60 — {rec['reason']}")
    notes=read(ROOT/"src"/"review_notes.json",{})
    if notes:
        rows+=["","## Ten assets for in-game art review",""]
        rows += [f"- \x60{i}\x60 — {note}" for i,note in notes.items()]
    rows+=["","## Rebuild","",
           "Run from the repository root with Python 3.11+ and Blender 4.2+. The release workstation used Blender 5.2.2, Python 3.15.0, Pillow 13.0.0, NumPy 2.5.4 and SciPy 1.18.1. Set the BLENDER environment variable if the executable is outside PATH and the standard Windows install directory.","",
           "\x60\x60\x60sh","git lfs install","git lfs pull","python -m pip install numpy scipy Pillow",
           "python assets/tools/build.py --all","python assets/tools/build.py --all --force",
           "python assets/tools/build.py --only ce_sh_imperial_oval",
           "python assets/tools/build.py --category shields","python assets/tools/validate.py",
           "python assets/tools/contact_sheet.py","python assets/tools/report.py","\x60\x60\x60","",
           "For an independent round trip of the binary exports, run the following from PowerShell. The audit reimports the FBXs, checks LOD geometry and UV overlaps, and follows the embedded material links to the sidecar files.","",
           "\x60\x60\x60powershell",r'& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python-exit-code 1 --python assets/tools/audit_fbx.py',"\x60\x60\x60","",
           "For a source-to-packed channel comparison, pass one or more model directories to the texture audit.","",
           "\x60\x60\x60sh","python assets/tools/audit_textures.py assets/build/shields/ce_sh_imperial_oval","\x60\x60\x60","",
           "To repack the metallic, gloss and ambient-occlusion channels directly from saved source maps, run the following command.","",
           "\x60\x60\x60sh","python assets/tools/pack_textures.py assets/build/shields/ce_sh_imperial_oval","\x60\x60\x60","",
           "The cached build checks source fingerprints and file hashes. Use --force for a clean regeneration of matching entries. The build records geometry measurements per object and LOD in asset_report.json.","",
           "## Integration","",
           "The pack uses the orientation and grip conventions in conventions.json. Engine import, equipped-hand alignment, game-shader response and War Sails inventory presentation require a Bannerlord integration pass. No in-game results are claimed here.",
           "", "Place licensed local references only in the ignored assets/reference directory. Fitted entries require original modelling, skinning and pose review once the references are present. Unspecified item tiers are recorded as null.",""]
    (ROOT/"REPORT.md").write_text("\n".join(rows),encoding="utf8")


if __name__=="__main__":
    generate()
