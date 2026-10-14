# Migration Workflow and Acceptance

Use this workflow for asset mods. For execution logic in `mod.lua`, runtime scripts, or external dependencies, also read [Script Migration](script-migration.md); for specific failures, read [Troubleshooting](troubleshooting.md). These steps define the work order; resource fields must follow the installed version's definitions.

## 1. Preserve the Source and Map Paths

Record the original mod ID, author, license, supported versions, `mod.lua` parameters/callbacks, resource types, and dependencies. Preserve license notices and assess local conversion separately from redistribution. Use the inventory script's `--hash` option when unchanged-source evidence is required, then compare source hashes after migration.

Keep three separate locations: the original package, a repair/conversion copy, and the final mod. Give the final mod an independent ID to avoid overwriting original or subscribed mods. Never batch-replace original game assets or the source package. Enumerate output paths before writing and detect collisions after case folding, Unicode NFC normalization, and extension conversion.

## 2. Use the Official Converter

TF2 commonly uses `mod.lua + res/`; TF3 uses `mod.json + content/`. Prefer the official Model Editor's TF2 conversion to produce native models, materials, and metadata. Current native models declare `version = 2`. Successful conversion still requires checking dependencies, nodes, formations, and display information.

Temporary layout used in the CR200J case:

```text
source_mod_id/
  mod.json                  # Temporary definition created with the current editor
  content/
    res/                    # Repaired copy of the source res directory
      models/model/vehicle/train/...

Bulk Convert prefix: source_mod_id::/res/models/model/vehicle/train/
```

This is a verified vehicle entry point, not a path for every mod. Follow the current editor's resolution rules. Convert one model and confirm source, output location, resource type, and target mod before bulk conversion. Do not feed native version-2 models back into TF2 conversion. Collect only native output and required assets into the final package; exclude the temporary `content/res/` tree.

Determine startup and user-data paths from the installation, configuration, and current official documentation. Do not assume another platform's or TF2's paths. Back up configuration before changing it. Same-ID copies in `staging_area` may override manual or subscribed installations; identify the active source.

## 3. Rebuild TF3 Definitions and References

Write `mod.json` for technical configuration, `_metadata/modinfo.json` for presentation, and `strings.json` when localization is needed. Preserve author and copyright information. Do not treat TF2 fields as the TF3 schema. Current constraints include lowercase letters, digits, and underscores in `modId`; revision starting at 1; display names up to 32 characters and summaries up to 100, without newlines; valid severity enums; and non-cosmetic classification for new runnable vehicles. Use official tags such as `Locomotive`, `Wagon`, and `Multiple Unit`, rather than inventing `Train`.

Migrate the cover to `_metadata/0.png` separately. Copying `image_00.*` or `workshop_preview.*` to the old location is insufficient. Preserve aspect ratio and author marks; the recommended size is 1920×1080. See [Mod Cover Migration](mod-cover.md).

Use UTF-8 without BOM. Official filename guidance uses `a-z`, digits, `_`, and `-`, avoiding spaces and non-ASCII characters. Preserve resource-specific extensions and official UI icon variants. Map legacy Chinese or space-containing filenames explicitly and update all file references. Engine acceptance does not prove publication compliance. Internal node names are outside filename normalization.

Resolve each reference according to its field and parser:

| Form | Meaning |
| --- | --- |
| `/path` | Root of the current mod's content |
| `::/path` | Native TF3 resource root |
| `other_mod_id::/path` | External mod resource; retain its real dependency |
| `tex/a.dds`, `::tex/a.dds` | Relative forms; use the owning field's base location |

Do not introduce `../` or machine-absolute paths. Native resources may be archived rather than loose files. Index resource aliases such as `.mu.lua → .mu`, `.snd.lua → .snd`, and `.trf.lua → .trf`. Strip Lua/Teal wrapper extensions only where the resource type defines that behavior, never for arbitrary Lua files.

## 4. Vehicles, Formations, and Textures

Compare capacity, speed, power, mass, availability years, and other semantic values with the source. Conversion may change units. Do not alter performance merely to silence validation messages.

Rail wheel references must use converted node names. Inspect each animated LOD for the required nodes. `transformatorConfig.skipFromLod` is the zero-based first excluded LOD; derive it from the actual tree. Use the valid `RAIL` driver category for rail vehicles only. Group/variant references must resolve to real models; clean up or explain empty and dangling references.

For fixed formations, compare each vehicle's count, order, model, and facing. Display names do not determine counts. A rear power car may already have a rotated root; flipping it again changes behavior. Document intentional formation changes separately.

Group textures by actual role before conversion: diffuse, normal, MGA, emissive, and transparent assets have different compression and color semantics. Prefer official import/save/conversion. Custom conversion must verify DDS headers, format, alpha, channels, and every mip payload. CR200J used BC5 normals, BC1 opaque textures, and BC3 transparent textures; choose formats from the current shader/editor contract rather than treating these as universal recipes. See [Troubleshooting](troubleshooting.md).

## 5. Layered Validation

1. **Static:** validate definitions, exact path case, local/native dependencies, mesh index bounds and layout, complete DDS data, animation nodes, and source-equivalent formations. For scripts, also check APIs, imports, parameters, and persistent state. Inventory results alone cannot prove all these checks passed.
2. **Editor:** validate every target model with the current editor and retain version/logs. Preview representative liveries, transparency, door/wheel animation, and LODs. Distinguish crashes, resource errors, and performance limits. If full validation has errors, record `failed` and separately state the successful load/preview coverage.
3. **Game:** within the user's permitted scope, actually load, enable, purchase, and run the mod during applicable years. Check script initialization, updates, events, save reloads, and parameter changes. Record uncompleted checks as `not run`.
4. **Windows:** confirm game/API/native-resource versions and actually test loading, purchase/run, and scripts. macOS editor and static path checks do not replace this step.

Reduce actual geometry/draw cost to optimize distant LODs and inspect the result. Do not hide failures by deleting distant levels or weakening log criteria. Use the target version's thresholds.

## 6. Packaging and Reporting

The ZIP must contain one mod root, with `mod.json` and `content/` directly underneath. Exclude temporary conversion trees, unused protection helpers, development logs, `.DS_Store`, `__MACOSX`, and symlinks. Preserve required legal scripts and dependencies; cleanup does not mean removing all Lua. Verify member paths, all CRCs, and SHA-256 after packaging.

Cross-platform review includes exact filename/reference matches, absence of local absolute paths, platform DLL/executable requirements, native-resource versions, and non-ASCII path compatibility. Pure assets may be shared; plugins and bytecode need independent platform verification.

Use the project's report format and include source/target versions, preserved/changed content, substitutes, evidence, unrun scope, remaining failures, and installation/next-validation steps. A test package may contain unresolved issues but must not be labeled fully passed or release-ready.

## Official Sources

Last checked: 2026-10-04. Web examples can lag the installation; verify current resources and APIs.

- [Model Editor: conversion, validation, textures, and staging](https://wiki.transportfever3.com/doku.php?id=modding:tools:modeleditor)
- [Resource types, paths, and naming](https://wiki.transportfever3.com/doku.php?id=modding:general:resourcetypes)
- [Mod definitions and directory priority](https://wiki.transportfever3.com/doku.php?id=modding:general:moddefinition)
- [Valid tags](https://wiki.transportfever3.com/doku.php?id=modding:general:modtags)
