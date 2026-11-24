# Coop Expanded art catalogue

Original game art for the Coop Expanded modpack. The catalogue counts a projectile and its filled quiver as one entry. Each icon entry includes both resolutions.

| Category | Built | Missing reference | Other / pending |
|---|---:|---:|---:|
| one handed swords | 8 | 0 | 0 |
| two handed swords | 4 | 0 | 0 |
| axes | 6 | 0 | 0 |
| maces hammers | 5 | 0 | 0 |
| polearms | 8 | 0 | 0 |
| daggers | 3 | 0 | 0 |
| thrown | 0 | 0 | 4 |
| ammunition | 0 | 0 | 4 |
| shields | 0 | 0 | 10 |
| trade goods | 0 | 0 | 12 |
| helmets | 0 | 0 | 16 |
| body armour | 0 | 0 | 14 |
| shoulders capes | 0 | 0 | 8 |
| gloves | 0 | 0 | 6 |
| boots | 0 | 0 | 6 |
| horse harness | 0 | 0 | 6 |
| bows crossbows | 0 | 0 | 6 |
| icons | 24 | 0 | 0 |
| branding | 9 | 0 | 0 |

## Skipped entries


## Rebuild

Run from the repository root with Python 3.11+ and Blender 4.2+. The release workstation used Blender 5.2.2. Set the BLENDER environment variable if the executable is outside PATH and the standard Windows install directory.

```sh
git lfs install
git lfs pull
python -m pip install numpy scipy Pillow
python assets/tools/build.py --all
python assets/tools/build.py --all --force
python assets/tools/build.py --only ce_sh_imperial_oval
python assets/tools/build.py --category shields
python assets/tools/validate.py
python assets/tools/contact_sheet.py
python assets/tools/report.py
```

To repack the metallic, gloss and ambient-occlusion channels directly from saved source maps, run the following command.

```sh
python assets/tools/pack_textures.py assets/build/shields/ce_sh_imperial_oval
```

The cached build checks source fingerprints and file hashes. Use --force for a clean regeneration of matching entries. The build records geometry measurements per object and LOD in asset_report.json.

## Integration

The pack uses the orientation and grip conventions in conventions.json. Engine import, equipped-hand alignment, game-shader response and War Sails inventory presentation require a Bannerlord integration pass. No in-game results are claimed here.

Place licensed local references only in the ignored assets/reference directory. Fitted entries require original modelling, skinning and pose review once the references are present. Unspecified item tiers are recorded as null.
