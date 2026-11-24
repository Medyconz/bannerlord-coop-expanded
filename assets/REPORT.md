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
| thrown | 4 | 0 | 0 |
| ammunition | 4 | 0 | 0 |
| shields | 10 | 0 | 0 |
| trade goods | 12 | 0 | 0 |
| helmets | 0 | 16 | 0 |
| body armour | 0 | 14 | 0 |
| shoulders capes | 0 | 8 | 0 |
| gloves | 0 | 0 | 6 |
| boots | 0 | 0 | 6 |
| horse harness | 0 | 0 | 6 |
| bows crossbows | 0 | 0 | 6 |
| icons | 24 | 0 | 0 |
| branding | 9 | 0 | 0 |

## Skipped entries

- `ce_hm_imperial_ridge` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_imperial_officer` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_vlandic_great` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_vlandic_kettle` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_sturgian_conical` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_sturgian_masked` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_nord_crested` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_nord_fur_cap` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_battanian_bronze` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_battanian_leather` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_khuzait_lamellar` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_khuzait_fur_steel` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_aserai_turban` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_aserai_pointed` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_relic_crowned` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_hm_relic_wolf` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_imperial_lamellar` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_imperial_scale_cloak` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_vlandic_coat_of_plates` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_vlandic_surcoat_mail` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_sturgian_mail_fur` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_sturgian_scale` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_nord_ringmail_tunic` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_battanian_bronze_cuirass` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_battanian_plaid_leather` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_khuzait_lamellar_coat` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_khuzait_padded_deel` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_aserai_mail_robe` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_aserai_mirror_plate` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_ba_relic_warden_plate` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_sp_imperial_pteruges` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_sp_vlandic_spaulders` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_sp_sturgian_fur_mantle` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_sp_nord_wolf_pelt` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_sp_battanian_plaid_cloak` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_sp_khuzait_lamellar_shoulders` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_sp_aserai_desert_cloak` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx
- `ce_sp_relic_warden_pauldrons` — Missing human_skeleton.fbx, body_male.fbx, body_female.fbx

## Rebuild

Run from the repository root with Python 3.11+ and Blender 4.2+. The release workstation used Blender 5.2.2, Python 3.15.0, Pillow 13.0.0, NumPy 2.5.4 and SciPy 1.18.1. Set the BLENDER environment variable if the executable is outside PATH and the standard Windows install directory.

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

For an independent round trip of the binary exports, run the following from PowerShell. The audit reimports the FBXs, checks LOD geometry and UV overlaps, and follows the embedded material links to the sidecar files.

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python-exit-code 1 --python assets/tools/audit_fbx.py
```

For a source-to-packed channel comparison, pass one or more model directories to the texture audit.

```sh
python assets/tools/audit_textures.py assets/build/shields/ce_sh_imperial_oval
```

To repack the metallic, gloss and ambient-occlusion channels directly from saved source maps, run the following command.

```sh
python assets/tools/pack_textures.py assets/build/shields/ce_sh_imperial_oval
```

The cached build checks source fingerprints and file hashes. Use --force for a clean regeneration of matching entries. The build records geometry measurements per object and LOD in asset_report.json.

## Integration

The pack uses the orientation and grip conventions in conventions.json. Engine import, equipped-hand alignment, game-shader response and War Sails inventory presentation require a Bannerlord integration pass. No in-game results are claimed here.

Place licensed local references only in the ignored assets/reference directory. Fitted entries require original modelling, skinning and pose review once the references are present. Unspecified item tiers are recorded as null.
