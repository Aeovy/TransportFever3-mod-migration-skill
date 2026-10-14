# CR200J Local Migration Case Study

First tested on 2026-10-04 on macOS with Transport Fever 3 Model Editor v13. Counts, editor results, and package sizes below describe revision 1 unless otherwise stated. The source was about 1.6 GB and the final directory about 1 GB. Use this case to recognize similar failures, not as a universal repair template. Original evidence lives in the source project's `docs/cr200j-migration.md`, `docs/validation/`, `docs/images/`, and `tools/`. Those project files are not required to understand or reuse this reference.

## Protection Helpers and UV Indices

The source contained 20 Lua 5.2 bytecode helper modules. Fourteen mesh descriptors used them to calculate UV-index offsets. The `.msh.blob` files remained ordinary inspectable mesh data.

Constants were reconstructed from verified contiguous little-endian uint32 index regions. Both offsets and descriptor counts here are measured in bytes; `indexByteCount` is not a count of index elements:

- One mesh class: `normalOffset = positionOffset + 2 × indexByteCount`, corresponding to `uvOffset = positionOffset + indexByteCount`.
- One advertisement/skinning layout: `uvOffset = tangentOffset + indexByteCount`, after checking actual ranges and vertex attributes.

The bytecode was neither executed nor decompiled. All index regions and upper bounds were checked individually, followed by texture inspection. The second rule is not a default else branch for unknown layouts. Other models require new proof of ordering, units, and attribute counts. This package did not contain genuinely encrypted unreadable geometry, so the case provides no evidence that such geometry can be migrated.

## Asset and Behavior Repairs

| Issue | Repair in this case | Reuse boundary |
| --- | --- | --- |
| `shuipai2.blob` had the wrong companion name | Added verified `shuipai2.msh.blob` | Confirm the same mesh; do not pair by approximate names |
| Missing second-class wheel path and reversed power-car LOD configuration | Repaired each level against correct sibling models | Verify actual nodes/meshes at every level |
| `2.tga` should reference `2_normal.tga` | Corrected advertisement normal reference | Do not infer all texture roles from names |
| Missing generic white lamp texture | Supplied a 16×16 white substitute | Disclosed substitute, not a replacement for real livery |
| Same-name DDS/TGA represented different liveries | Wrote TGA output as `*_from_tga.dds` and updated materials | Detect collisions before conversion |
| Wrong TGA-to-DDS orientation | Vertically flipped TGA in this toolchain | Did not flip existing DDS files |
| Invalid old group names/empty references | Used actual native ZE models or removed empty references | Preserved unrelated valid groups |
| Missing `CH_25K` and `CH_25K_SLM` sounds | Temporarily used native passenger-car audio | Did not claim complete custom-audio reproduction |
| Missing wheel nodes at the farthest LOD | Derived animation cutoff from the tree | Did not apply one cutoff to all vehicles |

Vehicle performance, availability years, and geometry were preserved. The four original formations actually contained 8, 11, 8, and 11 cars. Both named “12X” contained only 11 cars; no extra car was invented. Reversed power cars already had root rotations and were not flipped again.

Output filenames were lowercase and text was UTF-8 without BOM, but some legacy names still contained Chinese characters or spaces. The editor accepted them; strict publication compliance still requires explicit mapping and normalization. This case did not satisfy every publication requirement.

## Results and Limits

Final revision-1 assets: 12 native models, 120 mesh/binary pairs, 81 materials, 78 animations, 150 DDS textures, 48 UI TGA files, and 4 formations. The source package remained unchanged.

| Validation | Actual result |
| --- | --- |
| Dedicated static checks | Passed references, indices, animated LOD nodes, formations, and definitions |
| Full editor validation | Failed: all 12 checked; 2 dining cars passed, 10 exceeded farthest-LOD limits |
| Editor visual preview | Two power-car liveries and hard-sleeper door animation previewed; not all combinations |
| Game execution | Incomplete; the user subsequently prohibited opening the game, ending main-game attempts |
| Windows execution | Not run at this stage |
| ZIP | 617 entries, 135180361 bytes, all CRCs passed |

The 10 oversized models were 4 power cars at about 1.8 MB, 2 second-class cars at 847.6 KB, 2 soft sleepers at 291.5 KB, and 2 hard sleepers at 297.8 KB. The v13 farthest-LOD limit was 256 KB. Real distant-geometry simplification remained necessary; levels were not deleted to evade the limit.

Two local v13 observations: conversion output went into the current toolbar mod; Bulk Validation asserted `m_modelId < 0` with a model open but completed after restarting with no model loaded. Verify version and symptoms before reusing either observation.

The project's preparation, integration, and validation tools assume specific IDs, vehicle types, and counts. They are not general converters. The bundled inventory script provides general read-only checks without those fixed counts or a blanket ban on module imports.

## Later Windows Feedback and Opacity Repairs

The user subsequently tested on Windows and reported basic operation, but the whole body looked frosted and exposed the scene behind it. Game version, vehicle coverage, and save checks were not recorded. This is user evidence of basic loading and a visual defect, not full compatibility acceptance.

Many solid source parts already used transparent materials. The old integration script enabled sorting globally, putting bodies and wheelsets on the transparent sorting path. Inspection found power-car body alpha of 254–255 both before and after conversion, separate glass at 127, and passenger atlases mixing body and windows. The symptom could not be reduced to universally incorrect alpha conversion.

Revision 2 changed 34 almost-opaque materials to `PHYSICAL` / `PHYSICAL_NRML_MAP` with `map_albedo` + `albedoTex`; used cutout coverage and an unsorted path for 28 mixed body/window atlases; and retained 2 semitransparent glass materials. It changed 63 materials because one glass material already matched. Textures, geometry, and vehicle behavior were unchanged.

User screenshots after revision 2 still showed background through small body areas, so that revision did not establish resolution. Revision 3 changed six `*_body_albedo_opacity.mtl` materials to `PHYSICAL` / `PHYSICAL_NRML_MAP` and migrated bindings from `map_albedo_opacity` + `albedoOpacityTex` to `map_albedo` + `albedoTex`. Normal/MGA textures were preserved; separate glass stayed transparent and other mixed parts retained cutout. Target atlas alpha ranged from 125–255. Textures, geometry, UVs, and behavior were unchanged.

The user confirmed that revision 3 fully resolved the reported transparency in the Windows game. The final `cr200j_tf3_1.zip` had SHA-256 `6d6b8c8605bdf51dcb6dd3e25a4af3f83873940fd67fd040304677ff536963ca` and 617 CRC-verified entries. The agent did not launch the game. This is evidence for this CR200J asset combination, not a rule to make every `_body_` material opaque. Shared body/window alpha in other mods may require transparency; forcing opacity can seal glass. Inspect models, UVs, atlases, and target-game appearance. Splitting solid shells and glass in the source project is a more controlled general approach.

See the [official material documentation](https://wiki.transportfever3.com/doku.php?id=modding:general:resourcetypes:mtl) for transparency and coverage. Detailed project history was recorded in `docs/opacity-repair.md` and `docs/validation/opacity-repair-revision3.json`. These are project-local records, not files installed with the skill; use this reference's recorded results when reusing it.
