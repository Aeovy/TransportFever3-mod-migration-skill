# Migration Troubleshooting

Choose a section by symptom. Confirm each diagnosis from source files or target-version logs. A repair formula from one package must not become a rule for every package.

## “Encrypted” Models or Unloadable Descriptors

Inspect headers and references. Distinguish readable `.mdl/.msh/.mtl`, standard `.msh.blob`, Lua bytecode helpers, and genuinely unparseable geometry. A binary blob is not evidence of encryption. If official tools can read the source, use their converter first. If real geometry is unreadable and no source is available, record the blocker and specify what the author must supply.

Reconstructing script-calculated offsets requires index type/endianness, each region's offset/count/size, unintended overlap, vertex-component counts, and every index bound. In-range UV indices can still point into the wrong region, so preview texture placement. Never fill an unknown layout with a guessed value just because it loads. See [CR200J](cr200j-case-study.md) for that case's proven layouts.

## Missing Models, Meshes, Sounds, or Normals

Check reference bases, namespaces, exact case, and physical extensions. Meshes normally need a descriptor and its `.msh.blob`; verify a same-named `.blob` candidate actually matches before copying it. Native resources may live in archives; inspect members and aliases instead of deciding they are missing solely through `Path.exists()`.

Check whether the old package omitted a dependent mod. Retain legitimate dependencies for `other_mod::/path` references. If the source is unavailable, use a compatible native substitute only when its purpose is clear and within scope, and disclose differences. Node names, file references, and UI localization keys are distinct identifiers and must not be normalized together.

## Swapped Liveries or Upside-Down Textures

Compare same-directory, same-name DDS and TGA source files. They may be different liveries rather than backups. Assign unique outputs such as `body.dds` and `body_from_tga.dds`, then update materials. Detect collisions before extension conversion or lowercasing, not after overwriting files.

TGA origin flags interact with game/export-tool UV conventions. Pillow already handles the origin flag during decoding; the CR200J TGA-to-DDS pipeline additionally needed a vertical flip to match TF3 DDS orientation. Existing DDS files were not flipped. For other toolchains, verify reference models, text, stripes, and UV islands. Normal-map green-channel inversion is a separate coordinate-system issue and must not be assumed necessary because an image was flipped.

## DDS Previews Work but the Editor Reports Format/Mipmap Errors

Choose compression by actual texture role and shader. For BC5 normals, verify UNORM/SNORM and normal encoding; for example, DXGI 83 is BC5 UNORM. Transparent assets must preserve alpha. Opaque assets can use an appropriate opaque format. MGA channel semantics must match the shader; consider inversion only when the source provides roughness and the target expects gloss.

A full ordinary 2D mip chain contains `floor(log2(max(width, height))) + 1` levels, including 1×1. Inspect magic, header size, FourCC/DX10, dimensions, mip count, and actual per-level payload size. An extension or top-level preview cannot prove valid encoding. The inventory script checks headers/counts only. Prefer official conversion/save; custom encoders require output comparison and target-editor validation.

## Blank/Misplaced Destinations or Vehicle Names on the Body

Distinguish service-type textures, dynamic station names, and vehicle names. E2/E5/E6/H5 scrolling textures leave blank station areas filled by `NEXT_STOP` in `labelList`. Deleting the list preserves the service type and removes destinations. Earlier advice to delete labels whenever display assets exist has been withdrawn.

Compare source/final label counts, native layout dimensions, body-node binding, and actual display meshes. See [Dynamic Destination Labels](destination-labels.md) for conversion, source-coordinate defects, and validation limits. A surviving display mesh or loadable file does not prove dynamic destinations work.

## CR400AF: Audio, Placeholder Textures, and Default-Map Errors Together

This migration exposed a combined symptom pattern: every WAV reported `44100 Hz` where `48000 Hz` was required; TF2 `.pkf` files failed extension checks; many vehicle textures became `2x2` with one mip; and materials repeatedly lacked `/res/textures/default_normal_map.dds` and `default_metal_gloss_ao.tga`. This commonly indicated placeholder DDS files copied from Model Editor staging alongside unchanged TF2 audio-container files, rather than damaged model geometry.

Repair and rebuild in this order:

1. Compare source DDS dimensions/headers with staged counterparts. Prefer real source textures when substantially larger with full mip chains. Deduplicate candidates by asset family plus normalized filename; staged placeholders must not overwrite liveries.
2. Inspect every final DDS for magic, dimensions, FourCC/DX10, actual payload length, and mip count. Ordinary 2D chains need `floor(log2(max(width, height))) + 1` levels and the editor's minimum dimensions. Do not change headers without sufficient payload. For opaque `map_cblend_dirt_rust`, use BC1/DXT1 when required by the current validator; choose normal, transparent, and MGA formats by their semantics.
3. Resample PCM WAV to `48000 Hz` before packaging and remove rejected `.pkf` files. Match `.snd.lua` filenames to output samples; do not disguise `.pkf` by renaming extensions.
4. Resolve package-root `/res/textures/...` separately from native `::/vehicle/shared/...` dependencies. Supply decodable missing-map fallbacks at package-root `res/textures/`, and remove obsolete `content/res/` or other leftover output trees so incorrect same-name resources are not repackaged.
5. Rerun editor validation. Offline, check no `.pkf`, all WAV at 48 kHz, valid target DDS dimensions/mips/formats, resolvable local MTL references, ZIP CRCs, and SHA-256. Mark editor, game, and Windows individually `not run` where applicable.

Put the repair in a repeatable build script rather than patching binaries in a single ZIP. When staging directories are reused, clean stale output at build start and include covers, default maps, and dependency families explicitly in the output inventory.

## Incorrect Glass, Doors/Windows, or Lamps

Compare source material roles, shader, alpha, two-sided settings, and sorting. Some CR200J transparent PHYS materials needed alpha and sorting, but setting `sorted=true` everywhere is wrong. Official conversion may preserve flags for legacy appearance; do not remove them solely because their names include legacy. A generic white fallback only substitutes a missing generic white lamp texture, not real livery, normals, or important masks.

For frosted solid bodies or background visibility, follow actual mesh references to the material. Compare source/final alpha, shader, map/sampler, sorting, and depth-write settings. When changing a solid surface to an opaque shader, also use `map_albedo` + `albedoTex`; changing only `type` leaves incompatible bindings. Retain required normals/MGA. `sorted` does not turn a transparent shader opaque. For mixed atlases, first determine whether glass has separate meshes/materials; do not blindly strip alpha or replace every shader. Test on the affected platform. See [Material Opacity](material-opacity.md) for diagnosis and the Windows-verified CR200J case.

## Wheel or Animation Errors at One LOD

Inspect converted node trees and animation references at each level rather than old mesh paths. Derive `skipFromLod` from the participating hierarchy; its zero-based index identifies the first excluded level. Do not hardcode one value for every model. When nodes are absent, establish expected behavior first, then preview wheels, doors, and inter-car connections after repair.

Oversized farthest-LOD meshes require simplified geometry, not a changed cutoff or skipped validation. Use the target version's threshold; CR200J's 256 KB limit is evidence specifically from v13.

## Conversion Writes to the Wrong Mod or Material Changes Stay Invisible

Verify the current toolbar mod and Tools Target Mod with one actual conversion. CR200J v13 wrote to the current mod; treat this as an observed compatibility issue, not universal behavior.

Cached resources may retain old materials. Confirm disk content and references first, then reopen the model. If still stale, save work and restart the editor once. Animation looping does not reload materials. Keep version/log evidence instead of repeatedly overwriting assets without diagnosis.

## Bulk Validation Assertion or Crash

CR200J v13 asserted `m_modelId < 0` with a model open. Restarting with no model loaded allowed bulk validation to finish, indicating a tool-state failure in that run. Read current logs and use this recovery only for matching symptoms. If a reasonable retry repeats the failure, record the tool limitation and continue independent offline checks. Do not retry indefinitely or count a crash as an asset pass.

## Works on macOS, Fails on Windows

Check target versions, dependency sources, exact filenames, ZIP paths/encoding, non-ASCII or spaced names, hardcoded local paths, and DLL/native-tool/bytecode requirements. A case-insensitive development filesystem can hide mistakes; retain exact resource matching even if both platforms are commonly case-insensitive. Distinguish passed path checks from actual Windows runtime success.

## Sources

- [Model Editor conversion and validation](https://wiki.transportfever3.com/doku.php?id=modding:tools:modeleditor)
- [Blender tools and DDS orientation](https://wiki.transportfever3.com/doku.php?id=modding:tools:external:blender)
- [Resource rules and paths](https://wiki.transportfever3.com/doku.php?id=modding:general:resourcetypes)

Case-specific repairs and v13 anomalies come from [local CR200J testing](cr200j-case-study.md), not universal official behavior.
